"""Public-host end-to-end networking probe from an independent runner.
This intentionally does not claim to be a cellular device test.
"""
import asyncio
import json
import os
import ssl
import statistics
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse
import websockets

BASE = os.environ.get('NMD_PUBLIC_BASE', 'https://night-market-duel-dome.onrender.com').rstrip('/')
WS = 'wss://' + urlparse(BASE).netloc + '/ws'
EVIDENCE = Path(__file__).resolve().parent.parent / 'evidence'
EVIDENCE.mkdir(exist_ok=True)
RX = 0

async def receive_type(ws, typ, timeout=15):
    global RX
    deadline = asyncio.get_running_loop().time() + timeout
    while True:
        remain = deadline - asyncio.get_running_loop().time()
        if remain <= 0: raise TimeoutError(f'No {typ} message from server in {timeout}s')
        raw = await asyncio.wait_for(ws.recv(), remain)
        RX += len(raw.encode() if isinstance(raw, str) else raw)
        obj = json.loads(raw)
        if obj.get('type') == 'error':
            raise RuntimeError(f'Server error while awaiting {typ}: {obj}')
        if obj.get('type') == typ: return obj

async def transmit(ws, op, **rest):
    await ws.send(json.dumps(dict(op=op, **rest)))

async def main():
    assert urlparse(BASE).scheme == 'https', BASE
    results = dict(base_url=BASE, websocket_url=WS, test_type='Public HTTPS/WSS from independent CI runner, NOT a 4G/5G device', passed=False)
    for path in ('/', '/static/app.js', '/static/style.css', '/static/art/vex.svg', '/health'):
        with urllib.request.urlopen(BASE+path, timeout=30, context=ssl.create_default_context()) as res:
            body = res.read()
            assert res.status == 200 and len(body) > 10, (path,res.status,len(body))
            if path == '/health':
                assert json.loads(body).get('ok') is True
        results.setdefault('http_ok', []).append(path)
    timings=[]
    async with websockets.connect(WS, max_size=2_000_000, open_timeout=20) as p1, websockets.connect(WS, max_size=2_000_000, open_timeout=20) as p2:
        await receive_type(p1,'hello');await receive_type(p2,'hello')
        await transmit(p1,'create',name='Remote CI A',hero='nyra',id='create-ci')
        owner=await receive_type(p1,'joined');s1=await receive_type(p1,'state')
        await transmit(p2,'join',code=owner['code'],name='Remote CI B',hero='vex',id='join-ci')
        guest=await receive_type(p2,'joined');s2=await receive_type(p2,'state')
        s1=await receive_type(p1,'state')
        assert owner['token']!=guest['token']
        assert len(s1['players'])==len(s2['players'])==2
        assert {x['name'] for x in s1['players']} == {'Remote CI A','Remote CI B'}
        assert s1['phase']==s2['phase']=='shop'
        results['separate_player_sessions']=True
        results['shared_room_code']=owner['code']
        async with websockets.connect(WS, open_timeout=20) as intruder:
            await receive_type(intruder,'hello')
            await transmit(intruder,'join',code=owner['code'],name='third',hero='cael',id='third')
            over=json.loads(await intruder.recv())
            assert over.get('type')=='error' and 'full' in over['message'].lower(),over
            await transmit(intruder,'resume',code=owner['code'],token='invalid')
            invalid=json.loads(await intruder.recv())
            assert invalid.get('type')=='error' and 'token' in invalid['message'].lower(),invalid
        results['room_full_rejected']=True
        results['bad_token_rejected']=True
        for n in range(20):
            started=time.perf_counter()
            await transmit(p1,'ping',sent=n)
            got=await receive_type(p1,'pong')
            assert got['sent']==n
            timings.append((time.perf_counter()-started)*1000)
            await asyncio.sleep(.05)
        results['rtt_ms']={'p50':round(statistics.median(timings),2),'p95':round(sorted(timings)[int(len(timings)*.95)-1],2),'jitter_stddev':round(statistics.pstdev(timings),2),'n':len(timings)}
        await transmit(p1,'buy',index=0,id='public-buy')
        a_ack=await receive_type(p1,'ack');a_s=await receive_type(p1,'state')
        assert a_ack.get('ok') is True
        oldgold=a_s['players'][0]['gold']
        await transmit(p1,'buy',index=0,id='public-buy')
        duplicate=await receive_type(p1,'ack')
        assert duplicate.get('duplicate') is True
        await transmit(p1,'ready',id='ready-a')
        assert (await receive_type(p1,'ack'))['ok']
        await transmit(p2,'ready',id='ready-b')
        assert (await receive_type(p2,'ack'))['ok']
        battle=await receive_type(p2,'state')
        for _ in range(20):
            if battle['phase']=='battle':break
            battle=await receive_type(p2,'state')
        assert battle['phase']=='battle'
        results['battle_started_on_both_ready']=True
        snapshots=[];stamps=[];tick=[];sizes=[]
        for _ in range(12):
            x=await receive_type(p2,'state')
            if x['phase']!='battle':continue
            snapshots.append(x);stamps.append(time.perf_counter());tick.append(x['tickMs']);sizes.append(len(json.dumps(x).encode()))
        assert len(snapshots)>=5
        assert snapshots[-1]['battle']['elapsed']>snapshots[0]['battle']['elapsed']
        results['server_authoritative_battle']=True
        intervals=[(stamps[k]-stamps[k-1])*1000 for k in range(1,len(stamps))]
        results['snapshots']={'interval_ms_p50':round(statistics.median(intervals),2),'tick_ms_p95':round(sorted(tick)[int(len(tick)*.95)-1],4),'bytes_per_second_per_client':round(sum(sizes)/(stamps[-1]-stamps[0]),1)}
        async with websockets.connect(WS,open_timeout=20) as resumed:
            await receive_type(resumed,'hello')
            await transmit(resumed,'resume',code=owner['code'],token=owner['token'])
            same=await receive_type(resumed,'joined');joined_state=await receive_type(resumed,'state')
            assert same['token']==owner['token'] and joined_state['you']==0 and len(joined_state['players'])==2
        results['resume_same_seat']=True
        results['action_dedupe']=True
        results['sample_rx_bytes']=RX
        results['passed']=True
    (EVIDENCE/'network-public.json').write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(results,indent=2))

if __name__=='__main__':asyncio.run(main())