import test, {afterEach} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {chineseYearLabel, lifeYearsText, lifeYearCoordinate, westernYearFallbackHTML, personHeading} from '../assets/person-display.js';
import {ageAtDeath} from '../assets/profiles.js';
import {setLocale, DEFAULT_LOCALE} from '../assets/i18n.js';
const sample=JSON.parse(readFileSync(new URL('../data/people/person-zeng-jize.json',import.meta.url)));
afterEach(()=>setLocale(DEFAULT_LOCALE));
test('brackets delimit individual Chinese-year labels, not a Gregorian lifespan',()=>{
  assert.equal(chineseYearLabel(sample.life.birth),'[1839]');
  assert.equal(lifeYearsText(sample),'[1839]–[1890]');
  assert.equal(ageAtDeath(sample),52);
});
test('January in the next Gregorian year does not increase the bracketed year or age',()=>{
  const p=structuredClone(sample);p.life.birth.chineseYear=1890;p.life.death.chineseYear=1899;
  p.life.westernDates=[{event:'birth',calendar:'gregorian',value:'1890-06-01',source:'eccp'},{event:'death',calendar:'gregorian',value:'1900-01-01',source:'eccp'}];
  assert.equal(lifeYearsText(p),'[1890]–[1899]');assert.equal(lifeYearCoordinate(p,'death'),1899);
  assert.equal(ageAtDeath(p),10);assert.doesNotMatch(personHeading(p),/\[1900\]/);
});
test('a resolved death in the next Chinese year increases age by exactly one',()=>{
  const p=structuredClone(sample);p.life.birth.chineseYear=1899;p.life.death.chineseYear=1899;
  assert.equal(ageAtDeath(p),1);p.life.death.chineseYear=1900;assert.equal(ageAtDeath(p),2);
});
test('Gregorian-only evidence is never bracketed or used to calculate an exact age',()=>{
  const p=structuredClone(sample);p.life.birth=null;p.life.death=null;
  assert.equal(lifeYearsText(p),'[?]–[?]');assert.equal(ageAtDeath(p),null);
  assert.match(westernYearFallbackHTML(p),/1839–1890/);
  assert.doesNotMatch(westernYearFallbackHTML(p),/\[1839\]|\[1890\]/);
  assert.equal(lifeYearsText(p,{gregorianFallback:true}),'公曆 1839–1890');
  assert.doesNotMatch(personHeading(p),/person-sui/);
});
test('mixed calendar coverage retains an unknown Chinese endpoint and explicit Western fallback',()=>{
  const p=structuredClone(sample);p.life.death=null;
  assert.equal(lifeYearsText(p),'[1839]–[?]');assert.equal(ageAtDeath(p),null);
  assert.equal(lifeYearsText(p,{gregorianFallback:true}),'[1839]–公曆 1890');
});
test('invalid or unresolved Chinese years cannot become bracketed numbers',()=>{
  for(const chineseYear of [null,undefined,true,'1839',0,-1,10000,1839.5])assert.equal(chineseYearLabel({chineseYear}),'[?]');
});
test('Chinese and English headers preserve brackets with no age-reckoning commentary',()=>{
  for(const locale of ['zh-Hant','en']){
    setLocale(locale);const html=personHeading(sample);
    assert.match(html,/\[1839\]–\[1890\]/);assert.doesNotMatch(html.replace(/<[^>]*>/g,''),/虛歲|虚岁|sui|Not Western birthday age/i);
  }
});
test('displaying bracketed years does not mutate source evidence or profiles',()=>{
  const p=structuredClone(sample),before=JSON.stringify(p);personHeading(p);lifeYearsText(p);lifeYearCoordinate(p,'birth');
  assert.equal(JSON.stringify(p),before);
});
