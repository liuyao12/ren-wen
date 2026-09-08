# Architecture and editorial decisions

## One repository, three views

The browser loads `data/catalog.json` and the selected working HTML fragment. Its shared context is a witness, active passage, relevant entity IDs and a historical time cursor. Text, timeline and map render that state. Source switching keeps the same biographical subject but does not identify the two accounts as translations.

The initial reader has no backend, model dependency, account login or external runtime assets. An agent works through file changes and the Python CLI; a human inspects the same evidence in the reader. Local review proposals use browser storage when available and can always be exported. Reloading never claims an upstream edit occurred.

## Authoritative records

- `data/upstream/*.html`: manually prepared source snapshots before Ren-Wen annotations, with explicit provenance. These are not pristine downloaded HTML.
- `data/texts/*.html`: the corresponding marked-up working text. Stable paragraph and occurrence IDs are in the markup; people and passages have independent identities.
- `data/catalog.json`: source manifests, entity summaries, occurrence index, passage-supported events and relationships, and links between accounts.
- `data/reviews.jsonl`: accepted proposal history, created by explicit review commands.
- `build/renwen.sqlite`: a reproducible SQL index, not a separately editable authority.

The small seed format is an application data model, not a replacement for ctext's XML. The ctext adapter must preserve its original bytes and semantics before projecting anything into the reader.

## Revision versus witness

A corrected transcription is an update to a digital witness. A historical edition, a quotation, an abridgment or another account can coexist with it. Keep separate witness IDs and passage correspondences. Git records our editorial history; it does not decide which historical reading is correct.

For an update, compare old unannotated baseline, our annotation-bearing copy and incoming text. `merge` invokes `git merge-file --diff3` into a separate candidate. Ordinary line conflicts are reviewed; no elaborate custom merger is implemented yet. Alignments and annotation transfer across witnesses remain proposals until checked.

## Assertions and uncertainty

The pilot has explicitly sourced person life summaries and event records with witness/passage evidence. Events retain original date expressions and normalization notes. Regnal-year indexing in this seed is coarse: it is not a claim that an entire Chinese year equals a Gregorian calendar year. A production date model should preserve calendar, precision and uncertainty in each endpoint.

No date is manufactured for an unknown lifespan. Titles, offices, people and places are different entity kinds. `see under` is a cross-reference to an article, not proof of identity. Appointments do not become journeys or actual service periods without further evidence.

The catalogue has room for historical jurisdiction records, but the seed array is empty. The map deliberately shows a dissolved modern land backdrop and modern reference points. It does not imply historical boundaries, locations of every person, or journeys between the points.

## Punctuation

Stored punctuation is retained with source-level provenance. Chinese punctuation can be hidden without altering stored text or anchor IDs. Punctuation-insensitive collation is available, but punctuation-only changes still require interpretation review. Source paragraphs, not inferred sentence boundaries, identify the pilot passages.

## Implemented review boundary

The initial proposal operation is `relink-mention`: schema version, proposal ID, witness, source SHA-256, mention ID, before/after entity IDs, reason and proposed status. Both Python and JavaScript validate it. Acceptance is explicit, logs its actual reviewer, and updates the markup/index/checksum together in a Git working tree. Event/date edits and entity merges need future operations and tests; they are not silently generalized from mention replacement.

## Next adapters

A real ctext fixture establishes the import contract and unknown-field preservation. A MediaWiki importer should preserve raw snapshots, original links and content-bearing page revision dependencies. Historical geometry needs a separately licensed dataset and dated jurisdiction relations; absent polygons remain absent. See `roadmap.md`.
