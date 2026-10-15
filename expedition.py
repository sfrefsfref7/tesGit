"""Night Market Expedition: ORIGINAL data and authoritative roguelike mechanics.
Inspired by general autobattler design, NOT a copy of The Bazaar's content/assets.
No client-provided battle scores or state are accepted.
"""
from __future__ import annotations
import math
import random
import secrets
import time
from dataclasses import dataclass, field
from typing import Any
from game import HEROES, ITEMS as DUEL_ITEMS, GameError, valid_hero, valid_name

BOARD_WIDTH = 10
STASH_WIDTH = 10
MAX_SKILLS = 6
DAY_HOURS = 6
WIN_TARGET = 10
RARITY = ('bronze','silver','gold','diamond')
ENCHANTS = ('Fiery','Toxic','Turbo','Icy','Shielded','Radiant','Golden')

# Catalog: all original item names, icons and texts. Descriptive data only, no scraped art.
EXTRA = '''
moonshot|Moonshot Rifle|weapon|damage|rare|2|4.1|47|bow|Two-slot precision rifle
quartermaster|Quartermaster's Bell|relic|haste|rare|2|5.0|0.24|clock|Hastens your whole board
iron_maiden|Iron Maiden|machine|thorns|epic|3|5.5|55|shield|Massive armor and thorns
void_sabre|Void Sabre|weapon|leech|epic|2|4.6|61|dagger|Steals life with heavy blows
smolder_charm|Smolder Charm|relic|burn|common|1|3.3|13|flame|Builds a burning tempo
silk_bandage|Silk Bandage|potion|heal|common|1|2.7|21|heart|Restorative healing
ironclad|Ironclad Engine|machine|shield|epic|3|4.9|69|gear|Reinforced moving fortress
mercury_ink|Mercury Ink|potion|poison|common|1|2.1|5|vial|Speedy poison application
cursed_urn|Cursed Urn|relic|rupture|rare|2|5.3|19|lotus|Explodes harmful statuses
astral_bow|Astral Bow|weapon|damage|epic|2|3.8|52|bow|Magic arrows seek weak points
wyrm_scale|Wyrm Scale|relic|shield|rare|2|3.5|45|shield|Ancient defensive plating
blood_orchid|Blood Orchid|potion|leech|rare|1|3.7|33|lotus|Restores what it steals
storm_pillar|Storm Pillar|machine|slow|epic|3|4.6|26|spark|Electric paralysis
marrow_hook|Marrow Hook|weapon|execute|rare|1|2.9|30|fang|Finish wounded rivals
star_compass|Star Compass|relic|haste|common|1|4.1|0.18|clock|Accelerates cooldowns
alchemist_kit|Alchemist Kit|potion|cleanse|rare|2|3.9|39|vial|Cures and restores health
sand_blade|Sand Blade|weapon|damage|common|1|2.4|25|dagger|Well-balanced cutting edge
bonfire|Bonfire Engine|machine|burn|rare|2|4.1|31|flame|Persistent incineration
ivory_mask|Ivory Mask|relic|cleanse|epic|2|5.2|59|heart|Heals and cures negative effects
royal_ballista|Royal Ballista|machine|shatter|epic|3|5.4|81|bow|Strips shields before firing
spore_bag|Spore Bag|potion|poison|rare|2|4.0|11|lotus|A slow poisonous cloud
copper_watch|Copper Watch|relic|haste|common|1|4.3|0.16|clock|A reliable timing device
frost_anchor|Frost Anchor|machine|freeze|rare|2|4.7|9|clock|Freezes a rival item briefly
storm_whistle|Storm Whistle|relic|charge|rare|1|4.0|1.3|spark|Charges adjacent cooldowns
flame_lash|Flame Lash|weapon|burn|rare|2|3.0|33|flame|Binds opponents in flame
thorn_crown|Thorn Crown|relic|thorns|rare|2|4.3|32|shield|Punishes aggressive attacks
ruby_hammer|Ruby Hammer|weapon|damage|epic|3|5.6|92|gear|A devastating heavy hit
ancient_twine|Ancient Twine|relic|shield|common|1|2.8|27|rune|Woven protective energy
catalyst|Catalyst Furnace|machine|burn|epic|3|5.1|54|flame|Burns through stubborn defenses
crystal_needle|Crystal Needle|weapon|crit|rare|1|2.5|27|dagger|Critical strikes accelerate
silver_cogs|Silver Cogs|machine|haste|common|1|3.8|0.20|gear|Momentum for machines
basilisk_eye|Basilisk Eye|relic|freeze|epic|2|5.1|12|mirror|Freezes opposing items
solstice_rose|Solstice Rose|potion|regen|rare|2|4.6|20|lotus|Gain enduring regeneration
sky_harvester|Sky Harvester|machine|damage|epic|3|5.5|85|gear|Slow giant engine strike
witch_brew|Witch's Brew|potion|poison|epic|2|4.5|14|vial|Long-lasting toxin
sun_ward|Sun Ward|relic|shield|common|1|3.0|30|shield|A radiant barrier
hunter_scope|Hunter's Scope|relic|crit|rare|1|3.7|21|mirror|Consistent critical power
arc_conductor|Arc Conductor|machine|charge|rare|2|4.6|1.9|spark|Charges neighboring devices
midnight_veil|Midnight Veil|relic|slow|epic|2|4.5|25|mirror|Enemy cooldowns lengthen
amber_rejuvenator|Amber Rejuvenator|potion|regen|epic|2|4.8|34|heart|A healing aura grows
emerald_gong|Emerald Gong|relic|haste|rare|2|4.2|0.23|clock|A resonant timing pulse
flintlock|Flintlock Salvo|weapon|damage|common|1|2.0|22|bow|Rapid-fire wrist-mounted cannon
mystic_bloom|Mystic Bloom|potion|heal|rare|2|4.2|52|lotus|Restorative flowering
sea_glass|Sea Glass Guard|relic|shatter|rare|1|3.4|28|mirror|Fragile barriers shattered
hollow_bell|Hollow Bell|relic|charge|epic|2|4.3|2.0|clock|Energizes nearby tools
searing_chain|Searing Chain|weapon|burn|epic|2|3.7|42|flame|An unending stream of sparks
onyx_cannon|Onyx Cannon|machine|crit|epic|3|5.7|83|gear|Devastating charged critical shot
jungle_root|Jungle Root|potion|regen|common|1|3.7|13|lotus|Nature's slow restoration
'''

