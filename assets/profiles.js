/** Person records are independent of text witnesses and external services. */
export function canonicalName(profile) {
  const n = profile.name;
  const place = n.jiguan?.label ? `[${n.jiguan.label}] ` : '';
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

export async function loadProfiles(fetcher = fetch) {
  const response = await fetcher('data/people/index.json');
  if (!response.ok) throw new Error(`Profile index unavailable (${response.status}).`);
  const index = await response.json();
  if (index.schemaVersion !== 1 || !Array.isArray(index.profiles)) throw new Error('Unsupported profile index.');
  const result = [];
  const ids = new Set();
  for (const file of index.profiles) {
    if (typeof file !== 'string' || !/^person-[a-z0-9-]+\.json$/.test(file)) throw new Error('Invalid profile filename.');
    const r = await fetcher(`data/people/${file}`);
    if (!r.ok) throw new Error(`Cannot load ${file} (${r.status}).`);
    const p = await r.json();
    if (p.schemaVersion !== 1 || `${p.id}.json` !== file || ids.has(p.id)) throw new Error('Invalid or duplicate profile identity.');
    for (const provider of ['cbdb', 'geni']) {
      const x = p.externalIds?.[provider];
      if (!x || (x.id !== null && (typeof x.id !== 'string' || !/^[1-9][0-9]*$/.test(x.id)))) throw new Error(`${provider} IDs must be decimal strings or null.`);
    }
    ids.add(p.id); result.push(p);
  }
  return result;
}
