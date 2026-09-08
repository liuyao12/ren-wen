# Person navigation and calendar headings

Names in the reading pane open `profiles.html#person-ID` in Ren-Wen. Each occurrence keeps its source text and stable mention ID. `assets/person-links.js` decorates the rendered document; it does not edit source snapshots, working HTML or checksums. Existing source URLs are retained as metadata and in profile evidence.

The **Review names** checkbox (or Alt-click on an annotated name) opens the existing occurrence inspector instead. Ordinary links support keyboard activation and opening a new tab. The profile selector uses hash navigation with browser Back/Forward. An unknown ID produces a not-found view, never the first person's biography.

`assets/person-display.js` supplies the same heading to the reader and profile page:

```
[湖南湘鄉] 曾紀澤（劼剛）
1839–1890 AD
生：道光十九年己亥   卒：光緒十六年庚寅   享年 52 歲
```

籍貫 remains native-place affiliation, not an inferred precise birthplace. Unknown components are omitted rather than fabricated. Zi, hao and clan/surname fields retain their types; a banner is not substituted for a native place.

## Separate calendar evidence

AD years come from `life.westernDates` or the optional `life.westernYears` list. A year-only claim has event, `calendar: "gregorian"`, integer value, source and status. It does not acquire an invented month/day. The Python validator checks its year and source. Alternative AD years remain alternatives, not an averaged or continuous date range.

Chinese dates come only from explicit `life.birth/death.chineseYear` and associated reign records. The year label means the Chinese civil year beginning in that AD year. Do not equate its boundaries with a Gregorian year. Ganzhi is derived as `(ChineseYear - 4) mod 10/12`; never pass a Gregorian event year to that function. In particular, January before Chinese New Year can have a different AD year and Chinese year. Missing Chinese-year evidence stays unresolved, and no sui is calculated from Western years alone.

Calendar reference: Hong Kong Observatory, Heavenly Stems and Earthly Branches, https://www.hko.gov.hk/en/gts/time/stemsandbranches.htm . The displayed ganzhi is a calculation, not a new source quotation.

## Reference profiles and source links

Five basic reference records accompany the existing 曾紀澤 profile: 曾國藩, 郭嵩燾, 崇厚, 馬格理 and 董恂. This supplies destinations for all personal-name links in the current ECCP excerpt, including the previously unannotated Tung Hsün reference. Their full biographies and external-ID matching remain unfinished. The new CBDB/Geni slots are explicitly not searched. Original evidence URLs and access notes are in each JSON file.

The Chinese-year labels for dated Qing records are derived only when the ECCP month is after February and consequently after the Chinese New Year. Reign labels are calendar normalizations, not quotations of Chinese dates in the English source. Macartney's ECCP mention provides Western years alone: his Chinese year endpoints remain unresolved.

Only an explicit `principal-biography` account, together with matching visible name text, may retarget an unannotated source link. A `mentioned-in-biography` relationship is excluded. Thus Macartney's occurrence opens Macartney; the Kuo Sung-tao name in the adjacent “see under” reference opens Kuo, not Macartney.

A profile can precede an occurrence annotation. SQLite indexing creates a derived person-entity projection for such a profile (e.g. 董恂), refusing to overwrite a non-person ID. JSON profiles remain authoritative. Rebuild the database from source files to remove obsolete derived entries.

## Tests

Run the existing Python and JavaScript suites. New regressions cover calendar boundaries, Chinese numeral/ganzhi formatting, year-only claims, HTML escaping, local URLs, missing profiles and reference identities.

Optional browser DOM integration (Playwright and Chromium):

```
python tests/browser_person_navigation.py
```

It supplies local data via an in-memory fetch fixture, preserves original occurrence text, exercises review mode and source replacement, and verifies hash navigation and history. It is not a live-network deployment test.
