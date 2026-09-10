/** Place expressions and dated map illustrations are separate identities. */
export function placeURL(id) {
  return typeof id==='string' && /^place-[a-z0-9-]+$/.test(id) ? `places.html#${id}` : null;
}
export function visibleLabelLayers(layers,year,width,levels,enabled=true) {
  if(!enabled || !Number.isFinite(width) || width<=0)return [];
  const level=['county','prefecture','province'].find(x=>levels.includes(x));
  return layers.filter(l=>l.year===year && l.level===level && width>l.minViewWidth && width<=l.maxViewWidth
    && /^assets\/maps\/chgis-\d{4}-(province|prefecture|county)-names-(overview|regional|detail)\.png$/.test(l.file));
}
export function linkPlaceMentions(reader,places) {
  for(const span of reader.querySelectorAll('[data-entity]')) {
    const id=span.dataset.entity;
    if(!places.has(id) || !placeURL(id) || span.closest('[data-place-link]'))continue;
    for(const a of span.querySelectorAll('a'))a.replaceWith(...a.childNodes);
    const outer=span.closest('a');if(outer)outer.replaceWith(...outer.childNodes);
    const a=document.createElement('a');a.href=placeURL(id);a.dataset.placeLink=id;
    for(const attr of ['role','tabindex','title','aria-label'])span.removeAttribute(attr);
    span.replaceWith(a);a.append(span);
  }
}
