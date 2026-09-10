# ECCP first-round collection

All 1,008 extant subordinate pages listed by the Wikisource contents are
preserved: 809 narrative biography entries, 193 printed cross-reference entries,
and six editorial/reference texts. Four uncreated index pages in the upstream
contents are not biographies and have no source text to import. This is not a
claim that every annotation or historical assertion has been independently reviewed.

Full reading bodies, bibliography, bylines, notes and text outside ordinary
paragraph tags are retained. The existing five editorial witnesses and their
occurrence IDs are not rebuilt. New entries include hashes of their preserved
MediaWiki responses and separate upstream/marked-up text. The comparison permits
presentation whitespace and zero-width page-break markers, not wording changes.

## Profiles and annotation coverage

Shared full-name matches, explicit cross-references, romanized names with Han
forms, source-scoped name candidates and typographic work-title candidates are
marked as proposed. Every recognized person/work occurrence has its own local
record. Unknown identities, dates, CBDB/Geni IDs and registry details stay unknown.
Names not recognized by this first pass still need editorial annotation; the
presence of a complete imported text does not certify annotation recall.
Identical title strings in different sources do not automatically merge works.

A printed “see under” entry can describe somebody other than the destination
article's subject. The importer preserves both records and does not equate them
merely because a source hyperlink connects them. Reference-profile deduplication
and explicit coreference, including names expressed by titles, remain review work.

## 清史稿

The first-round concordance identifies candidate biographical openings in the
preserved QSG annal/biography volumes. The compared opening is recorded verbatim.
Matched volumes are imported in full, once per volume; links identify a passage
and selected person without cutting the account at an inferred ending. Namesakes,
variant names, subordinate biographies and mismatched editions require review.
Unmatched people are not declared absent from QSG. Source numbering is not copied
blindly from ECCP's historical citation system.

## Names and registration

The canonical qualifier is `name.bracket`, typed as `county` or `clan`.
A missing qualifier is null; a province/prefecture is not used as a substitute.
`name.jiguan` retains the source's native-place statement. `name.registration`
retains independently attributed wording and, where supported, an administrative
path. These fields do not claim a birthplace. For Manchu clan names such as 完顏,
the clan is the qualifier rather than a Han-style surname.

Examples: `[湘鄉] 曾紀澤（劼剛）`, `[完顏] 崇厚（地山）`.
The former profile records 湖南長沙府湘鄉縣 from the existing sourced geographical
hierarchy. It does not add 民籍. The latter retains QSG's 內務府鑲黃旗 and ECCP's
wording separately; an unrecorded 佐領 is not supplied.

## Reproduction

On an a2b5d70-baseline review worktree, with preserved source artifacts:

```
python -m scripts.round1_import --raw /path/to/eccp-artifact --qsg /path/to/qsg-artifact
python -m scripts.registry_display
python -m scripts.reading_indexes
python -m scripts.round1_validate
```

`reading_indexes` writes derived compact bundles. The authoritative person/work
JSON files remain individual records. Reader modules share a request cache and
load a full profile only when its dedicated page is opened. `library.html` uses
a small derived index instead of fetching the entire corpus.
