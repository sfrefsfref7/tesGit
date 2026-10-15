"""Guided (full-journey) mode contracts and server-authority tests."""
import pytest
from fastapi.testclient import TestClient
from app import app
from expedition import Run, CATALOG, GameError


def test_guided_start_option_is_required_and_applied_only_once():
    r=Run('Test','nyra',guided=True,seed=17)
    assert r.phase=='starter' and len(r.available())==3
    gold=r.gold
    with pytest.raises(GameError):r.action('choose',{'index':0})
    with pytest.raises(GameError):r.action('starter',{'choice':'999gold'})
    r.action('starter',{'choice':'economy'})
    assert r.phase=='route' and r.gold==gold+10 and r.income==7
    with pytest.raises(GameError):r.action('starter',{'choice':'economy'})
    r.day=1;r.hour=6;r.advance()
    assert r.day==2 and r.gold==gold+10+11


@pytest.mark.parametrize('hero, tag', [('vex','weapon'),('nyra','potion'),('bronn','machine'),('cael','relic')])
def test_starter_item_hero_specific(hero,tag):
    r=Run('Test',hero,guided=True,seed=20)
    r.action('starter',{'choice':'enchantment'})
    extra=[x for x in r.inventory.values() if x['enchant']]
    assert len(extra)==1
    assert CATALOG[extra[0]['key']]['tag']==tag
    assert extra[0]['enchant'] in ('Fiery','Toxic','Turbo','Shielded')


def test_guided_level_choice_blocks_progress():
    r=Run('Test','vex',guided=True,seed=22)
    r.action('starter',{'choice':'training'})
    assert len(r.skills)==1
    r.xp=7;r.advance()
    assert r.phase=='levelup' and len(r.available())==3
    with pytest.raises(GameError):r.action('choose',{'index':0})
    health=r.max_health
    r.action('level_reward',{'choice':'fortify'})
    assert r.phase=='route' and r.max_health==health+60
    with pytest.raises(GameError):r.action('level_reward',{'choice':'fortune'})


def test_route_monster_difficulty_has_distinct_rewards_and_real_loadout():
    r=Run('Test','bronn',seed=17)
    r.hour=3;r.route=r.make_route()
    assert [x['rank'] for x in r.route]==['BRONZE','SILVER','GOLD']
    assert r.route[0]['rewardGold']<r.route[1]['rewardGold']<r.route[2]['rewardGold']
    r.action('choose',{'index':2})
    before=list(r.public()['enemyLoadout'])
    assert before
    res=r.action('fight',{})
    assert res['enemy']
    assert all(CATALOG[k] for k in before)


def test_specialized_shops_and_reroll_keep_tag():
    r=Run('Test','nyra',seed=50)
    for tag in ('weapon','potion','machine','relic'):
        r.phase='route';r.route=[{'type':'merchant','title':f'Shop {tag}','merchantTag':tag}]
        r.action('choose',{'index':0})
        assert all(CATALOG[k]['tag']==tag for k in r.offers)
        r.action('reroll',{})
        assert all(CATALOG[k]['tag']==tag for k in r.offers)


def test_http_guided_session_preserves_token_and_phase():
    with TestClient(app) as client:
        res=client.post('/api/expedition/start',json={'name':'Player','hero':'vex','guided':True})
        assert res.status_code==200
        data=res.json();tok=data['token'];assert data['state']['phase']=='starter'
        q={'token':tok,'id':'starter-choice-112','op':'starter','choice':'economy'}
        first=client.post('/api/expedition/action',json=q)
        assert first.status_code==200 and first.json()['state']['gold']>=24
        assert client.post('/api/expedition/action',json=q).json()['duplicate'] is True
        assert client.post('/api/expedition/state',json={'token':tok}).json()['state']['income']==7
        assert client.post('/api/expedition/action',json={'token':tok,'id':'invalid-op-12','op':'level_reward','choice':'fortune'}).status_code==400


def test_new_collection_assets_load():
    with TestClient(app) as c:
        r=c.get('/expedition'); assert 'expedition-codex.js' in r.text
        assert c.get('/static/expedition-codex.js').status_code==200
        assert 'codexResults' in r.text