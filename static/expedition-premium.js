/* Presentation-only controls. All economic/combat commands stay server-authoritative. */
(() => {'use strict';
const el=id=>document.getElementById(id);
const settings=el('settingsPanel');
const toggle=el('settingsToggle');
const close=()=>{settings.hidden=true;toggle.setAttribute('aria-expanded','false')};
toggle.addEventListener('click',()=>{settings.hidden=!settings.hidden;toggle.setAttribute('aria-expanded',String(!settings.hidden))});
el('settingsClose').addEventListener('click',close);
window.addEventListener('keydown',event=>{if(event.key==='Escape')close()});
document.addEventListener('pointerdown',event=>{if(!settings.hidden&&!settings.contains(event.target)&&!toggle.contains(event.target))close()});
const read=(key)=>{try{return localStorage.getItem(key)==='true'}catch{return false}};
const save=(key,value)=>{try{localStorage.setItem(key,String(value))}catch{/* persistence optional */}};
for(const [id,cls,key] of [['lowEffects','reduce-fx','nightMarket:lowEffects'],['compactCards','compact-cards','nightMarket:compactCards']]){
 const checkbox=el(id);checkbox.checked=read(key);document.body.classList.toggle(cls,checkbox.checked);
 checkbox.addEventListener('change',()=>{document.body.classList.toggle(cls,checkbox.checked);save(key,checkbox.checked)});
}
const dock=el('mobileDock');const run=el('game');
const obs=new MutationObserver(()=>{dock.hidden=run.hidden});obs.observe(run,{attributes:true,attributeFilter:['hidden']});dock.hidden=run.hidden;
const jump=(target)=>document.getElementById(target)?.scrollIntoView({behavior:document.body.classList.contains('reduce-fx')?'instant':'smooth',block:'start'});
dock.querySelectorAll('button[data-target]').forEach(btn=>btn.addEventListener('click',()=>{dock.querySelectorAll('button').forEach(x=>x.classList.toggle('active',x===btn));jump(btn.dataset.target)}));
})();