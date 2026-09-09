# 人文 · Ren-Wen

**以文識人，因人讀文。**

介面預設繁體中文，頁首可切換 **中文 / English**。ECCP 等原文保持原語言；姓名、字號、書名、年號與干支在英文介面中仍予保留。選擇會於閱讀器、人物頁與著作頁間沿用。詳見 [介面語言說明](docs/language.md)。

*People through texts. Texts in context.*

Ren-Wen connects historical texts and people through source-linked biographies, annotated editions, timelines, and maps. 人 and 文 are equal pillars: a person is not reducible to one biography, and a text is not reducible to the facts extracted from it.

[Open the reader](https://liuyao12.github.io/ren-wen/) · [People](https://liuyao12.github.io/ren-wen/profiles.html) · [Works](https://liuyao12.github.io/ren-wen/works.html)

## ECCP 全書第一輪

開啟 **[傳記目錄](https://liuyao12.github.io/ren-wen/library.html)**，依中文名、原書英文拼寫或縣名搜尋。
已保存來源清單中全部 **1,008 頁：809 篇敘事傳記、193 篇參見條目及 6 篇編輯／參考資料**。
正文、引文、書目和署名均保留；文字完整性與身分標註覆核分開記錄。

目前有 **6,879 筆人物記錄、9,036 筆著作／書名候選記錄、63,716 處標註**。
這些數字不是已人工消歧的不同人物或著作總數。未知人物也有來源限定的簡略檔案；
未配對的 CBDB/Geni ID、中曆生卒年、民籍或佐領資訊不補造。

《清史稿》共 **789 個開頭定位候選**，所在 **235 卷完整文字** 已保存。
開頭配對仍待逐項核查；本紀另以「諱」字下的本人姓名建立配對候選。
未匹配不表示此人沒有本傳，且本紀、附傳、其他人物本傳中的記載不可混稱。

- 人名滑出選單可前往人物頁或 ECCP 本傳，原文異名與參見標記不改寫。
- 姓名採 **[縣名或氏族] 姓名（字或號）**，例如 **[湘鄉] 曾紀澤（劼剛）**、**[完顏] 崇厚（地山）**。
  完整籍貫、旗籍和佐領原文另列來源。氏族不是地理位置。
- 原文在左半，家屬年表和互動地圖在右半。政區圖為有明確參考年份和區域範圍的歷史插圖，
  不是任意敘事年份的精確行政區界。行跡線不冒充實際道路或航線。
- 引文有自己的文本記錄和出現位置，但完整保留於包含文本中。

詳見 **[第一輪範圍、來源及覆核規則](docs/eccp-round1.md)**、[文本層次](docs/text-layers.md)、
[歷史參考地圖](docs/reference-maps.md)和[家族閱讀布局](docs/family-reader.md)。

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

## Complete entry and layered texts

The current landing entry is **曾國藩 / Tsêng Kuo-fan**: all 17 ECCP paragraphs,
including the bibliography and Têng Ssŭ-yü's byline. Five complete ECCP entries
are now available. The existing 《清史稿》曾紀澤 account has also been restored
without the formerly omitted memorial. [Text units](texts.html) retain quoted
readings inside their original context while giving them reusable identities.
See [text layers](docs/text-layers.md).

The interactive map now includes actual **cropped, attributed 1820/1911 reference
map images** of the middle/lower Yangtze corridor. Province, prefecture, and
(for 1911) county outlines appear with zoom. These are explicitly dated snapshots,
not boundaries for every reading year, and not nationwide coverage. No CHGIS
source vector files are redistributed. See [map scope and terms](docs/reference-maps.md).

For bulk imports also run `python -m scripts.round1_validate`. Rebuild derived reading bundles with `python -m scripts.reading_indexes`.
