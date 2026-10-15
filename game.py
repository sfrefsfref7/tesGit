"""Pure authoritative rules for Night Market Duel. No rendering or network code."""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import deque
import random
import secrets
import time

HEROES = {
    'vex': {'name':'Vex','title':'The Nightblade','power':'Precision','color':'#e6a65a','hp':235,'attack':16,'cadence':1.75},
    'nyra': {'name':'Nyra','title':'The Venom Witch','power':'Toxic Bloom','color':'#a0dcae','hp':245,'attack':12,'cadence':1.75},
    'bronn': {'name':'Bronn','title':'The Iron Warden','power':'Ironheart','color':'#9dc2eb','hp':275,'attack':11,'cadence':1.9},
    'cael': {'name':'Cael','title':'The Chronomancer','power':'Timeweave','color':'#c7a6e9','hp':225,'attack':13,'cadence':1.55},
}
ITEMS = {
 'dagger': {'name':'Gilded Dagger','tag':'weapon','rarity':'common','cost':3,'cooldown':2.0,'power':19,'type':'damage','glyph':'dagger','text':'Fast precision strike. +6 beside a Weapon.'},
 'crossbow': {'name':'Moonpiercer','tag':'weapon','rarity':'rare','cost':6,'cooldown':3.1,'power':38,'type':'damage','glyph':'bow','text':'Piercing moonbolt. Bonus against shields.'},
 'blaster': {'name':'Clockwork Repeater','tag':'machine','rarity':'rare','cost':6,'cooldown':2.5,'power':27,'type':'damage','glyph':'gear','text':'Fires quicker beside another Machine.'},
 'bomb': {'name':'Cinder Bomb','tag':'weapon','rarity':'rare','cost':6,'cooldown':3.8,'power':18,'type':'burn','glyph':'flame','text':'Damages and inflicts 4 Burn stacks.'},
 'venom': {'name':'Viper Vial','tag':'potion','rarity':'common','cost':4,'cooldown':2.8,'power':5,'type':'poison','glyph':'vial','text':'Inflicts 5 Poison. Extra Poison beside a Potion.'},
 'toxin': {'name':'Widow Lotus','tag':'potion','rarity':'epic','cost':8,'cooldown':4.0,'power':9,'type':'poison','glyph':'lotus','text':'Inflicts 9 Poison and deals 8 immediate damage.'},
 'elixir': {'name':'Glassheart Elixir','tag':'potion','rarity':'common','cost':4,'cooldown':3.6,'power':23,'type':'heal','glyph':'heart','text':'Restore health. Improved beside a Relic.'},
 'ward': {'name':'Aegis Sigil','tag':'relic','rarity':'common','cost':4,'cooldown':3.0,'power':28,'type':'shield','glyph':'shield','text':'Gain a protective barrier.'},
 'bulwark': {'name':'Iron Bulwark','tag':'machine','rarity':'rare','cost':6,'cooldown':3.6,'power':43,'type':'shield','glyph':'shield','text':'Heavy shielding. Bonus if a Machine is adjacent.'},
 'spark': {'name':'Storm Lens','tag':'relic','rarity':'rare','cost':6,'cooldown':3.2,'power':30,'type':'damage','glyph':'spark','text':'Chain lightning. +10 beside a Relic.'},
 'clock': {'name':'Hourglass of Ash','tag':'relic','rarity':'epic','cost':8,'cooldown':4.6,'power':0.20,'type':'haste','glyph':'clock','text':'Temporarily reduces your item cooldowns.'},
 'fang': {'name':'Crimson Fang','tag':'weapon','rarity':'epic','cost':8,'cooldown':3.7,'power':44,'type':'leech','glyph':'fang','text':'Steals health when it strikes.'},
 'mirror': {'name':'Silver Mirror','tag':'relic','rarity':'rare','cost':6,'cooldown':4.0,'power':31,'type':'shield','glyph':'mirror','text':'Reflective ward; adds a little damage.'},
 'flask': {'name':'Phoenix Flask','tag':'potion','rarity':'rare','cost':6,'cooldown':4.4,'power':35,'type':'heal','glyph':'vial','text':'Powerful restorative brew.'},
 'rune': {'name':'Runic Talon','tag':'weapon','rarity':'common','cost':4,'cooldown':2.8,'power':29,'type':'damage','glyph':'rune','text':'Arcane slash. +6 beside a Relic.'},
 'ember': {'name':'Ember Core','tag':'machine','rarity':'common','cost':4,'cooldown':3.0,'power':14,'type':'burn','glyph':'flame','text':'Inflicts lingering Burn.'},
}
MAX_SLOTS = 6
SHOP_SIZE = 4
RECONNECT_SECONDS = 30


