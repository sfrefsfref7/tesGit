import pytest
from game import Player, Room, GameError, HEROES, ITEMS, SHOP_SIZE, BOONS, MAX_SLOTS, valid_name

def room(bot=True):
    return Room('ABCDE',Player('Dome','tok-a','nyra'),bot=bot,seed=42)

def test_hero_and_catalog():
    assert len(HEROES)==4
    assert len(ITEMS)>=16
    assert len(set(ITEMS))==len(ITEMS)
    assert all(item['cost']>0 and item['cooldown']>0 for item in ITEMS.values())

@pytest.mark.parametrize('name',['',' '*5,'x'*21,'\x00abc'])
def test_bad_names(name):
    with pytest.raises(GameError): valid_name(name)

def test_room_create_and_join():
    r=room(False)
    assert r.phase=='lobby' and len(r.players)==1
    p=r.add_player(' Friend ','vex')
    assert p.name=='Friend' and r.phase=='shop' and len(r.players)==2
    assert r.players[0].shop != [] and p.shop != []
    with pytest.raises(GameError,match='full'): r.add_player('Third','cael')
    with pytest.raises(GameError,match='token'):r.find('wrong')

def test_buy_and_duplicate_prices():
    r=room()
    p=r.players[0]
    initial=p.gold
    key=p.shop[0]
    price=ITEMS[key]['cost']
    r.act(p,'buy',{'index':0})
    assert p.gold==initial-price
    assert key in p.board
    assert len(p.shop)==SHOP_SIZE-1

def test_shop_move_sell_guardrails():
    r=room()
    p=r.players[0]
    with pytest.raises(GameError):r.act(p,'move',{'from':0,'to':999})
    with pytest.raises(GameError):r.act(p,'sell',{'index':5})
    p.shop=['dagger'];p.gold=99
    r.act(p,'buy',{'index':0})
    r.act(p,'move',{'from':0,'to':5})
    assert p.board[5]=='dagger' and p.board[0] is None
    r.act(p,'sell',{'index':5})
    assert all(x is None for x in p.board)

def test_readiness_and_authority():
    r=room(False); p=r.add_player('Other','vex'); owner=r.players[0]
    r.act(owner,'ready',{})
    assert r.phase=='shop'
    with pytest.raises(GameError): r.act(owner,'buy',{'index':0})
    r.act(owner,'unready',{})
    r.act(owner,'ready',{})
    r.act(p,'ready',{})
    assert r.phase=='battle'
    with pytest.raises(GameError): r.act(p,'buy',{'index':0})

def test_battle_runs_to_finish_and_advances():
    r=room()
    r.players[0].board=['dagger','venom','toxin','elixir','ward','spark']
    r.players[1].board=['bulwark','rune','spark','clock','flask','crossbow']
    r.act(r.players[0],'ready',{})
    assert r.phase=='battle'
    for _ in range(260):
        if r.update_battle(.1):break
    assert r.phase=='intermission'
    assert sum(p.wins for p in r.players)==1
    r.advance_round()
    assert r.round==2 and r.phase=='shop'
    assert r.players[0].gold>0

def test_all_heroes_battle_against_bot_without_errors():
    for hero in HEROES:
        r=Room('TEST1',Player('Hero','mytoken',hero),bot=True,seed=10)
        r.players[0].board=list(ITEMS)[:MAX_SLOTS]
        r.act(r.players[0],'ready',{})
        for _ in range(260):
            if r.update_battle(.1):break
        assert r.phase=='intermission'
        assert all(0<=f['hp']<=f['maxHp'] for f in r.battle['fighters'])

def test_snapshots_hide_private_inventory_and_token():
    r=room(False)
    p=r.add_player('Other','vex')
    data=r.snapshot('tok-a')
    assert 'token' not in data['players'][0]  # only transmitted once in joined packet
    assert 'token' not in data['players'][1]
    assert 'gold' not in data['players'][1] and 'shop' not in data['players'][1]

def test_finished_rematch_needs_both_players():
    r=room(False)
    guest=r.add_player('Friend','vex'); owner=r.players[0]
    owner.ready=guest.ready=True
    r.start_battle()
    r.players[0].wins=1
    r.finish_battle()
    assert r.phase=='finished'
    assert owner.ready is False and guest.ready is False
    r.act(owner,'rematch',{})
    assert r.phase=='finished' and owner.ready is True and guest.ready is False
    r.act(guest,'rematch',{})
    assert r.phase=='shop' and r.round==1 and owner.wins==guest.wins==0


def test_bot_rematch_starts_without_a_second_human():
    r=room(True)
    r.start_battle()
    r.players[0].wins=1
    r.finish_battle()
    assert r.phase=='finished'
    r.act(r.players[0],'rematch',{})
    assert r.phase=='shop' and r.round==1


def test_combat_effect_buffer_survives_intervening_tick():
    r=room(True)
    r.players[0].board=['dagger']+[None]*5
    r.start_battle()
    r.update_battle(.1)
    seqs=[e['seq'] for e in r.battle['effects']]
    assert seqs
    r.update_battle(.1)
    assert all(s in [e['seq'] for e in r.battle['effects']] for s in seqs)
    assert len(r.battle['effects'])<=36

def test_shop_rejects_overspend_and_full_board():
    r=room();p=r.players[0]
    p.gold=0
    with pytest.raises(GameError,match='gold'):r.act(p,'buy',{'index':0})
    p.gold=100
    p.board=['dagger']*MAX_SLOTS
    with pytest.raises(GameError,match='full'):r.act(p,'buy',{'index':0})
    with pytest.raises(GameError,match='gold'):
        p.gold=1;r.act(p,'reroll',{})

def test_rematch_resets_scores_but_requires_ready():
    r=room(False);p=r.add_player('B','vex');owner=r.players[0]
    r.phase='finished';r.winner=0
    owner.wins=2;p.wins=0
    r.act(owner,'rematch',{})
    assert r.phase=='finished' and owner.ready
    r.act(p,'rematch',{})
    assert r.phase=='shop' and r.round==1 and owner.wins==0 and p.wins==0

def test_battle_event_sequence_and_event_memory_bound():
    r=room();p=r.players[0]
    p.board=['dagger']*MAX_SLOTS
    r.act(p,'ready',{})
    for _ in range(60):
        if r.phase!='battle':break
        r.update_battle(.1)
    ev=r.battle['effects']
    assert len(ev)<=30
    ids=[x['seq'] for x in ev]
    assert ids==sorted(set(ids))
    assert ids[-1]>0

def test_battle_many_seeded_builds_never_exceed_health_or_effect_limit():
    for seed in range(100):
        hero=list(HEROES)[seed%len(HEROES)]
        r=Room('FUZZ1',Player('Dome','session-'+str(seed),hero),bot=True,seed=seed)
        keys=list(ITEMS)
        r.players[0].board=[keys[(seed+i*3)%len(keys)] for i in range(MAX_SLOTS)]
        r.start_battle()
        for _ in range(250):
            if r.update_battle(.1): break
            assert len(r.battle['effects'])<=36
            for f in r.battle['fighters']:
                assert 0<=f['hp']<=f['maxHp']
                assert f['poison']>=0 and f['burn']>=0
        assert r.phase in ('intermission','finished')