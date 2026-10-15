"""Regression tests for 0.3 depth: real costs, boons, forging, combat and rematches."""
import random
import pytest
from game import Room, Player, GameError, BOONS, ITEMS, HEROES, MAX_SLOTS, SHOP_SIZE


def arena(hero='nyra', seed=42, bot=True):
    return Room('ABCDE', Player('Dome', 'good-session', hero), bot=bot, seed=seed)


def test_catalog_complete_and_validated():
    assert len(ITEMS) >= 40 and len(BOONS) >= 14
    for item in ITEMS.values():
        assert item['tag'] in ('weapon', 'potion', 'relic', 'machine')
        assert item['rarity'] in ('common', 'rare', 'epic')
        assert item['type'] in {'damage','shield','burn','heal','poison','haste','leech','shatter','execute','slow','rupture','cleanse','thorns'}
        assert item['cost'] > 0 and item['cooldown'] > 0 and item['power'] >= 0
        assert item['glyph'] in ('dagger','bow','gear','flame','vial','lotus','heart','shield','spark','clock','fang','mirror','rune')

@pytest.mark.parametrize('hero', list(HEROES))
def test_shop_is_hero_themed_unique_and_affordable_first_round(hero):
    for seed in range(30):
        r=arena(hero, seed)
        p=r.players[0]
        assert len(p.shop)==SHOP_SIZE and len(set(p.shop))==SHOP_SIZE
        assert all(ITEMS[k]['cost']<=6 for k in p.shop)
        assert len(p.boon_choices)==3 and len(set(p.boon_choices))==3
        assert p.boon_chosen is False
        assert r.players[1].boon_chosen is True

@pytest.mark.parametrize('bad',[-1,3,True,3.3,'0',None,{},[]])
def test_boon_requires_valid_choice_and_single_use(bad):
    r=arena();p=r.players[0];before=p.gold
    with pytest.raises(GameError):r.act(p,'boon',{'index':bad})
    assert len(p.boons)==0 and p.gold==before
    r.act(p,'boon',{'index':0})
    assert p.boon_chosen and len(p.boons)==1
    with pytest.raises(GameError,match='already'):r.act(p,'boon',{'index':1})
    assert len(p.boons)==1


def test_windfall_grants_gold_only_once_and_round_rewards():
    r=arena();p=r.players[0]
    p.boon_choices=['windfall','ferocity','vigor']
    r.act(p,'boon',{'index':0})
    assert p.gold==20
    with pytest.raises(GameError):r.act(p,'boon',{'index':0})
    r.round=2;r.start_shop()
    assert p.gold==31 and len(p.boons)==1


def test_merchant_discount_applies_server_side():
    r=arena();p=r.players[0]
    p.boon_choices=['merchant','windfall','vigor'];r.act(p,'boon',{'index':0})
    item=p.shop[0];original=p.gold
    r.act(p,'buy',{'index':0})
    assert p.gold==original-max(1,ITEMS[item]['cost']-1)
    assert p.public(viewer=True)['discount']==1
    assert 'shop' not in p.public(viewer=False)


def test_upgrade_has_correct_cost_cap_and_forbid_invalid():
    r=arena();p=r.players[0]
    with pytest.raises(GameError,match='no item'):r.act(p,'upgrade',{'index':0})
    p.board[2]='cannon';p.gold=100
    r.act(p,'upgrade',{'index':2});assert p.gold==95 and p.upgrades[2]==1
    r.act(p,'upgrade',{'index':2});assert p.gold==87 and p.upgrades[2]==2
    with pytest.raises(GameError,match='fully upgraded'):r.act(p,'upgrade',{'index':2})
    assert p.gold==87
    r.act(p,'move',{'from':2,'to':5})
    assert p.board[5]=='cannon' and p.upgrades[5]==2 and p.upgrades[2]==0
    r.act(p,'sell',{'index':5})
    assert p.board[5] is None and p.upgrades[5]==0


