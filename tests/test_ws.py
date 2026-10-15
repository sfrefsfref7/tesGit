import pytest
from fastapi.testclient import TestClient
from app import app, rooms, peers

@pytest.fixture
def client():
    rooms.clear();peers.clear()
    with TestClient(app) as c: yield c
    rooms.clear();peers.clear()

def init(ws):
    msg=ws.receive_json()
    assert msg['type']=='hello'
    assert msg['items']

def create(ws,name='Dome',hero='nyra',bot=False):
    ws.send_json({'op':'create','name':name,'hero':hero,'bot':bot,'id':'create'})
    res=ws.receive_json();assert res['type']=='joined'
    state=ws.receive_json();assert state['type']=='state'
    return res,state

def test_create_join_two_distinct_sessions(client):
    with client.websocket_connect('/ws') as a:
        init(a)
        owner,s1=create(a)
        with client.websocket_connect('/ws') as b:
            init(b)
            b.send_json({'op':'join','name':'Friend','hero':'vex','code':owner['code'],'id':'join'})
            joined=b.receive_json();s2=b.receive_json();update_a=a.receive_json()
            assert joined['type']=='joined' and joined['token']!=owner['token']
            assert s2['phase']=='shop' and update_a['phase']=='shop'
            assert len(s2['players'])==2
            assert {p['name'] for p in s2['players']}=={'Dome','Friend'}
            b.send_json({'op':'join','name':'Hacker','hero':'vex','code':owner['code']})
            err=b.receive_json()
            assert err['type']=='error' and 'Already joined' in err['message']
            assert len(rooms[owner['code']].players)==2

def test_room_full_and_invalid_token(client):
    with client.websocket_connect('/ws') as a:
        init(a);r,_=create(a)
        with client.websocket_connect('/ws') as b:
            init(b);b.send_json({'op':'join','code':r['code'],'name':'B','hero':'vex'})
            assert b.receive_json()['type']=='joined';b.receive_json();a.receive_json()
            with client.websocket_connect('/ws') as c:
                init(c);c.send_json({'op':'join','code':r['code'],'name':'C','hero':'cael'})
                err=c.receive_json(); assert err['type']=='error' and 'full' in err['message']
            with client.websocket_connect('/ws') as hacker:
                init(hacker);hacker.send_json({'op':'resume','code':r['code'],'token':'wrong'})
                err=hacker.receive_json();assert err['type']=='error' and 'token' in err['message']

def test_idempotent_buy(client):
    with client.websocket_connect('/ws') as a:
        init(a);joined,s=create(a,bot=True)
        first=s['players'][0]
        a.send_json({'op':'buy','id':'buy-01','index':0})
        ack=a.receive_json();state=a.receive_json()
        assert ack['type']=='ack' and ack['ok']
        gold=state['players'][0]['gold'];board=state['players'][0]['board']
        a.send_json({'op':'buy','id':'buy-01','index':0})
        again=a.receive_json()
        assert again['duplicate'] is True
        assert rooms[joined['code']].players[0].gold==gold
        assert rooms[joined['code']].players[0].board==board

def test_reconnect_reuses_same_seat(client):
    with client.websocket_connect('/ws') as a:
        init(a);joined,s=create(a,bot=True)
        token=joined['token'];code=joined['code']
    with client.websocket_connect('/ws') as second:
        init(second)
        second.send_json({'op':'resume','code':code,'token':token})
        res=second.receive_json();current=second.receive_json()
        assert res['type']=='joined' and res['token']==token
        assert current['you']==0 and len(current['players'])==2
        assert len(rooms[code].players)==2

def test_disallow_origin_mismatch(client):
    with pytest.raises(Exception):
        with client.websocket_connect('/ws',headers={'origin':'https://evil.example','host':'testserver'}) as ws:
            ws.receive_json()

def test_leave_releases_socket_and_finishes_room(client):
    with client.websocket_connect('/ws') as a:
        init(a)
        joined,_=create(a,bot=True)
        a.send_json({'op':'leave','id':'exit'})
        ack=a.receive_json()
        assert ack['type']=='ack' and ack['ok']
        message=a.receive_json()
        assert message['type']=='state' and message['phase']=='finished'
        from starlette.websockets import WebSocketDisconnect
        with pytest.raises(WebSocketDisconnect):
            a.receive_json()
    assert rooms[joined['code']].players[0].connected is False

def test_invalid_json_does_not_kill_connection(client):
    with client.websocket_connect('/ws') as ws:
        init(ws)
        ws.send_text('{definitely not json')
        err=ws.receive_json()
        assert err['type']=='error'
        ws.send_json({'op':'ping','sent':77})
        pong=ws.receive_json()
        assert pong['type']=='pong' and pong['sent']==77


def test_missing_action_id_does_not_change_gold(client):
    with client.websocket_connect('/ws') as ws:
        init(ws)
        r, initial=create(ws,bot=True)
        ws.send_json({'op':'buy','index':0})
        err=ws.receive_json()
        assert err['type']=='error'
        assert rooms[r['code']].players[0].gold==initial['players'][0]['gold']

def test_action_before_session_is_rejected(client):
    with client.websocket_connect('/ws') as a:
        init(a)
        a.send_json({'op':'buy','index':0,'id':'x'})
        err=a.receive_json()
        assert err['type']=='error' and 'Create or join' in err['message']

def test_invalid_slot_rejected_over_socket(client):
    with client.websocket_connect('/ws') as a:
        init(a);create(a,bot=True)
        a.send_json({'op':'sell','index':999,'id':'evil'})
        err=a.receive_json()
        assert err['type']=='error' and err['id']=='evil'

def test_ghost_disconnection_expires_after_grace_period(client):
    import time
    with client.websocket_connect('/ws') as a:
        init(a);joined,_=create(a,bot=True)
    player=rooms[joined['code']].players[0]
    player.disconnected_at=time.monotonic()-31
    time.sleep(.23)
    assert rooms[joined['code']].phase=='finished'
    with client.websocket_connect('/ws') as a:
        init(a)
        a.send_json({'op':'resume','code':joined['code'],'token':joined['token']})
        err=a.receive_json()
        assert err['type']=='error' and 'expired' in err['message']