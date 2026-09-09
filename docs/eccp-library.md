# ECCP library: people, works and reading choices

Batch 01 imports four complete Wikisource ECCP entries: Tsêng Chi-tsê (曾紀澤), Kuo Sung-tao (郭嵩燾), Tung Hsün (董恂), and Ch'ung-hou (崇厚). Bibliographies and contributor bylines are included. The previously selected 清史稿 passages remain separate and partial.

The initial expansion has 71 person profiles, 48 named-work profiles and 354 indexed mention occurrences across all five sources. These are agent-proposed records, not independently reviewed identifications. Places, dates, events and geography remain partial. A named work includes books, articles, periodicals and titled diplomatic documents; generic references such as “the Classics” and anonymous or ambiguous role references are not assigned invented identities.

## Reading

Hover or keyboard-focus an annotated person to choose their local profile or ECCP entry. Imported entries open inside the three-panel reader; other principal entries are labelled as Wikisource destinations. A discussion under another person is labelled “Discussed in ECCP”, never presented as the subject's own biography. A person without an identified entry still has their own profile.

A work's hover card links to its distinct work profile and the supporting passage. Work profiles retain attested title forms, reported publication details, contributors with roles, source evidence, and occurrence backlinks. A person's profile lists their work contributions. Titles differing between sources are not silently conflated: the two Macartney biography titles are retained with a proposed correspondence.

Cards remain open while pointing at their links. Arrow Down enters the card, Escape dismisses it, and the first tap on touch screens opens the choices. Ordinary desktop clicks still open the profile. Review names, Alt-click, or “Review this occurrence” invokes the existing annotation inspector. Work identifications use the same proposal mechanism; after accepting a work relink, reconcile its profile's occurrence/evidence lists before publishing. The work validator catches stale backlinks.

## Sources and reproducibility

`data/imports/eccp-batch-01/` preserves the four actual MediaWiki parse responses, request metadata/checksums and extracted opening paragraphs for linked ECCP entries. The rendered response snapshot is the evidence actually imported; a containing-page revision alone is not claimed to pin all transclusions. Raw imported HTML is inert and is never inserted into the browser. The normalized source fragments allow only whitelisted formatting and links.

`data/editorial/eccp-batch-01.json` is an explicit, inspectable batch rule set. Full names and named works are matched exactly; shorter names are resolved within their biography, not by corpus-wide surname replacement. A longer work title takes precedence over a personal name inside that title. Existing occurrence IDs are preserved where their same textual occurrence survives. Source paragraphs can be subdivided for reading; the source paragraph mapping is retained. Apparent source errors, including Dong's publication-year reading “1992”, are preserved, not silently corrected. Punctuation and original inline italics are retained; display whitespace is normalized.

The compiler is an import tool, not a general-purpose named-entity recognizer. Run it only on the preserved inputs in a review worktree:

```sh
python -m scripts.eccp_batch
# Rebuilding an existing batch needs an explicit decision:
python -m scripts.eccp_batch --rebuild
python scripts/renwen.py validate
python scripts/profiles.py validate
python scripts/works.py validate
python -m unittest discover -s tests -v
npm test && npm run check
```

All person and work records are separate versioned JSON files. The catalogue remains the authority for live mention links. Derived SQLite gains `work_profiles` and `work_contributors` via `python scripts/works.py index-db` after the ordinary corpus build. Neither person identity nor work identity is derived from a page URL.

## Bootstrap workflow

The `eccp-library` branch workflow stages a known, checksum-verified import artifact produced by our own `ECCP import review` run, applies the small UI patch, compiles the explicit batch, runs validation/tests, and commits the generated files on that feature branch. It never pushes to main or edits upstream sites. Promotion to main is a separate reviewed operation. After the first import, snapshots live in the repository and the artifact is no longer required. The patch is a recorded one-time migration, not a command to rerun against edited UI files.

## Attribution

Underlying ECCP articles: Tu Lien-chê; Arthur W. Hummel, editor; United States government publication, marked PD-USGov by Wikisource. Wikisource contributor/transcription rights, where applicable, retain CC BY-SA 4.0 attribution. The MIT software license does not relicense these source contributions. No CBDB, Geni, ctext or historical boundary bulk dataset is imported by this batch. New CBDB/Geni slots remain unsearched rather than guessed; existing checked mappings are preserved.
