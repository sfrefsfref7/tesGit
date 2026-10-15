/* Bazaar Theatre: navigation + derived display only. No game state writes. */
(() => {
 'use strict';
 const $ = id => document.getElementById(id);
 const menu=$('gameMenuPanel'),toggle=$('gameMenuToggle'),settings=$('settingsToggle');
 const targets=new Set(['encounterPanel','boardPanel','skillsPanel','collectionPanel','chroniclePanel']);
 if(!menu||!toggle)return;
 const close=()=>{menu.hidden=true;toggle.setAttribute('aria-expanded','false');};
 const open=()=>{menu.hidden=false;toggle.setAttribute('aria-expanded','true');};
 toggle.addEventListener('click',()=>menu.hidden?open():close());
 $('gameMenuClose').addEventListener('click',close);
 document.addEventListener('keydown',e=>{if(e.key==='Escape')close();});
 document.addEventListener('pointerdown',e=>{if(!menu.hidden&&!menu.contains(e.target)&&!toggle.contains(e.target))close();});
 const nav=(target)=>{
  if(!targets.has(target))return;
  const el=$(target);
  if($('game').hidden){close();document.querySelector('#opening')?.scrollIntoView();return;}
  el?.scrollIntoView({behavior:document.body.classList.contains('reduce-fx')?'instant':'smooth',block:'start'});
  document.querySelectorAll('.run-tabs [data-scene],.mobile-dock [data-target]').forEach(n=>n.classList.toggle('active',n.dataset.scene===target||n.dataset.target===target));
  close();
 };
 document.querySelectorAll('[data-scene]').forEach(el=>el.addEventListener('click',()=>nav(el.dataset.scene)));
 $('menuSettingsBtn').addEventListener('click',()=>{close();settings.click()});
 const markers=$('victoryMarkers');
 for(let i=0;i<10;i++){const node=document.createElement('i');node.setAttribute('aria-hidden','true');markers.append(node);}
 window.addEventListener('nightmarket:render',e=>{
  const d=e.detail||{};
  const phase=['starter','route','merchant','trainer','event','rest','encounter','levelup','won','lost'].includes(d.phase)?d.phase:'route';
  const panel=$('encounterPanel');panel.dataset.encounter=phase;
  document.body.dataset.expeditionPhase=phase;
  const wins=Math.max(0,Math.min(10,Number(d.wins)||0));
  markers.querySelectorAll('i').forEach((node,i)=>node.classList.toggle('earned',i<wins));
  $('winTrailLabel').textContent=`${wins}/10`;
  document.querySelector('.win-trail')?.setAttribute('aria-label',`${wins} out of 10 victories`);
  const lane=phase==='merchant'?'MERCHANT':phase==='encounter'?'COMBAT SCOUT':phase==='trainer'?'SKILL TRAINER':phase==='levelup'?'LEVEL UP':phase==='starter'?'STARTING GIFT':phase==='route'?'CHOOSE A PATH':phase==='won'?'VICTORY':phase==='lost'?'DEFEAT':'EVENT';
  const subtitle=document.querySelector('.scene-mark');if(subtitle)subtitle.textContent=`DAY ${String(d.day||1).padStart(2,'0')} · ${lane}`;
 });
})();