import {t, ui, bindText, getLocale} from './i18n.js';
/** Progressive context panels. Text, source snapshots, and annotation IDs remain untouched. */
import {escapeHTML as h, safeURL, contextFor} from './core.js';
import {loadProfiles, canonicalName} from './profiles.js';
import {profilesWithStubs, westernYearText, profileURL} from './person-display.js';
import {createFamilyTimeline} from './family-timeline.js';
import {familyHierarchy} from './family-layout.js';
import {jurisdictionChain, inYears, project, arcPath,
  routeSegments, validateBoundaries, boundaryPath, clampView, referenceLevels, REGIONAL_VIEW} from './context-model.js';

const $=id=>document.getElementById(id), NS='http://www.w3.org/2000/svg';
const add=(tag,attrs,parent,text)=>{const n=document.createElementNS(NS,tag);for(const[k,v]of Object.entries(attrs))n.setAttribute(k,v);if(text!==undefined)n.textContent=text;parent.append(n);return n;};
const ext=(url,label)=>safeURL(url)?`<a href="${h(safeURL(url))}" target="_blank" rel="noopener">${h(label)} ↗</a>`:h(label);
const shortName=p=>(p.name.surname||'')+p.name.given;
const lifeYear=(p,key)=>{const s=westernYearText(p,key);return /^\d+$/.test(s)?Number(s):null;};
const labelYear=(p,key)=>westernYearText(p,key);

