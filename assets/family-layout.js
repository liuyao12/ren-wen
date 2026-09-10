/** Source-linked family layout. Kinship is read from assertions, never from surnames. */
export const FAMILY_ROLES = Object.freeze(['grandparents', 'parents', 'self', 'spouses', 'children']);
const usable = r => r && !['rejected', 'superseded'].includes(r.status)
  && r.subject !== r.object && Array.isArray(r.evidence) && r.evidence.length > 0;

export function familyHierarchy(subject, relations, availableIds) {
  const available = new Set(availableIds);
  const links = relations.filter(r => usable(r) && available.has(r.subject) && available.has(r.object));
  const parentsOf = id => links.filter(r => r.predicate === 'child-of' && r.subject === id).map(r => r.object);
  const parents = [...new Set(parentsOf(subject))].filter(id => id !== subject);
  const spouses = links.filter(r => ['spouse-of', 'wife-of', 'husband-of'].includes(r.predicate)
    && (r.subject === subject || r.object === subject)).map(r => r.subject === subject ? r.object : r.subject);
  const groups = {
    grandparents: [...new Set(parents.flatMap(parentsOf))].filter(id => id !== subject && !parents.includes(id)),
    parents, self: available.has(subject) ? [subject] : [], spouses,
    children: links.filter(r => r.predicate === 'child-of' && r.object === subject).map(r => r.subject)
  };
  const used = new Set(), members = [];
  for (const role of FAMILY_ROLES) for (const id of groups[role]) {
    if (!used.has(id)) { used.add(id); members.push({id, role}); }
  }
  return {members, links: links.filter(r => used.has(r.subject) && used.has(r.object))};
}

/** Inactive tiers fold to grey bands. All underlying identities remain accessible. */
export function familyFocusLayout({subject, relations, availableIds, sourceIds, activeIds,
  previous = [], focus = true, expanded = false, showOthers = false}) {
  const family = familyHierarchy(subject, relations, availableIds);
  const active = new Set([...activeIds, subject]), familyIds = new Set(family.members.map(m => m.id));
  const available = new Set(availableIds);
  const source = [...new Set(sourceIds)].filter(id => available.has(id));
  const stable = [...new Set([...previous, ...source])].filter(id => source.includes(id) && !familyIds.has(id));
  const focused = stable.filter(id => active.has(id)), remaining = stable.filter(id => !active.has(id));
  const rows = [];
  for (const role of FAMILY_ROLES) {
    const members = family.members.filter(m => m.role === role);
    // Preserve source/assertion order inside each tier; no claim to sibling seniority.
    const inactive = members.filter(m => !active.has(m.id));
    const collapse = focus && !expanded && inactive.length > 0;
    for (const m of members) if (!collapse || active.has(m.id)) {
      rows.push({key:m.id, ids:[m.id], kind:'person', role, active:active.has(m.id), height:42});
    }
    if (collapse) rows.push({key:`family-${role}`, ids:inactive.map(m => m.id), kind:'summary', role, active:false, height:18});
  }
  let y = 38;
  for (const row of rows) { row.y = y; y += row.height; }
  const familyEnd = y - 12;
  const others = focus ? [...focused, ...(showOthers ? remaining : [])] : stable;
  const dividerY = others.length ? y + 3 : null;
  if (others.length) y += 22;
  for (const id of others) {
    const row = {key:id, ids:[id], kind:'person', role:'other', active:active.has(id), height:42, y};
    rows.push(row); y += row.height;
  }
  return {rows, family, familyEnd, dividerY, height:Math.max(100, y + 8),
    otherOrder:focus ? [...focused, ...remaining] : stable, hiddenOthers:focus && !showOthers ? remaining.length : 0,
    focusedCount:rows.filter(r => r.kind === 'person' && r.active).length};
}