def create_catalog():
    data={}
    for key, item in DUEL_ITEMS.items():
        d=dict(item)
        d['size']=3 if key in ('cannon','engine','phoenix') else 2 if key in ('glaive','harpoon','prism','bulwark','meteor','plague_mask','royal_decree') else 1
        d['tier']=0 if d['rarity']=='common' else 1 if d['rarity']=='rare' else 2
        data[key]=d
    for line in EXTRA.strip().splitlines():
        key,name,tag,kind,rarity,size,cd,power,glyph,desc=line.split('|')
        data[key]={'name':name,'tag':tag,'rarity':rarity,'cost':(3 if rarity=='common' else 6 if rarity=='rare' else 9)+int(size)-1,
                   'cooldown':float(cd),'power':float(power),'type':kind,'glyph':glyph,'text':desc,'size':int(size),
                   'tier':0 if rarity=='common' else 1 if rarity=='rare' else 2}
    return data
CATALOG=create_catalog()

SKILLS = {
  'trigger_finger':{'name':'Hair-Trigger','tag':'weapon','text':'Weapon cooldowns -12%.','icon':'⚔'},
  'accelerator':{'name':'Overclock','tag':'machine','text':'Machine cooldowns -14%.','icon':'⚙'},
  'toxicologist':{'name':'Venom Scholar','tag':'potion','text':'Apply 3 bonus Poison.','icon':'☠'},
  'wildfire':{'name':'Cinder Connoisseur','tag':'potion','text':'Apply 3 bonus Burn.','icon':'✹'},
  'paladin':{'name':'Aegis Keeper','tag':'relic','text':'Shield effects +22%.','icon':'◆'},
  'meditation':{'name':'Stillwater','tag':'relic','text':'Healing effects +25%.','icon':'✚'},
  'chronologist':{'name':'Temporal Craft','tag':'relic','text':'All item cooldowns -7%.','icon':'◷'},
  'marksmanship':{'name':'Sharpsight','tag':'weapon','text':'Direct damage +15%.','icon':'◎'},
  'iron_lungs':{'name':'Iron Lungs','tag':'machine','text':'Starting shield +40.','icon':'▣'},
  'alchemy':{'name':'Sublime Alchemy','tag':'potion','text':'Poison/Burn effects last longer.','icon':'◇'},
  'ruthless':{'name':'Last Word','tag':'weapon','text':'Deal more damage below enemy half HP.','icon':'♜'},
  'regrowth':{'name':'Second Spring','tag':'potion','text':'Restore 3 HP each second.','icon':'❀'},
  'affinity':{'name':'Resonance','tag':'relic','text':'Adjacent same-type items +10% power.','icon':'✧'},
  'treasurer':{'name':'Merchant Mind','tag':'relic','text':'Earn 3 Gold each new day.','icon':'◈'},
  'scrapper':{'name':'Resourceful','tag':'machine','text':'Extra 2 Gold after monster wins.','icon':'⌘'},
  'sanctuary':{'name':'Sanctuary','tag':'relic','text':'Poison and Burn deal less damage.','icon':'♧'},
  'broker':{'name':'Golden Tongue','tag':'relic','text':'Buy items for 1 less Gold (minimum 1).','icon':'◈'},
  'salvager':{'name':'Junk to Jewels','tag':'machine','text':'Selling items gives 2 extra Gold.','icon':'⚙'},
  'bounty_hunter':{'name':'Bounty Ledger','tag':'weapon','text':'Monster victories grant 2 bonus XP.','icon':'♜'},
  'deep_pockets':{'name':'Deep Pockets','tag':'relic','text':'Gain 4 bonus Gold at the start of a new day.','icon':'◈'},
  'icebreak':{'name':'Unfrozen Will','tag':'relic','text':'Your items recover from Freeze more quickly.','icon':'❄'},
  'shrouded':{'name':'Smoke and Mirrors','tag':'relic','text':'Begin battles with an additional 55 Shield.','icon':'◇'},
  'twin_blades':{'name':'Twin Blades','tag':'weapon','text':'Basic attack +4 per equipped Weapon, max +16.','icon':'⚔'},
  'bloomcraft':{'name':'Corrosive Bloom','tag':'potion','text':'Poison ticks deal 20% additional damage.','icon':'☠'},
  'firebrand':{'name':'Cinderheart','tag':'potion','text':'Burn ticks deal 20% additional damage.','icon':'✹'},
  'heartwood':{'name':'Heartwood','tag':'potion','text':'Every heal grants 20% of its amount as Shield.','icon':'❀'},
  'quickdraw':{'name':'Quickdraw','tag':'weapon','text':'Basic hero attacks 15% faster.','icon':'➶'},
  'spellbinder':{'name':'Spellbinder','tag':'relic','text':'Charge item effects become 25% stronger.','icon':'✦'},
  'artful':{'name':'Fine Craft','tag':'machine','text':'Enchantments cost 6 instead of 9 Gold.','icon':'⚒'},
  'zealot':{'name':'Last Stand','tag':'weapon','text':'Attacks deal 12% more damage below 40% health.','icon':'♞'},
  'apothecary':{'name':'Field Remedy','tag':'potion','text':'Every 5 seconds recover 10 HP.','icon':'✚'},
  'cleanslate':{'name':'Clear Sky','tag':'relic','text':'Reduce incoming Poison tick damage by 25%.','icon':'◇'},
}