async function install(){
  if(!$('reader'))return;
  const [cr,gr,profiles]=await Promise.all([fetch('data/catalog.json'),fetch('data/geography.json'),loadProfiles()]);
  if(!cr.ok||!gr.ok)throw Error('Context data could not be loaded.');
  const catalog=await cr.json(), geo=await gr.json();
  if(geo.schemaVersion!==1)throw Error('Unsupported geography data.');
  // A failed reference-map fetch must not disable camera controls or the timeline.
  let reference=null;try {const r=await fetch('data/reference-maps.json');if(r.ok)reference=await r.json();} catch(error){console.warn('Reference map unavailable',error);}
  const people=new Map(profilesWithStubs(catalog,profiles).map(p=>[p.id,p]));
  const entities=new Map(catalog.entities.map(e=>[e.id,e]));
  let current=null, selectedPerson=null, pendingJump=null;
  let view=[...REGIONAL_VIEW], boundaries=validateBoundaries(geo.boundaries,geo.jurisdictions);
  let chosenJurisdiction=null, lastPassage=null, frame=0;
  const reduced=()=>matchMedia('(prefers-reduced-motion: reduce)').matches;
  const report=(text,params={})=>{bindText($('context-map-status'),text,params);};
  const placeName=p=>getLocale()==='zh-Hant'?(p?.label||p?.display||''):(p?.display||p?.label||'');
  const dialog=document.createElement('dialog');dialog.id='context-evidence';document.body.append(dialog);
  function evidence(title,body){dialog.innerHTML=`<button class="close" aria-label="${h(t("Close evidence"))}" data-i18n-aria-label="Close evidence">×</button><h2>${ui(title)}</h2>${body}`;dialog.querySelector('.close').onclick=()=>dialog.close();if(!dialog.open)dialog.showModal();}
  function focusPassage(witness,passage){
    dialog.close();const target=$(passage);
    if($('source-select').value===witness&&target){target.click();target.scrollIntoView({block:'start',behavior:reduced()?'instant':'smooth'});return;}
    pendingJump={witness,passage};$('source-select').value=witness;$('source-select').dispatchEvent(new Event('change',{bubbles:true}));
  }
  dialog.addEventListener('click',e=>{const b=e.target.closest('[data-evidence-passage]');if(b)focusPassage(b.dataset.witness,b.dataset.evidencePassage);});
  const passageButton=(w,p)=>`<button data-witness="${h(w)}" data-evidence-passage="${h(p)}">${ui("Read {passage}",{passage:p})}</button>`;

  // Keep legacy nodes as a fallback/API compatibility surface; expose only the new panels.
  const time=document.createElement('div');time.className='context-timeline';
  $('timeline').before(time);$('timeline').style.display='none';
  const familyTimeline=createFamilyTimeline({host:time,catalog,people,passageButton,onEvidence:evidence,
    onSelect(id){selectedPerson=id;$('trajectory-person').value=id;paintMap();report('Trajectory: {name}. Only documented movements are shown.',{name:shortName(people.get(id))});}});

  const panel=document.querySelector('.map-panel');
  const mapBody=document.createElement('div');mapBody.className='context-map-body';
  mapBody.innerHTML=`<div class="context-map-toolbar"><label>${ui("Trajectory")} <select id="trajectory-person" aria-label="${h(t("Whose life trajectory"))}" data-i18n-aria-label="Whose life trajectory"></select></label><label>${ui("Show")} <select id="trajectory-scope"><option value="all" data-i18n="All recorded journeys">${t("All recorded journeys")}</option><option value="passage" data-i18n="This passage">${t("This passage")}</option><option value="year" data-i18n="Through viewing year">${t("Through viewing year")}</option></select></label></div>
  <div class="reference-map-controls"><label>${ui("Historical reference map")} <select id="reference-year"><option value="1911">1911 · 宣統三年</option><option value="1820">1820 · 嘉慶二十五年</option><option value="none" data-i18n="Hide reference map">${t("Hide reference map")}</option></select></label><label>${ui("Detail")} <select id="reference-detail"><option value="auto" data-i18n="By zoom">${t("By zoom")}</option><option value="province">省</option><option value="prefecture">省／府</option><option value="county">省／府／縣</option></select></label></div>
  <div class="interactive-map"><svg id="historic-map" viewBox="125 38 22 16" role="group" tabindex="0" aria-label="${h(t("Interactive map. Drag or pinch; use plus, minus, arrow keys, or Home."))}" data-i18n-aria-label="Interactive map. Drag or pinch; use plus, minus, arrow keys, or Home."><defs><marker id="trajectory-arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L8 4 L0 8 Z"/></marker></defs><rect class="sea" x="0" y="0" width="170" height="80"/><image href="assets/land.svg" width="170" height="80"/><g id="historical-reference-images" pointer-events="none"></g><g id="historical-boundaries"></g><g id="life-trajectories"></g><g id="context-places"></g></svg>
  <div class="map-zoom"><button id="context-zoom-in" aria-label="${h(t("Zoom in"))}" data-i18n-aria-label="Zoom in">+</button><button id="context-zoom-out" aria-label="${h(t("Zoom out"))}" data-i18n-aria-label="Zoom out">−</button><button id="context-map-home" aria-label="${h(t("Reset map"))}" data-i18n-aria-label="Reset map">⌂</button></div></div>
  <div class="context-map-actions"><button id="context-world">${ui("World overview")}</button><button id="context-fit-passage">${ui("Fit passage")}</button><button id="context-fit-journey">${ui("Fit journeys")}</button><span id="context-map-year"></span></div>
  <p class="context-caption">${ui("Drag · scroll / pinch to zoom · arrows show stop order, not actual travel paths. Modern reference coastline and city points.")}</p><p id="reference-map-status" class="reference-status" role="status"></p><details class="reference-attribution"><summary>${ui("Map coverage and attribution")}</summary><p>${ui("Cropped middle/lower Yangtze reference maps only (108–123°E, 24–35°N). Snapshot dates are independent of the viewing year; no historical interpolation is implied. County boundaries are available only for the 1911 snapshot.")}</p><p>CHGIS Version 6. © Fairbank Center for Chinese Studies and the Institute for Chinese Historical Geography at Fudan University, Dec 2016.</p><p><a href="assets/maps/CHGIS-V6-EULA.txt" target="_blank" rel="noopener">${ui("Source terms and map-image attribution")}</a></p></details>
  <div id="context-map-status" class="context-caption" role="status"></div>
  <div class="context-jurisdictions"><h3>${ui("Historical jurisdictions · 政區")}</h3><div class="jurisdiction-selectors">${[['province','省'],['prefecture','府'],['county','縣']].map(([id,zh])=>`<label>${zh}<select id="jurisdiction-${id}" aria-label="${h(t(`Historical ${id}`))}" data-i18n-aria-label="Historical ${id}"></select></label>`).join('')}</div>
  <div id="jurisdiction-evidence"></div><details><summary>${ui("Boundary layer")}</summary><p>${ui("The dated reference map uses cropped map images, not bundled source polygons. Additional GeoJSON remains local to this browser session.")}</p><label>${ui("Level")} <select id="boundary-level"><option value="all" data-i18n="All levels">${t("All levels")}</option><option value="province" data-i18n="Provinces">${t("Provinces")}</option><option value="prefecture" data-i18n="Prefectures">${t("Prefectures")}</option><option value="county" data-i18n="Counties">${t("Counties")}</option></select></label><div class="context-map-actions"><button id="load-boundaries">${ui("Open GeoJSON")}</button><button id="clear-boundaries">${ui("Clear local layer")}</button></div><input id="boundary-file" type="file" accept=".json,.geojson,application/geo+json,application/json" hidden><p id="boundary-credit"></p></details></div>
  <div id="context-journeys"></div><div id="context-place-list"></div>`;
  for(const old of panel.querySelectorAll(':scope > .map-tools,:scope > .map-wrap,:scope > .map-note,:scope > .place-body'))old.hidden=true;
  $('map-reset').hidden=true;panel.querySelector('.panel-footer').before(mapBody);
  const map=$('historic-map');
  $('reference-year').onchange=()=>paintMap(false);
  $('reference-detail').onchange=()=>paintMap(false);
  $('context-world').onclick=()=>setView([0,0,170,80]);
  // Native SVG image loading with persistent nodes: zooming does not redownload layers.
  const referenceImages=[];
  for(const layer of reference?.layers||[]){
    if(!/^assets\/maps\/chgis-\d{4}-(province|prefecture|county)-yangtze\.png$/.test(layer.file))continue;
    const [west,south,east,north]=layer.bbox;
    const image=add('image',{href:layer.file,x:west+20,y:75-north,width:east-west,height:north-south,'data-reference-level':layer.level,'data-reference-year':layer.year,preserveAspectRatio:'none',visibility:'hidden'},$('historical-reference-images'));
    image.addEventListener('error',()=>{image.dataset.loadError='true';report('Reference map image could not be loaded.');});
    referenceImages.push({layer,image});
  }
  // County linework below prefectures and provinces.
  referenceImages.sort((a,b)=>['county','prefecture','province'].indexOf(a.layer.level)-['county','prefecture','province'].indexOf(b.layer.level)).forEach(r=>$('historical-reference-images').append(r.image));
  map.addEventListener('dblclick',e=>{e.preventDefault();zoom(.5,coord(e.clientX,e.clientY));});
  $('trajectory-scope').onchange=()=>paintMap();
  $('trajectory-person').onchange=e=>{selectedPerson=e.target.value;paintMap();};
  $('boundary-level').onchange=()=>paintMap();
  $('context-map-home').onclick=()=>setView([...REGIONAL_VIEW]);
  $('context-zoom-in').onclick=()=>zoom(.7);$('context-zoom-out').onclick=()=>zoom(1/.7);
  $('context-fit-passage').onclick=()=>fit(current?.context.entityIds||[]);
  $('context-fit-journey').onclick=()=>fit(visibleSegments().flatMap(s=>[s.from.place,s.to.place]));
  function fit(ids){
    const pts=[...new Set(ids)].map(id=>entities.get(id)?.point?.coordinates).filter(Boolean).map(project);
    if(!pts.length){report('No mapped coordinates for this selection; no location inferred.');return;}
    const xs=pts.map(p=>p[0]),ys=pts.map(p=>p[1]);
    const w=Math.max(10,Math.max(...xs)-Math.min(...xs)+12),hh=Math.max(8,Math.max(...ys)-Math.min(...ys)+10);
    setView([(Math.min(...xs)+Math.max(...xs)-w)/2,(Math.min(...ys)+Math.max(...ys)-hh)/2,w,hh]);
  }
  function setView(next){view=clampView(next);map.setAttribute('viewBox',view.join(' '));paintMap(false);}
  function zoom(factor,center=[view[0]+view[2]/2,view[1]+view[3]/2]){
    factor=Math.max(.15/view[2],Math.min(170/view[2],factor));
    setView([center[0]-(center[0]-view[0])*factor,center[1]-(center[1]-view[1])*factor,view[2]*factor,view[3]*factor]);
  }
  function coord(x,y){const p=new DOMPoint(x,y).matrixTransform(map.getScreenCTM().inverse());return[p.x,p.y];}
  map.addEventListener('wheel',e=>{e.preventDefault();const delta=e.deltaY*(e.deltaMode===1?16:e.deltaMode===2?300:1);zoom(Math.exp(Math.max(-.5,Math.min(.5,delta*.002))),coord(e.clientX,e.clientY));},{passive:false});
  const pointers=new Map();let moved=false;
  map.addEventListener('pointerdown',e=>{if(e.button!==0)return;pointers.set(e.pointerId,[e.clientX,e.clientY]);moved=false;});
  map.addEventListener('pointermove',e=>{
    if(!pointers.has(e.pointerId))return;
    const before=[...pointers.values()],old=pointers.get(e.pointerId),next=[e.clientX,e.clientY];
    if(Math.hypot(next[0]-old[0],next[1]-old[1])>3){moved=true;map.setPointerCapture(e.pointerId);}
    if(!moved&&pointers.size===1)return;
    if(pointers.size===1){const a=coord(...old),b=coord(...next);setView([view[0]+a[0]-b[0],view[1]+a[1]-b[1],view[2],view[3]]);}
    pointers.set(e.pointerId,next);
    if(pointers.size===2){const after=[...pointers.values()],dist=a=>Math.hypot(a[0][0]-a[1][0],a[0][1]-a[1][1]);const oldD=dist(before),newD=dist(after);if(oldD>0&&newD>0)zoom(oldD/newD,coord((after[0][0]+after[1][0])/2,(after[0][1]+after[1][1])/2));moved=true;}
  });
  for(const event of ['pointerup','pointercancel','lostpointercapture'])map.addEventListener(event,e=>pointers.delete(e.pointerId));
  map.addEventListener('click',e=>{if(moved){e.preventDefault();e.stopImmediatePropagation();moved=false;}},true);
  map.addEventListener('keydown',e=>{if(e.target!==map)return;const d={ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,-1],ArrowDown:[0,1]}[e.key];if(d){e.preventDefault();setView([view[0]+d[0]*view[2]*.1,view[1]+d[1]*view[3]*.1,view[2],view[3]]);}else if(['+','=','-','Home'].includes(e.key)){e.preventDefault();e.key==='Home'?setView([...REGIONAL_VIEW]):zoom(e.key==='-'?1/.7:.7);}});
  $('load-boundaries').onclick=()=>$('boundary-file').click();
  $('clear-boundaries').onclick=()=>{boundaries=geo.boundaries.features;paintMap();report('Local boundary layer removed.');};
  $('boundary-file').onchange=async e=>{const file=e.target.files[0];e.target.value='';if(!file)return;try{if(file.size>5_000_000)throw Error('GeoJSON is limited to 5 MB.');const checked=validateBoundaries(JSON.parse(await file.text()),geo.jurisdictions);boundaries=checked;paintMap();report('Loaded {count} local boundary features. Source claims have not been independently reviewed.',{count:checked.length});}catch(error){report(error.message);}};
  for(const level of ['province','prefecture','county'])$(`jurisdiction-${level}`).onchange=e=>{
    chosenJurisdiction=e.target.value||null;updateHierarchy();focusJurisdiction();paintMap(false);
  };
  function focusJurisdiction(){
    const j=geo.jurisdictions.find(j=>j.id===chosenJurisdiction);if(!j)return;
    const polygon=boundaries.find(f=>f.properties.jurisdictionId===j.id&&inYears({start:f.properties.startYear,end:f.properties.endYear},current.year));
    if(polygon){const rings=polygon.geometry.type==='Polygon'?polygon.geometry.coordinates:polygon.geometry.coordinates.flat();const pts=rings.flat().map(project),xs=pts.map(p=>p[0]),ys=pts.map(p=>p[1]);setView([Math.min(...xs)-1,Math.min(...ys)-1,Math.max(2,Math.max(...xs)-Math.min(...xs)+2),Math.max(2,Math.max(...ys)-Math.min(...ys)+2)]);}
    else{fit(j.relatedPlaces);report('{name}: hierarchy only; no historical boundary available. Located points, where present, are modern references.',{name:j.label});}
  }
  function updateHierarchy(){
    if(!current)return;
    let chain=jurisdictionChain(geo.jurisdictions,chosenJurisdiction,current.year);
    const available=geo.jurisdictions.filter(j=>inYears(j.coverage,current.year));
    for(const level of ['province','prefecture','county']){
      const selector=$(`jurisdiction-${level}`),selected=chain.find(j=>j.level===level);
      const parent=level==='prefecture'?chain.find(j=>j.level==='province')?.id:level==='county'?chain.find(j=>j.level==='prefecture')?.id:null;
      const options=available.filter(j=>j.level===level&&j.parent===(parent||null));
      selector.innerHTML=`<option value="">${t(level==='province'?'Choose province':'Choose / unspecified')}</option>`+options.map(j=>`<option value="${h(j.id)}">${ui(j.label)}</option>`).join('');selector.value=selected?.id||'';selector.disabled=!options.length;
    }
    const j=chain.at(-1),s=j&&geo.sources[j.source];
    const context=geo.placeContexts.find(c=>c.jurisdiction===chosenJurisdiction);
    $('jurisdiction-evidence').innerHTML=j?`<p class="jurisdiction-breadcrumb" lang="zh-Hant">${chain.map(j=>h(j.label)).join(' › ')}</p><p>${ext(s.url,s.title)} · ${h(j.locator)}</p><p class="context-caption">${ui(context?.note||'Administrative hierarchy, not an assertion of anyone’s whereabouts.')} ${ui("Coverage:")} ${j.coverage.start}–${j.coverage.end}${ui("; proposed continuity, not founding dates. Intermediate circuits and other jurisdictions are not yet entered.")}</p>`:`<p class="context-caption">${ui(available.length?'Choose a jurisdiction or a mentioned place.':'No hierarchy record covers this viewing year.')} ${ui("This pilot contains only selected late-Qing units; it is not a complete province or county list.")}</p>`;
  }
  function visibleSegments(){return current?routeSegments(geo.journeys,{person:selectedPerson||current.source.subject,witness:current.source.id,passage:current.passage,year:current.year,scope:$('trajectory-scope').value}):[];}
  function journeyEvidence(j){const s=catalog.sources.find(s=>s.id===j.witness);evidence(j.label,`<p>${ui(j.basis)}</p><p>${ui("Status:")} ${ui(j.status)} · ${ext(s.revisionUrl,s.shortTitle)}</p>${j.stops.map(stop=>`<p><strong>${h(stop.date)}</strong> · ${h(placeName(entities.get(stop.place))||stop.place)} · ${ui(stop.kind)}<br><small>${h(stop.original)}</small></p>`).join('')}${passageButton(j.witness,j.passage)}`);}
  function paintMap(details=true){
    const snapshot=Number($('reference-year').value),mode=$('reference-detail').value,levels=referenceLevels(snapshot,view[2],mode);
    for(const r of referenceImages)r.image.setAttribute('visibility',r.layer.year===snapshot&&levels.includes(r.layer.level)?'visible':'hidden');
    const levelLabels={province:'省',prefecture:'府',county:'縣'};
    bindText($('reference-map-status'),referenceImages.length?(levels.length?'Reference {year} · {levels} · cropped region, not a map of the viewing year':'Reference map hidden'):'Reference map unavailable',{year:snapshot,levels:levels.map(l=>levelLabels[l]).join('／')});
    if(snapshot===1820&&(mode==='county'||(mode==='auto'&&view[2]<=7)))$('reference-map-status').append(' · '+t('1820 county boundaries unavailable; select 1911.'));
    map.querySelector(':scope > image').setAttribute('opacity',levels.length&&view[2]<30?'0.12':'1');
    if(!current)return;
    const segments=visibleSegments(),ids=new Set(current.context.entityIds),k=Math.max(view[2]/(map.clientWidth||400),view[3]/(map.clientHeight||240));
    const shapes=$('historical-boundaries');shapes.replaceChildren();const shown=boundaries.filter(f=>inYears({start:f.properties.startYear,end:f.properties.endYear},current.year)&&($('boundary-level').value==='all'||f.properties.level===$('boundary-level').value));
    for(const f of shown){const p=f.properties,j=geo.jurisdictions.find(j=>j.id===p.jurisdictionId);const path=add('path',{d:boundaryPath(f.geometry),class:`historical-boundary ${p.level}`,'fill-rule':'evenodd',tabindex:0,role:'button','aria-label':j.label},shapes);add('title',{},path,`${j.label} · ${p.startYear}–${p.endYear} · locally supplied boundary`);const open=()=>{chosenJurisdiction=j.id;updateHierarchy();evidence(j.label,`<p>${ext(p.source,'Boundary source')}</p><p>${h(p.attribution)} · ${h(p.license)}</p><p>Valid ${p.startYear}–${p.endYear}. Locally supplied; not independently reviewed by Ren-Wen.</p>`);};path.onclick=open;path.onkeydown=e=>{if(e.key==='Enter')open();};}
    const routes=$('life-trajectories');routes.replaceChildren();
    for(const s of segments){const a=entities.get(s.from.place)?.point?.coordinates,b=entities.get(s.to.place)?.point?.coordinates;if(!a||!b)continue;const group=add('g',{'data-route':s.id},routes);const d=arcPath(a,b);add('path',{d,class:`trajectory ${s.active?'active':''} ${s.future?'future':''}`,'marker-end':'url(#trajectory-arrow)'},group);const hit=add('path',{d,class:'trajectory-hit',tabindex:0,role:'button','aria-label':`${s.journey.label}: ${s.from.date} → ${s.to.date}`},group);add('title',{},hit,`${s.from.date} ${entities.get(s.from.place).display} → ${s.to.date} ${entities.get(s.to.place).display}\nSchematic connection. Click for evidence.`);hit.onclick=()=>journeyEvidence(s.journey);hit.onkeydown=e=>{if(e.key==='Enter')journeyEvidence(s.journey);};}
    const points=$('context-places');points.replaceChildren();const routePlaces=new Set(segments.flatMap(s=>[s.from.place,s.to.place]));
    for(const p of catalog.entities.filter(e=>e.type==='place'&&e.point)){
      const[x,y]=project(p.point.coordinates),g=add('g',{class:`context-place ${ids.has(p.id)?'active':''}`,tabindex:0,role:'button','aria-label':placeName(p),'data-place-id':p.id},points);
      add('circle',{cx:x,cy:y,r:(ids.has(p.id)?4.7:3.5)*k},g);
      if(ids.has(p.id)||routePlaces.has(p.id)||view[2]<70){const right=x>135;add('text',{x:x+(right?-7:7)*k,y:y+(p.id==='place-paris'?14:-6)*k,'text-anchor':right?'end':'start','font-size':11*k,'stroke-width':2.5*k},g,placeName(p));}
      add('title',{},g,`${placeName(p)} · ${t('Modern reference point')}`);
      const open=()=>{const placeContext=geo.placeContexts.find(c=>c.place===p.id);chosenJurisdiction=placeContext?.jurisdiction||null;updateHierarchy();report(placeContext?placeContext.note:`${p.display}: no historical jurisdiction record imported.`);};g.onclick=open;g.onkeydown=e=>{if(e.key==='Enter')open();};
    }
    if(!details)return;
    bindText($('context-map-year'),'Viewing {year}',{year:current.year});
    $('boundary-credit').textContent=boundaries.length?`${shown.length}/${boundaries.length} features visible at ${current.year}. `+[...new Set(shown.map(f=>`${f.properties.attribution} (${f.properties.license})`))].join('; '):t('No extra vector layer loaded. Reference-map images remain available above.');
    const journeys=[...new Map(segments.map(s=>[s.journey.id,s.journey])).values()];
    $('context-journeys').innerHTML=`<h3>${ui("Documented journeys · 行跡")}</h3>${journeys.length?journeys.map(j=>`<button class="journey-card ${j.passage===current.passage?'active':''}" data-journey="${h(j.id)}"><strong>${ui(j.label)}</strong><small>${j.stops.filter(s=>$('trajectory-scope').value!=='year'||Number(s.date.slice(0,4))<=current.year).map(s=>`${h(s.date)} ${h(entities.get(s.place)?.label||s.place)}`).join(' → ')}</small></button>`).join(''):`<p class="context-caption">${ui("No documented journey for this person in this source and scope. Appointments and native-place references are not converted into journeys.")}</p>`}`;
    $('context-journeys').querySelectorAll('[data-journey]').forEach(b=>b.onclick=()=>journeyEvidence(geo.journeys.find(j=>j.id===b.dataset.journey)));
    $('context-place-list').innerHTML=`<h3>${ui("Places in this passage")}</h3>`+catalog.entities.filter(p=>p.type==='place'&&ids.has(p.id)).map(p=>`<button class="journey-card" data-context-place="${h(p.id)}">${h(placeName(p))}${p.display!==p.label?` · ${h(getLocale()==='zh-Hant'?p.display:p.label)}`:''}<small>${ui(p.point?'Modern reference point':'Not located; no point invented')}</small></button>`).join('');
    $('context-place-list').querySelectorAll('[data-context-place]').forEach(b=>b.onclick=()=>{const c=geo.placeContexts.find(c=>c.place===b.dataset.contextPlace);chosenJurisdiction=c?.jurisdiction||null;updateHierarchy();fit([b.dataset.contextPlace]);});
  }
  function updateTimeline(){if(current)familyTimeline.update(current);}
  function refresh(){
    frame=0;const source=catalog.sources.find(s=>s.id===$('source-select').value),paragraph=$('reader').querySelector('p[id].active');
    if(!source||!paragraph||!paragraph.id.startsWith(source.id+'-'))return;
    const context=contextFor(catalog,source.id,paragraph.id);
    const inNode=node=>[...node.querySelectorAll('[data-entity],a[data-person-link]')].map(n=>n.dataset.personLink||n.dataset.entity).filter(id=>people.has(id));
    const activePeople=inNode(paragraph);
    const familyIds=familyHierarchy(source.subject,catalog.relations,[...people.keys()]).members.map(m=>m.id);
    const ids=[...new Set([source.subject,...familyIds,...inNode($('reader')),...catalog.events.filter(e=>e.witness===source.id).flatMap(e=>e.people)])].filter(id=>people.has(id));
    const year=Number($('year').value),key=JSON.stringify([source.id,paragraph.id,year,ids,activePeople]);
    if(current?.key===key)return;
    const sourceChanged=current?.source.id!==source.id;
    current={source,passage:paragraph.id,context,activePeople,people:ids,year,key};
    if(sourceChanged){selectedPerson=source.subject;}
    if(!selectedPerson||!ids.includes(selectedPerson))selectedPerson=source.subject;
    $('trajectory-person').innerHTML=ids.map(id=>`<option value="${h(id)}">${h(shortName(people.get(id)))}</option>`).join('');$('trajectory-person').value=selectedPerson;
    if(lastPassage!==paragraph.id){const c=geo.placeContexts.find(c=>context.entityIds.includes(c.place));chosenJurisdiction=c?.jurisdiction||null;lastPassage=paragraph.id;report('');}
    updateTimeline();updateHierarchy();paintMap();
    if(pendingJump&&pendingJump.witness===source.id&&$(pendingJump.passage)){const p=pendingJump;pendingJump=null;focusPassage(p.witness,p.passage);}
  }
  const schedule=()=>{if(!frame)frame=requestAnimationFrame(refresh);};
  new MutationObserver(schedule).observe($('reader'),{subtree:true,childList:true,attributes:true,attributeFilter:['class']});
  new MutationObserver(schedule).observe($('year-label'),{childList:true,subtree:true,characterData:true});
  $('year').addEventListener('input',schedule);$('source-select').addEventListener('change',schedule);
  if(typeof ResizeObserver!=='undefined')new ResizeObserver(()=>paintMap(false)).observe(map);
  window.addEventListener('renwen:languagechange',()=>{updateTimeline();updateHierarchy();paintMap();});
  document.body.classList.add('context-enhanced');schedule();
}
install().catch(error=>{console.error(error);const status=$('status');if(status)status.textContent=`${error.message} The original reader remains available.`;});
