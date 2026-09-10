# Contextual identification review — 2026-09-10

A source transcription is not an entity decision. This release withdraws the
round-one **typography-only** work identifications from active reading links and
withdraws global matches of ambiguous temple/reign names. Withdrawal does not
assert that every candidate is wrong. Many are genuine works or people but still
need their particular occurrence and identity checked.

Every withdrawn occurrence retains its original span ID and original words.
`data/editorial/identification-review.json` retains the former target, reason,
source revision URL and pre-change source checksum. Work candidates remain at
their stable JSON/profile URLs, marked `identificationStatus: needs-review`,
but are not listed as established work profiles. No source text is deleted.
`review.html` filters these candidates by source, entity, reason and text, and
exports the filtered evidence as JSON. Export is not acceptance or publication.

## Focused review: 阿克敦

ECCP `eccp-3633207` is preserved in full, including its bibliography and both
contributor bylines. Its four explicitly described compilations/collected works
retain their links. The one-juan *nien-p'u* compiled by 那彥成 is given its own
`work-akedun-nianpu` record, rather than pointing to 曾國藩's chronology.

The 1726 emperor reference is linked to the Yin-chên principal biography; the
1749/1750/1754 reference is linked to Hung-li. In QSG volume 303, paragraphs
021–026, the individually selected `上`, `世宗`, and `高宗` occurrences distinguish
Kangxi, Yongzheng and Qianlong. `學士上行走` is not treated as an emperor reference.
The `聖祖` embedded in `聖祖實錄` is not independently assigned as a person.
The limited decisions retain agent-proposed status, not fictitious human review.

Evidence: preserved source revisions for ECCP A-k'o-tun and QSG volume 303.
This is not a completed review of every name, office, work or event in the book.

## Navigation

The reader uses source → subdivision → entry. ECCP uses the original alphabetical
ordering; QSG uses 25-volume ranges and a separate selected-accounts group.
Printed cross-reference slips do not appear as reading entries. Unique print
references route to the substantive source; alternative labels remain searchable.
Multi-person references lead to catalogue choices rather than merging people.
Unresolved destinations remain unresolved. Archival copies stay in the source
inventory so import-completeness checks still cover all captured pages.

## Continuing the review

For the next complete biography, inspect the review queue and original passage,
restore only supported identifications, and retain reasons for changed decisions.
Preserve stable mention IDs when restoring a withdrawn link. Update the active
mention index, working source checksum and work backlinks together; remove an
accepted candidate from quarantine only after its evidence has been recorded.
Run corpus, work, name-history and full-inventory checks and rebuild reading
indexes. The full Pages suite must pass before describing the change as live.
