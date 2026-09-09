# Complete entries, reusable texts, and their readings

## Import one biography, not another batch

The fifth ECCP entry is **Tsêng Kuo-fan / 曾國藩**, revision 11365232. All 17
source paragraphs are retained, including bibliography and Têng Ssŭ-yü's byline.
`data/imports/eccp-zeng-guofan/response.json` preserves the downloaded response.
The complete reading-body character stream is checked against the imported
paragraphs (allowing presentation whitespace and page-marker removal only).
Unsupported non-paragraph text raises an error instead of vanishing.

Run a new entry in a review worktree:

```sh
python -m scripts.import_entry SPEC.json RESPONSE.json MANIFEST.json
```

Existing entries are refused: do not regenerate old annotations when adding a
new biography. Upstream wording changes still need the established three-way
source update process. The script produces proposed annotations, never invented
human approval. Inspect the entire text, not just existing highlights.

The 曾國藩 import adds 228 occurrence annotations, identifying 68 people and
36 named works. Names in bibliographical references and repeated names are
included. It is an agent first pass, not an independently reviewed edition.
The retrospective `the Emperor` in paragraph 12 is unresolved. Original apparent
errors such as `ittempted`, `tbr`, `oten come`, `rook`, and `la addition` remain.
The additional source openings identify cross-reference targets; they do not
add another full biography to the reader. Unresolved Chinese names and external
identifiers are left unresolved. DILA's explicit cross-reference supplies the
main subject's CBDB mapping; no bulk CBDB record is imported.

## Text identity is not its occurrence

`data/text-units.json` has three collections:

- `units`: stable text identities (a biography, bibliography, memorial, quotation,
  letter, or smaller independently referenced piece). A work title, text unit,
  and physical/source edition are not interchangeable.
- `occurrences`: a particular reading in a particular witness, with source
  checksum and one or more exact code-point ranges. Every occurrence preserves
  its own wording, including punctuation. `container` locates it inside another
  occurrence in that witness. `parentUnit` is optional intellectual hierarchy.
- `relations`: explicitly evidenced correspondence such as quotes, paraphrases,
  translates, parallel-reading, or derived-from. Matching text is a retrieval
  candidate, not an automatic identity or dependency decision.

A repeated quotation receives the **same unit ID and a new occurrence ID** when
that relationship is established. It may have a different reading and a
different container. No source passage is removed or replaced by the preferred
reading. A source update invalidates affected version bindings until reviewed.
A quotation extracted from a source is not an additional independent witness.

## First real nested reading

The formerly missing `qsg-02` is restored from the full 卷446 response. The
曾紀澤 account now contains all four source paragraphs. Existing IDs qsg-01,
qsg-03, qsg-04 and their annotation records were not regenerated.

The memorial introduced by `紀澤乃疏言` is unit
`text-zeng-jize-yili-memorial`, with its quoted reading inside `occ-qsg`.
Its title is explicitly editorial/descriptive, not asserted to be the original
memorial's title. Only this source occurrence is registered; no parallel
attestation or original memorial has been fabricated. The 773-code-point
quotation stays intact in its original paragraph. The ECCP 曾國藩 bibliography
is also registered as a section inside that biography.

`texts.html` presents each reading and links back to its complete context.
The reader exposes text-structure, section and quotation links without altering
the stored source wording. Interface language changes do not translate readings.

```sh
python -m scripts.text_units validate
python scripts/renwen.py build-db
python -m scripts.text_units index-db
```

SQL tables `text_units`, `text_occurrences`, and `text_correspondences` are
rebuildable indexes, not separate editable sources of truth.
