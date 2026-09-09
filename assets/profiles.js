import {fetchData} from './data-cache.js';
/** Person records are independent of text witnesses and external services. */
export function canonicalName(profile) {
  const n = profile.name;
  const qualifier = Object.hasOwn(n, 'bracket') ? n.bracket?.label : n.jiguan?.label;
  const place = qualifier ? `[${qualifier}] ` : '';
  const alias = n.parenthetical ? `（${n.parenthetical.value}）` : '';
  return `${place}${n.surname || ''}${n.given || ''}${alias}`;
}

/** Parameters must already be resolved Chinese civil-year labels, never Gregorian dates. */
export function suiAge(birthChineseYear, eventChineseYear) {
  if (!Number.isSafeInteger(birthChineseYear) || !Number.isSafeInteger(eventChineseYear)
      || birthChineseYear < 1 || eventChineseYear < birthChineseYear) return null;
  return eventChineseYear - birthChineseYear + 1;
}

export function ageAtDeath(profile) {
  return suiAge(profile.life?.birth?.chineseYear, profile.life?.death?.chineseYear);
}

export function yearText(record) {
  if (!record || !Number.isSafeInteger(record.chineseYear)) return 'Unresolved';
  const era = record.era && record.eraYear ? ` · ${record.era}${record.eraYear}年` : '';
  return `${record.chineseYear}${era}`;
}

async function readProfiles(fetcher) {
  const response = await fetcher('data/people/index.json');
  if (!response.ok) throw new Error(`Profile index unavailable (${response.status}).`);
  const index = await response.json();
  if (index.schemaVersion !== 1 || !Array.isArray(index.profiles)) throw new Error('Unsupported profile index.');
  const result = [];
  const ids = new Set();
  // Bound concurrent reads so a larger profile library remains responsive.
  for (const file of index.profiles) {
    if (typeof file !== 'string' || !/^person-[a-z0-9-]+\.json$/.test(file)) throw new Error('Invalid profile filename.');
  }
  let records;
  if(index.bundle) {
    if(index.bundle!=='bundle.json')throw Error('Invalid profile bundle path.');
    const r=await fetcher('data/people/bundle.json');
    if(!r.ok)throw Error('Profile bundle unavailable.');
    const bundle=await r.json();
    if(bundle.schemaVersion!==1 || bundle.derived!==true || !Array.isArray(bundle.records) || bundle.records.length!==index.profiles.length)throw Error('Invalid profile bundle.');
    records=bundle.records;
  } else {
    records=[];
    for(let start=0;start<index.profiles.length;start+=8)records.push(...await Promise.all(index.profiles.slice(start,start+8).map(async file=>{
      const r=await fetcher(`data/people/${file}`);if(!r.ok)throw Error(`Cannot load ${file}.`);return r.json();
    })));
  }
  for(const [i,p] of records.entries()) {
    if(p.schemaVersion!==1 || `${p.id}.json`!==index.profiles[i] || ids.has(p.id))throw Error('Invalid or duplicate profile identity.');
    for(const provider of ['cbdb','geni']) {
      const x=p.externalIds?.[provider];
      if(!x || (x.id!==null && (typeof x.id!=='string' || !/^[1-9][0-9]*$/.test(x.id))))throw Error(`${provider} IDs must be decimal strings or null.`);
    }
    ids.add(p.id);result.push(p);
  }
  return result;
}

let defaultProfiles;
export function loadProfiles(fetcher=fetch) {
  if(fetcher!==fetch)return readProfiles(fetcher);
  return defaultProfiles ||= readProfiles(fetchData).catch(error=>{defaultProfiles=null;throw error;});
}
