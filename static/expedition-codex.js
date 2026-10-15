(() => {'use strict';
const filter=document.getElementById('codexFilter'),search=document.getElementById('codexSearch');
const results=document.getElementById('codexResults'),count=document.getElementById('codexCount');
let catalog={},skills={};
function render(){const tag=filter.value,q=search.value.trim().toLowerCase();
const data=tag==='skills'?Object.values(skills).map(x=>({...x,cat:'skill'})):Object.values(catalog).filter(x=>tag==='all'||x.tag===tag).map(x=>({...x,cat:x.tag}));
const matching=data.filter(item=>(`${item.name} ${item.text||''} ${item.type||''}`).toLowerCase().includes(q));
count.textContent=`${matching.length} matching entries`;
results.replaceChildren();for(const item of matching.slice(0,80)){const row=document.createElement('article');row.className='codex-entry';
const head=document.createElement('b');head.textContent=item.name;const body=document.createElement('p');body.textContent=item.text||`${item.type} · ${item.size} slots · ${item.cooldown}s cooldown`;
const meta=document.createElement('small');meta.textContent=item.cat.toUpperCase();row.append(head,body,meta);results.append(row);}
if(matching.length>80){const notice=document.createElement('p');notice.textContent='Refine the search to see more entries.';results.append(notice);}}
filter.addEventListener('change',render);search.addEventListener('input',render);
window.addEventListener('nightmarket:render',event=>{catalog=event.detail.catalog;skills=event.detail.skills;render()});
})();