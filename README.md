# 人文 · Ren-Wen

**People through texts. Texts in context.**

Ren-Wen is a research environment connecting people and historical texts through source-linked biographies, annotated editions, timelines, and maps. 人 and 文 are equal pillars: a person is not reducible to one biography, and a text is not reducible to the facts extracted from it.

## First working pilot

A static, desktop-first three-panel reader connects selected passages from the ECCP biography of **曾紀澤 / Tsêng Chi-tsê** with his account in **《清史稿》卷446**. This is a small, explicitly labelled excerpt collection, not a complete corpus or an independently reviewed edition.

- Scroll or select a paragraph to update the relevant people, events, and places.
- Inspect a marked name, place, office, or title; follow its evidence and other biographical accounts.
- Switch from ECCP to the same person's 清史稿 account without confusing different accounts with parallel editions.
- Show sourced lifespan bars and paragraph-specific events. Unknown lifespans remain unknown; appointment is not automatically service or travel.
- Hide Chinese editorial punctuation as a display operation, without changing the stored text.
- Propose an identification correction, keep a local review queue, and export/import agent-friendly JSON proposals.
- Inspect local XML and download its original bytes unchanged. This is **not yet a verified ctext semantic importer**.

The map currently shows modern reference points and a modern coastline backdrop. **No historical jurisdiction boundaries are asserted or bundled.** No ctext corpus, CBDB extract, or CHGIS dataset is redistributed.

## Run

Python 3.11+ is enough for the reader and all corpus tools; no framework, package installation, secret, or build step is required.

```sh
python -m http.server 8000
```

Open http://localhost:8000. Opening `index.html` directly as a local file will not load the corpus.

## Validate, query, and build the database

```sh
python scripts/renwen.py validate
python -m unittest discover -s tests -v
python scripts/renwen.py context eccp-03
python scripts/renwen.py build-db
```

The last command builds `build/renwen.sqlite`, a **derived** SQLite index with sources, entities, passages, mentions, events, biographical relations, and text relationships. The versioned HTML and JSON records remain authoritative. Do not edit the generated database as a second source of truth.

With Node.js installed, also run:

```sh
npm test
npm run check
```

## Human and agent contributions

Read [AGENTS.md](AGENTS.md) and [CONTRIBUTING.md](CONTRIBUTING.md). The browser never silently publishes edits or calls a model. Exported corrections can be checked and explicitly accepted in a Git working tree:

```sh
python scripts/renwen.py validate-proposals ren-wen-proposals.json
python scripts/renwen.py apply-proposals ren-wen-proposals.json --reviewer "Your name"
python scripts/renwen.py validate
```

Review the resulting diff before committing. The reviewer argument records the person actually making that decision; an agent must not invent human approval. Accepted changes update working markup, its mention index and checksum, and `data/reviews.jsonl`. The upstream snapshot is not changed. Stale or conflicting proposals are rejected.

## Text versions and editions

`data/upstream/` holds imported, unannotated snapshots; `data/texts/` holds our marked-up working edition. Use ordinary three-way comparison for upstream transcription corrections. Different historical editions, quotations, and other accounts coexist as distinct witnesses/relationships; they are **not** automatically merged into a single preferred text.

```sh
python scripts/renwen.py collate BASE.html INCOMING.html
python scripts/renwen.py merge BASE.html OURS.html INCOMING.html --output build/candidate.html
```

Merge only produces a review candidate. It never overwrites its inputs. Punctuation-only changes can affect historical interpretation and are flagged accordingly. The initial validator deliberately refuses unrecorded wording changes; accepting source-text updates requires a reviewed snapshot/catalog update, not merely running the merge command.

## ctext compatibility

The goal is to preserve ctext's XML, IDs, historical-date interpretations, and unknown fields, edit them in a better interface, and prepare reviewed upstream suggestions. Current implementation is **raw XML staging/inspection only**. A real annotated export, semantic field mapping, edit round-trip tests, permissions, and a supported upstream submission mechanism remain to be established. See [docs/ctext.md](docs/ctext.md).

## Documentation

- [Architecture and editorial decisions](docs/architecture.md)
- [Data provenance, punctuation, and rights](docs/provenance.md)
- [ctext adapter status](docs/ctext.md)
- [Roadmap](docs/roadmap.md)

## GitHub Pages

A deployment workflow is included. In repository **Settings → Pages**, select **GitHub Actions** as the publishing source, then run the **Pages** workflow or push a change to `main`. Site enablement requires repository administration permissions and is not accomplished by merely adding the workflow. The intended URL is `https://liuyao12.github.io/ren-wen/`; it is not a claim that deployment has already succeeded.

## Rights and affiliation

Original software is MIT-licensed. Historical texts, transcriptions, annotations, and geographic data have separately recorded provenance and applicable terms; see [docs/provenance.md](docs/provenance.md). The software license does not relicense imported data. Ren-Wen is an independent project, not affiliated with ctext, CBDB, Wikisource, or CHGIS.
