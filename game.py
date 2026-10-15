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
# Distinct combinations are more interesting than unlimited stat inflation.
ITEMS.update({
 'glaive': {'name':'Dusk Glaive','tag':'weapon','rarity':'rare','cost':6,'cooldown':3.4,'power':43,'type':'damage','glyph':'dagger','text':'A heavy strike that likes adjacent weapons.'},
 'duelist': {'name':"Duelist’s Rapier",'tag':'weapon','rarity':'common','cost':4,'cooldown':1.65,'power':15,'type':'damage','glyph':'dagger','text':'Quick attacks scale with surrounding weapons.'},
 'harpoon': {'name':'Leviathan Harpoon','tag':'weapon','rarity':'epic','cost':9,'cooldown':4.2,'power':49,'type':'shatter','glyph':'bow','text':'Shatters an enemy shield before striking.'},
 'sunblade': {'name':'Solstice Blade','tag':'weapon','rarity':'epic','cost':9,'cooldown':3.9,'power':49,'type':'execute','glyph':'dagger','text':'Hits harder against wounded enemies.'},
 'sling': {'name':'Mercury Sling','tag':'weapon','rarity':'common','cost':3,'cooldown':1.8,'power':16,'type':'damage','glyph':'bow','text':'Reliable rapid-fire sidearm.'},
 'toxic_needle': {'name':'Nightshade Needle','tag':'potion','rarity':'rare','cost':6,'cooldown':2.7,'power':7,'type':'poison','glyph':'vial','text':'Concentrated poison on a short cooldown.'},
 'plague_mask': {'name':'Plague Doctor Mask','tag':'relic','rarity':'epic','cost':9,'cooldown':4.2,'power':12,'type':'rupture','glyph':'lotus','text':'Burst damage scales with enemy Poison and Burn.'},
 'antidote': {'name':'Moonwater Antidote','tag':'potion','rarity':'common','cost':4,'cooldown':3.1,'power':17,'type':'cleanse','glyph':'heart','text':'Restores vitality and clears harmful statuses.'},
 'meteor': {'name':'Starfall Phial','tag':'potion','rarity':'epic','cost':9,'cooldown':4.7,'power':29,'type':'burn','glyph':'flame','text':'Heavy fire strike; applies intense Burn.'},
 'smoke': {'name':'Ember Incense','tag':'potion','rarity':'rare','cost':6,'cooldown':3.2,'power':13,'type':'burn','glyph':'flame','text':'Lingering flame that amplifies fire builds.'},
 'vessel': {'name':'Evergreen Vessel','tag':'potion','rarity':'rare','cost':6,'cooldown':3.2,'power':30,'type':'heal','glyph':'heart','text':'Strong sustain with Potion adjacency bonus.'},
 'totem': {'name':'Gravestone Totem','tag':'relic','rarity':'common','cost':4,'cooldown':3.3,'power':28,'type':'shield','glyph':'shield','text':'Constant mystical protection.'},
 'prism': {'name':'Shattered Prism','tag':'relic','rarity':'epic','cost':9,'cooldown':3.8,'power':36,'type':'shatter','glyph':'spark','text':'Destroys shields, then hits the target.'},
 'frost': {'name':'Winter Dial','tag':'relic','rarity':'rare','cost':6,'cooldown':4.0,'power':16,'type':'slow','glyph':'clock','text':'Cold magic briefly slows enemy item cooldowns.'},
 'phoenix': {'name':'Phoenix Crown','tag':'relic','rarity':'epic','cost':9,'cooldown':4.0,'power':40,'type':'heal','glyph':'heart','text':'Powerful periodic life restoration.'},
 'guardian': {'name':"Warden’s Plate",'tag':'machine','rarity':'common','cost':4,'cooldown':3.1,'power':31,'type':'shield','glyph':'shield','text':'Mechanical armor for defensive builds.'},
 'cannon': {'name':'Brass Howitzer','tag':'machine','rarity':'epic','cost':9,'cooldown':4.1,'power':55,'type':'damage','glyph':'gear','text':'Slower explosive power with Machine synergy.'},
 'saw': {'name':'Razor Automaton','tag':'machine','rarity':'rare','cost':6,'cooldown':2.1,'power':24,'type':'damage','glyph':'gear','text':'Rapid mechanical cutting attacks.'},
 'coil': {'name':'Tempest Coil','tag':'machine','rarity':'rare','cost':6,'cooldown':3.5,'power':22,'type':'slow','glyph':'spark','text':'Short-circuits opponents and slows their items.'},
 'engine': {'name':'Perpetual Engine','tag':'machine','rarity':'epic','cost':9,'cooldown':5.0,'power':0.25,'type':'haste','glyph':'gear','text':'Surges all your item cooldowns for five seconds.'},
 'thorns': {'name':'Briar Aegis','tag':'relic','rarity':'rare','cost':6,'cooldown':3.8,'power':23,'type':'thorns','glyph':'shield','text':'Builds shield and reflects part of incoming hits.'},
 'sundial': {'name':'Astral Sundial','tag':'relic','rarity':'common','cost':4,'cooldown':3.4,'power':0.14,'type':'haste','glyph':'clock','text':'Small but consistent haste enchantment.'},
 'bloodstone': {'name':'Bloodstone','tag':'relic','rarity':'rare','cost':6,'cooldown':3.2,'power':27,'type':'leech','glyph':'fang','text':'Drain your enemy while restoring vitality.'},
 'royal_decree': {'name':'Royal Decree','tag':'relic','rarity':'epic','cost':9,'cooldown':4.4,'power':33,'type':'execute','glyph':'rune','text':'Execute wounded foes; stronger beside relics.'},
})
BOONS = {
 'ferocity': {'name':'Ferocious Oath','glyph':'⚔','text':'+6 to every hero basic attack.'},
 'bulwark': {'name':'Iron Pact','glyph':'◆','text':'Start every fight with 38 more Shield.'},
 'vigor': {'name':'Deep Roots','glyph':'♥','text':'+38 maximum health every fight.'},
 'poisoner': {'name':'Serpent Blood','glyph':'☠','text':'Your poison items apply +3 Poison.'},
 'pyromancer': {'name':'Wildfire Pact','glyph':'✹','text':'Your burn items apply +3 Burn.'},
 'temporal': {'name':'Quick Hands','glyph':'◷','text':'All your item cooldowns are 8% shorter.'},
 'merchant': {'name':'Guild Discount','glyph':'◈','text':'Everything in your shops costs 1 less Gold.'},
 'windfall': {'name':'Buried Fortune','glyph':'✦','text':'Gain 6 Gold immediately.'},
 'medic': {'name':'Field Surgeon','glyph':'✚','text':'Your healing items restore +10 health.'},
 'scavenger': {'name':'Aftermarket','glyph':'⚙','text':'Machine items have 15% shorter cooldowns.'},
 'purifier': {'name':'Silver Soul','glyph':'◇','text':'Begin every battle with 1 less incoming Poison/Burn per tick.'},
 'drainer': {'name':'Crimson Pact','glyph':'♜','text':'Recover 8% of unshielded direct damage dealt.'},
 'focus': {'name':'Arcane Focus','glyph':'✧','text':'+5 item power for damage, poison and burn.'},
 'interest': {'name':'Clever Investor','glyph':'♢','text':'Gain +3 extra Gold at the start of later rounds.'},
}
MAX_SLOTS = 6
SHOP_SIZE = 5
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
    upgrades: list = field(default_factory=lambda: [0] * MAX_SLOTS)
    boons: list = field(default_factory=list)
    boon_choices: list = field(default_factory=list)
    boon_chosen: bool = False
    shop: list = field(default_factory=list)
    ready: bool = False
    last_seen: float = field(default_factory=time.monotonic)
    seen_actions: dict = field(default_factory=dict)

    def public(self, viewer: bool = False):
        out = dict(name=self.name, hero=self.hero, ready=self.ready, connected=self.connected,
                   wins=self.wins, board=self.board, upgrades=self.upgrades, boons=self.boons, bot=self.bot)
        if viewer:
            out.update(gold=self.gold, shop=self.shop, boonChoices=self.boon_choices, boonChosen=self.boon_chosen, discount=int("merchant" in self.boons))
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
            if self.round > 1 and 'interest' in p.boons: p.gold += 3
            p.shop = self.roll_shop(p)
            p.boon_choices = self.roll_boons(p)
            p.boon_chosen = False
            if p.bot:
                self.choose_boon(p, self.rng.randrange(len(p.boon_choices)))
                self.bot_shop(p)
                p.ready = True
        self.events.appendleft(f'Round {self.round} · The market is open')
        self.revision += 1

    def roll_shop(self, p=None):
        # A themed slot allows pursuing a coherent build, while variety keeps
        # choices interesting. Round 1 contains fewer expensive dead offers.
        affinity = {'vex':('weapon','machine'),'nyra':('potion','relic'),
                    'bronn':('machine','relic'),'cael':('relic','weapon')}
        hero = p.hero if p else 'vex'
        themed = [k for k,v in ITEMS.items() if v['tag'] in affinity[hero]
                  and (self.round > 1 or v['cost'] <= 6)]
        options = [self.rng.choice(themed)]
        rest = [k for k in ITEMS if k not in options and (self.round > 1 or ITEMS[k]['cost']<=6)]
        # Rarity weight increases in later rounds, without ever guaranteeing
        # the player can afford everything in a shop.
        weights = {'common':5,'rare':3,'epic':1} if self.round==1 else {'common':3,'rare':5,'epic':3}
        while len(options) < SHOP_SIZE:
            total = sum(weights[ITEMS[k]['rarity']] for k in rest)
            point = self.rng.randrange(total)
            for j,k in enumerate(rest):
                point -= weights[ITEMS[k]['rarity']]
                if point < 0:
                    options.append(rest.pop(j));break
        return options

    def roll_boons(self, p):
        available=[k for k in BOONS if k not in p.boons]
        return self.rng.sample(available, 3)

    @staticmethod
    def item_cost(p, key):
        return max(1, ITEMS[key]['cost'] - int('merchant' in p.boons))

    def choose_boon(self, p, index):
        if p.boon_chosen: raise GameError('You already chose a blessing this round.')
        i=checked_int(index,0,len(p.boon_choices)-1)
        chosen=p.boon_choices[i]
        p.boons.append(chosen)
        p.boon_chosen=True
        if chosen=='windfall': p.gold+=6
        self.events.appendleft(f'{p.name} pledged {BOONS[chosen]["name"]}')

    def bot_shop(self, p):
        # Bot chooses useful synergy items from its shop, keeping within budget.
        preferred = {'vex':('weapon','machine'),'nyra':('potion','relic'),'bronn':('machine','relic'),'cael':('relic','weapon')}[p.hero]
        available = sorted(p.shop, key=lambda k: (ITEMS[k]['tag'] in preferred, ITEMS[k]['cost']), reverse=True)
        for key in available:
            if key in p.shop and p.gold >= self.item_cost(p,key) and None in p.board:
                p.gold -= self.item_cost(p,key)
                slot=p.board.index(None); p.board[slot] = key; p.upgrades[slot]=0
                p.shop.remove(key)
        for slot,key in enumerate(p.board):
            if key and p.upgrades[slot]<1 and p.gold>=5:
                p.gold-=5;p.upgrades[slot]=1;break

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
                    x.upgrades=[0]*MAX_SLOTS; x.boons=[]; x.boon_choices=[]; x.boon_chosen=False
                self.start_shop()
            self.revision += 1
            return
        if self.phase != 'shop': raise GameError('Wait until the market opens.')
        if p.ready and op != 'unready': raise GameError('Already ready. Unready to edit.')
        if op == 'buy':
            i = checked_int(payload.get('index'), 0, len(p.shop)-1)
            key = p.shop[i]
            cost = self.item_cost(p,key)
            if p.gold < cost: raise GameError('Not enough gold.')
            if None not in p.board: raise GameError('Your board is full.')
            p.gold -= cost
            slot=p.board.index(None);p.board[slot]=key;p.upgrades[slot]=0
            p.shop.pop(i)
            self.events.appendleft(f'{p.name} acquired {ITEMS[key]["name"]}')
        elif op == 'reroll':
            if p.gold < 2: raise GameError('Need 2 gold to refresh.')
            p.gold -= 2
            p.shop = self.roll_shop(p)
        elif op == 'move':
            a = checked_int(payload.get('from'), 0, MAX_SLOTS-1)
            b = checked_int(payload.get('to'), 0, MAX_SLOTS-1)
            if p.board[a] is None: raise GameError('No item in that slot.')
            p.board[a],p.board[b] = p.board[b],p.board[a]
            p.upgrades[a],p.upgrades[b] = p.upgrades[b],p.upgrades[a]
        elif op == 'sell':
            i = checked_int(payload.get('index'), 0, MAX_SLOTS-1)
            k = p.board[i]
            if k is None: raise GameError('Empty slot.')
            p.gold += max(1, ITEMS[k]['cost']//2) + p.upgrades[i]*2
            p.board[i] = None
            p.upgrades[i]=0
        elif op == 'boon':
            self.choose_boon(p, payload.get('index'))
        elif op == 'upgrade':
            i=checked_int(payload.get('index'),0,MAX_SLOTS-1)
            if p.board[i] is None: raise GameError('There is no item to upgrade.')
            if p.upgrades[i]>=2: raise GameError('Item is already fully upgraded.')
            cost=5+3*p.upgrades[i]
            if p.gold<cost: raise GameError('Not enough gold to forge.')
            p.gold-=cost;p.upgrades[i]+=1
            self.events.appendleft(f'{p.name} forged {ITEMS[p.board[i]]["name"]} to +{p.upgrades[i]}')
        elif op == 'ready':
            # Old clients remain playable: their first offered boon becomes
            # the fallback rather than preventing the battle from starting.
            if not p.boon_chosen: self.choose_boon(p,0)
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
            hp = hero['hp'] + (38 if 'vigor' in p.boons else 0)
            fighter.append(dict(name=p.name, hp=hp,maxHp=hp, shield=(30 if p.hero=='bronn' else 0)+(38 if 'bulwark' in p.boons else 0),
                poison=0,burn=0,haste=0.0,slow=0.0,thorns=0,basic=0.0, cds=[self.rng.random()*0.5 for _ in p.board],
                hero=p.hero, board=list(p.board), upgrades=list(p.upgrades)))
        self.battle = dict(elapsed=0.0, fighters=fighter, effects=[], sequence=0)
        self.events.appendleft('⚔ The duel has begun')

    def apply_hit(self, source: int, target: int, power: float, kind: str, label: str):
        b=self.battle
        src, tar=b['fighters'][source], b['fighters'][target]
        dealt=max(0,int(power))
        if 'purifier' in self.players[target].boons and kind in ('poison','fire'):
            dealt=max(0,dealt-2)
        blocked=min(tar['shield'],dealt)
        tar['shield']-=blocked
        actual=dealt-blocked
        tar['hp']=max(0,tar['hp']-actual)
        if actual and tar.get('thorns',0) and source!=target and kind not in ('reflect',):
            reflected=min(15,tar['thorns'])
            src['hp']=max(0,src['hp']-reflected)
            b['effects'].append(dict(source=target,target=source,amount=reflected,
                                     blocked=0,kind='reflect',label='Briar Aegis',seq=b['sequence']))
            b['sequence']+=1
        if actual and source!=target and kind not in ('reflect',) and 'drainer' in self.players[source].boons:
            src['hp']=min(src['maxHp'],src['hp']+max(1,int(actual*.08)))
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
                power=hero['attack']+(5 if p.hero=='vex' else 0)+(6 if 'ferocity' in p.boons else 0)
                self.apply_hit(i,1-i,power,'hit',hero['power'])
            for j,k in enumerate(f['board']):
                if not k: continue
                item=ITEMS[k]
                cooldown=item['cooldown'] * (0.78 if p.hero=='cael' else 1.0)
                if f['haste']>0: cooldown*=0.78
                if 'temporal' in p.boons: cooldown*=.92
                if item['tag']=='machine' and 'scavenger' in p.boons: cooldown*=.85
                if f['slow']>0: cooldown*=1.35
                f['cds'][j]-=dt
                if f['cds'][j] > 0: continue
                f['cds'][j]+=max(.6,cooldown)
                adj=[x for x in f['board'][max(0,j-1):j]+f['board'][j+1:j+2] if x]
                synergy=sum(ITEMS[x]['tag']==item['tag'] for x in adj)
                amt=item['power']
                if item['type']!='haste':
                    amt=amt * (1+.4*f['upgrades'][j])
                if item['type'] in ('damage','poison','burn','execute','rupture','shatter','slow') and 'focus' in p.boons:
                    amt+=5
                if item['type']=='damage':
                    boost=6 if k in ('dagger','rune') and adj else 0
                    if k=='spark': boost+=10*synergy
                    if k=='blaster': boost+=5*synergy
                    if k=='crossbow': boost+=min(enemy['shield'],20)//2
                    if k=='glaive': boost+=8*synergy
                    if k=='duelist': boost+=5*synergy
                    if k=='cannon': boost+=8*synergy
                    self.apply_hit(i,1-i,amt+boost,'hit',item['name'])
                elif item['type']=='burn':
                    self.apply_hit(i,1-i,amt,'fire',item['name'])
                    enemy['burn']+=min(30,(3 if k=='ember' else 4)+(3 if 'pyromancer' in p.boons else 0))
                elif item['type']=='poison':
                    enemy['poison']=min(120,enemy['poison']+int(amt+2*synergy+(2 if p.hero=='nyra' else 0)+(3 if 'poisoner' in p.boons else 0)))
                    b['effects'].append(dict(source=i,target=1-i,amount=int(amt),kind='poison',label=item['name'],seq=b['sequence']))
                    b['sequence']+=1
                    if k=='toxin': self.apply_hit(i,1-i,8,'hit',item['name'])
                elif item['type']=='heal':
                    restored=min(f['maxHp']-f['hp'],int(amt+5*synergy+(10 if 'medic' in p.boons else 0)))
                    f['hp']+=restored
                    b['effects'].append(dict(source=i,target=i,amount=restored,kind='heal',label=item['name'],seq=b['sequence']))
                    b['sequence']+=1
                elif item['type']=='cleanse':
                    f['poison']=max(0,f['poison']-20)
                    f['burn']=max(0,f['burn']-12)
                    restored=min(f['maxHp']-f['hp'],int(amt+(10 if 'medic' in p.boons else 0)))
                    f['hp']+=restored
                    b['effects'].append(dict(source=i,target=i,amount=restored,kind='heal',label=item['name'],seq=b['sequence']))
                    b['sequence']+=1
                elif item['type']=='shatter':
                    enemy['shield']=max(0,enemy['shield']-int(amt*.8))
                    self.apply_hit(i,1-i,amt,'hit',item['name'])
                elif item['type']=='rupture':
                    self.apply_hit(i,1-i,amt+min(65,enemy['poison']*.55+enemy['burn']*1.5),'poison',item['name'])
                elif item['type']=='execute':
                    extra=.48 if enemy['hp']<enemy['maxHp']*.5 else 0
                    self.apply_hit(i,1-i,amt*(1+extra),'hit',item['name'])
                elif item['type']=='slow':
                    enemy['slow']=max(enemy['slow'],3.0)
                    self.apply_hit(i,1-i,amt,'hit',item['name'])
                elif item['type']=='thorns':
                    f['shield']=min(500,f['shield']+int(amt))
                    f['thorns']=min(20,f['thorns']+4)
                    b['effects'].append(dict(source=i,target=i,amount=int(amt),kind='shield',label=item['name'],seq=b['sequence']))
                    b['sequence']+=1
                elif item['type']=='shield':
                    f['shield']=min(500,f['shield']+int(amt+6*synergy))
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
            if f['slow']>0: f['slow']=max(0,f['slow']-dt)
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