def test_upgrade_insufficient_funds_no_partial_mutation():
    r=arena();p=r.players[0];p.board[0]='dagger';p.gold=4
    before=p.public(viewer=True).copy()
    with pytest.raises(GameError,match='gold'):r.act(p,'upgrade',{'index':0})
    assert p.gold==before['gold'] and p.upgrades[0]==0


def test_ready_fallback_auto_selects_boon_for_legacy_clients():
    r=arena();p=r.players[0]
    r.act(p,'ready',{})
    assert len(p.boons)==1 and p.boon_chosen
    assert r.phase=='battle'
    with pytest.raises(GameError):r.act(p,'upgrade',{'index':0})


def test_vigor_bulwark_and_item_forge_modify_authoritative_stats():
    r=arena();p=r.players[0]
    p.boons=['vigor','bulwark'];p.board[0]='dagger';p.upgrades[0]=2
    r.start_battle()
    f=r.battle['fighters'][0]
    assert f['hp']==HEROES[p.hero]['hp']+38 and f['shield']==38
    assert f['upgrades']==[2,0,0,0,0,0]


@pytest.mark.parametrize('key',list(ITEMS))
def test_all_items_have_safe_combat_effects(key):
    r=arena(seed=117)
    p=r.players[0];p.board=[key]*MAX_SLOTS
    p.upgrades=[2]*MAX_SLOTS
    p.boons=['focus','temporal','vigor']
    r.start_battle()
    for _ in range(240):
        if r.phase!='battle':break
        r.update_battle(.1)
        for f in r.battle['fighters']:
            assert 0<=f['hp']<=f['maxHp']
            assert 0<=f['shield']<=500
            assert 0<=f['poison']<=120
            assert 0<=f['thorns']<=20
            assert len(f['cds'])==MAX_SLOTS
        assert len(r.battle['effects'])<=30
    assert r.phase in ('finished','intermission')
    assert r.battle['victor'] in (0,1)


def test_two_players_buy_build_and_rematch_resets_all_progression():
    r=arena(bot=False)
    b=r.add_player('Guest','cael')
    a=r.players[0]
    for p in (a,b):
        r.act(p,'boon',{'index':0})
        r.act(p,'buy',{'index':0})
        r.act(p,'ready',{})
    assert r.phase=='battle'
    for _ in range(250):
        if r.phase!='battle':break
        r.update_battle(.1)
    assert r.phase in ('intermission','finished')
    r.phase='finished';r.winner=0;a.ready=False;b.ready=False
    r.act(a,'rematch',{})
    assert r.phase=='finished'
    r.act(b,'rematch',{})
    assert r.phase=='shop' and r.round==1
    assert all(not p.boons and all(x==0 for x in p.upgrades) and p.gold==14 and not p.ready for p in r.players)


def test_fuzz_shop_boons_forging_random_seeded_builds():
    for seed in range(125):
        r=arena(hero=list(HEROES)[seed%4],seed=seed)
        p=r.players[0]
        engine=random.Random(seed)
        for stage in range(3):
            if r.phase=='finished':break
            assert r.phase=='shop'
            r.act(p,'boon',{'index':engine.randrange(3)})
            for _ in range(7):
                if p.gold>=2 and engine.random()<.2:r.act(p,'reroll',{})
                elif p.shop and None in p.board:
                    affordable=[i for i,k in enumerate(p.shop) if r.item_cost(p,k)<=p.gold]
                    if affordable:r.act(p,'buy',{'index':engine.choice(affordable)})
            upgradeable=[i for i,k in enumerate(p.board) if k and p.upgrades[i]<2]
            if upgradeable and p.gold>=5:
                r.act(p,'upgrade',{'index':upgradeable[0]})
            r.act(p,'ready',{})
            for _ in range(260):
                if r.phase!='battle':break
                r.update_battle(.1)
            assert r.phase in ('finished','intermission')
            if r.phase=='intermission':r.advance_round()