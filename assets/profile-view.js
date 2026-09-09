import {fetchData} from './data-cache.js';
import {t, ui, bindText, getLocale} from './i18n.js';
import {escapeHTML as h, safeURL} from './core.js';
import {canonicalName, ageAtDeath, loadProfiles} from './profiles.js';
import {loadWorks,workURL,readerURL,eccpDestination,occurrences} from './library.js';
import {personHeading, chineseYearText, westernYearText, profilesWithStubs} from './person-display.js';

const link = (url, label) => {
  const safe = safeURL(url);
  return safe ? `<a href="${h(safe)}" target="_blank" rel="noopener">${h(label)} ↗</a>` : h(label);
};
const byId = id => document.getElementById(id);

let libraryCatalog=null,libraryWorks=[];
function render(p) {
  const sourceLink = key => link(p.sources[key]?.url, p.sources[key]?.title || key);
  const age = ageAtDeath(p);
  const destination=eccpDestination(p,libraryCatalog);
  const contributions=libraryWorks.filter(w=>(w.creators||[]).some(c=>c.person===p.id));
  const ms=occurrences(libraryCatalog,p.id);
  const accounts = (p.accounts || []).map(a => `<p>${a.readerWitness
    ? `<a href="${h(readerURL(a.readerWitness, /^[a-z0-9-]+$/.test(a.passage||'') ? a.passage : '', p.id))}">${h(p.sources[a.source].title)} →</a>`
    : sourceLink(a.source)}<br><small>${ui(a.relation)} · ${h(a.passage || '')}</small></p>`).join('');
  byId('profile').innerHTML = `
    <div class="eyebrow">${h(p.collection)} · ${ui("PERSON PROFILE")} · ${ui(p.reviewStatus)}</div>
    ${personHeading(p)}
    <p class="romanization">${(p.name.romanizations || []).map(r => h(r.value)).join(' · ')}</p>
    <div class="profile-source-navigation"><a href="./">${ui("Three-panel reader →")}</a>${(p.accounts || []).filter(a => a.readerWitness).map(a => `<a href="${h(readerURL(a.readerWitness, /^[a-z0-9-]+$/.test(a.passage||'') ? a.passage : '', p.id))}">${h(p.sources[a.source].title)} →</a>`).join('')}</div>
    ${destination?`<div class="reading-links"><a href="${h(destination.url)}"${destination.external?' target="_blank" rel="noopener"':''}>${ui(destination.label)}${destination.external?' ↗':' →'}</a></div>`:''}
    <p class="coverage">${ui(p.coverage)}</p>
    <div class="life-grid">
      ${['birth', 'death'].map(endpoint => `<section class="life-cell"><h2>${ui(endpoint === 'birth' ? '生年 · Birth' : '卒年 · Death')}</h2><div class="ad-detail">${h(westernYearText(p, endpoint))} ${ui("AD")}</div><strong lang="zh-Hant">${h(chineseYearText(p.life[endpoint]))}</strong><p>${p.life[endpoint]?.original ? h(p.life[endpoint].original) : ui('Chinese civil year not established.')}</p>${p.life[endpoint]?.source ? sourceLink(p.life[endpoint].source) : ''}</section>`).join('')}
      <section class="life-cell"><h2>${ui("享年 · Calculated sui")}</h2><strong>${age === null ? ui('Unresolved') : `${age} 歲`}</strong><p>${ui("Chinese death year − Chinese birth year + 1.")}</p><small>${ui("Not Western birthday age. 干支 is computed from the resolved Chinese year, not the Gregorian date.")}</small></section>
    </div>
    <div class="profile-grid">
      <section><h2>${ui("Identity · 名籍")}</h2><dl>
        <dt>${ui("姓 · Surname / clan")}</dt><dd>${p.name.surname ? h(p.name.surname) : ui('Not separately recorded')}</dd>
        <dt>${ui("名 · Given / attested name")}</dt><dd>${h(p.name.given)}</dd>
        <dt>${ui("籍貫 · Native place")}</dt><dd>${p.name.jiguan?.label ? h(p.name.jiguan.label) : ui('Unresolved')}</dd>
        <dt>${ui("氏族 · Clan")}</dt><dd>${p.name.clan?.label?h(p.name.clan.label):ui('Not separately recorded')}</dd>
        <dt>${ui("完整籍貫／旗籍 · Registration")}</dt><dd>${p.name.registration?.administrativeLabel?`<strong>${h(p.name.registration.administrativeLabel)}</strong><br><small>${sourceLink(p.name.registration.administrativeSource)} · ${ui('Registration category unresolved')}</small>`:''}${(p.name.registration?.attestations||[]).map(a=>`<p><span data-original>${h(a.text)}</span><br><small>${sourceLink(a.source)}</small></p>`).join('') || ui('Unresolved')}<p class="note">${ui('Civil registration and banner company are not inferred when the source does not specify them.')}</p></dd>
        <dt>${ui("字 · Courtesy names")}</dt><dd>${p.name.zi.map(x => h(x.value)).join('、') || ui('Not yet entered')}</dd>
        <dt>${ui("號 · Other names")}</dt><dd>${p.name.hao.map(x => h(x.value)).join('、') || ui('Not yet entered')}</dd>
      </dl><p class="note">${ui(p.name.note)}</p></section>
      <section><h2>${ui("External profiles · 人物對照")}</h2>
        ${Object.entries(p.externalIds).map(([provider, x]) => `<div class="external"><strong>${h(provider.toUpperCase())}</strong><p>${x.id ? link(x.url, x.id) : ui('Unresolved')}</p><small>${ui(x.status)}${x.method ? ' · ' + ui(x.method) : ''}</small>${x.evidence ? `<p class="note"><span data-original lang="en">${h(x.evidence)}</span></p>` : ''}</div>`).join('')}
      </section>
      <section><h2>${ui("Read the sources · 文")}</h2>${accounts || `<p>${ui("This reference profile has no locally imported biography yet.")}</p>`}
        <p class="note">${ui("Original-source links are kept here as evidence. Personal-name links in the reader open Ren-Wen profiles. Accounts not yet imported remain clearly marked external sources.")}</p>
      </section>
      <section><h2>${ui("Date evidence · 生卒考")}</h2>
        ${['birth', 'death'].map(e => `<p><strong>${ui(e === 'birth' ? 'Birth:' : 'Death:')}</strong> ${p.life[e]?.note ? h(p.life[e].note) : ui('Chinese civil year unresolved.')}</p>`).join('')}
        ${(p.life.reportedAges || []).map(a => `<p>${ui("Reported age:")} ${a.value} ${ui(a.system)} · ${sourceLink(a.source)}</p>`).join('')}
        <details><summary>${ui("Western dates and years as reported")}</summary>${[...(p.life.westernDates || []), ...(p.life.westernYears || [])].map(d => `<p>${ui(d.event)}: <code>${h(d.value)}</code> (${ui(d.calendar)}; ${ui(d.status || 'source-reported')})<br>${sourceLink(d.source)}${d.note ? `<br><small><span data-original lang="en">${h(d.note)}</span></small>` : ''}</p>`).join('')}</details>
        <p class="note">${ui("AD and Chinese civil-year labels are separate. A Chinese year can extend into the next AD year; missing calendar evidence is not filled in from a year number alone.")}</p>
      </section>
    </div>
    ${contributions.length?`<section><h2>${ui("Works and contributions · 文")}</h2><ul class="contribution-list">${contributions.map(w=>`<li><a href="${h(workURL(w.id))}">${h(w.title)}</a> · ${w.creators.filter(c=>c.person===p.id).map(c=>ui(c.role)).join('、')}</li>`).join('')}</ul></section>`:''}
    <section><h2>${ui("Occurrences in the imported texts ·")} ${ms.length}</h2><details><summary>${ui("Browse source passages")}</summary><ul class="mentions-list">${ms.map(m=>`<li><a href="${h(readerURL(m.witness,m.passage))}">${h(libraryCatalog.sources.find(s=>s.id===m.witness)?.shortTitle || m.witness)} · ${h(m.passage)} →</a><br><q data-original lang="${h(libraryCatalog.sources.find(s=>s.id===m.witness)?.language || 'en')}">${h(m.quote)}</q></li>`).join('')}</ul></details></section>
    <section class="sources"><h2>${ui("Evidence and provenance")}</h2>
      ${Object.values(p.sources).map(s => `<p>${link(s.url, s.title)}<br><small><span data-original lang="en">${h(s.locator)}</span> · ${ui("Access:")} ${ui(s.access)}<br><span data-original lang="en">${h(s.attribution)}</span></small></p>`).join('')}
      ${(p.notes || []).map(n => `<p class="note">${h(n)}</p>`).join('')}
      <p>${p.stub ? '' : `<a href="data/people/${encodeURIComponent(p.id)}.json">${ui("Profile JSON")}</a> · `}<code>${h(p.id)}</code></p>
    </section>`;
  document.title = `${canonicalName(p)} · 人文`;
}

