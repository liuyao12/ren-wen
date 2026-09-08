# Context timeline and historical geography

## Reading and profiles

The existing compact person heading stays above the source text. Name links still open the
independent person profile. The new panels do not rewrite a text, introduce new name
identifications, or alter a profile's dates. The initial scope remains the existing ECCP/QSG
excerpt pilot, not a complete biography.

`assets/reader-context.js` is a progressive reader adapter, like `person-links.js`. It observes
the active source paragraph and viewing-year controls. The original timeline/map nodes remain
hidden compatibility surfaces for the legacy reader; they are not a second editable database.
A future renderer consolidation can remove those nodes without changing the source records.

## Timeline

The biography's subject stays first. People referenced by the active passage's annotations,
existing person links, or extracted events form a contiguous group immediately below the
subject. Other rows retain their relative order where possible. Grouping can be switched off.
The source-wide AD scale stays fixed while the rows move, and keyed SVG rows and family
connectors animate together. Reduced-motion settings skip animation.

Only stored `child-of` assertions generate parent–child connectors. Proposed assertions have
dashed connectors and a clickable evidence entry. No family relationships are guessed from
names or temporal overlap. A connector is anchored to the child's birth year only when both
lifespans are resolved and the year lies within the parent's lifespan; otherwise a margin
connector makes no chronology claim. Family evidence can jump to its source passage.

Lifespan endpoints come from separately sourced Western year claims. Chinese-year and sui
fields remain independent; missing or conflicting Western endpoints are not guessed.
Click a name to open its profile, or a bar to choose whose journeys the map displays.

## Interactive map

Drag to pan; wheel, pinch, buttons or +/- zoom. Arrow keys pan and Home resets the overview.
The map view stays put while reading until explicitly fitted to the passage or the journeys.
The existing Natural Earth modern-reference land silhouette and cited rounded city points
remain the backdrop; this is not a historical coastline or an exact-location reconstruction.

Journey records in `data/geography.json` explicitly group dated stops into distinct journeys.
They are extracted from the cited local ECCP paragraphs, with original date expressions and
inference notes. Source order or appointments alone never generate trajectories. No links are
created between the three separate journeys in the pilot. Arcs indicate stop sequence, not
actual travel routes, intermediate visits, or shortest paths. Return and departure places are
allowed to recur. `breakBefore` prevents drawing across an unresolved gap.

The scope control selects all recorded journeys, the current passage, or legs whose destination
year is no later than the viewing year. Future legs in the full view are subdued and dashed.
Click an arc or journey card for stop dates and source evidence. Selecting another person or
switching to QSG never silently borrows the ECCP subject's trajectory.

## Historical hierarchy versus boundaries

`data/geography.json` contains a **partial**, source-linked hierarchy:

- 湖南省 → 長沙府 → 湘鄉縣, from 清史稿卷68.
- 江蘇省 → 松江府 → 上海縣, from 清史稿卷58.
- 直隸省 → 順天府 → 大興縣 / 宛平縣, from 清史稿卷54.

Sources consulted:
https://zh.wikisource.org/wiki/清史稿/卷68
https://zh.wikisource.org/wiki/清史稿/卷58
https://zh.wikisource.org/wiki/清史稿/卷54

These are administrative context records, not polygons, exact seats, or the person's proven
whereabouts. Shanghai's treaty-port/concession arrangements remain a separate issue. A
reference to Peking is not assigned arbitrarily to Daxing or Wanping. The province/prefecture/
county navigation omits intermediate circuits and does not imply they did not exist.

1839–1890 is the **pilot display coverage**, not a claim that these units were established or
abolished in those years. Continuity of these selected parent relations within that range is an
agent-proposed interpretation of the Qing geography accounts, not an exhaustive chronological
survey. Outside the coverage, the UI does not extrapolate. Every record has its own source
locator and proposed status. The catalogue's old empty `jurisdictions` slot remains unused;
this file is the authority for these new context records. The existing SQLite builder does not
yet index the new geography file.

No historical boundary polygons are bundled. CHGIS V6 explicitly prohibits redistribution:
https://chgis.fas.harvard.edu/data/chgis/v6/
Do not substitute modern administrative boundaries or trace plausible-looking borders.
A licensed dataset or separately documented digitization must precede a published boundary layer.

The Boundary layer control can inspect **local, session-only** GeoJSON with dated Polygon or
MultiPolygon features. It never uploads, persists or publishes the file. Each feature requires:
`jurisdictionId`, `level` (province/prefecture/county), `startYear`, `endYear`, `source` (HTTP/S URL),
`license`, and `attribution`. IDs must match the hierarchy. Closed rings, finite WGS84 longitude/
latitude coordinates, feature and vertex limits are validated; labels are escaped. Imported
layers retain their own attribution and are marked as locally supplied, not independently
reviewed. The time cursor and level control filter the geometry; polygon holes are preserved.
Local import does not establish permission to redistribute or the truth of the metadata.

Source transcription/attribution terms are retained. These small independently compiled
hierarchy assertions are not a CHGIS or CBDB extract.

## Tests

`node --test tests/context-model.test.mjs` runs deterministic layout, family, hierarchy,
journey and GeoJSON validation tests. They are also discovered by the existing GitHub CI.

`python tests/browser_context.py` exercises the rendered reader against local in-memory
fixtures, including scrolling, row reordering, family-source jumps, pan/zoom, marker clicks,
time/person/source filters, local geometry, and desktop/mobile layouts. It requires Playwright
and a Chromium installation (`BROWSER_EXECUTABLE` can select one). It makes no network requests
and does not claim to test a live deployment. Its synthetic boundary exists only in the test
browser and is cleared before the screenshot. `RENWEN_SCREENSHOT` optionally selects the
screenshot path; the default is `build/context-desktop.png`.
