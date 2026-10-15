"""Two REAL network socket clients over localhost (not two simulated pieces on one board).
This does not certify public HTTPS/WSS or iOS/Android browser behavior.
"""
import asyncio
import json
import os
import statistics
import time
import websockets
from pathlib import Path

URL=os.environ.get('NMD_WS_URL','ws://127.0.0.1:3000/ws')
network_rx_bytes=0

async def next_type(ws,typ,timeout=8):
    async with asyncio.timeout(timeout):
        while True:
            global network_rx_bytes
            payload=await ws.recv()
            network_rx_bytes+=len(payload.encode('utf-8') if isinstance(payload,str) else payload)
            msg=json.loads(payload)
            if msg.get('type')==typ:return msg

async def send(ws,op,**data):
    await ws.send(json.dumps({'op':op,**data}))

async def run():
    async with websockets.connect(URL,max_size=2_000_000) as a, websockets.connect(URL,max_size=2_000_000) as b:
        await next_type(a,'hello');await next_type(b,'hello')
        await send(a,'create',name='Dome',hero='nyra',id='c1')
        owner=await next_type(a,'joined');sa=await next_type(a,'state')
        await send(b,'join',code=owner['code'],name='Friend',hero='vex',id='j1')
        guest=await next_type(b,'joined');sb=await next_type(b,'state')
        sa=await next_type(a,'state')
        assert owner['token']!=guest['token']
        assert {p['name'] for p in sa['players']}=={'Dome','Friend'}
        results={'scope':'localhost internal test; NOT external cellular','two_distinct_ws_clients':True,'same_room':owner['code'],'same_two_players':True,'reconnect_same_slot':False,'room_full_rejected':False,'wrong_token_rejected':False,'round_simulated':False,'rtt_ms':{},'battle':{},'frontend_fps':'not measured (browser blocked by administrator)','public_https_wss':'NOT TESTED'}
        async with websockets.connect(URL) as c:
            await next_type(c,'hello');await send(c,'join',code=owner['code'],name='Third',hero='bronn')
            error=await next_type(c,'error');results['room_full_rejected']='full' in error['message']
        async with websockets.connect(URL) as c:
            await next_type(c,'hello');await send(c,'resume',code=owner['code'],token='bad-token')
            error=await next_type(c,'error');results['wrong_token_rejected']='token' in error['message']
        rtts=[]
        for k in range(30):
            stamp=time.perf_counter()
            await send(a,'ping',sent=k)
            await next_type(a,'pong')
            rtts.append((time.perf_counter()-stamp)*1000)
            await asyncio.sleep(.07)
        sorted_rtt=sorted(rtts)
        results['rtt_ms']={'p50':round(statistics.median(sorted_rtt),2),'p95':round(sorted_rtt[int(len(sorted_rtt)*.95)-1],2),'jitter_stddev':round(statistics.pstdev(rtts),2),'samples':len(rtts)}
        # Each real socket purchases a distinct item, both mark ready, then watch shared fight state.
        await send(a,'buy',id='buy-a',index=0)
        await next_type(a,'ack');sa=await next_type(a,'state')
        await send(b,'buy',id='buy-b',index=0)
        await next_type(b,'ack');sb=await next_type(b,'state')
        await send(a,'ready',id='r-a')
        await next_type(a,'ack')
        await send(b,'ready',id='r-b')
        await next_type(b,'ack')
        state_b=await next_type(b,'state')
        # Battle was triggered and broadcast only after both ready.
        while state_b['phase']!='battle': state_b=await next_type(b,'state')
        snapshots=[];timestamp=[];tick_times=[];size_bytes=[];age_ms=[];start=time.perf_counter()
        for _ in range(18):
            new=await next_type(b,'state',timeout=5)
            if new['phase']=='battle':
                snapshots.append(new)
                timestamp.append(time.perf_counter())
                tick_times.append(new['tickMs'])
                size_bytes.append(len(json.dumps(new).encode('utf-8')))
                age_ms.append(max(0,(time.time()-new['serverTime'])*1000))
        results['round_simulated']=len(snapshots)>2 and snapshots[-1]['battle']['elapsed']>snapshots[0]['battle']['elapsed']
        intervals=[(timestamp[i]-timestamp[i-1])*1000 for i in range(1,len(timestamp))]
        results['battle']={'snapshot_interval_ms_p50':round(statistics.median(intervals),2),'snapshot_interval_ms_p95':round(sorted(intervals)[int(len(intervals)*.95)-1],2),'server_tick_ms_p50':round(statistics.median(tick_times),4),'server_tick_ms_p95':round(sorted(tick_times)[int(len(tick_times)*.95)-1],4),'snapshot_count':len(snapshots),'snapshot_age_ms_p50_loopback':round(statistics.median(age_ms),2),'snapshot_age_ms_p95_loopback':round(sorted(age_ms)[int(len(age_ms)*.95)-1],2),'approx_snapshot_bytes_per_second':round(sum(size_bytes)/(timestamp[-1]-timestamp[0]),2),'elapsed_game_seconds':round(snapshots[-1]['battle']['elapsed'],2)}
        # Reload/reconnect of the guest session happens on a distinct third socket while preserving seat.
        async with websockets.connect(URL) as c:
            await next_type(c,'hello');await send(c,'resume',code=guest['code'],token=guest['token'])
            newjoin=await next_type(c,'joined');rejoined=await next_type(c,'state')
            results['reconnect_same_slot']=newjoin['token']==guest['token'] and rejoined['you']==1 and len(rejoined['players'])==2
        results['bandwidth_bytes_per_player']='snapshot payload only; see approx_snapshot_bytes_per_second (not total transport)' 
        result_path=Path(__file__).resolve().parents[1]/'evidence'/'network-internal.json'
        result_path.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(results,indent=2))

if __name__=='__main__':asyncio.run(run())