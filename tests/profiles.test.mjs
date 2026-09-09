import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {canonicalName, suiAge, ageAtDeath, yearText, loadProfiles} from '../assets/profiles.js';
const profile = JSON.parse(readFileSync(new URL('../data/people/person-zeng-jize.json', import.meta.url), 'utf8'));

test('canonical name follows native-place, xing+ming and typed alias', () => {
  assert.equal(canonicalName(profile), '[湘鄉] 曾紀澤（劼剛）');
  const p = structuredClone(profile);p.name.jiguan=null;p.name.bracket=null;p.name.parenthetical=null;
  assert.equal(canonicalName(p), '曾紀澤');
});
test('Chinese-year sui computation and missing endpoints', () => {
  assert.equal(ageAtDeath(profile),52);assert.equal(suiAge(1839,1839),1);
  for(const values of [[null,1890],[1839,null],['1839',1890],[true,2],[1840,1839],[0,1]])assert.equal(suiAge(...values),null);
});
test('Western January date never supplies the Chinese death year', () => {
  const p=structuredClone(profile);p.life.birth.chineseYear=1890;p.life.death.chineseYear=1899;
  p.life.westernDates=[{event:'death',calendar:'gregorian',value:'1900-01-01'}];
  assert.equal(ageAtDeath(p),10);p.life.death=null;assert.equal(ageAtDeath(p),null);
});
test('Geni ID is preserved exactly', () => {assert.equal(profile.externalIds.geni.id,'6000000012827521360');assert.equal(typeof profile.externalIds.geni.id,'string');});
test('year labels keep the era and unresolved state', () => {assert.equal(yearText(profile.life.birth),'1839 · 道光19年');assert.equal(yearText(null),'Unresolved');});
test('fetch profile index and keep matching identity', async () => {
  const fake=async path=>({ok:true,json:async()=>path.endsWith('index.json')?{schemaVersion:1,profiles:['person-zeng-jize.json']}:structuredClone(profile)});
  assert.equal((await loadProfiles(fake))[0].id,profile.id);
});
test('reject unsafe paths and numeric IDs', async () => {
  const unsafe=async()=>({ok:true,json:async()=>({schemaVersion:1,profiles:['../escape.json']})});
  await assert.rejects(loadProfiles(unsafe),/filename/);
  const p=structuredClone(profile);p.externalIds.geni.id=6000000012827521360;
  const fake=async path=>({ok:true,json:async()=>path.endsWith('index.json')?{schemaVersion:1,profiles:['person-zeng-jize.json']}:p});
  await assert.rejects(loadProfiles(fake),/decimal strings/);
});
