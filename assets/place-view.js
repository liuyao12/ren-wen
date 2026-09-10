import {fetchData} from './data-cache.js';
import {escapeHTML as h,safeURL} from './core.js';
import {placeURL} from './place-model.js';
import {readerURL} from './library.js';
import {getLocale} from './i18n.js';
const $=id=>document.getElementById(id);
const en=()=>getLocale()==='en';
let records=[],candidates=null,page=0;
const SIZE=60;
try {
  const r=await fetchData('data/places.json');if(!r.ok)throw Error('地名資料無法載入');
  records=(await r.json()).records;
  function occurrence(m){return `<li class="place-occurrence"><strong>${h(m.quote)}</strong><br><a href="${h(readerURL(m.witness,m.passage))}">${h(m.passage)}</a>${safeURL(m.sourceUrl)?`<a href="${h(safeURL(m.sourceUrl))}" target="_blank" rel="noopener">${en()?'Source':'原始文獻'} ↗</a>`:''}</li>`;}
  async function render(){
    const id=decodeURIComponent(location.hash.slice(1));
    $('place-search').placeholder=en()?'Place / source spelling':'地名／原文拼寫';
    $('place-mode').options[0].text=en()?'Place records':'地名記錄';$('place-mode').options[1].text=en()?'Candidates to review':'待辨地名候選';
    if(id){
      const p=records.find(r=>r.id===id);
      if(!p){$('place-results').textContent=en()?'Place record not found.':'未找到地名記錄。';return;}
      const evidence=p.evidence||[];
      $('place-count').textContent=`${evidence.length} ${en()?'recorded occurrences':'處原文提及'}`;
      $('place-results').innerHTML=`<a href="places.html">← ${en()?'All places':'全部地名'}</a><h1>${h(p.label)}</h1><p>${h(p.display)}${p.provinceExpression?' · '+h(p.provinceExpression):''}</p><p class="place-note">${en()?'Source-limited draft; historical jurisdiction, coordinates and identification need review.':'來源限定初稿；歷史政區、坐標與身分仍需審校。'}</p><p>${h(p.resolution)}</p><p>${h(p.spellingForms.join(' · '))}</p><h2>${en()?'Source occurrences':'原文出處'}</h2><ul class="place-evidence">${evidence.slice(page*SIZE,(page+1)*SIZE).map(occurrence).join('')}</ul>`;
      paginate(evidence.length);return;
    }
    const needle=$('place-search').value.trim().toLocaleLowerCase();let rows;
    if($('place-mode').value==='candidates'){
      if(!candidates){const r=await fetchData('data/editorial/place-candidates.json');if(!r.ok)throw Error('候選資料無法載入');candidates=(await r.json()).candidates;}
      rows=candidates.filter(c=>`${c.quote} ${c.witness}`.toLocaleLowerCase().includes(needle));
      $('place-results').innerHTML=rows.slice(page*SIZE,(page+1)*SIZE).map(c=>`<article class="place-candidate"><strong>${h(c.quote)}</strong><p>${h(c.context)}</p><a href="${h(readerURL(c.witness,c.passage))}">${h(c.passage)}</a><small> · ${en()?'Lexical candidate only — not an entity identification':'僅字形候選，未作實體認定'}</small></article>`).join('');
    }else{
      rows=records.filter(p=>`${p.label} ${p.display} ${p.provinceExpression||''} ${p.spellingForms.join(' ')}`.toLocaleLowerCase().includes(needle));
      $('place-results').innerHTML=rows.slice(page*SIZE,(page+1)*SIZE).map(p=>`<article class="place-record"><h2><a href="${h(placeURL(p.id))}">${h(p.label)}</a></h2><p>${h(p.display)}${p.provinceExpression?' · '+h(p.provinceExpression):''}</p><small>${p.evidence.length} ${en()?'occurrences · proposed identification':'處提及 · 待覆核'}</small></article>`).join('');
    }
    $('place-count').textContent=`${rows.length} ${en()?'records':'筆'}`;paginate(rows.length);
  }
  function paginate(total){$('place-pagination').innerHTML=`<button id="place-prev" ${page===0?'disabled':''}>←</button> ${page+1} / ${Math.max(1,Math.ceil(total/SIZE))} <button id="place-next" ${(page+1)*SIZE>=total?'disabled':''}>→</button>`;$('place-prev').onclick=()=>{page--;render();};$('place-next').onclick=()=>{page++;render();};}
  $('place-search').oninput=()=>{page=0;render();};$('place-mode').onchange=()=>{page=0;if(location.hash)location.hash='';else render();};
  window.addEventListener('hashchange',()=>{page=0;render();});window.addEventListener('renwen:languagechange',render);await render();
}catch(error){$('place-results').textContent=error.message;console.error(error);}
