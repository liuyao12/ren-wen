/** Deterministic layout and geography helpers. No source facts are inferred here. */
export function orderedPeople(ids, activeIds, subject, previous = []) {
  const available = new Set(ids), active = new Set(activeIds);
  const stable = [...new Set([...previous, ...ids])].filter(id => available.has(id));
  return [...(available.has(subject) ? [subject] : []),
    ...stable.filter(id => id !== subject && active.has(id)),
    ...stable.filter(id => id !== subject && !active.has(id))];
}

export function familyEdges(relations, visibleIds) {
  const visible = new Set(visibleIds);
  return relations.filter(r => r.predicate === 'child-of' && r.status !== 'rejected'
    && visible.has(r.subject) && visible.has(r.object) && r.subject !== r.object)
    .map(r => ({id:r.id, parent:r.object, child:r.subject, evidence:r.evidence || [], status:r.status}));
}

export function jurisdictionChain(records, id, year) {
  const result = [], visited = new Set();
  while (id) {
    if (visited.has(id)) throw Error('Cyclic jurisdiction hierarchy.');
    visited.add(id);
    const r = records.find(r => r.id === id);
    if (!r || !inYears(r.coverage, year)) return [];
    result.unshift(r); id = r.parent;
  }
  return result;
}
export const inYears = (range, year) => Number.isFinite(year) && range
  && year >= range.start && year <= range.end;
export const project = ([lon,lat]) => [lon + 20, 75 - lat];
export const validPoint = p => Array.isArray(p) && p.length >= 2
  && Number.isFinite(p[0]) && Number.isFinite(p[1]) && Math.abs(p[0]) <= 180 && Math.abs(p[1]) <= 90;

/** The curvature is a visual connector, NOT a reconstructed route or a geodesic. */
export function arcPath(a, b) {
  const [x1,y1] = project(a), [x2,y2] = project(b);
  const dx=x2-x1, dy=y2-y1, length=Math.hypot(dx,dy);
  if (!length) return '';
  const bend=Math.min(12,length*.22);
  return `M${x1},${y1} Q${(x1+x2)/2+dy/length*bend},${(y1+y2)/2-dx/length*bend} ${x2},${y2}`;
}

/** Separate journey records are never joined; source order alone is not a trajectory. */
export function routeSegments(journeys, {person, witness, passage, year, scope='all'}) {
  const result=[];
  for (const journey of journeys.filter(j => j.person === person && j.witness === witness)) {
    for (let i=1;i<journey.stops.length;i++) {
      const from=journey.stops[i-1], to=journey.stops[i];
      if (from.place === to.place || to.breakBefore) continue;
      if (scope === 'passage' && journey.passage !== passage) continue;
      if (scope === 'year' && Number(to.date.slice(0,4)) > year) continue;
      result.push({id:`${journey.id}-${i}`, from,to,journey,
        active:journey.passage === passage, future:Number(to.date.slice(0,4))>year});
    }
  }
  return result;
}

/** Optional local GeoJSON: inert, bounded input with explicit temporal and source metadata. */
export function validateBoundaries(data, jurisdictions) {
  if (data?.type !== 'FeatureCollection' || !Array.isArray(data.features) || data.features.length>2000)
    throw Error('Expected a GeoJSON FeatureCollection (at most 2,000 features).');
  let vertices=0; const keys=new Set();
  for (const f of data.features) {
    const p=f.properties, g=f.geometry;
    if (f.type !== 'Feature' || !p || !g || !['Polygon','MultiPolygon'].includes(g.type))
      throw Error('Only Polygon and MultiPolygon boundary features are accepted.');
    const j=jurisdictions.find(j => j.id === p.jurisdictionId);
    if (!j || p.level !== j.level) throw Error('Boundary must identify a known jurisdiction and its level.');
    if (!Number.isSafeInteger(p.startYear) || !Number.isSafeInteger(p.endYear) || p.startYear>p.endYear)
      throw Error('Boundary needs startYear and endYear.');
    if (!['source','license','attribution'].every(k => typeof p[k] === 'string' && p[k].trim()))
      throw Error('Boundary needs a source URL, license and attribution.');
    let u; try {u=new URL(p.source);} catch {throw Error('Invalid boundary source URL.');}
    if (!['https:','http:'].includes(u.protocol)) throw Error('Unsafe boundary source URL.');
    const key=`${p.jurisdictionId}:${p.startYear}:${p.endYear}`;
    if(keys.has(key)) throw Error('Duplicate boundary interval.'); keys.add(key);
    const polygons=g.type === 'Polygon' ? [g.coordinates] : g.coordinates;
    if(!Array.isArray(polygons) || !polygons.length) throw Error('Empty boundary geometry.');
    for(const polygon of polygons) {
      if(!Array.isArray(polygon) || !polygon.length) throw Error('Empty polygon.');
      for(const ring of polygon) {
        if(!Array.isArray(ring) || ring.length<4 || !ring.every(validPoint)
          || ring[0][0]!==ring.at(-1)[0] || ring[0][1]!==ring.at(-1)[1]) throw Error('Invalid or unclosed polygon ring.');
        vertices+=ring.length; if(vertices>100000) throw Error('Simplify boundaries to at most 100,000 vertices.');
      }
    }
  }
  return data.features;
}

export function boundaryPath(geometry) {
  const polygons=geometry.type === 'Polygon' ? [geometry.coordinates] : geometry.coordinates;
  return polygons.flatMap(poly=>poly.map(ring=>ring.map((p,i)=>`${i?'L':'M'}${project(p).join(',')}`).join('')+'Z')).join('');
}
export function clampView([x,y,w,h]) {
  w=Math.max(.15,Math.min(170,w)); h=Math.max(.10,Math.min(80,h));
  // Allow a modest overscroll margin even at the overview scale.
  return [Math.max(-20,Math.min(190-w,x)),Math.max(-12,Math.min(92-h,y)),w,h];
}

/** A reference snapshot never masquerades as the current narrative year. */
export function referenceLevels(year, width, mode='auto') {
  const available=year===1820?['province','prefecture']:year===1911?['province','prefecture','county']:[];
  const target=mode==='auto'?(width>18?'province':width>7?'prefecture':'county'):mode;
  const order=['province','prefecture','county'];
  return available.filter(level=>order.indexOf(level)<=order.indexOf(target));
}
export const REGIONAL_VIEW=Object.freeze([125,38,22,16]);
