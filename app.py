"""Night Market Duel: free single-process WebSocket game server.
Run: python -m uvicorn app:app --host 127.0.0.1 --port 3000
"""
import asyncio
import json
import logging
import os
import time
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from game import GameError, HEROES, ITEMS, BOONS, Player, Room, code, valid_hero, valid_name, RECONNECT_SECONDS
import secrets

ROOT = Path(__file__).parent
rooms: dict[str, Room] = {}
peers: dict[str, dict[str, WebSocket]] = {}
logger = logging.getLogger('night_market')

async def safe_send(ws, payload):
    try:
        await asyncio.wait_for(ws.send_json(payload), timeout=0.35)
        return True
    except (Exception):
        return False

async def broadcast(room):
    current=peers.get(room.code,{})
    if not current: return
    packets=[]
    for token,ws in list(current.items()):
        try:
            packets.append((token,ws,room.snapshot(token)))
        except GameError: continue
    results=await asyncio.gather(*(safe_send(ws,payload) for token,ws,payload in packets),return_exceptions=True)
    for (token,ws,_), ok in zip(packets,results):
        if ok is not True and current.get(token) is ws:
            current.pop(token,None)
            with suppress(Exception): await ws.close(code=1011)

async def game_loop():
    loop=asyncio.get_running_loop()
    last=loop.time()
    tick=0
    while True:
        await asyncio.sleep(.1)
        now=loop.time()
        dt=max(.01,min(.18,now-last)); last=now
        tick+=1
        for room in list(rooms.values()):
            if room.phase=='battle':
                was_end=room.update_battle(dt)
                if was_end:
                    await broadcast(room)
                    asyncio.create_task(next_round_after(room,3.0))
            for p in room.players:
                if p.bot: continue
                if p.connected and p.disconnected_at is not None: p.disconnected_at=None
                if not p.connected and p.disconnected_at is not None and now-p.disconnected_at>RECONNECT_SECONDS:
                    # Old seats do not persist forever: claim the remaining human player as winner.
                    p.disconnected_at=None
                    if room.phase in ('battle','shop','intermission'):
                        room.phase='finished'; room.winner=1-room.players.index(p)
                        room.events.appendleft(f'{p.name} forfeited after disconnect')
                        await broadcast(room)
                    elif room.phase=='lobby':
                        rooms.pop(room.code,None); peers.pop(room.code,None)
            if tick%2 == 0 and room.phase=='battle': await broadcast(room)
            if now-room.created>4*3600 and not peers.get(room.code):
                rooms.pop(room.code,None); peers.pop(room.code,None)

async def next_round_after(room,seconds):
    await asyncio.sleep(seconds)
    if rooms.get(room.code) is room and room.phase=='intermission':
        room.advance_round()
        await broadcast(room)

@asynccontextmanager
async def lifespan(app):
    task=asyncio.create_task(game_loop())
    try: yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError): await task

app=FastAPI(title='Night Market Duel',docs_url=None,redoc_url=None,lifespan=lifespan)
app.mount('/static',StaticFiles(directory=ROOT/'static'),name='static')

@app.get('/')
async def index():
    return FileResponse(ROOT/'static'/'index.html',headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})

@app.get('/health')
async def health():
    return JSONResponse({'ok':True,'rooms':len(rooms),'build':'0.6.0','mode':'hosted' if os.environ.get('RENDER') else 'local'},headers={'Cache-Control':'no-store'})

