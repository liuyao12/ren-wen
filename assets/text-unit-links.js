import {loadTextUnits,unitURL} from './text-units.js';
import {escapeHTML as h} from './core.js';
import {ui} from './i18n.js';
(async()=>{
 const reader=document.getElementById('reader');if(!reader)return;
 const data=await loadTextUnits();let scheduled=false;
 function decorate(){scheduled=false;
  for(const old of reader.querySelectorAll('.text-unit-control'))if(!document.getElementById(old.dataset.unitPassage))old.remove();
  for(const o of data.occurrences){const p=document.getElementById(o.selectors[0].passage);if(!p||!reader.contains(p)||reader.querySelector(`[data-unit-occurrence="${o.id}"]`))continue;
   const u=data.units.find(u=>u.id===o.unit);const a=document.createElement('a');a.className='text-unit-control';a.dataset.unitOccurrence=o.id;a.dataset.unitPassage=p.id;a.href=unitURL(u.id);a.innerHTML=`${ui(o.role==='quotation'?'Quotation record':o.role==='section'?'Section record':'Text structure')} · ${h(u.title)} →`;p.before(a);
  }
 }
 new MutationObserver(()=>{if(!scheduled){scheduled=true;queueMicrotask(decorate);}}).observe(reader,{childList:true});decorate();
})().catch(error=>console.error('Text-unit controls:',error));
