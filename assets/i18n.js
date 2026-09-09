/** Chinese-first UI localization. Explicit message bindings only: never walk or translate source prose. */
import chinese from './locale-zh.js';

export const DEFAULT_LOCALE = 'zh-Hant';
export const STORAGE_KEY = 'ren-wen:language:v1';
export const LOCALES = ['zh-Hant', 'en'];
const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function normalizeLocale(value) { return value === 'en' ? 'en' : DEFAULT_LOCALE; }
export function readLocale(storage) {
  try { return normalizeLocale(storage?.getItem(STORAGE_KEY)); } catch { return DEFAULT_LOCALE; }
}
let locale = DEFAULT_LOCALE;
if (typeof window !== 'undefined') {
  try { locale = readLocale(window.localStorage); } catch { /* Restricted storage: use Chinese. */ }
}
export const getLocale = () => locale;
export function t(key, params = {}, language = locale) {
  const text = normalizeLocale(language) === 'en' ? String(key) : (chinese[key] ?? String(key));
  return text.replace(/\{([a-zA-Z][a-zA-Z0-9_]*)\}/g, (whole, name) => Object.hasOwn(params, name) ? String(params[name]) : whole);
}
/** HTML helper for UI labels, not source wording. All interpolation values are escaped. */
export function ui(key, params = {}) {
  return `<span lang="${locale}" data-i18n="${escape(key)}"${Object.keys(params).length ? ` data-i18n-params="${escape(JSON.stringify(params))}"` : ''}>${escape(t(key, params))}</span>`;
}
/** Bind a dynamic label (including SVG text) without replacing surrounding controls. */
export function bindText(node, key, params = {}) {
  node.dataset.i18n = key;
  if (Object.keys(params).length) node.dataset.i18nParams = JSON.stringify(params);
  else delete node.dataset.i18nParams;
  node.textContent = t(key, params);
  return node;
}
const attributes = ['title', 'aria-label', 'placeholder', 'content'];
const selector = '[data-i18n],'+attributes.map(a=>`[data-i18n-${a}]`).join(',');
const protectedSelector = '[data-source-text],#reader > p[id],pre,code,textarea,[data-original]';
export function applyTranslations(root = document) {
  const nodes = [];
  if (root.nodeType === 1 && root.matches(selector)) nodes.push(root);
  if (root.querySelectorAll) nodes.push(...root.querySelectorAll(selector));
  for (const node of nodes) {
    // A source can contain markup that looks like our attributes: it must still remain untouched.
    if (node.closest(protectedSelector)) continue;
    let params = {};
    try { params = JSON.parse(node.dataset.i18nParams || '{}'); } catch { /* Corrupt UI metadata: no interpolation. */ }
    if (node.hasAttribute('data-i18n')) {
      node.setAttribute('lang', locale);
      const next = t(node.dataset.i18n, params);
      if (node.textContent !== next) node.textContent = next;
    }
    for (const attribute of attributes) {
      const key = node.getAttribute(`data-i18n-${attribute}`);
      if (key !== null) {
        const next = t(key, params);
        if (node.getAttribute(attribute) !== next) node.setAttribute(attribute, next);
      }
    }
  }
}
export function setLocale(value, {persist = true} = {}) {
  const next = normalizeLocale(value), changed = next !== locale; locale = next;
  if (typeof document === 'undefined') return locale;
  if (persist) { try { window.localStorage.setItem(STORAGE_KEY, locale); } catch { /* Keep session preference. */ } }
  document.documentElement.lang = locale;
  applyTranslations();
  for (const button of document.querySelectorAll('[data-set-locale]')) button.setAttribute('aria-pressed', String(button.dataset.setLocale === locale));
  if (changed) window.dispatchEvent(new CustomEvent('renwen:languagechange', {detail:{locale}}));
  return locale;
}
function install() {
  document.documentElement.lang = locale;
  document.addEventListener('click', event => {
    const button = event.target.closest?.('[data-set-locale]');
    if (button) setLocale(button.dataset.setLocale);
  });
  window.addEventListener('storage', event => { if (event.key === STORAGE_KEY || event.key === null) setLocale(event.newValue, {persist:false}); });
  // Newly rendered dialogs/cards opt in through data-i18n; body text is not scanned for matches.
  const pending = new Set(); let queued = false;
  new MutationObserver(records => {
    for (const record of records) for (const node of record.addedNodes) if (node.nodeType === 1) pending.add(node);
    if (queued || !pending.size) return;
    queued = true;
    queueMicrotask(() => { queued = false; const roots = [...pending]; pending.clear(); for (const root of roots) if (root.isConnected) applyTranslations(root); });
  }).observe(document.body, {childList:true, subtree:true});
  setLocale(locale, {persist:false});
}
if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', install, {once:true});
  else install();
}