EVENTS = [
 ('pawn','Pawnbroker','Sell one item for an enhanced price or take 4 Gold'),
 ('forge','Forge Master','Enhance an equipped item, or receive free materials'),
 ('oracle','Starlight Oracle','Choose a new permanent skill'),
 ('inn','Twilight Inn','Rest to gain maximum health, or take Gold'),
 ('rift','Void Rift','Take a risk for high reward'),
 ('auction','Mysterious Auction','Gain a random relic or a bag of gold'),
 ('garden','Moon Garden','Increase health and regenerate'),
 ('clocktower','Clock Tower','Improve speed and item cooldowns'),
 ('shrine','Shrine of Echoes','Choose protection, enlightenment or a fortune'),
 ('runes','Runebound Crossing','Choose magic or money'),
 ('scrapyard','Clockwork Scrapyard','Improve your machinery or gain salvage'),
 ('carnival','Lantern Carnival','Take a measured gamble'),
 ('guild','Night Guild','Learn from the shadow merchants'),
 ('sanctum','Sanctum of Roots','Strengthen your vitality'),
 ('alley','Silver Alley','Trade opportunities under moonlight'),
 ('archives','Forbidden Archives','Open books that should stay closed'),
 ('cave','Crystal Cave','Acquire an enchanted artifact or materials'),
 ('tavern','The Glass Tavern','Swap rumors for power'),
 ('arena','Training Arena','Prepare for the next battle'),
 ('observatory','The Observatory','Look into distant possibilities'),
 ('bridge','Whisper Bridge','Listen to the river spirit'),
 ('council','Council of Ash','Choose a boon before nightfall'),
 ('reliquary','Ancient Reliquary','Seek equipment from an old era'),
 ('gamble','The Loaded Dice','Risk your fortune'),
 ('trader','Opal Exchange','Invest your income'),
 ('fountain','Fountain of Dawn','Restore your spirit or secure wealth'),
 ('thicket','Silverwood Thicket','Scavenge rare materials'),
 ('tower','The Last Bell Tower','Learn an ancient skill'),
]
MONSTERS = [
 ('Gutter Imp','weapon','damage'),('Scavenger Bot','machine','shield'),('Glass Wraith','relic','slow'),
 ('Toxic Basilisk','potion','poison'),('Ash Hound','weapon','burn'),('Clockwork Guardian','machine','damage'),
 ('Crystal Leviathan','relic','shatter'),('Storm Matron','machine','freeze'),('Shadow Collector','relic','leech'),
 ('Dusk Hydra','potion','regen'),('Abyssal Knight','weapon','execute'),('Ancient Colossus','machine','shield'),
 ('Sunken Marauder','weapon','leech'),('Violet Drake','relic','burn'),('Ember Sentry','machine','burn'),
 ('Dustborne Duelist','weapon','crit'),('Cinder Oracle','potion','heal'),('Iron Serpent','machine','poison'),
 ('Moth Queen','relic','haste'),('Hollow Captain','weapon','shatter'),('Pearl Golem','relic','shield'),
 ('Frost Revenant','relic','freeze'),('Pale Harvester','weapon','execute'),('Bog Witch','potion','rupture'),
 ('Gilded Watcher','machine','charge'),('Forgotten Artisan','machine','crit'),('Scarlet Griffin','weapon','burn'),
 ('Gloom Siren','relic','slow'),('Thornbound King','potion','thorns'),('Obsidian Widow','potion','poison'),
 ('Steam Colossus','machine','damage'),('Moon Templar','weapon','shield'),('Rune Collector','relic','charge'),
 ('Sable Merchant','relic','leech'),('Grave Apothecary','potion','cleanse'),('Aurora Stag','potion','regen'),
]

