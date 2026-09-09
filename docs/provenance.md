# Data provenance, punctuation and rights

The software license does not relicense source texts, contributed transcriptions, annotations, or geographic data.

## Pilot texts

The seed contains **selected paragraphs**, manually prepared from the rendered Wikisource pages consulted on 2026-09-08. It is not a complete biography, a raw HTML/API download, a scan transcription freshly made by Ren-Wen, or an independently human-reviewed critical edition. Paragraph IDs retain gaps, and the interface marks omissions. Markup wrappers and normalized whitespace/small-cap presentation are local; wording, selected italics and original cross-reference destinations are retained.

### ECCP: Tsêng Chi-tsê / 曾紀澤

- Work: Arthur W. Hummel, ed., *Eminent Chinese of the Ch'ing Period* (1943); entry by Tu Lien-chê.
- Reading page: https://en.wikisource.org/wiki/Eminent_Chinese_of_the_Ch%27ing_Period/Ts%C3%AAng_Chi-ts%C3%AA
- Recorded revision: https://en.wikisource.org/w/index.php?oldid=11365218
- Scope: seven selected paragraphs. Existing `[q.v.]` and `see under` references are preserved. Macartney's cross-reference to Kuo Sung-tao is not an identification of those two people.
- The source's printed death-day wording is not silently corrected; the pilot lifespan display uses years only. Likewise the reading `Livadis` is preserved in the excerpt.
- Wikisource marks the underlying work as a US government public-domain work. Attribution to the authors/editors and Wikisource contributors is retained; any separately applicable contributor transcription/markup rights remain under Wikisource's stated CC BY-SA terms, not MIT.
- Additional lifespan references: https://en.wikisource.org/wiki/Eminent_Chinese_of_the_Ch%27ing_Period/Ts%C3%AAng_Kuo-fan and https://en.wikisource.org/wiki/Eminent_Chinese_of_the_Ch%27ing_Period/Kuo_Sung-tao . Those entries are linked, not copied in full.

### 清史稿 卷446: 曾紀澤

- Work: 趙爾巽等，《清史稿》卷446.
- Reading page: https://zh.wikisource.org/wiki/%E6%B8%85%E5%8F%B2%E7%A8%BF/%E5%8D%B7446
- Recorded revision: https://zh.wikisource.org/w/index.php?oldid=2640966
- Scope: three selected paragraphs; the long intervening memorial is omitted.
- Printed base edition: **not yet identified**. Do not infer it from the work title or volume number.
- Punctuation is taken from the Wikisource transcription; the particular punctuator is not identified. Hiding it does not reconstruct a diplomatic facsimile.
- The page marks the underlying work public domain (PD-old). Applicable Wikisource contributor/transcription terms and attribution remain separate from the software license.

The revision identifiers record the pages consulted. They do not prove that historical rendered transclusions can be reconstructed from a containing page's revision alone. A future automated importer must track content-bearing dependencies and preserve its actual raw response.

## Local annotations and historical assertions

The 34 seed mention links and 12 events were prepared for this pilot with direct paragraph references and are labelled `proposed`. They are not represented as ctext/CBDB imports or as user-approved scholarship. Year-scale normalizations preserve the original expression and any inference note. Chinese regnal years are indexed coarsely by associated Western year, not converted to exact whole Gregorian-year intervals.

Modern reference coordinates are rounded points linked to their Wikidata place records. They are not historical jurisdictions, exact historical seats, or proof that a person was present. 湘鄉 is deliberately unlocated in this seed rather than assigning an unjustified historic point.

## Map backdrop

`assets/land.svg` was derived from the locally installed `pyogrio` test fixture `naturalearth_lowres/naturalearth_lowres.shp`. Its embedded release version was not established. All country geometries were dissolved, clipped to longitude -20 to 150 and latitude -5 to 75, and simplified for this overview. No political/internal administrative borders are rendered. Small islands may be omitted by simplification.

Natural Earth describes its map data as public domain: https://www.naturalearthdata.com/about/terms-of-use/ . Credit: Natural Earth. This is a **modern reference silhouette**, not a historical coastline reconstruction or a territorial claim.

## External datasets not included

No ctext corpus/export, CBDB extract, or CHGIS dataset is bundled. Their licenses and access rules must be checked per dataset and use; public accessibility is not permission to redistribute. In particular, a license stated for one ctext export type should not be assumed to cover all text/XML or images.

ctext reference documentation: https://ctext.org/instructions/annotation/client and https://ctext.org/tools/linked-open-data . CHGIS dataset information: https://chgis.fas.harvard.edu/data/chgis/v6/ .

Source URLs, revision metadata, attribution, rights notes, and checksums travel with each source in `data/catalog.json`. Corrections to those records should be reviewed like corrections to the text.

## Subsequent complete-text and map update
The original excerpt descriptions above record the initial pilot. The five ECCP entries are now complete. QSG qsg-02 is restored from revision 2640966, completing the 曾紀澤 account. The source responses, checksums and coverage are in the current catalogue. Cropped 1820/1911 CHGIS map images (not source vectors) are attributed under the file EULA; see `reference-maps.md` and `data/reference-maps.json`.
