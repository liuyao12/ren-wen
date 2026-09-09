/** Unit identity is distinct from each occurrence and that occurrence's wording. */
export const unitURL=id=>/^text-[a-z0-9-]+$/.test(id)?`texts.html#${encodeURIComponent(id)}`:null;
export function occurrencesOf(data,id){return data.occurrences.filter(o=>o.unit===id);}
export function readingText(occurrence){return occurrence.selectors.map(a=>a.exact).join('\n\n');}
export function unitContainers(data,occurrence){
  const result=[],seen=new Set();let id=occurrence.container;
  while(id){if(seen.has(id))throw Error('Cyclic occurrence hierarchy');seen.add(id);const o=data.occurrences.find(o=>o.id===id);if(!o)throw Error('Missing containing reading');result.unshift(o);id=o.container;}
  return result;
}
export async function loadTextUnits(){const r=await fetch('data/text-units.json');if(!r.ok)throw Error(`Text units unavailable (${r.status})`);const d=await r.json();if(d.schemaVersion!==1||!Array.isArray(d.units)||!Array.isArray(d.occurrences))throw Error('Unsupported text-unit data');return d;}
