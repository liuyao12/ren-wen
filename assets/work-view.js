import {escapeHTML as h,safeURL} from './core.js';
import {loadProfiles,canonicalName} from './profiles.js';
import {profileURL} from './person-display.js';
import {loadWorks,workURL,readerURL,occurrences} from './library.js';
const $=id=>document.getElementById(id);
const external=(url,label)=>safeURL(url)?`<a href="${h(safeURL(url))}" target="_blank" rel="noopener">${h(label)} ↗</a>`:h(label);

(async()=>{
  try{
    const [works,people,response]=await Promise.all([loadWorks(),loadProfiles(),fetch('data/catalog.json')]);
    if(!response.ok)throw Error('Catalogue unavailable.');
    const catalog=await response.json(),byWork=new Map(works.map(w=>[w.id,w])),byPerson=new Map(people.map(p=>[p.id,p]));
    const select=$('work-select'),search=$('work-search');
    function options(){
      const needle=search.value.trim().toLocaleLowerCase();
      const matching=works.filter(w=>[w.title,...w.attestedTitles].join(' ').toLocaleLowerCase().includes(needle));
      select.innerHTML=matching.map(w=>`<option value="${h(w.id)}">${h(w.title)}</option>`).join('');
      const current=decodeURIComponent(location.hash.slice(1));if(matching.some(w=>w.id===current))select.value=current;
      $('work-count').textContent=`${matching.length} / ${works.length} works`;
    }
    function route(){
      let id;try{id=decodeURIComponent(location.hash.slice(1));}catch{id='invalid';}
      if(!id && works.length){id=works[0].id;history.replaceState(null,'',`#${id}`);}
      const w=byWork.get(id);select.value=id;
      if(!w){$('work').innerHTML='<h1>Work not found</h1><p role="alert">Select a work above.</p>';return;}
      const ms=occurrences(catalog,id);
      const related=[['translationOf','Translation of'],['commentsOn','Commentary on'],['possibleSameAs','Possible title correspondence; unresolved']].filter(([key])=>w[key]).map(([key,label])=>`<p><strong>${h(label)}:</strong> <a href="${h(workURL(w[key]))}">${h(byWork.get(w[key])?.title || w[key])}</a></p>`).join('');
      $('work').innerHTML=`<div class="eyebrow">WORK PROFILE · 文 · ${h(w.reviewStatus)}</div><h1>${h(w.title)}</h1><p class="work-subtitle">${h(w.kind || 'work')}</p><p class="coverage">A distinct work record, not a person or a particular physical copy. Source-reported details remain open to review.</p>
        <div class="profile-grid"><section><h2>Titles as attested</h2>${w.attestedTitles.map(t=>`<p>${h(t)}</p>`).join('')}</section>
        <section><h2>People and roles</h2>${(w.creators||[]).length?`<ul class="contribution-list">${w.creators.map(c=>`<li><a href="${h(profileURL(c.person))}">${h(byPerson.has(c.person)?canonicalName(byPerson.get(c.person)):c.person)}</a> · ${h(c.role)}</li>`).join('')}</ul>`:'<p>Authorship not entered.</p>'}<p class="note">Roles are first-pass interpretations of the cited ECCP passages.</p></section>
        <section><h2>Bibliographical notes</h2>${w.extent?`<p><strong>Extent:</strong> ${h(w.extent)}</p>`:''}${w.publication?`<p><strong>Publication:</strong> ${h(w.publication)}</p>`:''}<p>${h(w.note)}</p>${related}</section>
        <section><h2>Sources</h2>${Object.values(w.sources).map(s=>`<p>${external(s.url,s.title)}<br><small>${h(s.attribution)}</small></p>`).join('')}</section></div>
        <section><h2>Occurrences in the imported texts · ${ms.length}</h2><ul class="mentions-list">${ms.map(m=>{const s=catalog.sources.find(s=>s.id===m.witness);return `<li><a href="${h(readerURL(m.witness,m.passage))}">${h(s?.shortTitle || m.witness)} · ${h(m.passage)} →</a><br><q>${h(m.quote)}</q></li>`;}).join('')}</ul></section>
        <p class="note"><a href="data/works/${h(w.id)}.json">Work JSON</a> · <code>${h(w.id)}</code></p>`;
      document.title=`${w.title} · 文 · Ren-Wen`;
    }
    search.oninput=options;select.onchange=()=>{location.hash=select.value;};window.addEventListener('hashchange',route);options();route();
  }catch(error){$('work').innerHTML=`<h1>Work records could not be loaded</h1><p role="alert">${h(error.message)}</p>`;}
})();
