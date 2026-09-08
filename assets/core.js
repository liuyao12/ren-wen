/** Small deterministic helpers shared by the reader and tests. */
export const PUNCTUATION = /[，。；：！？、「」『』（）《》〈〉〔〕【】…—]/u;
export const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function safeURL(value) {
  try { const url = new URL(value); return ['https:', 'http:'].includes(url.protocol) ? url.href : null; }
  catch { return null; }
}
export function contextFor(catalog, witness, passage) {
  const mentions = catalog.mentions.filter(m => m.witness === witness && m.passage === passage);
  const events = catalog.events.filter(e => e.witness === witness && e.passage === passage);
  return {mentions, events, entityIds: [...new Set([...mentions.map(m => m.entity), ...events.flatMap(e => [...e.people, ...e.places])])]};
}
export function validateProposal(p, catalog) {
  if (!p || p.schemaVersion !== 1 || p.operation !== 'relink-mention') throw Error('Unsupported proposal format.');
  const source = catalog.sources.find(s => s.id === p.witness);
  const mention = catalog.mentions.find(m => m.id === p.mention);
  if (!source || !mention || mention.witness !== source.id) throw Error('Unknown witness or mention.');
  if (p.baseSha256 !== source.sha256) throw Error('Stale source version. Rebase this proposal before reviewing it.');
  if (p.before !== mention.entity) throw Error('The original identification no longer matches.');
  if (!catalog.entities.some(e => e.id === p.after)) throw Error('Unknown target entity.');
  if (p.before === p.after) throw Error('The proposed identification is unchanged.');
  if (typeof p.reason !== 'string' || p.reason.trim().length < 8) throw Error('Explain the correction and its evidence.');
  if (typeof p.id !== 'string' || !/^[A-Za-z0-9_-]{1,100}$/.test(p.id)) throw Error('Invalid proposal ID.');
  if (p.status !== 'proposed') throw Error('Only proposed changes can enter the review queue.');
  return p;
}
export function punctuationInsensitive(text) { return [...text].filter(c => !PUNCTUATION.test(c) && !/\s/u.test(c)).join(''); }
export function yearLabel(time) { return time.start === time.end ? String(time.start) : `${time.start}–${time.end}`; }
