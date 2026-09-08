import {escapeHTML as h, safeURL} from './core.js';
import {canonicalName, ageAtDeath, loadProfiles} from './profiles.js';
import {personHeading, chineseYearText, westernYearText, profilesWithStubs} from './person-display.js';

const link = (url, label) => {
  const safe = safeURL(url);
  return safe ? `<a href="${h(safe)}" target="_blank" rel="noopener">${h(label)} ↗</a>` : h(label);
};
const byId = id => document.getElementById(id);

function render(p) {
  const sourceLink = key => link(p.sources[key]?.url, p.sources[key]?.title || key);
  const age = ageAtDeath(p);
  const accounts = (p.accounts || []).map(a => `<p>${a.readerWitness
    ? `<a href="./#${encodeURIComponent(a.readerWitness)}">${h(p.sources[a.source].title)} →</a>`
    : sourceLink(a.source)}<br><small>${h(a.relation)} · ${h(a.passage || '')}</small></p>`).join('');
  byId('profile').innerHTML = `
    <div class="eyebrow">${h(p.collection)} · PERSON PROFILE · ${h(p.reviewStatus)}</div>
    ${personHeading(p)}
    <p class="romanization">${(p.name.romanizations || []).map(r => h(r.value)).join(' · ')}</p>
    <div class="profile-source-navigation"><a href="./">Three-panel reader →</a>${(p.accounts || []).filter(a => a.readerWitness).map(a => `<a href="./#${encodeURIComponent(a.readerWitness)}">${h(p.sources[a.source].title)} →</a>`).join('')}</div>
    <p class="coverage">${h(p.coverage)}</p>
    <div class="life-grid">
      ${['birth', 'death'].map(endpoint => `<section class="life-cell"><h2>${endpoint === 'birth' ? '生年 · Birth' : '卒年 · Death'}</h2><div class="ad-detail">${h(westernYearText(p, endpoint))} AD</div><strong lang="zh-Hant">${h(chineseYearText(p.life[endpoint]))}</strong><p>${h(p.life[endpoint]?.original || 'Chinese civil year not established.')}</p>${p.life[endpoint]?.source ? sourceLink(p.life[endpoint].source) : ''}</section>`).join('')}
      <section class="life-cell"><h2>享年 · Calculated sui</h2><strong>${age === null ? 'Unresolved' : `${age} 歲`}</strong><p>Chinese death year − Chinese birth year + 1.</p><small>Not Western birthday age. 干支 is computed from the resolved Chinese year, not the Gregorian date.</small></section>
    </div>
    <div class="profile-grid">
      <section><h2>Identity · 名籍</h2><dl>
        <dt>姓 · Surname / clan</dt><dd>${h(p.name.surname || 'Not separately recorded')}</dd>
        <dt>名 · Given / attested name</dt><dd>${h(p.name.given)}</dd>
        <dt>籍貫 · Native place</dt><dd>${h(p.name.jiguan?.label || 'Unresolved')}</dd>
        <dt>字 · Courtesy names</dt><dd>${p.name.zi.map(x => h(x.value)).join('、') || 'Not yet entered'}</dd>
        <dt>號 · Other names</dt><dd>${p.name.hao.map(x => h(x.value)).join('、') || 'Not yet entered'}</dd>
      </dl><p class="note">${h(p.name.note)}</p></section>
      <section><h2>External profiles · 人物對照</h2>
        ${Object.entries(p.externalIds).map(([provider, x]) => `<div class="external"><strong>${h(provider.toUpperCase())}</strong><p>${x.id ? link(x.url, x.id) : 'Unresolved'}</p><small>${h(x.status)}${x.method ? ' · ' + h(x.method) : ''}</small>${x.evidence ? `<p class="note">${h(x.evidence)}</p>` : ''}</div>`).join('')}
      </section>
      <section><h2>Read the sources · 文</h2>${accounts || '<p>This reference profile has no locally imported biography yet.</p>'}
        <p class="note">Original-source links are kept here as evidence. Personal-name links in the reader open Ren-Wen profiles. Accounts not yet imported remain clearly marked external sources.</p>
      </section>
      <section><h2>Date evidence · 生卒考</h2>
        ${['birth', 'death'].map(e => `<p><strong>${e === 'birth' ? 'Birth' : 'Death'}:</strong> ${h(p.life[e]?.note || 'Chinese civil year unresolved.')}</p>`).join('')}
        ${(p.life.reportedAges || []).map(a => `<p>Reported age: ${a.value} ${h(a.system)} · ${sourceLink(a.source)}</p>`).join('')}
        <details><summary>Western dates and years as reported</summary>${[...(p.life.westernDates || []), ...(p.life.westernYears || [])].map(d => `<p>${h(d.event)}: <code>${h(d.value)}</code> (${h(d.calendar)}; ${h(d.status || 'source-reported')})<br>${sourceLink(d.source)}${d.note ? `<br><small>${h(d.note)}</small>` : ''}</p>`).join('')}</details>
        <p class="note">AD and Chinese civil-year labels are separate. A Chinese year can extend into the next AD year; missing calendar evidence is not filled in from a year number alone.</p>
      </section>
    </div>
    <section class="sources"><h2>Evidence and provenance</h2>
      ${Object.values(p.sources).map(s => `<p>${link(s.url, s.title)}<br><small>${h(s.locator)} · Access: ${h(s.access)}<br>${h(s.attribution)}</small></p>`).join('')}
      ${(p.notes || []).map(n => `<p class="note">${h(n)}</p>`).join('')}
      <p>${p.stub ? '' : `<a href="data/people/${encodeURIComponent(p.id)}.json">Profile JSON</a> · `}<code>${h(p.id)}</code></p>
    </section>`;
  document.title = `${canonicalName(p)} · 人文`;
}

(async () => {
  try {
    const [detailed, response] = await Promise.all([loadProfiles(), fetch('data/catalog.json')]);
    if (!response.ok) throw Error('The person catalogue could not be loaded.');
    const profiles = profilesWithStubs(await response.json(), detailed);
    if (!profiles.length) throw Error('No profiles have been entered.');
    const select = byId('profile-select');
    select.innerHTML = profiles.map(p => `<option value="${h(p.id)}">${h(canonicalName(p))}</option>`).join('');
    function route() {
      let requested;
      try { requested = decodeURIComponent(location.hash.slice(1)); } catch { requested = '(invalid)'; }
      if (!requested) { history.replaceState(null, '', `#${encodeURIComponent(profiles[0].id)}`); requested = profiles[0].id; }
      const profile = profiles.find(p => p.id === requested);
      if (!profile) {
        select.value = '';
        byId('profile').innerHTML = `<h1>Profile not found</h1><p role="alert">No person record matches <code>${h(requested)}</code>.</p><p>Select a known person above or <a href="./">return to the reader</a>.</p>`;
        document.title = 'Profile not found · 人文';
        return;
      }
      select.value = profile.id;
      render(profile);
    }
    select.onchange = () => { location.hash = encodeURIComponent(select.value); };
    window.addEventListener('hashchange', route);
    route();
  } catch (error) {
    byId('profile').innerHTML = `<h1>Profiles could not be loaded</h1><p role="alert">${h(error.message)}</p><p>Serve this directory over HTTP, rather than opening the file directly.</p>`;
  }
})();
