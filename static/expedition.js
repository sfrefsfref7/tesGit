/* Night Market Expedition • original UI for the server-authoritative roguelike.
   No score, gold, item or combat outcome is ever accepted from the browser. */
(() => {
'use strict';
const $ = (id) => document.getElementById(id);
const state = { run: null, token: null, selected: null, hero: 'nyra', pending: false, animation: null, modal: false };
const tokenKey = 'nightMarket:expedition:v05'; // session format deliberately unchanged for existing runs
const art = (key) => `/static/art/${['vex','nyra','bronn','cael'].includes(key) ? key : 'vex'}.svg`;
const icons = { dagger:'⚔', bow:'➶', gear:'⚙', flame:'✹', heart:'✚', lotus:'❀', vial:'⚗', shield:'◆', fang:'♜', clock:'◷', spark:'ϟ', mirror:'◇', rune:'✧' };
const tierLabels = ['BRONZE', 'SILVER', 'GOLD', 'DIAMOND'];
const escapeHTML = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const button = (label, f, className='') => {
  const b = document.createElement('button'); b.type='button'; b.textContent=label; if(className)b.className=className; b.addEventListener('click',f); return b;
};
const empty = (element) => {element.replaceChildren();return element;};
let toastTimer;
function toast(message, isError=false){const el=$('toast');el.textContent=message;el.classList.toggle('error-toast',isError);el.classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.classList.remove('show'),3400);}
function busy(on){state.pending=on;$('startBtn').disabled=on;document.querySelectorAll('[data-action]').forEach(b=>b.disabled=on);}
async function post(path,payload){
  const controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),18000);
  try{
    const response=await fetch(`/api/expedition/${path}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),signal:controller.signal,cache:'no-store'});
    const data=await response.json();
    if(!response.ok||data.ok===false)throw new Error(data.error || 'Server rejected this action');
    $('connectionLabel').textContent='● SERVER CONNECTED';return data;
  }catch(err){$('connectionLabel').textContent='● CONNECTION INTERRUPTED';throw err;
  }finally{clearTimeout(timeout);}
}
async function action(op,fields={}){
  if(state.pending||!state.token)return;
  busy(true);
  try{
    const response=await post('action',{token:state.token,id:`action-${crypto.randomUUID()}`,op,...fields});
    state.run=response.state;state.selected=null;render();
    if(op==='fight'&&response.result){showBattle(response.result);}
    else if(op==='buy')toast('Artifact added to your stash');
    else if(op==='combine')toast('Two artifacts merged into a higher tier');
    else if(op==='upgrade')toast('Artifact upgraded');
    else if(op==='learn')toast('New permanent skill acquired');
  }catch(err){toast(err.message,true);}
  finally{busy(false);}
}
function renderHeroes(){
  const holder=empty($('heroes'));
  for(const [key,h] of Object.entries({
    vex:['Vex','The Nightblade'],nyra:['Nyra','The Venom Witch'],bronn:['Bronn','The Iron Warden'],cael:['Cael','The Chronomancer']
  })){
    const el=button('',()=>{state.hero=key;renderHeroes();},'hero-card'+(key===state.hero?' selected':''));
    el.setAttribute('aria-pressed',String(key===state.hero));
    const img=document.createElement('img');img.src=art(key);img.alt='';img.loading='lazy';
    const title=document.createElement('span');title.textContent=h[0];
    el.append(img,title);holder.append(el);
  }
}
async function start(){
  if(state.pending)return;
  $('openingError').textContent='';busy(true);
  try{
    const response=await post('start',{name:$('playerName').value.trim()||'Night Wanderer',hero:state.hero});
    state.token=response.token;localStorage.setItem(tokenKey,response.token);
    state.run=response.state;state.selected=null;render();toast('Your expedition begins');
  }catch(err){$('openingError').textContent=err.message;toast(err.message,true);}
  finally{busy(false);}
}
async function resume(){
  const token=localStorage.getItem(tokenKey);if(!token)return;
  try{const response=await post('state',{token});state.token=token;state.run=response.state;render();toast('Your journey has been restored');}
  catch{localStorage.removeItem(tokenKey);$('connectionLabel').textContent='● READY FOR NEW RUN';}
}
function itemData(uid){const r=state.run;return r.inventory[uid]&&r.catalog[r.inventory[uid].key];}
function itemGlyph(item){return icons[item?.glyph]||'✧';}
function itemVisual(glyph){
  const slot = document.createElement('span'); slot.className = 'vector-art';
  // The icon library contains only fixed, authored SVG paths. Never interpolate network content.
  if (typeof iconArt === 'function' && Object.hasOwn(icons,glyph)) slot.innerHTML=iconArt(glyph);
  else slot.textContent=icons[glyph]||'✧';
  return slot;
}
function descriptor(uid){const obj=state.run.inventory[uid],data=itemData(uid);return data?`${data.name} · ${tierLabels[obj.tier]||'LEGENDARY'} · ${data.size} slot${data.size>1?'s':''}`:'Unknown artifact';}
function setModal(open){state.modal=open;$('itemModal').hidden=!open;document.body.classList.toggle('modal-open',open);}
function inspect(uid){
  if(!itemData(uid))return; const r=state.run,obj=r.inventory[uid],item=itemData(uid);
  $('modalTag').textContent=`${(item.tag||'Artifact').toUpperCase()} · ${tierLabels[obj.tier]||'DIAMOND'} · ${item.size} SLOT${item.size===1?'':'S'}`;
  $('modalGlyph').replaceChildren(itemVisual(item.glyph));
  $('modalName').textContent=item.name;
  $('modalDescription').textContent=item.text || `${item.type} item with ${item.cooldown}s cooldown`;
  const stats=empty($('modalProperties'));
  for(const label of [`${item.type.toUpperCase()}`,`${Number(item.cooldown).toFixed(1)}s COOLDOWN`,`${Math.round(item.power * (1+Math.max(0,obj.tier-item.tier)*.45))} POWER`,obj.enchant?`${obj.enchant.toUpperCase()} ENCHANT`:`SELL ≈ ${Math.floor(item.cost/2)} ◈`]){
    const p=document.createElement('span');p.textContent=label;stats.append(p);
  }
  const area=empty($('modalButtons'));
  const equipped=r.board.includes(uid);
  if(equipped){area.append(button('MOVE ON BOARD',()=>{state.selected=uid;setModal(false);renderBoard();toast('Tap a free board slot to move this item');}));}
  else{area.append(button('EQUIP TO BOARD',()=>{state.selected=uid;setModal(false);renderBoard();toast('Choose a position on the board');}));}
  if(equipped)area.append(button('SEND TO STASH',()=>{setModal(false);action('store',{uid});}));
  if(obj.tier<3)area.append(button(`UPGRADE · ${5+obj.tier*3} ◈`,()=>{setModal(false);action('upgrade',{uid});}));
  const other=Object.keys(r.inventory).find(x=>x!==uid&&r.inventory[x].key===obj.key&&r.inventory[x].tier===obj.tier);
  if(other&&obj.tier<3)area.append(button('COMBINE DUPLICATE',()=>{setModal(false);action('combine',{uid,other});}));
  if(r.phase==='trainer'&&!obj.enchant){
    for(const effect of ['Fiery','Toxic','Turbo','Icy','Shielded','Radiant','Golden']){
      area.append(button(`ENCHANT ${effect} · ${r.skills.includes('artful')?6:9} ◈`,()=>{setModal(false);action('enchant',{uid,effect});}));
    }
  }
  area.append(button('SELL FOR GOLD',()=>{setModal(false);action('sell',{uid});},'danger-action'));
  setModal(true);
}
function renderBoard(){
  const r=state.run, holder=empty($('board'));let used=0;
  for(let i=0;i<10;){
    const uid=r.board[i];if(uid&&r.inventory[uid]){
      const item=itemData(uid),obj=r.inventory[uid];const size=Math.max(1,item.size);used+=size;
      const el=button('',()=>inspect(uid),`board-item ${item.rarity||'common'} ${state.selected===uid?'selected':''}`);
      el.style.gridColumn=`span ${size}`;el.dataset.uid=uid;
      el.setAttribute('aria-label',descriptor(uid));
      const sign=document.createElement('span');sign.className='big-glyph';sign.append(itemVisual(item.glyph));
      const nm=document.createElement('span');nm.className='item-name';nm.textContent=item.name;
      const tier=document.createElement('small');tier.textContent=tierLabels[obj.tier]||'DIAMOND';
      const time=document.createElement('span');time.className='cooldown-stamp';time.textContent=`◷ ${Number(item.cooldown).toFixed(1)}s`;
      const tag=document.createElement('span');tag.className='card-tag';tag.textContent=item.type;
      el.dataset.size=String(size);el.dataset.tier=String(obj.tier);el.dataset.glyph=item.glyph;
      el.append(sign,nm,tier,time,tag);holder.append(el);i+=size;
    }else{
      const enabled=i<r.boardLimit;
      const el=button(enabled?'+':'🔒',()=>{
        if(!enabled)return;
        if(state.selected){const uid=state.selected;action('equip',{uid,slot:i});}
        else toast('Select an artifact from your stash first');
      },`board-cell ${enabled?'open':'locked'}`);
      el.setAttribute('aria-label',enabled?`Equip to board slot ${i+1}`:`Locked board slot ${i+1}`);holder.append(el);i++;
    }
  }
  $('boardUsed').textContent=`${used} / ${r.boardLimit} unlocked`;
  const stash=empty($('stash'));
  for(const uid of r.stash){const item=itemData(uid);if(!item)continue;
    const el=button('',()=>inspect(uid),`stash-item ${item.rarity||'common'}`);el.setAttribute('aria-label',descriptor(uid));
    const sym=document.createElement('span');sym.className='glyph';sym.append(itemVisual(item.glyph));
    const nm=document.createElement('span');nm.className='name';nm.textContent=item.name;
    const tier=document.createElement('small');tier.textContent=tierLabels[r.inventory[uid].tier]||'DIAMOND';
    el.dataset.tier=String(r.inventory[uid].tier);el.append(sym,nm,tier);
    stash.append(el);
  }
  if(!r.stash.length){const p=document.createElement('div');p.className='stash-empty';p.textContent='Your stash is empty · visit a merchant';stash.append(p);}
  $('stashUsed').textContent=`${r.stash.reduce((n,uid)=>n+(itemData(uid)?.size||0),0)} / 10`;
}
function renderSkills(){const r=state.run;const el=empty($('skills'));$('skillCount').textContent=`${r.skills.length} / 6`;
  if(!r.skills.length){const p=document.createElement('p');p.className='hint';p.textContent='Visit a skill trainer to learn permanent abilities.';el.append(p);return;}
  for(const key of r.skills){const skill=r.skillCatalog[key];if(!skill)continue;const s=document.createElement('div');s.className='skill-chip';s.title=skill.text;s.textContent=`${skill.icon||'✧'} ${skill.name}`;el.append(s);}
}
function offerCard(title,description,icon,metadata,onClick,rarity='',disabled=false){
  const el=button('',onClick,`offer ${rarity}`);el.dataset.action='true';el.disabled=state.pending||disabled;
  const symbol=document.createElement('i');
  const key=Object.keys(icons).find(k=>icons[k]===icon);
  if(key)symbol.append(itemVisual(key));else symbol.textContent=icon;
  const heading=document.createElement('b');heading.textContent=title;
  const text=document.createElement('small');text.textContent=description;
  const price=document.createElement('span');price.className='price';price.textContent=metadata;
  el.append(symbol,heading,text,price);
  const top=document.createElement('span');top.className='offer-topline';top.textContent=(rarity||'ENCOUNTER').toUpperCase();
  el.prepend(top);return el;
}
function actionButton(label,fn,primary=false){const el=button(label,fn,primary?'primary':'ghost');el.dataset.action='true';el.disabled=state.pending;return el;}
function renderEncounter(){
  const r=state.run,body=empty($('encounterContent')),actions=empty($('encounterActions'));actions.className='encounter-actions';
  $('encounterBadge').textContent=`DAY ${r.day} · HOUR ${r.hour}`;
  const grid=document.createElement('div');grid.className='offers';body.append(grid);
  if(r.phase==='route'){
    $('encounterTitle').textContent='Choose your path';$('encounterIntro').textContent='Pick one of three encounters. Every choice consumes one hour.';
    const map={merchant:'◈',trainer:'✦',monster:'⚔',rival:'♜',event:'✧',rest:'❀'};
    r.route.forEach((e,i)=>grid.append(offerCard(e.title,e.description,map[e.type]||'✧',`ENCOUNTER ${i+1} · ${e.type.toUpperCase()}`,()=>action('choose',{index:i}))));
  }else if(r.phase==='merchant'){
    $('encounterTitle').textContent=r.selected.title||'The Merchant';$('encounterIntro').textContent='Tap a card to buy. New items go to your stash; make space before purchase.';
    r.offers.forEach((off,i)=>{const item=r.catalog[off.key];if(!item)return;grid.append(offerCard(item.name,`${item.size} slot · ${item.type} · ${item.cooldown}s`,itemGlyph(item),`${off.price} ◈ · ${item.rarity.toUpperCase()}`,()=>action('buy',{index:i}),item.rarity,r.gold<off.price));});
    actions.append(actionButton('↻ REROLL MERCHANT · 2 GOLD',()=>action('reroll')));
    actions.append(actionButton('CONTINUE JOURNEY →',()=>action('leave'),true));
  }else if(r.phase==='trainer'){
    $('encounterTitle').textContent='Master of Techniques';$('encounterIntro').textContent='Permanent skill slots: 6. You may also enchant any owned item for 9 Gold.';
    r.offers.forEach((off,i)=>{const skill=r.skillCatalog[off.key];if(!skill)return;grid.append(offerCard(skill.name,skill.text,skill.icon||'✦',`${off.price} ◈`,()=>action('learn',{index:i}),'',r.gold<off.price));});
    actions.append(actionButton('CONTINUE JOURNEY →',()=>action('leave'),true));
  }else if(r.phase==='event'||r.phase==='rest'){
    $('encounterTitle').textContent=r.selected.title||'Quiet Courtyard';$('encounterIntro').textContent='Select one boon for your journey.';
    const rewards={treasure:['Gold Cache','Take gold to spend in the market','◈'],vitality:['Vital Essence','Permanently increase your Max HP','❤'],arcana:['Arcane Knowledge','Gain experience toward your next level','✦'],gold:['Earn Gold','Take gold for the road','◈'],health:['Max HP +40','Fortify your next battle','❤'],xp:['Experience +4','Level up sooner','✦'],relic:['Mystery Relic','Receive a random original relic (needs stash space)','◇'],skill:['Arcane Insight','Learn a permanent skill, if space permits','✧'],forge:['Free Forge','Upgrade a random equipped item (up to Diamond)','⚒'],gamble:['Roll the Dice','58% chance of gold; otherwise lose 25 Max HP','♜']};
    r.offers.forEach(key=>{const info=rewards[key]||[key,key,'✦'];grid.append(offerCard(info[0],info[1],info[2],'CLAIM REWARD',()=>action('event',{choice:key})));});
    actions.append(actionButton('SKIP ENCOUNTER →',()=>action('leave')));
  }else if(r.phase==='encounter'){
    $('encounterTitle').textContent=r.selected.title||'Enemy ahead';$('encounterIntro').textContent=`${r.selected.type==='rival'?'VICTORY CREST BATTLE':'MONSTER HUNT'} · Your current equipped board will enter combat.`;
    grid.append(offerCard(r.selected.title,'The server determines every attack, status and reward.','⚔','ENEMY ENCOUNTER',()=>action('fight')));
    actions.append(actionButton('⚔ ENGAGE IN COMBAT',()=>action('fight'),true));
  }else if(r.phase==='won'||r.phase==='lost'){
    $('encounterTitle').textContent=r.phase==='won'?'THE NIGHT BELONGS TO YOU':'THE MARKET CLAIMS ITS DEBT';
    $('encounterIntro').textContent=r.phase==='won'?'You earned all ten Victory Crests.':'Your Prestige reached zero. Try a different build.';
    grid.replaceChildren();actions.append(actionButton('BEGIN A NEW RUN',newRun,true));
  }
}
function render(){
  const r=state.run;if(!r){$('opening').hidden=false;$('game').hidden=true;return;}
  $('opening').hidden=true;$('game').hidden=false;
  $('journeyDay').textContent=`${String(r.day).padStart(2,'0')} · ${String(r.hour).padStart(2,'0')}/06`;
  $('journeyGold').textContent=`◈ ${r.gold}`;$('journeyLevel').textContent=`${r.level} · ${r.xp}/8`;
  $('journeyPrestige').textContent=`♛ ${r.prestige}`;$('journeyWins').textContent=`${r.wins} / 10`;
  $('myPortrait').src=art(r.hero);$('myName').textContent=r.name;$('myClass').textContent=r.heroCatalog[r.hero]?.title||r.hero;
  $('heroHealth').textContent=`MAX HEALTH · ${r.maxHealth}`;$('healthTrack').style.width=`${Math.max(0,Math.min(100,r.prestige/20*100))}%`;
  renderBoard();renderSkills();renderEncounter();
  empty($('chronicle'));for(const row of r.history){const p=document.createElement('p');p.textContent=row;$('chronicle').append(p);}
  document.querySelectorAll('[data-action]').forEach(b=>b.disabled=b.disabled||state.pending);
}
function newRun(){if(state.pending)return;if(state.run && !window.confirm('Start a new expedition? Your current progress will be lost.'))return;
  state.token=null;state.run=null;state.selected=null;localStorage.removeItem(tokenKey);setModal(false);$('playerName').value='';render();}
function showBattle(battle){
  const modal=$('battleModal');modal.hidden=false;const events=Array.isArray(battle.events)?battle.events:[];
  $('battleTitle').textContent=battle.victor===0?'VICTORY IN THE MIDNIGHT MARKET':'THE MARKET TAKES ITS DUE';
  $('battleTitle').className=battle.victor===0?'win-text':'lose-text';
  $('battleMeArt').src=art(state.run.hero);$('battleEnemyArt').src=art(battle.fighters?.[1]?.hero||'bronn');
  $('battleMe').textContent=state.run.name;$('battleEnemy').textContent=battle.enemy||'Night Rival';
  const max0=battle.fighters?.[0]?.maxHp||state.run.maxHealth,max1=battle.fighters?.[1]?.maxHp||250;
  let hp=[max0,max1],idx=0,start=performance.now();empty($('battleEvents'));
  function update(){
    const targets=[['battleMeHp','battleMeHpBar',max0],['battleEnemyHp','battleEnemyHpBar',max1]];
    targets.forEach((row,i)=>{$(row[0]).textContent=`${Math.round(hp[i])} / ${row[2]}`;$(row[1]).style.width=`${Math.max(0,Math.min(100,hp[i]/row[2]*100))}%`;});
  }
  update();
  function frame(){
    const elapsed=(performance.now()-start)/1000;
    while(idx<events.length&&events[idx].time<=elapsed){
      const e=events[idx++];if(e.kind==='hit'||e.kind==='fire'||e.kind==='dot'||e.kind==='storm')hp[e.target]=Math.max(0,hp[e.target]-Number(e.amount||0));
      else if(e.kind==='heal')hp[e.target]=Math.min(e.target===0?max0:max1,hp[e.target]+Number(e.amount||0));
      const line=document.createElement('div');line.textContent=`${Number(e.time).toFixed(1)}s · ${e.label||e.kind} · ${Math.round(e.amount||0)} ${e.kind}`;
      $('battleEvents').prepend(line);while($('battleEvents').childElementCount>7)$('battleEvents').lastChild.remove();
    }
    $('battleClock').textContent=`${Math.min(elapsed,Number(battle.elapsed)||0).toFixed(1)}s`;
    if(idx>=events.length&&elapsed>=Number(battle.elapsed||0)){
      hp=battle.fighters.map(f=>Number(f.hp));update();$('battleClock').textContent=battle.victor===0?'VICTORY':'DEFEAT';state.animation=null;return;
    }
    update();state.animation=requestAnimationFrame(frame);
  }
  if(state.animation)cancelAnimationFrame(state.animation);state.animation=requestAnimationFrame(frame);
  $('battleSkip').textContent='CONTINUE JOURNEY →';
  $('battleSkip').onclick=()=>{if(state.animation)cancelAnimationFrame(state.animation);state.animation=null;modal.hidden=true;};
}
$('startBtn').addEventListener('click',start);
$('playerName').addEventListener('keydown',e=>{if(e.key==='Enter')start();});
$('newRunBtn').addEventListener('click',newRun);
$('clearSelection').addEventListener('click',()=>{state.selected=null;renderBoard();toast('Selection cleared');});
$('closeModal').addEventListener('click',()=>setModal(false));
$('itemModal').addEventListener('click',e=>{if(e.target?.dataset?.close)setModal(false);});
$('battleSkip').addEventListener('click',()=>{$('battleModal').hidden=true;});
window.addEventListener('keydown',e=>{if(e.key==='Escape')setModal(false);});
renderHeroes();resume();
})();