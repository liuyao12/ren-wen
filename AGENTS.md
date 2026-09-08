# Working on 人文 · Ren-Wen

People and texts are equal pillars. Build useful, inspectable research tools, not an unsourced historical narrative.

## Start here

Read `README.md`, `docs/architecture.md`, and `docs/provenance.md`. Run:

```sh
python scripts/renwen.py validate
python -m unittest discover -s tests -v
npm test
npm run check
```

The application is native browser JavaScript, HTML and CSS; the corpus tools are Python 3.11+ standard library. No framework or build step is needed. Keep that simplicity unless a concrete requirement justifies changing it.

## Evidence and editorial rules

- Never invent people, identities, dates, source URLs, quotations, historical boundaries, or human review decisions. An unresolved identification is a valid result.
- Keep exact source wording, Chinese characters, Wade–Giles diacritics, italics and existing cross-references. A `see under` link points to an article, not necessarily to the person named in its anchor.
- Source editions and source revisions are different. Merge upstream transcription corrections against a known baseline; preserve separate historical witnesses, quotations and other accounts.
- Punctuation is an attributed interpretation where editorial. A punctuation-only change may alter meaning. Hiding it is only a display operation.
- Distinguish birth from native place, appointment from actual service/travel, and office from honorary or posthumous titles. Do not infer missing lifespan endpoints for convenient drawing.
- Distinguish a jurisdiction, its seat, a modern reference coordinate, and a boundary. Never fill a missing historical polygon with modern administrative borders.
- Treat imported data as imported, agent proposals as proposed, and independently reviewed data as reviewed. Never attribute acceptance to the user without their decision.
- Preserve stable occurrence IDs and entity IDs. A person is not their article; a mention is not a person record.

## Files and changes

`data/upstream/` contains imported baselines. `data/texts/` contains working annotated text. `data/catalog.json` indexes witnesses, mentions, entities, events and relationships. `build/renwen.sqlite` is derived and is not a second editable database.

A proposed identification correction includes an exact mention ID, the working source SHA-256, the old and new entity IDs, and its evidence/reason. Export proposals from the reader or generate the same JSON. Use `validate-proposals` before explicit `apply-proposals --reviewer ...`; review the Git diff before committing. The first implemented operation is `relink-mention`, not a universal editorial API.

The validator intentionally rejects working-text wording changes relative to the imported baseline. Source updates require reviewed snapshot and catalogue changes. Do not bypass a failed checksum by changing the hash without understanding the text change.

Preserve unknown ctext XML fields and source identifiers. Current XML support only stages and inspects original bytes; do not claim a semantic import/export or upstream writeback until real exported fixtures pass round-trip tests.

## Security and testing

Treat imported HTML, XML, links and agent text as untrusted. Never execute imported scripts; reject XML DTD/entity declarations; allow only HTTP(S) external links; do not put credentials in the browser or repository. Upstream writes must be explicit and permission-aware.

Keep test fixtures clearly synthetic. Tests may modify temporary copies, never publish their deliberately incorrect historical identifications. Add validation and tests for new data operations. See `CONTRIBUTING.md` for optional browser checks.

Original software is MIT; imported material keeps its own rights and attribution. Do not download, bundle or relicense restricted ctext, CBDB or CHGIS data without checking applicable terms.