(async () => {
  try {
    const [detailed, response, works] = await Promise.all([loadProfiles(), fetchData('data/catalog.json'),loadWorks()]);
    if (!response.ok) throw Error('The person catalogue could not be loaded.');
    libraryCatalog=await response.json();libraryWorks=works;
    const profiles = profilesWithStubs(libraryCatalog, detailed);
    if (!profiles.length) throw Error('No profiles have been entered.');
    const select = byId('profile-select');
    select.innerHTML = profiles.map(p => `<option value="${h(p.id)}">${h(canonicalName(p))}</option>`).join('');
    let routeSequence=0;
    async function route() {
      const sequence=++routeSequence;
      let requested;
      try { requested = decodeURIComponent(location.hash.slice(1)); } catch { requested = '(invalid)'; }
      if (!requested) { history.replaceState(null, '', `#${encodeURIComponent(profiles[0].id)}`); requested = profiles[0].id; }
      let profile = profiles.find(p => p.id === requested);
      if (!profile) {
        select.value = '';
        byId('profile').innerHTML = `<h1>${ui("Profile not found")}</h1><p role="alert">${ui("No person record matches")} <code>${h(requested)}</code>.</p><p>${ui("Select a known person above or")} <a href="./">${ui("return to the reader")}</a>.</p>`;
        document.title = 'Profile not found · 人文';
        return;
      }
      select.value = profile.id;
      if(profile.summaryOnly) {
        const response=await fetchData(`data/people/${profile.id}.json`);
        if(!response.ok)throw Error('Person record unavailable.');
        const full=await response.json();if(full.id!==profile.id)throw Error('Mismatched person record.');profile=full;
      }
      if(sequence===routeSequence)render(profile);
    }
    select.onchange = () => { location.hash = encodeURIComponent(select.value); };
    window.addEventListener('hashchange', ()=>route().catch(error=>{byId('profile').textContent=error.message;}));
    await route();
  } catch (error) {
    byId('profile').innerHTML = `<h1>${ui("Profiles could not be loaded")}</h1><p role="alert">${h(error.message)}</p><p>${ui("Serve this directory over HTTP, rather than opening the file directly.")}</p>`;
  }
})();
