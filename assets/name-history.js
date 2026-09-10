/** Dated identities and source attestations. No source prose is rewritten. */
import {escapeHTML as h} from './core.js';
import {ui} from './i18n.js';
import {fetchData} from './data-cache.js';
let loadedHistory={};
let loading;
export function loadNameHistory(){return loading ||= fetchData('data/name-history.json').then(async r=>{if(!r.ok)throw Error('Name history unavailable.');const d=await r.json();if(d.schemaVersion!==1)throw Error('Unsupported name history.');return loadedHistory=d;}).catch(e=>{loading=null;throw e;});}

export const usable = record => record && !['rejected','superseded'].includes(record.status);
export function identityName(profile) {
  const n=profile?.name || {};
  const qualifier=Object.hasOwn(n,'bracket') ? n.bracket?.label : n.jiguan?.label;
  return `${qualifier ? '['+qualifier+'] ' : ''}${n.surname || ''}${n.given || ''}`;
}
export function nameDetails(profile, history=loadedHistory) {
  const n=profile?.name || {}, extra=history.people?.[profile?.id]?.aliases || {};
  return [['zi','字'],['hao','號'],['posthumous','諡']].flatMap(([kind,prefix])=>{
    const values=[...(n[kind]||[]),...(extra[kind]||[])].filter(usable);
    return [...new Set(values.map(x=>x.value).filter(Boolean))].map(value=>({kind,prefix,value}));
  });
}
export function nameDetailsHTML(profile, history=loadedHistory) {
  return nameDetails(profile,history).map(x=>`<span class="name-detail" lang="zh-Hant"><span class="name-kind">${x.prefix}</span>${h(x.value)}</span>`).join('');
}
const validYear = n=>Number.isSafeInteger(n) && n>=1 && n<=9999;
/** Bounds are inclusive start, exclusive end. Unknown onset is NOT an open start. */
export function periodContains(period,year) {
  return usable(period) && validYear(year) && validYear(period.from)
    && year>=period.from && (period.to===null || (validYear(period.to)&&year<period.to));
}
function choose(periods,year) {
  const candidates=periods.filter(p=>periodContains(p,year)).sort((a,b)=>(b.priority||0)-(a.priority||0));
  if(!candidates.length)return null;
  const top=candidates.filter(p=>(p.priority||0)===(candidates[0].priority||0));
  // Conflicting equally preferred readings are not silently resolved by array order.
  if(new Set(top.map(p=>p.shortLabel||p.label||`${p.surname||''}${p.given||''}`)).size>1)return null;
  return top[0];
}
export function nameAtYear(profile, year, history=loadedHistory) {
  const record=history.people?.[profile.id] || {}, bare=(profile.name?.surname||'')+(profile.name?.given||'');
  const names=[...(profile.namePeriods||[]),...(record.names||[])].filter(usable);
  const titles=[...(profile.titlePeriods||[]),...(record.titles||[])].filter(usable);
  const personal=choose(names,year);
  const personName=personal ? (personal.label||`${personal.surname||''}${personal.given||''}`) : bare;
  let title=validYear(year) ? choose(titles,year) : titles.find(p=>p.defaultDisplay);
  // Posthumous designations enter ordinary bar labels only by explicit editorial choice.
  if(title && ['posthumous','temple'].includes(title.kind) && !title.primaryPosthumous)title=null;
  const titleText=title?.shortLabel||title?.label||'';
  return {name:personName,title:titleText,label:`${titleText}${titleText&&personName?' ':''}${personName}`,
    namePeriod:personal?.id||null,titlePeriod:title?.id||null,year:validYear(year)?year:null};
}
/** Publication date, not narrative date, access date, or the acquisition date of an alias. */
export function sourceDate(source,history=loadedHistory) {
  const date=source?.sourceDate || history.sourceDates?.[source?.id] || history.workDates?.[source?.work];
  if(date)return date;
  return {label:null,kind:'unresolved'};
}
export function sourceNameGroups(catalog,personId,history=loadedHistory) {
  const sources=new Map(catalog.sources.map(s=>[s.id,s])),groups=new Map();
  for(const m of catalog.mentions) {
    if(m.entity!==personId)continue;
    if(!groups.has(m.witness))groups.set(m.witness,{source:sources.get(m.witness),date:sourceDate(sources.get(m.witness),history),forms:new Map()});
    const forms=groups.get(m.witness).forms;
    if(!forms.has(m.quote))forms.set(m.quote,[]);
    forms.get(m.quote).push({id:m.id,passage:m.passage,status:m.status||'proposed'});
  }
  return [...groups.values()];
}
/** Only an explicit editorial anchor or a unique dated event is followed automatically. */
export function paragraphAnchor(context,witness,passage,history=loadedHistory) {
  const stored=(history.paragraphAnchors||[]).find(a=>a.witness===witness&&a.passage===passage&&usable(a));
  if(stored && validYear(stored.year))return {...stored,kind:'recorded'};
  const years=[...new Set((context?.events||[]).filter(e=>e.time?.start===e.time?.end&&validYear(e.time.start)).map(e=>e.time.start))];
  if(years.length===1)return {year:years[0],kind:'event',witness,passage};
  return null;
}
export function nameHistoryHTML(profile, history=loadedHistory) {
  const record=history.people?.[profile.id] || {};
  const periods=[...(profile.namePeriods||[]),...(record.names||[]),...(profile.titlePeriods||[]),...(record.titles||[])].filter(usable);
  if(!periods.length)return `<p class="note">${ui('No dated name or title periods entered yet.')}</p>`;
  return `<ul class="dated-names">${periods.map(p=>`<li><strong>${h(p.shortLabel||p.label||`${p.surname||''}${p.given||''}`)}</strong> <span>${p.from===null?'?':h(p.from)}–${p.to===null?'':h(p.to-1)}</span><small>${h(p.kind)} · ${ui(p.status||'proposed')}</small>${p.note?`<p>${h(p.note)}</p>`:''}${(p.evidence||[]).map(e=>`<a href="./?passage=${encodeURIComponent(e.passage)}#${encodeURIComponent(e.witness)}">${h(e.passage)} →</a>`).join(' ')}</li>`).join('')}</ul>`;
}

/** Source-local name classification, kept separate from a preferred display. */
export function typedAttestationsHTML(profile,catalog,history=loadedHistory){
  const records=(history.people?.[profile.id]?.attestations||[]).filter(usable);
  if(!records.length)return '';
  return `<h3>${ui('Typed name attestations')}</h3><p class="note">${ui('A source classification is preserved even when another source disagrees.')}</p><ul>${records.map(a=>{
    const e=a.evidence?.[0]||a,s=catalog.sources.find(s=>s.id===e?.witness),d=sourceDate(s,history);
    return `<li><strong>${h(({zi:'字',hao:'號',posthumous:'諡'})[a.kind]||a.kind)}${h(a.value)}</strong> · ${h(s?.shortTitle||'')} · ${d.label?h(d.label):ui('Source date unresolved')}${e?` <a href="./?passage=${encodeURIComponent(e.passage)}#${encodeURIComponent(e.witness)}">${h(e.passage)} →</a>`:''}</li>`;
  }).join('')}</ul>`;
}
