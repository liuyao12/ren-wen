# Roadmap

## 0.1 — initial working slice

Implemented: static three-panel reader; small ECCP/QSG same-person pilot; original-source links and omitted-passage labels; source-filtered events; modern reference geography explicitly distinguished from historical jurisdictions; Chinese punctuation visibility; mention inspection and correction proposals; reviewed CLI application; raw XML staging; basic collation/three-way merge candidates; validation and derived SQLite index.

Not claimed: complete ECCP import, independently reviewed historical dataset, ctext semantic compatibility or upstream publication, historical jurisdiction polygons, exact calendar conversion, authenticated multi-user editing.

## 0.2 — real import and ctext round trip

Get a licensed real ctext XML fixture; preserve unknown data; map its entities and dates; edit one annotation and reopen in the original client. Add an automated MediaWiki snapshot importer with original link destinations, attribution, revision dependencies and stable source identities. Expand the ECCP pilot only after source fidelity checks.

## 0.3 — evidence and multiple witnesses

Add assertion-level operations for names, kinship, appointments and competing dates. Add explicit punctuation alternatives and passage alignments between editions/quotations. Keep other accounts distinct from editions of one text. Test transfer proposals and changes to supporting passages, not merely the words inside a highlight.

## 0.4 — historical geography

Establish permitted data sources, time coverage, jurisdiction identities, dated parent relations, seats and geometry provenance. Render an administrative hierarchy without inventing missing boundaries. Keep actual presence, appointment jurisdiction, native place and modern reference coordinates distinct.

## 0.5 — contribution service

Verify ctext writeback with permission-aware review, concurrency checks and remote acknowledgments. Add collaborative review only when a real workflow requires it; never embed secrets in a static GitHub Pages app. Consider generating adapter-compatible changes without publishing them automatically.
