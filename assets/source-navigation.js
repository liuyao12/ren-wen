/** Source → subdivision → entry. Printed cross-reference slips are lookup aliases. */
import {getLocale} from './i18n.js';
export function sourceFamily(source) {
  return source.work === 'work-eccp' ? 'eccp' : ['work-qingshigao','work-qsg'].includes(source.work) ? 'qsg' : 'other';
}
export function sourceGroup(source) {
  if (source.kind === 'reference-material') return 'reference';
  if (sourceFamily(source) === 'eccp') {
    return source.title.normalize('NFD').replace(/\p{M}/gu,'').match(/[A-Za-z]/)?.[0].toUpperCase() || 'other';
  }
  const volume=source.id.match(/^qsg-volume-(\d+)$/);
  return volume ? String(Math.floor((Number(volume[1])-1)/25)*25+1).padStart(3,'0') : 'accounts';
}
export function readingSources(catalog) { return catalog.sources.filter(s=>s.kind !== 'cross-reference'); }
export function resolveSource(catalog,id) {
  const seen=new Set();let target=id;
  while(catalog.navigation?.redirects?.[target]) {
    if(seen.has(target))throw Error('Circular source redirect.');seen.add(target);
    target=catalog.navigation.redirects[target].target;
  }
  return catalog.sources.find(s=>s.id===target);
}
export function installSourceNavigation(catalog,select,navigate) {
  const sources=readingSources(catalog),family=document.createElement('select'),group=document.createElement('select');
  const host=document.createElement('div');host.className='source-navigation';
  family.id='source-family';group.id='source-group';select.before(host);host.append(family,group,select);
  const words=()=>getLocale()==='en'?['Source','Subdivision','Entry']:['來源','分組','篇目'];
  function options(node,rows,value) {node.replaceChildren(...rows.map(([id,label])=>new Option(label,id)));if(rows.some(r=>r[0]===value))node.value=value;}
  function groupLabel(key) {
    const en=getLocale()==='en';
    if(key==='reference')return en?'Editorial / reference':'編輯／參考資料';
    if(key==='accounts')return en?'Selected accounts':'人物選段';
    if(/^\d+$/.test(key))return `${en?'Volumes':'卷'} ${Number(key)}–${Number(key)+24}`;
    return key;
  }
  function rebuild(id,keepGroup=false) {
    const chosen=sources.find(s=>s.id===id),labels=words();
    [family,group,select].forEach((n,i)=>n.setAttribute('aria-label',labels[i]));
    const families=[...new Set(sources.map(sourceFamily))];
    options(family,families.map(f=>[f,{eccp:'ECCP',qsg:'清史稿',other:getLocale()==='en'?'Other sources':'其他文獻'}[f]]),chosen?sourceFamily(chosen):family.value);
    const pool=sources.filter(s=>sourceFamily(s)===family.value),keys=[...new Set(pool.map(sourceGroup))].sort();
    options(group,keys.map(k=>[k,groupLabel(k)]),chosen&&!keepGroup?sourceGroup(chosen):group.value);
    const entries=pool.filter(s=>sourceGroup(s)===group.value);
    options(select,entries.map(s=>[s.id,s.shortTitle]),id);
  }
  family.onchange=()=>{rebuild(null);if(select.value)navigate(select.value);};
  group.onchange=()=>{rebuild(null,true);if(select.value)navigate(select.value);};
  window.addEventListener('renwen:languagechange',()=>rebuild(select.value));
  rebuild(catalog.defaultWitness);
  return {select(id){rebuild(id);}};
}
