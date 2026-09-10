import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {ganzhi, chineseNumber, chineseYearText, westernYearText, personHeading, profileURL, profilesWithStubs} from '../assets/person-display.js';
import {linkPersonMentions} from '../assets/person-links.js';
const sample = JSON.parse(readFileSync(new URL('../data/people/person-zeng-jize.json', import.meta.url)));

test('ganzhi is computed from Chinese civil-year labels', () => {
  assert.equal(ganzhi(1839), '己亥'); assert.equal(ganzhi(1890), '庚寅');
  assert.equal(ganzhi(1984), '甲子'); assert.equal(ganzhi(2044), '甲子');
  assert.equal(ganzhi(1899), '己亥'); assert.equal(ganzhi(1900), '庚子');
  assert.equal(ganzhi(1807), '丁卯');
});
test('invalid Chinese years never acquire a ganzhi', () => {
  for (const y of [null, undefined, true, '1839', 0, -1, 10000, 1839.5]) assert.equal(ganzhi(y), null);
});
test('regnal years use Chinese numerals', () => {
  assert.equal(chineseNumber(19), '十九'); assert.equal(chineseNumber(23), '二十三');
  assert.equal(chineseYearText(sample.life.birth), '道光十九年己亥');
  assert.equal(chineseYearText(sample.life.death), '光緒十六年庚寅');
  assert.equal(chineseYearText({chineseYear:1875,era:'光緒',eraYear:1}), '光緒元年乙亥');
});
test('header contains canonical name, AD dates and Chinese dates', () => {
  const html = personHeading(sample);
  assert.match(html, /\[湘鄉\] 曾紀澤/);
  assert.match(html, /1839–1890/); assert.match(html, /道光十九年己亥/);
  assert.match(html, /光緒十六年庚寅/); assert.match(html, /52 歲/);
});
test('January Western year remains separate from Chinese year', () => {
  const p = structuredClone(sample);
  p.life.death.chineseYear = 1899; p.life.death.eraYear = 25;
  p.life.westernDates = [{event:'death',calendar:'gregorian',value:'1900-01-01',source:'eccp'}];
  assert.equal(westernYearText(p, 'death'), '1900');
  assert.equal(chineseYearText(p.life.death), '光緒二十五年己亥');
});
test('neither calendar is silently copied into the other', () => {
  const p = structuredClone(sample); p.life.westernDates=[]; p.life.westernYears=[];
  assert.equal(westernYearText(p, 'birth'), '?');
  p.life.birth = null;
  assert.equal(chineseYearText(p.life.birth), '中曆年未定');
});
test('year-only claims need no invented month or day', () => {
  const p = structuredClone(sample); p.life.westernDates=[];
  p.life.westernYears=[{event:'birth',calendar:'gregorian',value:1826,source:'eccp'}];
  assert.equal(westernYearText(p, 'birth'), '1826');
});
test('conflicting AD years are displayed as alternatives, not an interval', () => {
  const p = structuredClone(sample);
  p.life.westernDates.push({event:'death',calendar:'gregorian',value:'1891-03-12',source:'eccp'});
  assert.equal(westernYearText(p, 'death'), '1890 / 1891');
});
test('person URLs are local and reject malformed IDs', () => {
  assert.equal(profileURL(sample.id), 'profiles.html#person-zeng-jize');
  for (const id of ['../../x', 'person-x"', '', null]) assert.equal(profileURL(id), null);
  assert.equal(typeof linkPersonMentions, 'function');
});
test('header escapes imported names', () => {
  const p = structuredClone(sample); p.name.given='<img src=x onerror=alert(1)>';
  assert.ok(!personHeading(p).includes('<img'));
});
test('missing detailed profiles keep their own identity', () => {
  const ps=profilesWithStubs({entities:[{id:'person-other',type:'person',label:'甲',life:null}],sources:[]}, [sample]);
  assert.equal(ps.length, 2); assert.equal(ps[1].id, 'person-other');
  assert.match(personHeading(ps[1]), /中曆年未定/);
  assert.ok(!personHeading(ps[1]).includes('曾紀澤'));
});
test('the Macartney account remains a mention, not identity with Kuo', () => {
  const p=JSON.parse(readFileSync(new URL('../data/people/person-macartney.json', import.meta.url)));
  assert.equal(p.accounts[0].relation, 'mentioned-in-biography');
  assert.equal(p.name.given, '馬格理'); assert.equal(p.life.birth, null);
  assert.equal(westernYearText(p,'birth'), '1833');
});
