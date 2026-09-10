import {fetchData} from './data-cache.js';
import {t, ui, bindText, getLocale} from './i18n.js';
import {escapeHTML as h,safeURL} from './core.js';
import {loadProfiles,canonicalName} from './profiles.js';
import {profileURL} from './person-display.js';
import {loadWorks,workURL,readerURL,occurrences} from './library.js';
const $=id=>document.getElementById(id);
const external=(url,label)=>safeURL(url)?`<a href="${h(safeURL(url))}" target="_blank" rel="noopener">${h(label)} ↗</a>`:h(label);

(async()=>{
  try{
    const [works,people,response]=await Promise.all([loadWorks(),loadProfiles(),fetchData('data/catalog.json')]);
    if(!response.ok)throw Error('Catalogue unavailable.');
    const catalog=await response.json(),byWork=new Map(works.map(w=>[w.id,w])),byPerson=new Map(people.map(p=>[p.id,p]));
    const select=$('work-select'),search=$('work-search');
    function options(){
      const needle=search.value.trim().toLocaleLowerCase();
      const matching=works.filter(w=>w.identificationStatus!=='needs-review').filter(w=>[w.title,...w.attestedTitles].join(' ').toLocaleLowerCase().includes(needle));
      select.innerHTML=matching.map(w=>`<option value="${h(w.id)}">${h(w.title)}</option>`).join('');
      const current=decodeURIComponent(location.hash.slice(1));if(matching.some(w=>w.id===current))select.value=current;
      bindText($('work-count'), '{count} / {total} works', {count:matching.length,total:works.length});
    }
    let routeSequence=0;
    async function route(){
      const sequence=++routeSequence;
      let id;try{id=decodeURIComponent(location.hash.slice(1));}catch{id='invalid';}
      if(!id && works.length){id=(works.find(w=>w.identificationStatus!=='needs-review')||works[0]).id;history.replaceState(null,'',`#${id}`);}
      let w=byWork.get(id);select.value=id;
      if(!w){$('work').innerHTML=`<h1>${ui("Work not found")}</h1><p role="alert">${ui("Select a work above.")}</p>`;return;}
      if(w.summaryOnly){const r=await fetchData(`data/works/${w.id}.json`);if(!r.ok)throw Error('Work record unavailable.');const full=await r.json();if(full.id!==w.id)throw Error('Mismatched work record.');w=full;}
      if(sequence!==routeSequence)return;
      const ms=occurrences(catalog,id);
      const related=[['translationOf','Translation of'],['commentsOn','Commentary on'],['possibleSameAs','Possible title correspondence; unresolved']].filter(([key])=>w[key]).map(([key,label])=>`<p><strong>${ui(label)}:</strong> <a href="${h(workURL(w[key]))}">${h(byWork.get(w[key])?.title || w[key])}</a></p>`).join('');
      $('work').innerHTML=`<div class="eyebrow">${ui("WORK PROFILE · 文")} · ${ui(w.reviewStatus)}</div><h1>${h(w.title)}</h1><p class="work-subtitle">${ui(w.kind || 'work')}</p><p class="coverage">${w.identificationStatus==='needs-review'?'斜體候選：尚未確定是著作。原有連結已暫停，請依上下文覆核。':ui("A distinct work record, not a person or a particular physical copy. Source-reported details remain open to review.")}</p>
        <div class="profile-grid"><section><h2>${ui("Titles as attested")}</h2>${w.attestedTitles.map(t=>`<p>${h(t)}</p>`).join('')}</section>
        <section><h2>${ui("People and roles")}</h2>${(w.creators||[]).length?`<ul class="contribution-list">${w.creators.map(c=>`<li><a href="${h(profileURL(c.person))}">${h(byPerson.has(c.person)?canonicalName(byPerson.get(c.person)):c.person)}</a> · ${ui(c.role)}</li>`).join('')}</ul>`:`<p>${ui("Authorship not entered.")}</p>`}<p class="note">${ui("Roles are first-pass interpretations of the cited ECCP passages.")}</p></section>
        <section><h2>${ui("Bibliographical notes")}</h2>${w.extent?`<p><strong>${ui("Extent:")}</strong> ${h(w.extent)}</p>`:''}${w.publication?`<p><strong>${ui("Publication:")}</strong> ${h(w.publication)}</p>`:''}<p>${ui(w.note)}</p>${related}</section>
        <section><h2>${ui("Sources")}</h2>${Object.values(w.sources).map(s=>`<p>${external(s.url,s.title)}<br><small><span data-original lang="en">${h(s.attribution)}</span></small></p>`).join('')}</section></div>
        <section><h2>${ui("Occurrences in the imported texts ·")} ${ms.length}</h2><ul class="mentions-list">${ms.map(m=>{const s=catalog.sources.find(s=>s.id===m.witness);return `<li><a href="${h(readerURL(m.witness,m.passage))}">${h(s?.shortTitle || m.witness)} · ${h(m.passage)} →</a><br><q data-original lang="${h(s?.language || 'en')}">${h(m.quote)}</q></li>`;}).join('')}</ul></section>
        <p><a href="review.html?entity=${h(w.id)}">標註覆核 / Identification review</a></p><p class="note"><a href="data/works/${h(w.id)}.json">${ui("Work JSON")}</a> · <code>${h(w.id)}</code></p>`;
      document.title=`${w.title} · 文 · Ren-Wen`;
    }
    search.oninput=options;select.onchange=()=>{location.hash=select.value;};window.addEventListener('hashchange',()=>route().catch(error=>{$('work').textContent=error.message;}));options();await route();
  }catch(error){$('work').innerHTML=`<h1>${ui("Work records could not be loaded")}</h1><p role="alert">${h(error.message)}</p>`;}
})();
