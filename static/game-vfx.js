/* Night Market Duel visual feedback: no gameplay authority and no network actions.
   Capped particles, clean-up on animation end, reduced-motion respecting. */
(() => {
  'use strict';
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  const noFx = () => prefersReduced.matches || document.body.classList.contains('reduce-fx') || document.visibilityState !== 'visible';
  function fallbackImages() {
    document.querySelectorAll('img[src*="-portrait.webp"]').forEach(img => {
      if (img.dataset.fallbackReady) return;
      img.dataset.fallbackReady = 'true';
      img.addEventListener('error', () => {
        const result = img.src.match(/\/(vex|nyra|bronn|cael)-portrait\.webp(?:\?|$)/);
        if (result) img.src = `/static/art/${result[1]}.svg`;
      }, {once:true});
    });
  }
  function burst(target) {
    if (!target || noFx() || target.closest('[hidden]')) return;
    target.classList.remove('hit-flash');
    // Re-trigger even when two authoritative hit updates arrive quickly.
    void target.offsetWidth;
    target.classList.add('hit-flash');
    let fx = target.querySelector('.fx-burst');
    if (fx) fx.remove();
    fx = document.createElement('div'); fx.className = 'fx-burst'; fx.setAttribute('aria-hidden','true');
    const count = 8;
    for (let i=0;i<count;i++) {
      const node = document.createElement('i'); node.className='spark';
      node.style.setProperty('--a',`${(360/count)*i}deg`);
      node.style.setProperty('--r',`${-(22+(i%3)*16)}px`);
      fx.append(node);
    }
    target.append(fx);
    setTimeout(()=>{fx.remove();target.classList.remove('hit-flash')},550);
  }
  const targets = [
    ['hpA','duelistA'], ['hpB','duelistB'],
    ['battleMeHp','battleMeArt'], ['battleEnemyHp','battleEnemyArt']
  ];
  function observeHealth(labelId, targetId) {
    const label=document.getElementById(labelId), targetEl=document.getElementById(targetId);
    if (!label || !targetEl) return;
    const target = targetEl.closest('.combatant') || targetEl;
    let previous = Number.NaN;
    let nextValue = () => {
      const m = String(label.textContent||'').match(/^\s*(\d+(?:\.\d+)?)/);
      if (!m) return;
      const current=Number(m[1]);
      if (Number.isFinite(previous) && current < previous && (previous-current)>=1) burst(target);
      previous=current;
    };
    new MutationObserver(nextValue).observe(label, {childList:true,subtree:true,characterData:true});
    nextValue();
  }
  for (const [label,target] of targets) observeHealth(label,target);
  fallbackImages();
  new MutationObserver(fallbackImages).observe(document.body,{subtree:true,childList:true});
})();