def code():
    return ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(5))

@dataclass
class Player:
    name: str
    token: str
    hero: str
    bot: bool = False
    connected: bool = True
    disconnected_at: float | None = None
    gold: int = 14
    wins: int = 0
    board: list = field(default_factory=lambda: [None] * MAX_SLOTS)
    shop: list = field(default_factory=list)
    ready: bool = False
    last_seen: float = field(default_factory=time.monotonic)
    seen_actions: dict = field(default_factory=dict)

    def public(self, viewer: bool = False):
        out = dict(name=self.name, hero=self.hero, ready=self.ready, connected=self.connected,
                   wins=self.wins, board=self.board, bot=self.bot)
        if viewer:
            out.update(gold=self.gold, shop=self.shop)
        return out


class GameError(Exception):
    pass


class Room:
    def __init__(self, code_: str, owner: Player, bot: bool = False, seed: int | None = None):
        self.code = code_
        self.players: list[Player] = [owner]
        self.phase = 'lobby'
        self.round = 1
        self.max_rounds = 3
        self.created = time.monotonic()
        self.last_active = self.created
        self.events = deque(maxlen=15)
        self.battle = None
        self.winner = None
        self.tick_ms = 0.0
        self.rng = random.Random(seed if seed is not None else secrets.randbits(48))
        self.revision = 0
        if bot:
            self.players.append(Player('The Curator', 'bot-'+code_, self.rng.choice(list(HEROES)), bot=True))
            self.start_shop()

    def add_player(self, name: str, hero: str):
        if len(self.players) >= 2: raise GameError('This room is full.')
        if self.phase != 'lobby': raise GameError('Match already started.')
        p = Player(valid_name(name), secrets.token_urlsafe(32), valid_hero(hero))
        self.players.append(p)
        self.start_shop()
        return p

    def find(self, token: str) -> Player:
        for p in self.players:
            if not p.bot and secrets.compare_digest(p.token, str(token)):
                return p
        raise GameError('Invalid session token.')

    def start_shop(self):
        self.phase = 'shop'
        self.battle = None
        self.winner = None
        for p in self.players:
            p.ready = False
            if self.round > 1: p.gold += 11
            p.shop = self.roll_shop()
            if p.bot:
                self.bot_shop(p)
                p.ready = True
        self.events.appendleft(f'Round {self.round} · The market is open')
        self.revision += 1

    def roll_shop(self):
        pool = list(ITEMS)
        return self.rng.sample(pool, SHOP_SIZE)

    def bot_shop(self, p):
        # Bot chooses useful synergy items from its shop, keeping within budget.
        preferred = {'vex':('weapon','machine'),'nyra':('potion','relic'),'bronn':('machine','relic'),'cael':('relic','weapon')}[p.hero]
        available = sorted(p.shop, key=lambda k: (ITEMS[k]['tag'] in preferred, ITEMS[k]['cost']), reverse=True)
        for key in available:
            if key in p.shop and p.gold >= ITEMS[key]['cost'] and None in p.board:
                p.gold -= ITEMS[key]['cost']; p.board[p.board.index(None)] = key
                p.shop.remove(key)

    def act(self, p: Player, op: str, payload: dict):
        if p.bot: raise GameError('Bot cannot accept player actions.')
        if op == 'rematch':
            if self.phase != 'finished': raise GameError('Match is not finished.')
            p.ready = True
            for opponent in self.players:
                if opponent.bot: opponent.ready = True
            if all(x.ready for x in self.players):
                self.round = 1
                for x in self.players:
                    x.wins=0; x.gold=14; x.board=[None]*MAX_SLOTS
                self.start_shop()
            self.revision += 1
            return
        if self.phase != 'shop': raise GameError('Wait until the market opens.')
        if p.ready and op != 'unready': raise GameError('Already ready. Unready to edit.')
        if op == 'buy':
            i = checked_int(payload.get('index'), 0, len(p.shop)-1)
            key = p.shop[i]
            cost = ITEMS[key]['cost']
            if p.gold < cost: raise GameError('Not enough gold.')
            if None not in p.board: raise GameError('Your board is full.')
            p.gold -= cost
            p.board[p.board.index(None)] = key
            p.shop.pop(i)
            self.events.appendleft(f'{p.name} acquired {ITEMS[key]["name"]}')
        elif op == 'reroll':
            if p.gold < 2: raise GameError('Need 2 gold to refresh.')
            p.gold -= 2
            p.shop = self.roll_shop()
        elif op == 'move':
            a = checked_int(payload.get('from'), 0, MAX_SLOTS-1)
            b = checked_int(payload.get('to'), 0, MAX_SLOTS-1)
            if p.board[a] is None: raise GameError('No item in that slot.')
            p.board[a],p.board[b] = p.board[b],p.board[a]
        elif op == 'sell':
            i = checked_int(payload.get('index'), 0, MAX_SLOTS-1)
            k = p.board[i]
            if k is None: raise GameError('Empty slot.')
            p.gold += max(1, ITEMS[k]['cost']//2)
            p.board[i] = None
        elif op == 'ready':
            p.ready = True
            if all(x.ready for x in self.players): self.start_battle()
        elif op == 'unready':
            p.ready = False
        else: raise GameError('Unknown action.')
        self.revision += 1

    def start_battle(self):
        self.phase = 'battle'
        fighter = []
        for p in self.players:
            hero = HEROES[p.hero]
            hp = hero['hp']
            fighter.append(dict(name=p.name, hp=hp,maxHp=hp, shield=(30 if p.hero=='bronn' else 0),
                poison=0,burn=0,haste=0.0, basic=0.0, cds=[self.rng.random()*0.5 for _ in p.board],
                hero=p.hero, board=list(p.board)))
        self.battle = dict(elapsed=0.0, fighters=fighter, effects=[], sequence=0)
        self.events.appendleft('⚔ The duel has begun')

    def apply_hit(self, source: int, target: int, power: float, kind: str, label: str):
        b=self.battle
        src, tar=b['fighters'][source], b['fighters'][target]
        dealt=max(0,int(power))
        blocked=min(tar['shield'],dealt)
        tar['shield']-=blocked
        tar['hp']=max(0,tar['hp']-(dealt-blocked))
        b['effects'].append(dict(source=source, target=target, amount=dealt-blocked,
                                 blocked=blocked,kind=kind,label=label,seq=b['sequence']))
        b['sequence']+=1
        return dealt-blocked

    def update_battle(self, dt=0.1):
        if self.phase!='battle': return False
        st = time.perf_counter()
        b=self.battle; b['elapsed']+=dt
        for i, p in enumerate(self.players):
            f=b['fighters'][i]; enemy=b['fighters'][1-i]
            if f['hp'] <= 0 or enemy['hp'] <= 0: continue
            hero=HEROES[f['hero']]
            f['basic']-=dt
            if f['basic'] <= 0:
                f['basic']+=hero['cadence']
                power=hero['attack']+(5 if p.hero=='vex' else 0)
                self.apply_hit(i,1-i,power,'hit',hero['power'])
            for j,k in enumerate(f['board']):
                if not k: continue
                item=ITEMS[k]
                cooldown=item['cooldown'] * (0.78 if p.hero=='cael' else 1.0)
                if f['haste']>0: cooldown*=0.78
                f['cds'][j]-=dt
                if f['cds'][j] > 0: continue
                f['cds'][j]+=max(.6,cooldown)
                adj=[x for x in f['board'][max(0,j-1):j]+f['board'][j+1:j+2] if x]
                synergy=sum(ITEMS[x]['tag']==item['tag'] for x in adj)
                amt=item['power']
                if item['type']=='damage':
                    boost=6 if k in ('dagger','rune') and adj else 0
                    if k=='spark': boost+=10*synergy
                    if k=='blaster': boost+=5*synergy
                    if k=='crossbow': boost+=min(enemy['shield'],20)//2
                    self.apply_hit(i,1-i,amt+boost,'hit',item['name'])
                elif item['type']=='burn':
                    self.apply_hit(i,1-i,amt,'fire',item['name'])
                    enemy['burn']+=3 if k=='ember' else 4
                elif item['type']=='poison':
                    enemy['poison']+=int(amt+2*synergy+(2 if p.hero=='nyra' else 0))
                    b['effects'].append(dict(source=i,target=1-i,amount=int(amt),kind='poison',label=item['name'],seq=b['sequence']))
                    b['sequence']+=1
                    if k=='toxin': self.apply_hit(i,1-i,8,'hit',item['name'])
                elif item['type']=='heal':
                    restored=min(f['maxHp']-f['hp'],int(amt+5*synergy))
                    f['hp']+=restored
                    b['effects'].append(dict(source=i,target=i,amount=restored,kind='heal',label=item['name'],seq=b['sequence']))
                    b['sequence']+=1
                elif item['type']=='shield':
                    f['shield']+=int(amt+6*synergy)
                    b['effects'].append(dict(source=i,target=i,amount=int(amt+6*synergy),kind='shield',label=item['name'],seq=b['sequence']))
                    b['sequence']+=1
                    if k=='mirror': self.apply_hit(i,1-i,7,'hit',item['name'])
                elif item['type']=='leech':
                    dealt=self.apply_hit(i,1-i,amt,'hit',item['name'])
                    f['hp']=min(f['maxHp'], f['hp']+int(dealt*0.42))
                elif item['type']=='haste':
                    f['haste']=5
                    b['effects'].append(dict(source=i,target=i,amount=0,kind='haste',label=item['name'],seq=b['sequence']))
                    b['sequence']+=1
            if f['haste']>0: f['haste']=max(0,f['haste']-dt)
        # Poison/burn tick every 1s using integer second boundary.
        if int((b['elapsed']-dt)*10)//10 != int(b['elapsed']*10)//10:
            for i,f in enumerate(b['fighters']):
                if f['poison']>0:
                    self.apply_hit(1-i,i,min(16,f['poison']),'poison','Venom')
                    f['poison']=max(0,f['poison']-1)
                if f['burn']>0:
                    self.apply_hit(1-i,i,min(12,f['burn']*2),'fire','Burn')
                    f['burn']=max(0,f['burn']-1)
        b['effects']=b['effects'][-36:]
        end=(any(x['hp']<=0 for x in b['fighters']) or b['elapsed']>=24)
        # The recent event tail survives several snapshots; the client deduplicates by sequence.
        b['effects'] = b['effects'][-30:]
        self.tick_ms = (time.perf_counter()-st)*1000
        self.revision+=1
        if end: self.finish_battle()
        return end

    def finish_battle(self):
        if self.phase!='battle': return
        ff=self.battle['fighters']
        scores=[x['hp']+min(x['shield']*.25,30) for x in ff]
        # Exact ties use seeded RNG, instead of quietly favoring the room owner.
        win=0 if scores[0]>scores[1] else 1 if scores[1]>scores[0] else self.rng.choice((0,1))
        self.players[win].wins+=1
        self.battle['victor']=win
        self.events.appendleft(f'{self.players[win].name} wins round {self.round}')
        if self.players[win].wins >= 2 or self.round >= self.max_rounds:
            self.phase='finished'; self.winner=win
            # Rematch requires fresh consent from both human players.
            for player in self.players: player.ready=False
        else:
            self.phase='intermission'
        self.revision+=1

    def advance_round(self):
        if self.phase != 'intermission': return
        self.round += 1
        self.start_shop()

    def snapshot(self, token: str):
        me=self.find(token)
        idx=self.players.index(me)
        return dict(type='state',code=self.code,phase=self.phase,round=self.round,
            players=[p.public(viewer=(p is me)) for p in self.players],you=idx,
            winner=self.winner,battle=self.battle,events=list(self.events)[:8],
            revision=self.revision,serverTime=time.time(),tickMs=round(self.tick_ms,3))


def valid_name(s):
    if not isinstance(s,str): raise GameError('Enter a player name.')
    s=' '.join(s.strip().split())
    if not (1<=len(s)<=20) or any(ord(c)<32 for c in s): raise GameError('Name must contain 1–20 characters.')
    return s


def valid_hero(s):
    if s not in HEROES: raise GameError('Choose a valid hero.')
    return s


def checked_int(value, lo, hi):
    if type(value) is not int or value<lo or value>hi: raise GameError('Invalid slot or item index.')
    return value