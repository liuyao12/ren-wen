# Person records

Read ../../docs/people.md before adding or editing a profile. Work through ECCP one biography at a time. Keep the same local person ID across sources.

Canonical name: [籍貫] 姓名（字或號）. Store its components separately; preserve the distinction between zi and hao and between native place and birthplace. Do not rewrite source wording to match the display name.

Use sourced Chinese civil-year labels for birth/death and sui calculation. Preserve Western dates as separate source claims; do not silently reuse Gregorian years or infer exact years from uncertain ages. Unknowns remain null.

Keep CBDB and Geni identifiers as strings with matching evidence and status. Geni supplies genealogical leads, not blanket verification of every relationship. Never invent human approval, missing identities or dates. Run python scripts/profiles.py validate from the repository root, plus the Python and JavaScript tests. Rebuild the corpus SQLite DB and run profiles.py index-db; never edit SQLite as an independent authority.
