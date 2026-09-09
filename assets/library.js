import {fetchData} from './data-cache.js';
/** Shared navigation for people, texts and works; no title-based identity guessing. */
import {safeURL} from './core.js';

export function workURL(id) {
  return typeof id === 'string' && /^work-[a-z0-9-]+$/.test(id) ? `works.html#${id}` : null;
}
export function readerURL(witness, passage = '', person = '') {
  if (typeof witness !== 'string' || !/^[a-z0-9-]+$/.test(witness)) return null;
  if (passage && (typeof passage !== 'string' || !/^[a-z0-9-]+$/.test(passage))) return null;
  if(person && (typeof person!=='string' || !/^person-[a-z0-9-]+$/.test(person)))return null;
  const params=new URLSearchParams();if(passage)params.set('passage',passage);if(person)params.set('person',person);
  return `./${params.size?'?'+params:''}#${encodeURIComponent(witness)}`;
}
function isECCP(url) {
  try { const u=new URL(url); return u.hostname==='en.wikisource.org' && decodeURIComponent(u.pathname).replaceAll('_',' ').startsWith("/wiki/Eminent Chinese of the Ch'ing Period/"); }
  catch { return false; }
}
export function eccpDestination(profile, catalog) {
  const local=catalog.sources.find(s=>s.work==='work-eccp' && s.subject===profile.id && s.kind!=='cross-reference');
  if(local) return {url:readerURL(local.id),label:'Read ECCP entry',external:false,relation:'principal-biography'};
  for(const a of profile.accounts || []) {
    const url=safeURL(a.url || profile.sources?.[a.source]?.url);
    if(a.relation==='principal-biography' && isECCP(url))
      return {url,label:'ECCP entry on Wikisource',external:true,relation:a.relation};
  }
  for(const a of profile.accounts || []) {
    const url=safeURL(a.url || profile.sources?.[a.source]?.url);
    if(['mentioned-in','mentioned-in-biography'].includes(a.relation) && isECCP(url)) {
      const entry=catalog.sources.find(s=>s.url===url);
      return {url:entry ? readerURL(entry.id) : url,label:'Discussed in ECCP',external:!entry,relation:'mentioned-in'};
    }
  }
  return null;
}
export function occurrences(catalog, id) {
  return (catalog.mentions || []).filter(m=>m.entity===id);
}
async function readWorks(fetcher) {
  const r=await fetcher('data/works/index.json');
  if(!r.ok)throw Error(`Work index unavailable (${r.status}).`);
  const index=await r.json();
  if(index.schemaVersion!==1 || !Array.isArray(index.works))throw Error('Unsupported work index.');
  const seen=new Set();
  for(const file of index.works) {
    if(typeof file!=='string' || !/^work-[a-z0-9-]+\.json$/.test(file) || seen.has(file))throw Error('Invalid or duplicate work filename.');
    seen.add(file);
  }
  let result=[];
  if(index.bundle) {
    if(index.bundle!=='bundle.json')throw Error('Invalid work bundle path.');
    const r=await fetcher('data/works/bundle.json');if(!r.ok)throw Error('Work bundle unavailable.');
    const bundle=await r.json();
    if(bundle.schemaVersion!==1 || bundle.derived!==true || !Array.isArray(bundle.records) || bundle.records.length!==index.works.length)throw Error('Invalid work bundle.');
    result=bundle.records;
  } else {
    for(let start=0;start<index.works.length;start+=8)result.push(...await Promise.all(index.works.slice(start,start+8).map(async file=>{
      const r=await fetcher(`data/works/${file}`);if(!r.ok)throw Error(`Cannot load ${file}.`);return r.json();
    })));
  }
  for(const [i,p] of result.entries()) {
    if(p.schemaVersion!==1 || p.type!=='work' || `${p.id}.json`!==index.works[i] || typeof p.title!=='string')throw Error('Invalid work record.');
  }
  return result;
}
let defaultWorks;
export function loadWorks(fetcher=fetch) {
  if(fetcher!==fetch)return readWorks(fetcher);
  return defaultWorks ||= readWorks(fetchData).catch(error=>{defaultWorks=null;throw error;});
}