@app.websocket('/ws')
async def websocket_endpoint(ws:WebSocket):
    origin=ws.headers.get('origin')
    host=ws.headers.get('host','').split(':')[0].lower()
    if origin:
        parsed=urlparse(origin)
        if parsed.hostname is None or parsed.hostname.lower()!=host:
            await ws.close(code=1008,reason='Origin not allowed')
            return
    await ws.accept()
    room=None; player=None
    try:
        await safe_send(ws,dict(type='hello',heroes=HEROES,items=ITEMS,boons=BOONS,build='0.5.0'))
        count=0; bucket=time.monotonic()
        while True:
            data=await ws.receive_text()
            if len(data)>2048:
                await safe_send(ws,{'type':'error','message':'Message too large.'});continue
            now=time.monotonic()
            if now-bucket>2: count=0; bucket=now
            count+=1
            if count>35:
                await safe_send(ws,{'type':'error','message':'Rate limit exceeded.'});continue
            msg=None
            try:
                msg=json.loads(data)
                if not isinstance(msg,dict): raise GameError('Invalid request.')
                op=msg.get('op'); reqid=msg.get('id')
                if not isinstance(op,str): raise GameError('Invalid action.')
                if op=='ping':
                    await safe_send(ws,{'type':'pong','sent':msg.get('sent'),'serverTime':time.time()})
                    continue
                if op in ('create','join','resume'):
                    if player is not None: raise GameError('Already joined a room on this connection.')
                    room_code=''.join(str(msg.get('code','')).upper().split())
                    if op=='create':
                        if len(rooms)>=100: raise GameError('Server room limit reached.')
                        player=Player(valid_name(msg.get('name')),secrets.token_urlsafe(32), valid_hero(msg.get('hero')))
                        key=code()
                        while key in rooms: key=code()
                        room=Room(key,player,bot=msg.get('bot') is True)
                        rooms[room.code]=room
                    else:
                        room=rooms.get(room_code)
                        if not room: raise GameError('Room not found or has expired.')
                        if op=='resume':
                            player=room.find(msg.get('token',''))
                            if player.disconnected_at is None and player.connected and player.token in peers.get(room.code,{}):
                                # A reconnect may replace an old connection, but never creates a new player.
                                previous=peers[room.code][player.token]
                                if previous is not ws:
                                    await safe_send(previous,{'type':'error','message':'Session opened in another tab.'})
                                    with suppress(Exception): await previous.close(code=1000)
                            if room.phase=='finished' and room.winner is not None and player.disconnected_at is None and not player.connected:
                                raise GameError('Reconnect window expired.')
                        else:
                            if not (len(room_code)==5): raise GameError('Enter a five-character room code.')
                            player=room.add_player(msg.get('name'),msg.get('hero'))
                    player.connected=True;player.disconnected_at=None;player.last_seen=now
                    peers.setdefault(room.code,{})[player.token]=ws
                    await safe_send(ws,{'type':'joined','code':room.code,'token':player.token})
                    await broadcast(room)
                    continue
                if player is None or room is None: raise GameError('Create or join a room first.')
                if peers.get(room.code,{}).get(player.token) is not ws:
                    raise GameError('Session is not active.')
                if room.find(player.token) is not player:
                    raise GameError('Invalid session.')
                player.last_seen=now
                if op=='leave':
                    if room.phase=='lobby':
                        rooms.pop(room.code,None)
                    elif room.phase!='finished':
                        room.phase='finished';room.winner=1-room.players.index(player) if len(room.players)==2 else None
                        room.events.appendleft(f'{player.name} left the duel')
                    await safe_send(ws,{'type':'ack','id':reqid,'ok':True})
                    await broadcast(room)
                    await ws.close(code=1000)
                    break
                if reqid is None or not isinstance(reqid,str) or len(reqid)>64:
                    raise GameError('Missing action ID.')
                if reqid in player.seen_actions:
                    await safe_send(ws,{'type':'ack','id':reqid,'ok':True,'duplicate':True})
                    continue
                room.act(player,op,msg)
                player.seen_actions[reqid]=True
                if len(player.seen_actions)>80:
                    player.seen_actions.pop(next(iter(player.seen_actions)))
                await safe_send(ws,{'type':'ack','id':reqid,'ok':True})
                await broadcast(room)
            except (GameError,ValueError,TypeError,KeyError) as e:
                await safe_send(ws,{'type':'error','id':msg.get('id') if isinstance(msg,dict) else None,'message':str(e)})
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning('ws error: %s', e)
    finally:
        if player is not None and room is not None:
            conn=peers.get(room.code,{})
            if conn.get(player.token) is ws:
                conn.pop(player.token,None)
                player.connected=False
                player.disconnected_at=time.monotonic()
                await broadcast(room)

# Expedition is an independent game mode. The existing 1v1 protocol is preserved.
from pydantic import BaseModel, Field
from fastapi import Request
from expedition import Run, CATALOG, SKILLS, BOARD_WIDTH, STASH_WIDTH, DAY_HOURS

expeditions: dict[str, Run] = {}

class ExpedStart(BaseModel):
    name: str
    hero: str

class ExpedRequest(BaseModel):
    token: str = Field(max_length=128)
    op: str | None = Field(default=None, max_length=30)
    id: str | None = Field(default=None, max_length=64)
    index: int | None = None
    uid: str | None = Field(default=None, max_length=32)
    slot: int | None = None
    effect: str | None = Field(default=None, max_length=32)
    choice: str | None = Field(default=None, max_length=32)


def same_origin(req:Request):
    origin=req.headers.get('origin')
    if origin:
        parsed=urlparse(origin)
        if not parsed.hostname or parsed.hostname.lower()!=req.url.hostname.lower():
            raise GameError('Origin not allowed.')

@app.get('/expedition')
async def expedition_page():
    return FileResponse(ROOT/'static'/'expedition.html',headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})

@app.post('/api/expedition/start')
async def expedition_start(req:Request, payload:ExpedStart):
    try:
        same_origin(req)
        now=time.monotonic()
        # Clean old independent sessions, never touch room-based multiplayer.
        for k,v in list(expeditions.items()):
            if now-v.last_active>3*3600:expeditions.pop(k,None)
        if len(expeditions)>=400:raise GameError('Expedition server is busy. Try again shortly.')
        run=Run(payload.name,payload.hero)
        expeditions[run.token]=run
        return JSONResponse({'token':run.token,'state':run.public()},headers={'Cache-Control':'no-store'})
    except GameError as exc:
        return JSONResponse({'ok':False,'error':str(exc)},status_code=400)

@app.post('/api/expedition/state')
async def expedition_state(req:Request, payload:ExpedRequest):
    try:
        same_origin(req)
        run=expeditions.get(payload.token)
        if not run:raise GameError('Session expired. Start a new expedition.')
        return JSONResponse({'state':run.public()},headers={'Cache-Control':'no-store'})
    except GameError as exc:
        return JSONResponse({'ok':False,'error':str(exc)},status_code=400)

@app.post('/api/expedition/action')
async def expedition_action(req:Request, payload:ExpedRequest):
    try:
        same_origin(req)
        run=expeditions.get(payload.token)
        if not run:raise GameError('Session expired. Start a new expedition.')
        if not payload.id or len(payload.id)<6:raise GameError('Missing action ID.')
        if payload.id in run.seen:
            return JSONResponse({'state':run.public(),'duplicate':True,'result':run.seen[payload.id]},headers={'Cache-Control':'no-store'})
        if not payload.op:raise GameError('Missing action.')
        result=run.action(payload.op,payload.model_dump(exclude_none=True))
        run.seen[payload.id]=result
        if len(run.seen)>150:run.seen.pop(next(iter(run.seen)))
        return JSONResponse({'state':run.public(),'result':result},headers={'Cache-Control':'no-store'})
    except GameError as exc:
        return JSONResponse({'ok':False,'error':str(exc)},status_code=400,headers={'Cache-Control':'no-store'})