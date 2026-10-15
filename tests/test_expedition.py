import random
import pytest
from fastapi.testclient import TestClient
from expedition import Run, CATALOG, SKILLS, BOARD_WIDTH, STASH_WIDTH, simulate, ENCHANTS, WIN_TARGET, GameError
from app import app


def run(seed=12,hero='vex'):
    return Run('Tester',hero=hero,seed=seed)


def test_catalog_valid_and_original():
    assert len(CATALOG)>=85
    assert len(SKILLS)>=12
    assert len(set(CATALOG))==len(CATALOG)
    assert all(1<=x['size']<=3 and x['cooldown']>0 and x['cost']>0 for x in CATALOG.values())
    assert all(x['type'] in {'damage','heal','cleanse','shield','haste','poison','burn','leech','thorns','slow','shatter','execute','rupture','crit','regen','freeze','charge'} for x in CATALOG.values())

@pytest.mark.parametrize('hero',['vex','nyra','bronn','cael'])
def test_run_initial_hero_state(hero):
    r=run(hero=hero)
    assert len(r.board)==BOARD_WIDTH and r.board_limit==4
    assert r.inventory and r.board[0] in r.inventory
    assert len(r.route)==3 and r.phase=='route'
    assert r.gold==14 and r.prestige==20


def test_stash_capacity_and_item_sizes():
    r=run()
    for i in range(3):r.obtain('ruby_hammer')
    assert r.occupied_size(r.stash)==9
    with pytest.raises(GameError,match='Stash is full'):r.obtain('moonshot')
    assert len(r.inventory)==4


def test_equipment_cannot_overlap_or_exceed_unlocked_slots():
    r=run();large=r.obtain('iron_maiden')
    with pytest.raises(GameError):r.equip(large,2)
    r.equip(large,1)
    assert r.board[1:4]==[large]*3 and large not in r.stash
    r.store(large)
    assert r.board[1:4]==[None]*3 and large in r.stash
    with pytest.raises(GameError):r.equip(large,8)


def test_sell_and_enchant_and_combine():
    r=run();r.gold=100
    a=r.obtain('flintlock');b=r.obtain('flintlock')
    r.action('combine',{'uid':a,'other':b})
    assert b not in r.inventory and r.inventory[a]['tier']==1
    r.phase='trainer';r.action('enchant',{'uid':a,'effect':'Fiery'})
    assert r.inventory[a]['enchant']=='Fiery'
    with pytest.raises(GameError):r.action('enchant',{'uid':a,'effect':'Toxic'})
    g=r.gold;r.action('sell',{'uid':a});assert r.gold>g
    assert a not in r.inventory


def test_stage_actions_server_authoritative():
    r=run()
    with pytest.raises(GameError):r.action('buy',{'index':0})
    with pytest.raises(GameError):r.action('choose',{'index':999})
    r.route=[{'type':'merchant','title':'Wandering Armorer','description':''}]*3
    r.action('choose',{'index':0}); assert r.phase=='merchant'
    assert len(r.offers)==5
    r.gold=100
    r.action('buy',{'index':0})
    assert len(r.offers)==4 and len(r.stash)>0
    r.action('reroll',{})
    r.action('leave',{});assert r.hour==2 and r.phase=='route'


def test_choose_rest_event_reward():
    r=run()
    r.route=[{'type':'rest','title':'Courtyard','description':''}]
    r.action('choose',{'index':0});assert r.phase=='rest'
    old=r.max_health
    r.action('event',{'choice':'health'}); assert r.max_health==old+40 and r.hour==2

@pytest.mark.parametrize('hero',['vex','nyra','bronn','cael'])
def test_simulate_combat_all_heroes(hero):
    r=run(hero=hero)
    r.selected={'type':'rival','title':'Duelist','tag':'weapon','style':'damage'}
    battle=r.fight()
    assert battle['victor'] in (0,1)
    assert battle['elapsed']<=38
    assert len(battle['events'])<=850
    assert all(0<=f['hp']<=f['maxHp'] for f in battle['fighters'])
    assert all(battle['events'][j]['seq']<battle['events'][j+1]['seq'] for j in range(len(battle['events'])-1))


def test_day_progression_prestige_victory_and_end():
    r=run();r.day=3;r.hour=6
    r.phase='encounter';r.selected={'type':'rival','title':'Duelist','tag':'weapon','style':'damage'}
    r.fight=lambda:{'victor':1,'events':[],'fighters':[],'elapsed':1}
    r.action('fight',{})
    assert r.losses==1 and r.prestige==17 and r.day==4
    r.day=12;r.hour=6;r.prestige=12;r.phase='encounter';r.selected={'type':'rival','tag':'weapon'}
    r.action('fight',{})
    assert r.phase=='lost' and r.prestige==0
    w=run();w.wins=9;w.hour=6;w.phase='encounter';w.selected={'type':'rival','tag':'weapon'}
    w.fight=lambda:{'victor':0,'events':[],'fighters':[],'elapsed':1}
    w.action('fight',{});assert w.phase=='won' and w.wins==WIN_TARGET


def test_expedition_http_authenticated_and_idempotent():
    with TestClient(app) as c:
        page=c.get('/expedition'); assert page.status_code==200
        assert 'text/html' in page.headers['content-type']
        result=c.post('/api/expedition/start',json={'name':'Player A','hero':'nyra'})
        assert result.status_code==200
        token=result.json()['token']
        assert token and result.json()['state']['boardLimit']==4
        assert c.post('/api/expedition/state',json={'token':'bad'}).status_code==400
        data=c.post('/api/expedition/action',json={'token':token,'op':'choose','index':0,'id':'choice-0001'})
        assert data.status_code==200
        revision=data.json()['state']['revision']
        dupe=c.post('/api/expedition/action',json={'token':token,'op':'choose','index':0,'id':'choice-0001'})
        assert dupe.json()['duplicate'] and dupe.json()['state']['revision']==revision
        assert c.post('/api/expedition/action',json={'token':'bad','op':'fight','id':'fight-0001'}).status_code==400
        assert c.get('/expedition.py').status_code==404


def test_no_remote_origin():
    with TestClient(app) as c:
        r=c.post('/api/expedition/start',headers={'origin':'https://evil.invalid'},json={'name':'A','hero':'vex'})
        assert r.status_code==400

@pytest.mark.parametrize('seed',range(120))
def test_seeded_run_and_combat_fuzz(seed):
    hero=list(['vex','nyra','bronn','cael'])[seed%4]
    r=run(seed,hero)
    r.gold=10000
    for i in range(4):
        k=list(CATALOG)[(seed+i*37)%len(CATALOG)]
        try:r.obtain(k)
        except GameError:break
    r.selected={'type':'monster','title':'Fuzz','tag':'machine','style':'shield'}
    result=r.fight()
    assert result['victor'] in (0,1)
    assert len(result['events'])<=850
    assert all(0<=x['hp']<=x['maxHp'] for x in result['fighters'])