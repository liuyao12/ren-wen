import {escapeHTML as h, safeURL} from './core.js';
import {canonicalName, ageAtDeath, yearText, loadProfiles} from './profiles.js';

const link = (url, label) => {
  const safe = safeURL(url);
  return safe ? `<a href="${h(safe)}" target="_blank" rel="noopener">${h(label)} ↗</a>` : h(label);
};
const byId = id => document.getElementById(id);

function render(p) {
  const sourceLink = key => link(p.sources[key]?.url, p.sources[key]?.title || key);
  const age = ageAtDeath(p);
  byId('profile').innerHTML = `
    <div class="eyebrow">${h(p.collection)} · PERSON PROFILE · ${h(p.reviewStatus)}</div>
    <h1 lang="zh-Hant">${h(canonicalName(p))}</h1>
    <p class="romanization">${p.name.romanizations.map(r => h(r.value)).join(' · ')}</p>
    <p class="coverage">${h(p.coverage)}</p>
    <div class="life-grid">
      ${['birth', 'death'].map(endpoint => `<section class="life-cell"><h2>${endpoint === 'birth' ? '生年 · Birth' : '卒年 · Death'}</h2><strong>${h(yearText(p.life[endpoint]))}</strong><p>${h(p.life[endpoint]?.original || 'No source date established.')}</p>${p.life[endpoint]?.source ? sourceLink(p.life[endpoint].source) : ''}</section>`).join('')}
      <section class="life-cell"><h2>享年 · Calculated sui</h2><strong>${age === null ? 'Unresolved' : `${age} 歲`}</strong><p>Chinese death year − Chinese birth year + 1.</p><small>This is not Western birthday age.</small></section>
    </div>
    <div class="profile-grid">
      <section><h2>Identity · 名籍</h2><dl>
        <dt>姓 · Surname</dt><dd>${h(p.name.surname || 'Unresolved')}</dd>
        <dt>名 · Given name</dt><dd>${h(p.name.given)}</dd>
        <dt>籍貫 · Native place</dt><dd>${h(p.name.jiguan?.label || 'Unresolved')}</dd>
        <dt>字 · Courtesy names</dt><dd>${p.name.zi.map(x => h(x.value)).join('、') || 'Not yet entered'}</dd>
        <dt>號 · Other names</dt><dd>${p.name.hao.map(x => h(x.value)).join('、') || 'Not yet entered'}</dd>
      </dl><p class="note">${h(p.name.note)}</p></section>
      <section><h2>External profiles · 人物對照</h2>
        ${Object.entries(p.externalIds).map(([provider, x]) => `<div class="external"><strong>${h(provider.toUpperCase())}</strong><p>${x.id ? link(x.url, x.id) : 'Unresolved'}</p><small>${h(x.status)}${x.method ? ' · ' + h(x.method) : ''}</small>${x.evidence ? `<p class="note">${h(x.evidence)}</p>` : ''}</div>`).join('')}
      </section>
      <section><h2>Read the sources · 文</h2>
        ${p.accounts.map(a => `<p><a href="./#${encodeURIComponent(a.readerWitness)}">${h(p.sources[a.source].title)} →</a><br><small>${h(a.relation)} · ${h(a.passage)}</small></p>`).join('')}
        <p class="note">These are different accounts of one person, not editions of a single text. The reader currently shows selected excerpts.</p>
      </section>
      <section><h2>Date evidence · 生卒考</h2>
        ${['birth', 'death'].map(e => `<p><strong>${e === 'birth' ? 'Birth' : 'Death'}:</strong> ${h(p.life[e]?.note || 'Unresolved.')}</p>`).join('')}
        ${p.life.reportedAges.map(a => `<p>Reported age: ${a.value} ${h(a.system)} · ${sourceLink(a.source)}</p>`).join('')}
        <details><summary>Western dates as reported, kept separately</summary>${p.life.westernDates.map(d => `<p>${h(d.event)}: <code>${h(d.value)}</code> (${h(d.calendar)}; ${h(d.status)})<br>${sourceLink(d.source)}${d.note ? `<br><small>${h(d.note)}</small>` : ''}</p>`).join('')}</details>
      </section>
    </div>
    <section class="sources"><h2>Evidence and provenance</h2>
      ${Object.values(p.sources).map(s => `<p>${link(s.url, s.title)}<br><small>${h(s.locator)} · Access: ${h(s.access)}<br>${h(s.attribution)}</small></p>`).join('')}
      ${p.notes.map(n => `<p class="note">${h(n)}</p>`).join('')}
      <p><a href="data/people/${encodeURIComponent(p.id)}.json">Profile JSON</a> · <code>${h(p.id)}</code></p>
    </section>`;
  document.title = `${canonicalName(p)} · 人文`;
  history.replaceState(null, '', `#${encodeURIComponent(p.id)}`);
}

(async () => {
  try {
    const profiles = await loadProfiles();
    if (!profiles.length) throw new Error('No profiles have been entered.');
    const select = byId('profile-select');
    select.innerHTML = profiles.map(p => `<option value="${h(p.id)}">${h(canonicalName(p))}</option>`).join('');
    let requested = '';
    try { requested = decodeURIComponent(location.hash.slice(1)); } catch { /* Use the first profile. */ }
    const initial = profiles.find(p => p.id === requested) || profiles[0];
    select.value = initial.id; render(initial);
    select.onchange = () => render(profiles.find(p => p.id === select.value));
  } catch (error) {
    byId('profile').innerHTML = `<h1>Profiles could not be loaded</h1><p role="alert">${h(error.message)}</p><p>Serve this directory over HTTP, rather than opening the file directly.</p>`;
  }
})();
