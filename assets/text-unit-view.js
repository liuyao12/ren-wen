import {escapeHTML as h} from './core.js';
import {t,ui} from './i18n.js';
import {loadTextUnits,occurrencesOf,unitContainers,unitURL} from './text-units.js';
import {readerURL} from './library.js';
const $=id=>document.getElementById(id);let data,selected;
function render(id){
 const unit=data.units.find(u=>u.id===id);if(!unit){$('text-unit').innerHTML=`<h1>${ui('Text not found')}</h1>`;return;}selected=id;$('unit-select').value=id;
 const readings=occurrencesOf(data,id);
 $('text-unit').innerHTML=`<div class="eyebrow">${ui('Text units and readings')}</div><h1>${h(unit.title)}</h1><p>${ui(unit.kind)} · ${ui(unit.reviewStatus)}</p>${unit.note?`<p class="note" data-original>${h(unit.note)}</p>`:''}<p class="coverage">${ui('A quotation remains in its full context. Each source occurrence retains its own wording; similar readings are not merged automatically.')}</p>
 ${readings.map(o=>`<section class="text-reading"><h2>${ui(o.role)} · ${h(o.witness)}</h2><nav class="unit-breadcrumb">${unitContainers(data,o).map(parent=>{const u=data.units.find(u=>u.id===parent.unit);return `<a href="${unitURL(u.id)}">${h(u.title)}</a>`;}).join(' → ')}</nav><p><a href="${h(readerURL(o.witness,o.selectors[0].passage))}">${ui('Read in full context')} →</a></p>${o.note?`<p data-original class="note">${h(o.note)}</p>`:''}<div class="unit-reading" data-source-text>${o.selectors.map(a=>`<p>${h(a.exact)}</p>`).join('')}</div><details><summary>${ui('Occurrence and source version')}</summary><p><code>${h(o.id)}</code></p><p><code>${h(o.sourceSha256)}</code></p></details></section>`).join('')}
 <h2>${ui('Contained texts')}</h2>${data.occurrences.filter(o=>readings.some(p=>p.id===o.container)).map(o=>{const u=data.units.find(u=>u.id===o.unit);return `<p><a href="${unitURL(u.id)}">${h(u.title)}</a> · ${ui(o.role)}</p>`;}).join('')||`<p>${ui('No child text registered.')}</p>`}`;
 document.title=unit.title+' · 人文';
}
(async()=>{try{data=await loadTextUnits();$('unit-select').innerHTML=data.units.map(u=>`<option value="${h(u.id)}">${h(u.title)}</option>`).join('');const open=()=>{let id;try{id=decodeURIComponent(location.hash.slice(1));}catch{}render(id||data.units[0].id);};$('unit-select').onchange=e=>{location.hash=e.target.value;};window.addEventListener('hashchange',open);window.addEventListener('renwen:languagechange',()=>render(selected));open();}catch(e){$('text-unit').innerHTML=`<p role="alert">${h(e.message)}</p>`;}})();
