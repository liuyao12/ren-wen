/** Shared navigation for people, texts and works; no title-based identity guessing. */
import {safeURL} from './core.js';

export function workURL(id) {
  return typeof id === 'string' && /^work-[a-z0-9-]+$/.test(id) ? `works.html#${id}` : null;
}
export function readerURL(witness, passage = '') {
  if (typeof witness !== 'string' || !/^[a-z0-9-]+$/.test(witness)) return null;
  if (passage && (typeof passage !== 'string' || !/^[a-z0-9-]+$/.test(passage))) return null;
  return `./${passage ? '?passage=' + encodeURIComponent(passage) : ''}#${encodeURIComponent(witness)}`;
}
function isECCP(url) {
  try { const u=new URL(url); return u.hostname==='en.wikisource.org' && decodeURIComponent(u.pathname).replaceAll('_',' ').startsWith("/wiki/Eminent Chinese of the Ch'ing Period/"); }
  catch { return false; }
}
export function eccpDestination(profile, catalog) {
  const local=catalog.sources.find(s=>s.work==='work-eccp' && s.subject===profile.id);
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
export async function loadWorks(fetcher=fetch) {
  const r=await fetcher('data/works/index.json');
  if(!r.ok)throw Error(`Work index unavailable (${r.status}).`);
  const index=await r.json();
  if(index.schemaVersion!==1 || !Array.isArray(index.works))throw Error('Unsupported work index.');
  const seen=new Set();
  for(const file of index.works) {
    if(typeof file!=='string' || !/^work-[a-z0-9-]+\.json$/.test(file) || seen.has(file))throw Error('Invalid or duplicate work filename.');
    seen.add(file);
  }
  const result=[];
  for(let start=0;start<index.works.length;start+=8) result.push(...await Promise.all(index.works.slice(start,start+8).map(async file=>{
    const r=await fetcher(`data/works/${file}`);if(!r.ok)throw Error(`Cannot load ${file}.`);
    const p=await r.json();
    if(p.schemaVersion!==1 || p.type!=='work' || `${p.id}.json`!==file || typeof p.title!=='string')throw Error('Invalid work record.');
    return p;
  })));
  return result;
}
