import {loadNameHistory, paragraphAnchor} from './name-history.js';
import {fetchData} from './data-cache.js';
import {t, ui, bindText, getLocale} from './i18n.js';
import {escapeHTML as h, safeURL, contextFor, validateProposal, PUNCTUATION, yearLabel} from './core.js';

const $ = id => document.getElementById(id);
const state = {catalog:null, source:null, passage:null, year:1878, selected:null, queue:[], timer:null};
const STORE = 'ren-wen:proposals:v1';
function proposalID() { return 'proposal-' + [...crypto.getRandomValues(new Uint8Array(16))].map(b=>b.toString(16).padStart(2,'0')).join(''); }
const svgNS = 'http://www.w3.org/2000/svg';
const entity = id => state.catalog.entities.find(e => e.id === id);
const link = (url,label) => safeURL(url) ? `<a href="${h(safeURL(url))}" target="_blank" rel="noopener">${ui(label)} ↗</a>` : h(label);
function toast(text) { bindText($('status'),text); clearTimeout(state.timer); state.timer=setTimeout(()=>bindText($('status'),''),6500); }
function modal(title,html) { $('dialog-body').innerHTML=`<h2>${ui(title)}</h2>${html}`; if (!$('dialog').open) $('dialog').showModal(); }
function svg(tag,attrs,parent) { const n=document.createElementNS(svgNS,tag);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,v);parent.append(n);return n; }
function download(name,bytes,type='application/json') { const url=URL.createObjectURL(new Blob([bytes],{type}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000); }
function saveQueue() { try {localStorage.setItem(STORE,JSON.stringify(state.queue));}catch{toast('Browser storage unavailable. Export the queue before closing.');}$('queue-count').textContent=state.queue.length; }
function setYear(value, note) { state.year=Number(value);$('year').value=state.year;$('year-label').textContent=state.year;bindText($('date-note'),note||'Viewing year is not a date assigned to the entire passage.');renderTimeline(); }
function selectEntity(id) {state.selected=id;document.querySelectorAll('#reader [data-entity]').forEach(n=>n.classList.toggle('selected',n.dataset.entity===id));renderTimeline();renderMap();}
function jump(passage) { const node=$(passage);if(node){node.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'start'});activate(passage);} }
function activate(id) {
  if (!id || !$(id)) return;
  state.passage=id;
  document.querySelectorAll('#reader p[id]').forEach(p=>p.classList.toggle('active',p.id===id));
  const ctx=contextFor(state.catalog,state.source.id,id);
  $('reading-context').textContent=`${state.source.shortTitle} · ${id} · ${ctx.events.length ? [...new Set(ctx.events.map(e=>yearLabel(e.time)))].join(', ') : t('no single event date')}`;
  const anchor=paragraphAnchor(ctx,state.source.id,id);
  if(anchor)$('reading-context').textContent=`${state.source.shortTitle} · ${id} · ${t('Paragraph anchor: {year}',{year:anchor.year})}`;
  if($('follow').checked && anchor) setYear(anchor.year, 'Following a recorded paragraph year; other events may have different dates.');
  else if($('follow').checked)bindText($('date-note'),'This paragraph has no unique year anchor. Use the year control to explore.');
  renderTimeline();renderEvents();renderMap();
}
function safeFragment(text) {
  const doc=new DOMParser().parseFromString(text,'text/html');
  const allowed=new Set(['P','SPAN','A','I','EM','B','STRONG','SUP','SUB','BR']);
  for(const el of [...doc.body.querySelectorAll('*')]) {
    if(!allowed.has(el.tagName)){el.remove();continue;}
    for(const attr of [...el.attributes]) if(!['id','data-entity','href','lang'].includes(attr.name)) el.removeAttribute(attr.name);
    if(el.hasAttribute('href')) {const url=safeURL(el.getAttribute('href'));if(url){el.setAttribute('href',url);el.setAttribute('target','_blank');el.setAttribute('rel','noopener');}else el.removeAttribute('href');}
  }
  return doc.body;
}
let loadSequence=0;
async function loadSource(id) {
  const seq=++loadSequence; const source=state.catalog.sources.find(s=>s.id===id);
  if(!source)throw Error('Unknown source.');
  const r=await fetch(source.text); if(!r.ok)throw Error(`Cannot load ${source.text} (${r.status}).`);
  const text=await r.text(); if(seq!==loadSequence)return;
  state.source=source; state.passage=null; $('inspector').hidden=true; $('source-select').value=id;$('punctuation').checked=false;
  $('punctuation').disabled=source.language==='en';document.body.classList.remove('punctuation-off');
  const reader=$('reader');reader.innerHTML=`<div class="kicker">${h(source.edition)}</div><h1>${h(source.title)}</h1><div class="source-caption">${ui(source.extent)}<br>${ui("Annotations are proposals awaiting independent review.")} ${link(source.revisionUrl,'Read source')}<div class="source-language-note">${ui('Original text · language unchanged')}</div></div>`;
  const root=safeFragment(text);let last=0;
  for(const p of [...root.children]) {
    const number=Number(p.id.split('-').at(-1));
    if(last&&number>last+1){const gap=document.createElement('div');gap.className='excerpt-gap';bindText(gap,'· · · intervening text omitted · · ·');reader.append(gap);}
    last=number;p.lang=source.language;p.dataset.sourceText='';reader.append(p);
    if(source.language.startsWith('zh')) {
      const walker=document.createTreeWalker(p,NodeFilter.SHOW_TEXT);const nodes=[];while(walker.nextNode())nodes.push(walker.currentNode);
      for(const n of nodes)if([...n.data].some(c=>PUNCTUATION.test(c))){const f=document.createDocumentFragment();for(const c of n.data){if(PUNCTUATION.test(c)){const s=document.createElement('span');s.className='editorial-punctuation';s.textContent=c;f.append(s);}else f.append(document.createTextNode(c));}n.replaceWith(f);}
    }
  }
  for(const span of reader.querySelectorAll('[data-entity]')) {const e=entity(span.dataset.entity);span.dataset.type=e?.type||'unknown';span.tabIndex=0;span.setAttribute('role','button');span.setAttribute('aria-label',`Inspect ${span.textContent}`);span.title='Inspect this occurrence; Ctrl/Cmd-click an original link to follow Wikisource.';}
  reader.scrollTop=0;activate(reader.querySelector('p[id]')?.id);selectEntity(source.subject || new URLSearchParams(location.search).get('person') || null);
  history.replaceState(null,'',`${location.search}#${encodeURIComponent(id)}`);
  const requested=new URLSearchParams(location.search).get('passage');
  if(requested && reader.querySelector('p[id]') && document.getElementById(requested)?.parentElement===reader)requestAnimationFrame(()=>jump(requested));
}
function renderTimeline() {
  if(!state.source || document.body.classList.contains('context-enhanced'))return;
  const root=$('timeline');root.replaceChildren();
  const ctx=contextFor(state.catalog,state.source.id,state.passage);
  const allIds=new Set(state.catalog.mentions.filter(m=>m.witness===state.source.id).map(m=>m.entity));if(state.source.subject)allIds.add(state.source.subject);
  const people=state.catalog.entities.filter(e=>e.type==='person'&&allIds.has(e.id));
  root.setAttribute('viewBox',`0 0 400 ${people.length*60+45}`);
  const x=y=>95+(y-1800)*2.85;
  for(let y=1800;y<=1900;y+=20){svg('line',{x1:x(y),x2:x(y),y1:22,y2:people.length*60+20,class:'ruler'},root);svg('text',{x:x(y),y:13,'text-anchor':'middle'},root).textContent=y;}
  people.forEach((p,i)=>{
    const active=ctx.entityIds.includes(p.id)||p.id===state.source.subject;const g=svg('g',{class:`person-row ${active?'active':'dim'}`,tabindex:0,role:'button','aria-label':`Inspect ${p.display}`},root);const y=i*60+40;
    svg('text',{x:3,y:y+2,class:'name'},g).textContent=p.label;
    svg('text',{x:3,y:y+16},g).textContent=p.life?`${p.life.birth}–${p.life.death}`:'dates unknown';
    if(p.life)svg('rect',{x:x(p.life.birth),y:y-8,width:Math.max(2,x(p.life.death)-x(p.life.birth)),height:15,class:'life-bar'},g);
    else svg('text',{x:100,y:y+2},g).textContent='No lifespan assertion imported';
    if(p.id===state.selected)svg('line',{x1:0,x2:80,y1:y+22,y2:y+22,stroke:'#ab543e','stroke-width':1},g);
    for(const e of ctx.events.filter(e=>e.people.includes(p.id)))svg('circle',{cx:x(e.time.start),cy:y,r:3,class:'event-dot'},g);
    const open=()=>{selectEntity(p.id);inspect(p.id);};g.addEventListener('click',open);g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();open();}});
  });
  svg('line',{x1:x(state.year),x2:x(state.year),y1:21,y2:people.length*60+20,class:'cursor'},root);
}
function renderEvents() {
  const events=contextFor(state.catalog,state.source.id,state.passage).events;$('event-count').textContent=events.length||'';
  $('events').innerHTML=events.length?events.map(e=>`<button class="event-card" data-event="${h(e.id)}"><span class="date">${h(yearLabel(e.time))}</span><strong>${ui(e.label)}</strong><small>${h(e.time.original)} · ${ui(e.kind)} · ${ui("proposed")}</small></button>`).join(''):`<p class="empty">${ui("No dated event has been extracted from this passage. No date is inferred just to fill the timeline.")}</p>`;
}
function renderMap() {
  if(!state.source)return;const ctx=contextFor(state.catalog,state.source.id,state.passage);const group=$('map-points');group.replaceChildren();
  const places=state.catalog.entities.filter(e=>e.type==='place');
  for(const p of places.filter(p=>p.point)) {
    const[lon,lat]=p.point.coordinates;const g=svg('g',{class:`map-point ${ctx.entityIds.includes(p.id)||state.selected===p.id?'active':''}`,tabindex:0,role:'button','aria-label':`Inspect ${p.display}`},group);
    svg('circle',{cx:lon+20,cy:75-lat,r:.9},g);svg('text',{x:lon+21.5,y:75-lat+(p.id==='place-paris'?3:-1.5)},g).textContent=p.display;
    const open=()=>{selectEntity(p.id);inspect(p.id);};g.addEventListener('click',open);g.addEventListener('keydown',e=>{if(e.key==='Enter')open();});
  }
  const here=places.filter(p=>ctx.entityIds.includes(p.id));$('places').innerHTML=here.length?here.map(p=>`<button class="place-card" data-place="${h(p.id)}"><strong>${h(p.display)} <span lang="zh-Hant">${h(p.label)}</span></strong><small>${ui(p.point?'Modern reference point; historical jurisdiction not imported.':'Historical location / jurisdiction unresolved; no point invented.')}</small></button>`).join(''):`<p class="empty">${ui("No identified places in this passage.")}</p>`;
}
function inspect(id,mentionId=null) {
  const e=entity(id);if(!e)return;const mention=state.catalog.mentions.find(m=>m.id===mentionId);const holder=$('inspector-body');
  holder.innerHTML=`<div class="small-label">${ui(e.type)} · ${ui(mention?'occurrence-level annotation':'entity record')}</div><h2>${ui(e.label)}</h2><p>${h(e.display)}</p>${e.note?`<p class="notice">${h(e.note)}</p>`:''}${e.life?`<p>${ui("Life dates:")} ${e.life.birth}–${e.life.death}<br>${link(e.life.source,'Evidence for the life bar')}</p>`:''}${e.point?`<p>${h(e.point.note)}<br>${link(e.point.source,'Coordinate reference')}</p>`:''}<p><code>${h(e.id)}</code></p>`;
  const sources=state.catalog.sources.filter(s=>(e.sources||[]).includes(s.id));
  if(sources.length||(e.externalSources||[]).length){holder.innerHTML+=`<h3>${ui("Other accounts of this person")}</h3>`;for(const s of sources)holder.innerHTML+=`<p><button data-source="${h(s.id)}">${h(s.shortTitle)}</button></p>`;for(const s of e.externalSources||[])holder.innerHTML+=`<p>${link(s.url,s.label)}</p>`;}
  const ms=state.catalog.mentions.filter(m=>m.entity===id&&m.witness===state.source.id);if(ms.length)holder.innerHTML+=`<h3>${ui("Mentions in this source")}</h3><div class="actions">${[...new Set(ms.map(m=>m.passage))].map(p=>`<button data-passage="${h(p)}">${h(p)}</button>`).join('')}</div>`;
  if(mention){holder.innerHTML+=`<h3>${ui("Review this occurrence")}</h3><blockquote data-original lang="${h(state.source.language)}">${h(mention.quote)}</blockquote><p>${ui("Status:")} ${ui(mention.status)} · ${ui(mention.origin)}<br><code>${h(mention.id)}</code></p><label for="candidate">${ui("Proposed identification")}<select id="candidate">${state.catalog.entities.filter(x=>x.type===e.type).map(x=>`<option value="${h(x.id)}" ${x.id===id?'selected':''}>${h(x.label)} · ${h(x.display)}</option>`).join('')}</select></label><label for="reason">${ui("Reason and supporting evidence")}<textarea id="reason" placeholder="${h(t("Explain why this occurrence refers to a different entity…"))}" data-i18n-placeholder="Explain why this occurrence refers to a different entity…"></textarea></label><div class="actions"><button class="primary" id="propose">${ui("Add to review queue")}</button></div><p class="notice">${ui("This creates a local proposal. It does not alter the edition, publish to GitHub, or edit ctext.")}</p>`;
    $('propose').onclick=()=>{try{const p=validateProposal({schemaVersion:1,id:proposalID(),operation:'relink-mention',witness:mention.witness,mention:mention.id,baseSha256:state.source.sha256,before:mention.entity,after:$('candidate').value,reason:$('reason').value.trim(),status:'proposed',created:new Date().toISOString()},state.catalog);state.queue=state.queue.filter(x=>x.mention!==p.mention);state.queue.push(p);saveQueue();toast('Correction added to your local review queue.');}catch(error){toast(error.message);}};
  }
  $('inspector').hidden=false;
}
function showSourceInfo(){const s=state.source;modal('Source & edition',`<p><strong>${h(s.title)}</strong></p><p>${h(s.edition)}</p><p>${h(s.extent)}</p><h3>${ui("Import")}</h3><p>${h(s.importMethod)}</p><p>${link(s.revisionUrl,'Wikisource revision '+s.revision)} · retrieved ${h(s.retrieved)}</p><h3>${ui("Punctuation")}</h3><p>${h(s.punctuation.attribution)}</p><h3>${ui("Rights & attribution")}</h3><p>${h(s.rights.attribution)}<br>${h(s.rights.text)}<br>${h(s.rights.transcription)}</p><h3>${ui("Working-copy checksum")}</h3><p><code>${h(s.sha256)}</code></p><p class="notice">${ui("ECCP and 清史稿 are different accounts, not editions or translations of one another. The pilot has no aligned historical variants yet.")}</p>`);}
function showQueue(){modal('Review queue',`<p>${ui("Local proposals only. Export these for an agent or a reviewed repository change. Nothing is sent upstream.")}</p><div class="actions"><button id="export-queue" ${state.queue.length?'':'disabled'}>${ui("Export JSON")}</button><button id="import-queue">${ui("Import proposal JSON")}</button></div>${state.queue.length?state.queue.map(p=>`<div class="queue-item"><strong>${h(p.mention)}</strong><p>${h(entity(p.before)?.label)} → ${h(entity(p.after)?.label)}</p><p>${h(p.reason)}</p><button data-remove="${h(p.id)}">${ui("Remove proposal")}</button></div>`).join(''):`<p class="empty">${ui("Select a marked name, inspect its identification, and propose a correction.")}</p>`}`);$('export-queue').onclick=()=>download('ren-wen-proposals.json',JSON.stringify(state.queue,null,2)+'\n');$('import-queue').onclick=()=>$('proposal-file').click();}

