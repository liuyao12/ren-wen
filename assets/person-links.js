import {ui} from './i18n.js';
import {readerURL} from './library.js';
import {fetchData} from './data-cache.js';
/** Reader adapter: decorate rendered text only; preserve source snapshots and occurrence IDs. */
import {loadProfiles} from './profiles.js';
import {nameDetailsHTML, loadNameHistory} from './name-history.js';
import {personHeading, profileURL, profilesWithStubs} from './person-display.js';

function articleKey(url) {
  try {
    const u = new URL(url);
    if (u.hostname !== 'en.wikisource.org' || !u.pathname.startsWith('/wiki/')) return null;
    return decodeURIComponent(u.pathname).replaceAll('_', ' ');
  } catch { return null; }
}

export function linkPersonMentions(reader, people) {
  for (const span of reader.querySelectorAll('[data-entity]')) {
    const id = span.dataset.entity;
    if (!people.has(id) || !profileURL(id) || span.closest('a[data-person-link]')) continue;
    // Remove imported navigation inside this occurrence, retaining the original URL as metadata.
    // In particular, Macartney's "see under Kuo" is not a person-identity mapping.
    let upstream = null;
    for (const a of span.querySelectorAll('a')) {
      upstream ||= a.getAttribute('href');
      a.replaceWith(...a.childNodes);
    }
    const outer = span.closest('a');
    if (outer) {
      upstream ||= outer.getAttribute('href');
      // Never create nested anchors or redirect unrelated text contained in an outer source link.
      outer.replaceWith(...outer.childNodes);
    }
    const a = document.createElement('a');
    a.href = profileURL(id);
    a.dataset.personLink = id;
    if (upstream) a.dataset.sourceHref = upstream;
    a.title = 'Open this person’s Ren-Wen profile. Use Review names or Alt-click to inspect this occurrence.';
    span.removeAttribute('role');
    span.removeAttribute('tabindex');
    span.removeAttribute('aria-label');
    span.removeAttribute('title');
    span.replaceWith(a);
    a.append(span);
  }
  // Explicit principal-biography mappings also cover source links not yet annotated as mentions.
  // A "mentioned-in" account is deliberately NOT mapped to that article's subject.
  const articles = new Map();
  for (const p of people.values()) for (const account of p.accounts || []) {
    if (account.relation !== 'principal-biography') continue;
    const key = articleKey(account.url || p.sources?.[account.source]?.url);
    if (!key) continue;
    if (articles.has(key) && articles.get(key)?.id !== p.id) articles.set(key, null);
    else if (!articles.has(key)) articles.set(key, p);
  }
  for (const a of reader.querySelectorAll('p[id] a[href]:not([data-person-link])')) {
    const p = articles.get(articleKey(a.getAttribute('href')));
    if (!p) continue;
    const names = [canonicalBareName(p), ...(p.name.romanizations || []).map(n => n.value)];
    const normalized = text => text.trim().replace(/\s+/gu, ' ').toLocaleLowerCase();
    if (!names.some(n => normalized(n) === normalized(a.textContent))) continue;
    a.dataset.sourceHref = a.getAttribute('href');
    a.href = profileURL(p.id);
    a.dataset.personLink = p.id;
    a.removeAttribute('target');
    a.removeAttribute('rel');
    a.title = 'Open this person’s Ren-Wen profile';
  }
}

function canonicalBareName(p) { return (p.name.surname || '') + p.name.given; }

async function install() {
  const reader = document.getElementById('reader');
  if (!reader) return;
  const [response, detailed] = await Promise.all([fetchData('data/catalog.json'), loadProfiles(), loadNameHistory()]);
  if (!response.ok) throw Error('Person navigation: catalogue unavailable.');
  const catalog = await response.json();
  const people = new Map(profilesWithStubs(catalog, detailed).map(p => [p.id, p]));
  const selector = document.getElementById('source-select');
  const review = document.getElementById('review-names');
  const summary = document.getElementById('reader-biography');
  let displayedPerson=null;
  const observer = new MutationObserver(enhance);
  function enhance() {
    observer.disconnect();
    try {
      linkPersonMentions(reader, people);
      const source = catalog.sources.find(s => s.id === selector?.value);
      const requested=new URLSearchParams(location.search).get('person');
      const p = source && people.get(source.subject || requested);
      if(!p && summary){summary.replaceChildren();displayedPerson=null;}
      if (p && summary && reader.querySelector('p[id]') && displayedPerson !== p.id) {
        const title = reader.querySelector(':scope > h1');
        if (title) {
          const h2 = document.createElement('h2');
          h2.className = 'source-reading-title';
          h2.textContent = title.textContent;
          title.replaceWith(h2);
        }
        summary.innerHTML = personHeading(p, {linked:true});
        displayedPerson=p.id;
        summary.dataset.person=p.id;
        fetchData(`data/people/${p.id}.json`).then(r=>r.ok?r.json():p).then(full=>{if(displayedPerson===full.id)summary.querySelector('.person-name-details').innerHTML=nameDetailsHTML(full);}).catch(console.warn);
        const qsg=(p.accounts||[]).filter(a=>a.readerWitness && catalog.sources.find(s=>s.id===a.readerWitness)?.work==='work-qingshigao');
        const preferred=qsg.find(a=>a.relation==='principal-biography') || qsg[0];
        if(preferred) {
          const nav=document.createElement('div');nav.className='profile-source-navigation';
          const a=document.createElement('a');a.href=readerURL(preferred.readerWitness,/^[a-z0-9-]+$/.test(preferred.passage||'')?preferred.passage:'',p.id);
          a.innerHTML=ui(preferred.matchStatus==='proposed'?'QSG account (match proposed)':'QSG account')+' →';nav.append(a);
          summary.querySelector('[data-profile-heading]').append(nav);
        }
      }
    } finally {
      observer.observe(reader, {childList:true, subtree:true});
    }
  }
  // Native links support keyboard navigation, open-in-new-tab and browser history.
  // Capture prevents the legacy occurrence editor from swallowing ordinary navigation.
  reader.addEventListener('click', event => {
    const a = event.target.closest('a[data-person-link]');
    if (!a) return;
    const modified = event.ctrlKey || event.metaKey || event.shiftKey || event.button !== 0;
    if (!modified && a.querySelector('[data-entity]') && (event.altKey || review?.checked)) {
      event.preventDefault(); // Bubble to the existing occurrence inspector, retaining its ID.
    } else event.stopPropagation();
  }, true);
  enhance();
}

if (typeof document !== 'undefined') install().catch(error => {
  const status = document.getElementById('status');
  if (status) status.textContent = `${error.message} The original reader remains available.`;
  console.error(error);
});
