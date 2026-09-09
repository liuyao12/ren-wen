# 人文 · Ren-Wen

**People through texts. Texts in context.**

Ren-Wen connects historical texts and people through source-linked biographies, annotated editions, timelines, and maps. 人 and 文 are equal pillars: a person is not reducible to one biography, and a text is not reducible to the facts extracted from it.

[Open the reader](https://liuyao12.github.io/ren-wen/) · [People](https://liuyao12.github.io/ren-wen/profiles.html) · [Works](https://liuyao12.github.io/ren-wen/works.html)

## Current ECCP library

Four complete entries from *Eminent Chinese of the Ch'ing Period* are included: **曾紀澤 / Tsêng Chi-tsê, 郭嵩燾 / Kuo Sung-tao, 董恂 / Tung Hsün, and 崇厚 / Ch'ung-hou**. Bibliographies and contributor bylines are retained. The separate 《清史稿》 account of 曾紀澤 remains a selected excerpt, not a complete import.

The first expanded batch contains **71 person profiles, 48 named-work profiles, and 354 indexed occurrences** across the five texts. These are source-linked, agent-proposed records, not independently reviewed scholarship. Unsearched CBDB/Geni IDs and unresolved dates remain empty; place and event extraction is still partial.

- Hover or keyboard-focus a person to choose **Person profile** or **Read ECCP entry**. Imported entries open in the reader; external entries are identified as Wikisource links. A discussion under somebody else is labelled as a discussion, not the person's own biography.
- Work titles have separate profiles with attested forms, contributors and roles, bibliographical notes, related works and links back to their occurrences. Person profiles list work contributions.
- On touch screens, tap a name to open the choices. Arrow Down enters a focused card; Escape dismisses it. Ordinary desktop clicks still open the profile. **Review names**, Alt-click, or the card's review button opens the annotation inspector.
- Scroll or select a paragraph to update the timeline and map. Active people move together, with source-linked parent–child connectors. The interactive map shows evidenced journey sequences and a partial historical administrative hierarchy; arcs are not reconstructed travel routes.
- Canonical person names use **[籍貫] 姓名（字或號）**. AD years and Chinese civil/regnal years remain separate; ganzhi and sui use resolved Chinese years only.

No historical boundary polygons are bundled. The map backdrop and coordinates are modern references, distinct from historical jurisdictions. A local-only dated GeoJSON layer can be loaded where appropriate. No restricted ctext, CBDB or CHGIS bulk dataset is redistributed.

See [ECCP library, annotation scope and provenance](docs/eccp-library.md) and [timeline / map interaction](docs/reader-context.md). Earlier pilot notes describe the initial excerpt collection; the preserved parse responses and batch manifest now document the four complete ECCP imports.

## Run locally

The reader is static HTML, CSS and native JavaScript; no framework, package installation, credentials or build step is required to serve it.

```sh
python -m http.server 8000
```

Open http://localhost:8000. Opening `index.html` as a local file cannot load the data. Python 3.11+ runs the corpus tools.

## Validate and build the database

```sh
python scripts/renwen.py validate
python scripts/profiles.py validate
python scripts/works.py validate
python -m unittest discover -s tests -v
npm test
npm run check
python scripts/renwen.py build-db
python scripts/profiles.py index-db
python scripts/works.py index-db
```

`build/renwen.sqlite` is a **derived** index of sources, entities, passages, mentions, events, relationships, person profiles and work contributions. Versioned HTML and JSON remain authoritative. Do not edit the generated database as a second source of truth.

Optional Playwright browser checks are in `tests/browser_library.py`. They render local data fixtures and real browser modules; they are not claims of live-site network verification. The deployment workflow separately publishes accepted source files.

## Source versions and imports

`data/upstream/` contains source fragments before Ren-Wen annotations; `data/texts/` contains the corresponding working editions. The raw MediaWiki responses for the expanded ECCP batch are preserved in `data/imports/eccp-batch-01/`, with request metadata, revisions and checksums. Existing wording, diacritics, inline italics and cross-references are retained. Apparent source errors are not silently repaired.

Different historical editions, quotations and other accounts coexist; they are **not** merged into a single preferred text. Git-style three-way comparison is for upstream transcription corrections:

```sh
python scripts/renwen.py collate BASE.html INCOMING.html
python scripts/renwen.py merge BASE.html OURS.html INCOMING.html --output build/candidate.html
```

The command creates a review candidate and never overwrites its inputs. Punctuation-only changes can alter interpretation. Hiding editorial Chinese punctuation is a display operation, not a source correction.

## Human and agent contributions

Read [AGENTS.md](AGENTS.md) and [CONTRIBUTING.md](CONTRIBUTING.md). The browser never silently publishes edits or calls a model. Identification proposals can be exported and checked in a Git working tree:

```sh
python scripts/renwen.py validate-proposals ren-wen-proposals.json
python scripts/renwen.py apply-proposals ren-wen-proposals.json --reviewer "Actual reviewer"
python scripts/renwen.py validate
python scripts/works.py validate
```

Record only the reviewer who actually made the decision. Acceptance updates the working markup, mention index, checksum and review log; it does not change the upstream snapshot. After relinking a work occurrence, reconcile its profile's occurrence/evidence list before publishing; validation detects stale backlinks.

The explicit rule set in `data/editorial/eccp-batch-01.json` records the first-pass import decisions. It is not a general entity recognizer. Rebuilding an existing batch requires an explicit `--rebuild` in a review worktree; ordinary editorial changes should edit the records directly. The feature-branch bootstrap workflow never promotes itself to `main`.

## ctext compatibility

Current XML support is **raw byte preservation and inspection only**, not a verified semantic importer or upstream editor. Real ctext fixtures, field mapping, edit round-trip tests, permission checks and supported writeback remain to be established. See [ctext status](docs/ctext.md).

## Documentation

- [ECCP library and work profiles](docs/eccp-library.md)
- [Person conventions](docs/people.md) and [person navigation](docs/person-navigation.md)
- [Contextual timeline and map](docs/reader-context.md)
- [Initial architecture](docs/architecture.md) and [pilot provenance](docs/provenance.md)
- [Roadmap](docs/roadmap.md)

## GitHub Pages

The Pages workflow validates the data and publishes the reader, person/work pages, assets and source records on pushes to `main`. A successful deployment is recorded separately from validation. Hosting must be enabled with **GitHub Actions** as the Pages publishing source. No access tokens or client secrets are included in the webapp.

## Rights and affiliation

Original software is MIT-licensed. Source texts, transcriptions, annotations and geographic data retain their separately recorded terms and attribution; the software license does not relicense imported material. ECCP is marked as a United States government public-domain work on Wikisource; applicable Wikisource contributor rights and CC BY-SA attribution are preserved. Ren-Wen is independent and is not affiliated with ctext, CBDB, Geni, Wikisource or CHGIS.