$('close-inspector').onclick=()=>$('inspector').hidden=true;$('close-dialog').onclick=()=>$('dialog').close();
$('source-select').onchange=e=>{const url=new URL(location.href);url.search='';url.hash=e.target.value;history.replaceState(null,'',url);loadSource(e.target.value).catch(error=>toast(error.message));};
window.addEventListener('hashchange',()=>{let id;try{id=decodeURIComponent(location.hash.slice(1));}catch{return;}if(state.catalog?.sources.some(s=>s.id===id) && state.source?.id!==id)loadSource(id).catch(error=>toast(error.message));});
window.addEventListener('renwen:languagechange',()=>{
  if(!state.source || !state.passage)return;
  const ctx=contextFor(state.catalog,state.source.id,state.passage);
  const anchor=paragraphAnchor(ctx,state.source.id,state.passage);
  $('reading-context').textContent=`${state.source.shortTitle} · ${state.passage} · ${anchor?t('Paragraph anchor: {year}',{year:anchor.year}):ctx.events.length ? [...new Set(ctx.events.map(e=>yearLabel(e.time)))].join(', ') : t('no single event date')}`;
});
$('source-info').onclick=showSourceInfo;$('queue-button').onclick=showQueue;
$('year').oninput=e=>{$('follow').checked=false;setYear(e.target.value,'Manual viewing year; source assertions are unchanged.');};
$('follow').onchange=()=>activate(state.passage);
$('punctuation').onchange=e=>{document.querySelectorAll('.editorial-punctuation').forEach(n=>n.classList.toggle('hidden-mark',e.target.checked));document.body.classList.toggle('punctuation-off',e.target.checked);};
$('reader').addEventListener('click',e=>{if(e.ctrlKey||e.metaKey)return;const span=e.target.closest('[data-entity]');const p=e.target.closest('p[id]');if(p)activate(p.id);if(span){e.preventDefault();selectEntity(span.dataset.entity);inspect(span.dataset.entity,span.id);}});
$('reader').addEventListener('keydown',e=>{if((e.key==='Enter'||e.key===' ')&&e.target.matches('[data-entity]')){e.preventDefault();e.target.click();}});
let scrollFrame; $('reader').addEventListener('scroll',()=>{if(!$('follow').checked||scrollFrame)return;scrollFrame=requestAnimationFrame(()=>{scrollFrame=null;const top=$('reader').getBoundingClientRect().top+130;const ps=[...document.querySelectorAll('#reader p[id]')];const p=ps.find(n=>n.getBoundingClientRect().bottom>top);if(p&&p.id!==state.passage)activate(p.id);});});
$('events').addEventListener('click',e=>{const id=e.target.closest('[data-event]')?.dataset.event;const ev=state.catalog.events.find(x=>x.id===id);if(ev){setYear(ev.time.start,`${ev.time.original}. ${ev.note}`);modal('Event evidence',`<p><strong>${h(ev.label)}</strong></p><p>${ui("Source date:")} ${h(ev.time.original)}<br>${ui("Display index:")} ${h(yearLabel(ev.time))} (${h(ev.time.precision)} precision)</p><p>${h(ev.note)}</p><p>${ui("Status:")} ${ui(ev.status)} · ${ui(ev.kind)}</p><p>${ui("Evidence:")} ${h(ev.passage)} · ${link(state.source.revisionUrl,state.source.shortTitle)}</p><p class="notice">${ui("The display year is not a new assertion about every person or place in this paragraph.")}</p>`);}});
$('places').addEventListener('click',e=>{const id=e.target.closest('[data-place]')?.dataset.place;if(id){selectEntity(id);inspect(id);}});
$('inspector-body').addEventListener('click',e=>{const source=e.target.closest('[data-source]')?.dataset.source;const passage=e.target.closest('[data-passage]')?.dataset.passage;if(source){$('inspector').hidden=true;loadSource(source).catch(x=>toast(x.message));}if(passage){$('inspector').hidden=true;jump(passage);}});
$('dialog-body').addEventListener('click',e=>{const id=e.target.closest('[data-remove]')?.dataset.remove;if(id){state.queue=state.queue.filter(p=>p.id!==id);saveQueue();showQueue();}});
$('map-reset').onclick=()=>$('map').setAttribute('viewBox','0 0 170 80');
$('map-fit').onclick=()=>{const ids=contextFor(state.catalog,state.source.id,state.passage).entityIds;const pts=state.catalog.entities.filter(e=>e.point&&ids.includes(e.id)).map(e=>e.point.coordinates);if(!pts.length){toast('No located place in this passage.');return;}const xs=pts.map(p=>p[0]+20),ys=pts.map(p=>75-p[1]);const cx=(Math.min(...xs)+Math.max(...xs))/2,cy=(Math.min(...ys)+Math.max(...ys))/2;const w=Math.max(25,Math.max(...xs)-Math.min(...xs)+15),height=Math.max(18,Math.max(...ys)-Math.min(...ys)+12);$('map').setAttribute('viewBox',`${cx-w/2} ${cy-height/2} ${w} ${height}`);};
$('about-button').onclick=()=>modal('人文 · Ren-Wen',`<p>${ui("People through texts. Texts in context.")}</p><p>${ui("The first-round collection preserves 809 biographical entries, 193 cross-reference notices and 6 reference texts from ECCP. Source text, bibliography, quotations and contributor names remain intact.")}</p><h3>${ui("What is deliberately not claimed")}</h3><p>${ui("Person and work identifications and QSG opening matches are first-pass proposals, not independently reviewed facts. QSG links may lead to a complete containing volume rather than an isolated biography. Dated name and title periods are a limited pilot. Map boundaries are dated regional reference images, not reconstructions for every narrative year.")}</p><h3>${ui("Original text and versions")}</h3><p>${ui("Imported wording is stored separately from our annotated working copy. Historical witnesses coexist; they are never automatically merged into one “correct” text. Chinese punctuation can be hidden for reading without changing the stored text.")}</p><p>${link('https://github.com/liuyao12/ren-wen','Project, documentation, and Python tools')}</p>`);
$('xml-button').onclick=()=>$('xml-file').click();
$('xml-file').onchange=async e=>{const file=e.target.files[0];e.target.value='';if(!file)return;try{if(file.size>5_000_000)throw Error('XML files are limited to 5 MB in the pilot.');const bytes=new Uint8Array(await file.arrayBuffer());const text=new TextDecoder('utf-8',{fatal:true}).decode(bytes);if(text.includes('\0') || /<!\s*(DOCTYPE|ENTITY)/i.test(text))throw Error('DTD and entity declarations are not accepted.');const xml=new DOMParser().parseFromString(text,'application/xml');if(xml.querySelector('parsererror'))throw Error('This is not well-formed XML.');const counts={};xml.querySelectorAll('*').forEach(n=>counts[n.tagName]=(counts[n.tagName]||0)+1);modal('XML preservation check',`<p><strong>${h(file.name)}</strong> · ${bytes.length.toLocaleString()} bytes</p><p class="notice">This is a raw XML inspector, not yet a verified ctext semantic importer. Unknown elements and attributes are preserved in the original bytes. No entity identifications or dates are inferred.</p><pre>${h(JSON.stringify(counts,null,2))}</pre><div class="actions"><button id="xml-export">${ui("Download unchanged XML")}</button></div><h3>${ui("Text preview (inert)")}</h3><pre>${h(xml.documentElement.textContent.slice(0,2500))}</pre>`);$('xml-export').onclick=()=>download(file.name,bytes,'application/xml');}catch(error){toast(error.message);}};
$('proposal-file').onchange=async e=>{const file=e.target.files[0];e.target.value='';if(!file)return;try{if(file.size>1_000_000)throw Error('Proposal file too large.');const parsed=JSON.parse(await file.text());const list=Array.isArray(parsed)?parsed:[parsed];const checked=list.map(p=>validateProposal(p,state.catalog));const staged=[...state.queue];const existing=new Set(staged.map(p=>p.id));for(const p of checked)if(!existing.has(p.id)){if(staged.some(x=>x.mention===p.mention))throw Error('A proposal for this mention already exists. Remove it first.');staged.push(p);existing.add(p.id);}state.queue=staged;saveQueue();showQueue();}catch(error){toast(error.message);}};
(async()=>{try{const r=await fetchData('data/catalog.json');if(!r.ok)throw Error(`Catalog request failed (${r.status}).`);await loadNameHistory();state.catalog=await r.json();$('source-select').innerHTML=state.catalog.sources.map(s=>`<option value="${h(s.id)}">${h(s.shortTitle)}</option>`).join('');const search=document.createElement('input');search.type='search';search.className='source-search';search.setAttribute('aria-label',t('Find another biography'));search.placeholder=t('Find another biography');$('source-select').before(search);search.oninput=()=>{const needle=search.value.toLocaleLowerCase();for(const option of $('source-select').options){const source=state.catalog.sources.find(s=>s.id===option.value);option.hidden=option.value!==state.source?.id && !`${source.title} ${source.shortTitle}`.toLocaleLowerCase().includes(needle);}};try{const stored=JSON.parse(localStorage.getItem(STORE)||'[]');state.queue=stored.filter(p=>{try{validateProposal(p,state.catalog);return true;}catch{return false;}});}catch{state.queue=[];}saveQueue();for(let lon=0;lon<=160;lon+=20)svg('line',{x1:lon,x2:lon,y1:0,y2:80,class:'gridline'},$('graticule'));for(let lat=15;lat<=75;lat+=15)svg('line',{x1:0,x2:170,y1:lat,y2:lat,class:'gridline'},$('graticule'));let id;try{id=decodeURIComponent(location.hash.slice(1));}catch{id='';}await loadSource(state.catalog.sources.some(s=>s.id===id)?id:state.catalog.defaultWitness);}catch(error){$('reader').innerHTML=`<h1>${ui("Unable to load Ren-Wen")}</h1><p class="error">${h(error.message)}</p><p>Serve this directory over HTTP, for example with <code>python -m http.server 8000</code>. Opening index.html as a local file cannot load the corpus.</p>`;$('reading-context').textContent='Loading failed';}})();