@dataclass
class Run:
    name:str
    hero:str
    token:str=field(default_factory=lambda:secrets.token_urlsafe(32))
    seed:int=field(default_factory=lambda:secrets.randbits(48))
    day:int=1
    hour:int=1
    gold:int=14
    level:int=1
    xp:int=0
    prestige:int=20
    wins:int=0
    losses:int=0
    max_health:int=280
    board:list=field(default_factory=lambda:[None]*BOARD_WIDTH)
    stash:list=field(default_factory=list)
    inventory:dict=field(default_factory=dict)
    skills:list=field(default_factory=list)
    phase:str='route'
    route:list=field(default_factory=list)
    selected:dict=field(default_factory=dict)
    offers:list=field(default_factory=list)
    last_battle:dict|None=None
    revision:int=0
    created:float=field(default_factory=time.monotonic)
    last_active:float=field(default_factory=time.monotonic)
    seen:dict=field(default_factory=dict)
    history:list=field(default_factory=list)
    guided:bool=False
    pending_levels:int=0
    enemy_loadout:list=field(default_factory=list)
    income:int=5

    def __post_init__(self):
        self.name=valid_name(self.name)
        self.hero=valid_hero(self.hero)
        self.rng=random.Random(self.seed)
        self.max_health=HEROES[self.hero]['hp']+45
        first={'vex':'dagger','nyra':'venom','bronn':'ward','cael':'sundial'}[self.hero]
        self.obtain(first, board_slot=0)
        self.route=self.make_route()
        if self.guided:self.phase='starter'
        self.history.append('Day 1 — entered the Midnight Exchange')

    def new_item(self,key,tier=None,enchant=None):
        if key not in CATALOG:raise GameError('Unknown item.')
        uid=secrets.token_hex(6)
        obj={'uid':uid,'key':key,'tier':CATALOG[key]['tier'] if tier is None else int(tier),'enchant':enchant}
        self.inventory[uid]=obj
        return uid

    def occupied_size(self,uids):
        return sum(CATALOG[self.inventory[x]['key']]['size'] for x in uids)

    def obtain(self,key,board_slot=None,tier=None,enchant=None):
        uid=self.new_item(key,tier,enchant)
        size=CATALOG[key]['size']
        if board_slot is not None and self.can_place(uid,board_slot):
            for pos in range(board_slot,board_slot+size):self.board[pos]=uid
        elif self.occupied_size(self.stash)+size<=STASH_WIDTH:
            self.stash.append(uid)
        else:
            del self.inventory[uid]
            raise GameError('Stash is full. Sell or move equipment first.')
        return uid

    @property
    def board_limit(self):
        return min(BOARD_WIDTH, 4+max(0,self.level-1)*2)

    def can_place(self,uid,start):
        if uid not in self.inventory:return False
        size=CATALOG[self.inventory[uid]['key']]['size']
        return type(start) is int and 0<=start<=self.board_limit-size and all(x in (None,uid) for x in self.board[start:start+size])

    def equip(self,uid,start):
        if uid not in self.inventory:raise GameError('Unknown equipment.')
        if not self.can_place(uid,start):raise GameError('Equipment does not fit those slots.')
        self.board=[None if x==uid else x for x in self.board]
        if uid in self.stash:self.stash.remove(uid)
        for j in range(start,start+CATALOG[self.inventory[uid]['key']]['size']):self.board[j]=uid

    def store(self,uid):
        if uid not in self.inventory:raise GameError('Unknown equipment.')
        if uid in self.stash:return
        if self.occupied_size(self.stash)+CATALOG[self.inventory[uid]['key']]['size']>STASH_WIDTH:
            raise GameError('Stash is full.')
        if uid not in self.board:raise GameError('Equipment not on board.')
        self.board=[None if x==uid else x for x in self.board]
        self.stash.append(uid)

    def sell(self,uid):
        if uid not in self.inventory:raise GameError('Unknown equipment.')
        obj=self.inventory.pop(uid)
        self.board=[None if x==uid else x for x in self.board]
        if uid in self.stash:self.stash.remove(uid)
        item=CATALOG[obj['key']]
        self.gold+=max(1,int(item['cost']*.5*(1.5**(obj['tier']-item['tier']))))+(3 if obj['enchant']=='Golden' else 0)+(2 if 'salvager' in self.skills else 0)

    def starter_options(self):
        return [
            {'key':'economy','title':'Guild Patronage','text':'Receive 10 Gold and +2 permanent income.', 'icon':'◈'},
            {'key':'enchantment','title':'Arcane Inheritance','text':'Receive a hero-aligned enchanted Small item.', 'icon':'✦'},
            {'key':'training','title':'Master\'s Lesson','text':'Learn a permanent skill suited to your hero.', 'icon':'⚔'},
        ]

    def level_options(self):
        return [
            {'key':'fortify','title':'Vitality Training','text':'Gain 60 maximum Health.', 'icon':'❤'},
            {'key':'fortune','title':'Merchant Dividend','text':'Receive 8 Gold immediately.', 'icon':'◈'},
            {'key':'mastery','title':'Refine Your Craft','text':'Upgrade one equipped item by a tier, or gain 5 Gold.', 'icon':'⚒'},
        ]

    def choose_starter(self,key):
        if self.phase!='starter':raise GameError('Starting choice is no longer available.')
        if key not in {o['key'] for o in self.starter_options()}:raise GameError('Invalid starting option.')
        if key=='economy': self.gold+=10;self.income+=2
        elif key=='enchantment':
            tag={'vex':'weapon','nyra':'potion','bronn':'machine','cael':'relic'}[self.hero]
            options=[k for k,v in CATALOG.items() if v['tag']==tag and v['size']==1 and v['tier']==0]
            if not options:options=[k for k,v in CATALOG.items() if v['size']==1 and v['tier']==0]
            self.obtain(self.rng.choice(options),enchant=self.rng.choice(['Fiery','Toxic','Turbo','Shielded']))
        else:
            tag={'vex':'weapon','nyra':'potion','bronn':'machine','cael':'relic'}[self.hero]
            candidates=[k for k,v in SKILLS.items() if v['tag']==tag]
            self.skills.append(self.rng.choice(candidates))
        self.phase='route'
        self.history.insert(0,'Starting boon: '+next(o['title'] for o in self.starter_options() if o['key']==key))

    def choose_level(self,key):
        if self.phase!='levelup' or self.pending_levels<=0:raise GameError('Not at a level-up reward.')
        if key not in {o['key'] for o in self.level_options()}:raise GameError('Unknown level-up reward.')
        if key=='fortify':self.max_health+=60
        elif key=='fortune':self.gold+=8
        else:
            possible=[uid for uid in dict.fromkeys(self.board) if uid and self.inventory[uid]['tier']<3]
            if possible:self.inventory[self.rng.choice(possible)]['tier']+=1
            else:self.gold+=5
        self.pending_levels-=1
        self.phase='levelup' if self.pending_levels else 'route'
        self.history.insert(0, 'Level-up reward: '+key)

    def merchant_roll(self,count=4,tag=None):
        choices=[key for key,item in CATALOG.items() if (not tag or item['tag']==tag)]
        weights=[]
        for key in choices:
            rarity=CATALOG[key]['rarity']
            value=(5 if rarity=='common' else 3 if rarity=='rare' else 1)
            if self.day>=5 and rarity=='epic':value*=4
            if CATALOG[key]['tag'] in {'vex':'weapon','nyra':'potion','bronn':'machine','cael':'relic'}[self.hero]:value*=2
            weights.append(value)
        if count>len(choices):count=len(choices)
        result=[]
        for _ in range(count):
            idx=self.rng.choices(range(len(choices)),weights=weights,k=1)[0]
            result.append(choices.pop(idx));weights.pop(idx)
        return result

    def make_route(self):
        if self.hour==3:
            # Each choice has a different risk/reward profile, rather than cosmetic tiers.
            challengers=self.rng.sample(MONSTERS,3)
            labels=('BRONZE','SILVER','GOLD')
            return [{'type':'monster','title':enemy[0], 'tag':enemy[1], 'style':enemy[2],
                     'difficulty':i, 'rank':labels[i],
                     'rewardGold':4+self.day//2+3*i, 'rewardXP':3+i,
                     'description':f'{labels[i]} HUNT · {4+self.day//2+3*i} Gold, {3+i} XP and a loot drop'}
                    for i,enemy in enumerate(challengers)]
        if self.hour==DAY_HOURS: return [{'type':'rival','title':'The Midnight Duel','description':'Fight a rival phantom. Win to earn a victory crest.'}]
        candidates=[
            {'type':'merchant','title':'Wandering Armorer','description':'Weapons, fast strikes and blades','merchantTag':'weapon'},
            {'type':'merchant','title':'Curio Caravan','description':'Relics and enchanted curios','merchantTag':'relic'},
            {'type':'trainer','title':'Master of Techniques','description':'Acquire special skills and enchantments'},
            {'type':'monster','title':'Hunt the Night','description':'Fight a creature for gold, XP and loot'},
            {'type':'event','title':self.rng.choice(EVENTS)[1],'description':'A strange opportunity approaches'},
            {'type':'event','title':'The Fortune Alley','description':'Take risks or safe rewards'},
            {'type':'merchant','title':'Shadow Apothecary','description':'Poisons, restoratives and reagents','merchantTag':'potion'},
            {'type':'merchant','title':'Clockwork Artisan','description':'Mechanical devices and automatons','merchantTag':'machine'},
            {'type':'rest','title':'Quiet Courtyard','description':'Free gold, healing or preparation'},
        ]
        picks=self.rng.sample(candidates,3)
        if self.hour==1 and self.day==1 and not any(x['type']=='merchant' for x in picks):picks[0]=candidates[0]
        return picks

    def pick(self,index):
        if self.phase!='route':raise GameError('First finish the current encounter.')
        if type(index) is not int or not 0<=index<len(self.route):raise GameError('Invalid encounter.')
        e=self.route[index]
        self.selected=e.copy()
        kind=e['type']
        if kind in ('merchant','trainer'):
            self.offers=self.merchant_roll(5,e.get('merchantTag')) if kind=='merchant' else self.rng.sample([k for k in SKILLS if k not in self.skills],min(3,len(SKILLS)-len(self.skills)))
            self.phase=kind
        elif kind=='event':
            self.phase='event'
            # Distinct rewards across event types; all rolled on the server.
            kind=sum(map(ord,e['title']))%5
            self.offers=[
                ['treasure','vitality','arcana'],
                ['relic','vitality','treasure'],
                ['skill','treasure','gamble'],
                ['forge','arcana','relic'],
                ['gamble','skill','vitality'],
            ][kind]
        elif kind=='rest':
            self.phase='rest';self.offers=['gold','health','xp']
        elif kind in ('monster','rival'):
            self.phase='encounter'
            enemy=(e['title'],e.get('tag','weapon'),e.get('style','damage')) if kind=='monster' else self.rng.choice(MONSTERS)
            if kind=='rival':
                enemy=('The Wandering Duelist' if self.day%2 else 'The Veiled Magistrate',self.rng.choice(('weapon','machine','potion','relic')),'damage')
            self.selected={'type':kind,'title':enemy[0],'tag':enemy[1],'style':enemy[2],'day':self.day,
                           'difficulty':e.get('difficulty',1), 'rank':e.get('rank','SILVER'),
                           'rewardGold':e.get('rewardGold',4+self.day//2),'rewardXP':e.get('rewardXP',3)}
            self.offers=['fight']
            pool=[k for k,v in CATALOG.items() if v['tag']==self.selected['tag']]
            self.enemy_loadout=[self.rng.choice(pool) for _ in range(min(7,2+self.day//2))]

    def advance(self):
        self.selected={};self.offers=[]
        self.hour+=1
        self.xp+=1
        while self.xp>=8 and self.level<20:
            self.level+=1;self.xp-=8;self.max_health+=42
            if self.guided:self.pending_levels+=1
            self.gold+=4
            self.history.insert(0,f'Level {self.level}! Gained 42 max HP and 4 Gold')
        if self.hour>DAY_HOURS:
            self.day+=1;self.hour=1;self.gold+=self.income+4+(3 if 'treasurer' in self.skills else 0)+(4 if 'deep_pockets' in self.skills else 0)
            self.history.insert(0,f'Day {self.day} begins — received income')
        self.route=self.make_route();self.phase='levelup' if self.pending_levels else 'route'

    def available(self):
        if self.phase=='starter':return self.starter_options()
        if self.phase=='levelup':return self.level_options()
        if self.phase=='merchant':return [{'key':k,'price':CATALOG[k]['cost']} for k in self.offers]
        if self.phase=='trainer':return [{'key':k,'price':6+self.day} for k in self.offers]
        return self.offers

    def action(self,op:str,data:dict):
        if self.phase in ('won','lost'):raise GameError('Run has finished. Start a new run.')
        if op=='starter':self.choose_starter(data.get('choice'));self.revision+=1;return None
        if op=='level_reward':self.choose_level(data.get('choice'));self.revision+=1;return None
        if op=='choose':
            self.pick(data.get('index'));self.revision+=1;return None
        if op in ('equip','store','sell','combine','upgrade','enchant') and self.phase in ('route','merchant','trainer','event','rest','encounter'):
            uid=data.get('uid')
            if type(uid) is not str or uid not in self.inventory:raise GameError('Unknown equipment.')
            if op=='equip':self.equip(uid,data.get('slot'))
            elif op=='store':self.store(uid)
            elif op=='sell':self.sell(uid)
            elif op=='combine':
                other=data.get('other')
                if other==uid or other not in self.inventory:raise GameError('Choose a second copy to combine.')
                primary=self.inventory[uid];duplicate=self.inventory[other]
                if primary['key']!=duplicate['key'] or primary['tier']!=duplicate['tier'] or primary['tier']>=3:
                    raise GameError('Combine two identical items of the same tier below Diamond.')
                self.board=[None if x==other else x for x in self.board]
                if other in self.stash:self.stash.remove(other)
                del self.inventory[other]
                primary['tier']+=1
            elif op=='upgrade':
                obj=self.inventory[uid];cost=5+obj['tier']*3
                if obj['tier']>=3:raise GameError('Already Diamond tier.')
                if self.gold<cost:raise GameError('Not enough Gold.')
                self.gold-=cost;obj['tier']+=1
            elif op=='enchant':
                if self.phase!='trainer':raise GameError('Visit a trainer to enchant equipment.')
                effect=data.get('effect')
                if effect not in ENCHANTS:raise GameError('Unknown enchantment.')
                if self.inventory[uid]['enchant']:raise GameError('Already enchanted.')
                if self.gold<(6 if 'artful' in self.skills else 9):raise GameError('Not enough Gold to enchant.')
                self.gold-=(6 if 'artful' in self.skills else 9);self.inventory[uid]['enchant']=effect
            else:raise GameError('Invalid action.')
        elif op=='buy':
            if self.phase!='merchant':raise GameError('Not in a merchant encounter.')
            index=data.get('index')
            if type(index) is not int or index<0 or index>=len(self.offers):raise GameError('Invalid offer.')
            key=self.offers[index];cost=max(1,CATALOG[key]['cost']-(1 if 'broker' in self.skills else 0))
            if self.gold<cost:raise GameError('Not enough Gold.')
            self.obtain(key)
            self.gold-=cost;self.offers.pop(index)
        elif op=='reroll':
            if self.phase!='merchant':raise GameError('Not in a merchant encounter.')
            if self.gold<2:raise GameError('Need 2 Gold to refresh.')
            self.gold-=2;self.offers=self.merchant_roll(5,self.selected.get('merchantTag'))
        elif op=='learn':
            if self.phase!='trainer':raise GameError('Not in a trainer encounter.')
            index=data.get('index')
            if type(index) is not int or not 0<=index<len(self.offers):raise GameError('Invalid skill.')
            key=self.offers[index]
            if key in self.skills or len(self.skills)>=MAX_SKILLS:raise GameError('Skill slots are full.')
            price=6+self.day
            if self.gold<price:raise GameError('Not enough Gold.')
            self.gold-=price;self.skills.append(key);self.offers.pop(index)
        elif op=='event':
            if self.phase not in ('event','rest'):raise GameError('Not in an event encounter.')
            choice=data.get('choice')
            if choice not in self.offers:raise GameError('Invalid event option.')
            if choice in ('treasure','gold'):self.gold+=7+self.day
            elif choice in ('vitality','health'):self.max_health+=40
            elif choice in ('arcana','xp'):self.xp+=4
            elif choice=='relic':
                picks=[k for k,v in CATALOG.items() if v['tag']=='relic']
                self.obtain(self.rng.choice(picks))
            elif choice=='skill':
                options=[k for k in SKILLS if k not in self.skills]
                if options and len(self.skills)<MAX_SKILLS:self.skills.append(self.rng.choice(options))
                else:self.gold+=7
            elif choice=='forge':
                eligible=[uid for uid in dict.fromkeys(self.board) if uid and self.inventory[uid]['tier']<3]
                if eligible:self.inventory[self.rng.choice(eligible)]['tier']+=1
                else:self.gold+=6
            elif choice=='gamble':
                if self.rng.random()<.58:self.gold+=17+self.day
                else:self.max_health=max(80,self.max_health-25)
            self.history.insert(0, f'Encounter reward: {choice}')
            self.advance()
        elif op=='leave':
            if self.phase not in ('merchant','trainer','rest','event'):raise GameError('Cannot leave this encounter.')
            self.advance()
        elif op=='fight':
            if self.phase!='encounter':raise GameError('Choose a combat encounter first.')
            result=self.fight()
            if self.selected['type']=='rival':
                if result['victor']==0:
                    self.wins+=1;self.gold+=7+self.day
                    self.history.insert(0, f'Day {self.day}: Victory crest {self.wins}/{WIN_TARGET}')
                else:
                    self.losses+=1;self.prestige=max(0,self.prestige-self.day)
                    self.history.insert(0, f'Day {self.day}: Lost {self.day} Prestige')
                if self.wins>=WIN_TARGET:self.phase='won'
                elif self.prestige<=0:self.phase='lost'
                else:self.advance()
            else:
                if result['victor']==0:
                    self.gold+=self.selected.get('rewardGold',4+self.day//2)+(2 if 'scrapper' in self.skills else 0)
                    self.xp+=self.selected.get('rewardXP',3)+(2 if 'bounty_hunter' in self.skills else 0)
                    prize=self.merchant_roll(1)[0]
                    try:self.obtain(prize);self.history.insert(0,f'Monster defeated: claimed {CATALOG[prize]["name"]}')
                    except GameError:self.gold+=CATALOG[prize]['cost']//2
                else:
                    self.gold+=1;self.history.insert(0,'Monster survived — 1 Gold consolation')
                self.advance()
            self.revision+=1
            return result
        else:raise GameError('Unknown action.')
        self.revision+=1
        return None

    def hero_strength(self):
        return min(4000,self.max_health+int(50*(self.level-1)))

    def fight(self):
        # Deterministic 100ms simulation. A server-only seed drives both sides;
        # the client receives a time-stamped event timeline, not authority.
        opponent=self.selected
        monster=opponent['type']=='monster'
        selected_keys=list(dict.fromkeys(uid for uid in self.board if uid is not None))
        owned=[]
        for uid in selected_keys:
            positions=[idx for idx,x in enumerate(self.board) if x==uid]
            neighbor_ids=[]
            for slot in (min(positions)-1,max(positions)+1):
                if 0<=slot<BOARD_WIDTH and self.board[slot] and self.board[slot]!=uid:
                    neighbor_ids.append(self.board[slot])
            obj=dict(self.inventory[uid])
            obj['adjTags']=[CATALOG[self.inventory[n]['key']]['tag'] for n in neighbor_ids]
            owned.append(obj)
        enemy_tag=opponent['tag']
        pool=[k for k,v in CATALOG.items() if v['tag']==enemy_tag]
        enemy_n=min(7,2+self.day//2)
        enemy_items=[]
        for k in (self.enemy_loadout or [self.rng.choice(pool) for _ in range(enemy_n)]):
            enemy_items.append({'uid':'enemy'+str(len(enemy_items)),'key':k,'tier':min(3,max(0,(self.day-2)//3)),'enchant':None})
        self.last_battle=simulate(self.hero,owned,self.max_health,self.skills,
                                  'bronn' if opponent['style']=='shield' else self.rng.choice(list(HEROES)),enemy_items,
                                  max(175, 190+self.day*(39 if monster else 48)+(int(opponent.get('difficulty',1))-1)*65 if monster else 190+self.day*48),[],self.rng)
        self.last_battle['enemy']=opponent['title']
        self.last_battle['day']=self.day
        return self.last_battle

    def public(self):
        self.last_active=time.monotonic()
        return {'ok':True,'build':'0.7.0','name':self.name,'hero':self.hero,'day':self.day,'hour':self.hour,
                'gold':self.gold,'level':self.level,'xp':self.xp,'prestige':self.prestige,'wins':self.wins,
                'losses':self.losses,'maxHealth':self.max_health,'boardLimit':self.board_limit,'board':list(self.board),'stash':list(self.stash),
                'inventory':self.inventory,'skills':self.skills,'phase':self.phase,'route':self.route,
                'selected':self.selected,'offers':self.available(),'battle':self.last_battle,
                'revision':self.revision,'history':self.history[:12], 'income':self.income, 'enemyLoadout':self.enemy_loadout if self.phase=='encounter' else [], 'catalog':CATALOG,'skillCatalog':SKILLS,
                'heroCatalog':HEROES}


def simulate(hero_a,board_a,hp_a,skills_a,hero_b,board_b,hp_b,skills_b,rng):
    fighters=[]
    for hero,board,hp,skills in ((hero_a,board_a,hp_a,skills_a),(hero_b,board_b,hp_b,skills_b)):
        fighters.append({'hero':hero,'hp':float(hp),'maxHp':float(hp),'shield':(40.0 if 'iron_lungs' in skills else 0.0)+(55.0 if 'shrouded' in skills else 0.0),
                         'poison':0.0,'burn':0.0,'regen':3 if 'regrowth' in skills else 0.0,
                         'slow':0.0,'haste':0.0,'frozen':0.0,'basic':HEROES[hero]['cadence']*(.85 if 'quickdraw' in skills else 1.0),
                         'board':board,'cds':[max(.25,CATALOG[x['key']]['cooldown']*(.5+rng.random()*.5)) for x in board],
                         'skills':skills})
    events=[]
    seq=0; t=0.0
    def evt(owner,target,kind,amount,label):
        nonlocal seq
        if len(events)<850:
            events.append({'time':round(t,1),'seq':seq,'source':owner,'target':target,'kind':kind,
                           'amount':round(amount,1),'label':label})
        seq+=1
    def hit(owner,target,value,kind,label,pierce=False):
        tar=fighters[target];src=fighters[owner];value=max(0,float(value))
        blocked=0 if pierce else min(value,tar['shield'])
        tar['shield']-=blocked
        actual=value-blocked;tar['hp']=max(0,tar['hp']-actual)
        evt(owner,target,kind,actual,label)
        if blocked:evt(owner,target,'blocked',blocked,label)
        return actual
    for tick in range(380):
        t=(tick+1)*.1
        for i,f in enumerate(fighters):
            enemy=fighters[1-i]
            if f['hp']<=0 or enemy['hp']<=0:continue
            hero=HEROES[f['hero']]
            f['basic']-=.1
            if f['basic']<=0:
                f['basic']+=hero['cadence']*(.85 if 'quickdraw' in f['skills'] else 1.0)
                weapon_count=sum(x['key'] in CATALOG and CATALOG[x['key']]['tag']=='weapon' for x in f['board'])
                basic_damage=hero['attack']+(5 if 'marksmanship' in f['skills'] else 0)+(min(16,4*weapon_count) if 'twin_blades' in f['skills'] else 0)
                hit(i,1-i,basic_damage,'hit',hero['power'])
            for j,obj in enumerate(f['board']):
                item=CATALOG[obj['key']]
                cool=item['cooldown']
                if item['tag']=='weapon' and 'trigger_finger' in f['skills']:cool*=.88
                if item['tag']=='machine' and 'accelerator' in f['skills']:cool*=.86
                if 'chronologist' in f['skills']:cool*=.93
                if f['haste']>0:cool*=.76
                if f['slow']>0 and obj.get('enchant')!='Radiant':cool*=1.38
                if f['frozen']>0 and obj.get('enchant')!='Radiant':continue
                f['cds'][j]-=.1
                if f['cds'][j]>0:continue
                f['cds'][j]+=max(.45,cool)
                same=sum(tag==item['tag'] for tag in obj.get('adjTags',[])) if 'adjTags' in obj else (int(j>0 and CATALOG[f['board'][j-1]['key']]['tag']==item['tag'])+int(j+1<len(f['board']) and CATALOG[f['board'][j+1]['key']]['tag']==item['tag']))
                adj_boost=1+same*(.13 if 'affinity' in f['skills'] else .08)
                power=item['power']*(1+max(0,obj['tier']-item['tier'])*.45)*adj_boost
                if item['type'] in ('damage','leech','crit','execute','rupture','shatter') and 'marksmanship' in f['skills']:power*=1.15
                if f['hp']<f['maxHp']*.4 and 'zealot' in f['skills'] and item['type'] in ('damage','crit','leech','execute','rupture','shatter'):power*=1.12
                if item['type'] in ('heal','regen','cleanse') and 'meditation' in f['skills']:power*=1.25
                if item['type'] in ('shield','thorns') and 'paladin' in f['skills']:power*=1.22
                typ=item['type']
                if typ in ('damage','execute','crit','leech','shatter','rupture'):
                    if typ=='shatter':enemy['shield']=max(0,enemy['shield']-power*.6)
                    if typ=='execute' and enemy['hp']<enemy['maxHp']*.5:power*=1.5
                    if typ=='rupture':power+=min(80,enemy['poison']*.5+enemy['burn']*1.2)
                    if typ=='crit' and rng.random()<.35:power*=1.85
                    if 'ruthless' in f['skills'] and enemy['hp']<enemy['maxHp']*.5:power*=1.2
                    actual=hit(i,1-i,power,'hit',item['name'])
                    if typ=='leech':f['hp']=min(f['maxHp'],f['hp']+actual*.35)
                elif typ=='burn':
                    enemy['burn']=min(200,enemy['burn']+power*.27+(3 if 'wildfire' in f['skills'] else 0));evt(i,1-i,'burn',power*.27,item['name'])
                elif typ=='poison':
                    enemy['poison']=min(220,enemy['poison']+power+(3 if 'toxicologist' in f['skills'] else 0));evt(i,1-i,'poison',power,item['name'])
                elif typ in ('heal','cleanse'):
                    healed=min(f['maxHp']-f['hp'],power);f['hp']+=healed
                    if typ=='cleanse':f['poison']=max(0,f['poison']-22);f['burn']=max(0,f['burn']-12)
                    if 'heartwood' in f['skills']:f['shield']=min(1200,f['shield']+healed*.2)
                    evt(i,i,'heal',healed,item['name'])
                elif typ in ('shield','thorns'):
                    f['shield']=min(1200,f['shield']+power);evt(i,i,'shield',power,item['name'])
                elif typ=='regen':
                    f['regen']=min(120,f['regen']+power*.33);evt(i,i,'regen',power*.33,item['name'])
                elif typ=='haste':f['haste']=max(f['haste'],2.6);evt(i,i,'haste',2.6,item['name'])
                elif typ=='slow':enemy['slow']=max(enemy['slow'],2.4);evt(i,1-i,'slow',2.4,item['name'])
                elif typ=='freeze':enemy['frozen']=max(enemy['frozen'],.7);evt(i,1-i,'freeze',.7,item['name'])
                elif typ=='charge':
                    for n in range(max(0,j-1),min(len(f['board']),j+2)):
                        if n!=j:f['cds'][n]=max(.05,f['cds'][n]-power*(1.25 if 'spellbinder' in f['skills'] else 1))
                    evt(i,i,'charge',power,item['name'])
                enchant=obj.get('enchant')
                if enchant=='Fiery':enemy['burn']+=2;evt(i,1-i,'burn',2,'Fiery')
                elif enchant=='Toxic':enemy['poison']+=2;evt(i,1-i,'poison',2,'Toxic')
                elif enchant=='Turbo':f['haste']=max(f['haste'],1.5)
                elif enchant=='Icy':enemy['frozen']=max(enemy['frozen'],.4)
                elif enchant=='Shielded':f['shield']=min(1200,f['shield']+12)
                elif enchant=='Golden':pass
        for i,f in enumerate(fighters):
            f['slow']=max(0,f['slow']-.1);f['haste']=max(0,f['haste']-.1);f['frozen']=max(0,f['frozen']-(.2 if 'icebreak' in f['skills'] else .1))
            if tick%10==9 and f['hp']>0:
                poison=max(0,f['poison']-(2 if 'sanctuary' in f['skills'] else 0))
                burn=max(0,f['burn']-(2 if 'sanctuary' in f['skills'] else 0))
                if poison:hit(1-i,i,min(40,poison)*(1.2 if 'bloomcraft' in fighters[1-i]['skills'] else 1)*(.75 if 'cleanslate' in f['skills'] else 1),'dot','Toxic corrosion',pierce=True)
                if burn:hit(1-i,i,min(32,burn*1.1)*(1.2 if 'firebrand' in fighters[1-i]['skills'] else 1),'fire','Scorch')
                f['poison']=max(0,f['poison']-(.5 if 'alchemy' in fighters[1-i]['skills'] else 1));f['burn']=max(0,f['burn']-(.5 if 'alchemy' in fighters[1-i]['skills'] else 1))
                if 'apothecary' in f['skills'] and tick%50==49:f['hp']=min(f['maxHp'],f['hp']+10);evt(i,i,'heal',10,'Field Remedy')
                if f['regen']>0:
                    healed=min(f['maxHp']-f['hp'],f['regen']);f['hp']+=healed;evt(i,i,'heal',healed,'Regeneration')
        if t>=28 and tick%10==9:
            storm=(t-27)*8
            hit(1,0,storm,'storm','Midnight Sandstorm',pierce=True)
            hit(0,1,storm,'storm','Midnight Sandstorm',pierce=True)
        if any(f['hp']<=0 for f in fighters):break
    scores=[f['hp']+f['shield']*.1 for f in fighters]
    victor=0 if scores[0]>scores[1] else 1 if scores[1]>scores[0] else rng.choice((0,1))
    return {'victor':victor,'elapsed':round(t,1),'events':events,
            'fighters':[{'hp':round(f['hp']),'maxHp':round(f['maxHp']),'shield':round(f['shield']),
                         'poison':round(f['poison']),'burn':round(f['burn']),'hero':f['hero']} for f in fighters]}