/** Display projections. Stored source wording and calendar assertions are never rewritten. */
import {canonicalName, ageAtDeath} from './profiles.js';
import {escapeHTML as h} from './core.js';

const STEMS = [...'甲乙丙丁戊己庚辛壬癸'];
const BRANCHES = [...'子丑寅卯辰巳午未申酉戌亥'];
const validYear = year => Number.isSafeInteger(year) && year >= 1 && year <= 9999;

/** Input is an explicitly resolved Chinese civil-year label, NOT a Gregorian event year. */
export function ganzhi(chineseYear) {
  if (!validYear(chineseYear)) return null;
  const mod = (a, n) => ((a % n) + n) % n;
  return STEMS[mod(chineseYear - 4, 10)] + BRANCHES[mod(chineseYear - 4, 12)];
}

export function chineseNumber(number) {
  if (!Number.isSafeInteger(number) || number < 1) return '';
  if (number > 99) return String(number);
  const digits = [...'零一二三四五六七八九'];
  if (number < 10) return digits[number];
  const tens = Math.floor(number / 10), ones = number % 10;
  return (tens === 1 ? '' : digits[tens]) + '十' + (ones ? digits[ones] : '');
}

export function chineseYearText(record) {
  if (!validYear(record?.chineseYear)) return '中曆年未定';
  const reign = record.era && Number.isSafeInteger(record.eraYear) && record.eraYear > 0
    ? `${record.era}${record.eraYear === 1 ? '元' : chineseNumber(record.eraYear)}年`
    : `中曆 ${record.chineseYear} 年`;
  return `${reign}${ganzhi(record.chineseYear)}`;
}

/** Independent Western-year claims; no fallback to Chinese-year labels. Conflicts stay visible. */
export function westernYearText(profile, endpoint) {
  const life = profile.life || {};
  const dates = (life.westernDates || []).filter(d => d.event === endpoint && d.calendar === 'gregorian'
    && typeof d.value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(d.value));
  const years = (life.westernYears || []).filter(d => d.event === endpoint && d.calendar === 'gregorian'
    && validYear(d.value) && d.source && profile.sources?.[d.source]);
  const values = [...new Set([...dates.map(d => Number(d.value.slice(0, 4))), ...years.map(d => d.value)])]
    .filter(validYear).sort((a, b) => a - b);
  return values.length ? values.join(' / ') : '?';
}

export function profileURL(id) {
  return typeof id === 'string' && /^person-[a-z0-9-]+$/.test(id)
    ? `profiles.html#${encodeURIComponent(id)}` : null;
}

/** A shared compact header for both the reader and the person's own page. */
export function personHeading(profile, {linked = false} = {}) {
  const name = h(canonicalName(profile));
  const url = profileURL(profile.id);
  const age = ageAtDeath(profile);
  return `<div class="person-heading" data-profile-heading="${h(profile.id)}">
    <h1 lang="zh-Hant">${linked && url ? `<a href="${h(url)}">${name}</a>` : name}</h1>
    <p class="person-ad">${h(westernYearText(profile, 'birth'))}–${h(westernYearText(profile, 'death'))} <span>AD</span></p>
    <p class="person-chinese" lang="zh-Hant"><span>生：${h(chineseYearText(profile.life?.birth))}</span><span>卒：${h(chineseYearText(profile.life?.death))}</span>${age === null ? '' : `<span class="person-sui">享年 ${age} 歲</span>`}</p>
  </div>`;
}

/** An unfinished entity gets its own landing page, never someone else's default profile. */
export function profilesWithStubs(catalog, profiles) {
  const records = new Map(profiles.map(p => [p.id, p]));
  for (const e of catalog.entities || []) {
    if (e.type !== 'person' || records.has(e.id)) continue;
    const source = e.life?.source || e.externalSources?.[0]?.url || catalog.sources?.find(s => (e.sources || []).includes(s.id))?.url;
    const westernYears = ['birth', 'death'].filter(key => source && validYear(e.life?.[key]))
      .map(key => ({event:key, calendar:'gregorian', value:e.life[key], source:'catalog'}));
    records.set(e.id, {
      id:e.id, stub:true, collection:'Ren-Wen', reviewStatus:'unfinished',
      coverage:'Reference profile: only information already in the catalogue is shown; a full biographical record has not been prepared.',
      name:{surname:null, given:e.label || e.display, jiguan:null, zi:[], hao:[], parenthetical:null,
        romanizations:e.display ? [{value:e.display}] : [], note:'Name components and native place await source review.'},
      life:{birth:null, death:null, westernDates:[], westernYears, reportedAges:[]},
      sources:source ? {catalog:{title:'Catalogue evidence', url:source, locator:'Existing entity record', access:'imported', attribution:'See original source'}} : {},
      externalIds:{cbdb:{id:null,status:'not-searched'},geni:{id:null,status:'not-searched'}},
      accounts:[], notes:[e.note || 'Unresolved fields have not been inferred.']
    });
  }
  return [...records.values()];
}
