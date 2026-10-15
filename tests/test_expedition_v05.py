"""Build 0.5 rules, original-content invariants and adversarial validation."""
import random
import pytest
from fastapi.testclient import TestClient
from app import app
from expedition import Run, CATALOG, SKILLS, MONSTERS, EVENTS, GameError, simulate


def test_expedition_web_asset_and_entry_link():
    with TestClient(app) as c:
        assert c.get('/health').json()['build']=='0.6.0'
        home=c.get('/').text
        assert 'href="/expedition"' in home
        page=c.get('/expedition')
        assert page.status_code==200
        assert '/static/expedition.js?v=0.6.0' in page.text
        js=c.get('/static/expedition.js')
        assert js.status_code==200 and 'action(' in js.text and 'showBattle' in js.text
        assert c.get('/expedition.py').status_code==404


def test_catalog_and_mechanics_have_real_data():
    assert len(CATALOG)>=88
    assert len(SKILLS)>=32
    assert len(MONSTERS)>=36
    assert len(EVENTS)>=28
    for item in CATALOG.values():
        assert item['size'] in (1,2,3)
        assert item['tier'] in range(4)
        assert 1<=item['cost']<=30

@pytest.mark.parametrize('seed',range(45))
def test_forced_monster_hunt_and_rival(seed):
    r=Run('Test','vex',seed=seed)
    r.hour=3
    choice=r.make_route()
    assert len(choice)==3
    assert all(x['type']=='monster' and x['title'] for x in choice)
    r.route=choice;r.pick(seed%3)
    assert r.phase=='encounter' and r.selected['type']=='monster'
    assert r.selected['title']==choice[seed%3]['title']
    r.hour=6;r.phase='route';r.route=r.make_route()
    assert len(r.route)==1 and r.route[0]['type']=='rival'


def test_bigger_board_and_stash_capacity():
    r=Run('hero','bronn');r.level=4
    assert r.board_limit==10
    uid=r.obtain('royal_ballista')
    r.equip(uid,7)
    assert r.board[7:10]==[uid]*3
    r.store(uid)
    assert all(x is None for x in r.board[7:10])
    r.level=1
    with pytest.raises(GameError):r.equip(uid,7)


def test_apprentice_discount_and_idempotence():
    with TestClient(app) as c:
        start=c.post('/api/expedition/start',json={'name':'Tester','hero':'cael'}).json()
        token=start['token'];state=start['state']
        index=next(i for i,v in enumerate(state['route']) if v['type']=='merchant')
        q={'token':token,'id':'choose-once-100','op':'choose','index':index}
        a=c.post('/api/expedition/action',json=q)
        assert a.status_code==200
        b=c.post('/api/expedition/action',json=q)
        assert b.json().get('duplicate') is True
        assert b.json()['state']['revision']==a.json()['state']['revision']
        assert c.post('/api/expedition/action',json={'token':'invalid','id':'fake-1299','op':'upgrade'}).status_code==400
        assert c.post('/api/expedition/action',json={'token':token,'id':'invalid-123','op':'buy','index':999}).status_code==400
        assert c.post('/api/expedition/action',headers={'origin':'https://example.com'},json={'token':token,'id':'buy-123','op':'buy','index':0}).status_code==400


def test_skill_commerce_and_economy():
    r=Run('Trader','nyra',seed=333);r.skills=['broker','salvager','artful','deep_pockets'];r.gold=100
    r.phase='merchant';r.offers=['flintlock'];before=r.gold
    r.action('buy',{'index':0})
    assert before-r.gold==CATALOG['flintlock']['cost']-1
    uid=r.stash[0];before=r.gold
    r.action('sell',{'uid':uid})
    assert r.gold-before>=3
    t=r.obtain('copper_watch');r.phase='trainer';before=r.gold
    r.action('enchant',{'uid':t,'effect':'Fiery'})
    assert before-r.gold==6
    r.phase='route';r.day=2;r.hour=6;before=r.gold;r.advance()
    assert r.gold-before==13

@pytest.mark.parametrize('choice',['treasure','vitality','arcana','relic','skill','forge','gamble'])
def test_event_actions_have_distinct_server_effects(choice):
    r=Run('Explorer','nyra',seed=5)
    r.phase='event';r.offers=[choice]
    r.action('event',{'choice':choice})
    assert r.phase=='route' and r.hour==2
    assert r.history[0].startswith('Encounter reward:')
    assert r.max_health>=80
    assert r.gold>=0

@pytest.mark.parametrize('key',list(CATALOG))
def test_every_catalog_item_standalone_simulates(key):
    r=Run('Item Tester','vex',seed=100)
    item={'key':key,'tier':CATALOG[key]['tier'],'enchant':None,'uid':'test'}
    result=simulate('vex',[item],400,[],'bronn',[{'key':'flintlock','tier':0,'uid':'enemy','enchant':None}],360,[],random.Random(1))
    assert result['victor'] in (0,1)
    assert 0<result['elapsed']<=38
    assert all(0<=f['hp']<=f['maxHp'] for f in result['fighters'])


def test_untrusted_item_index_and_overflow_rejected():
    r=Run('Validator','bronn')
    with pytest.raises(GameError):r.action('choose',{'index':True})
    with pytest.raises(GameError):r.action('equip',{'uid':'unknown','slot':0})
    r.phase='trainer';uid=next(iter(r.inventory))
    with pytest.raises(GameError):r.action('enchant',{'uid':uid,'effect':'cheat'})
    r.phase='event';r.offers=['treasure']
    with pytest.raises(GameError):r.action('event',{'choice':'admin'})