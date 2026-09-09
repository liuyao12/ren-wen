# Historical reference maps and camera correction

## What was wrong

A Chrome check on the actually deployed Chinese interface found working zoom,
but dragging at the full overview was clamped to the same camera bounds. It also
confirmed **zero historical boundary shapes**. The prior cascading hierarchy
controls did not constitute a boundary map.

The map now starts in the biography's middle/lower Yangtze region, permits bounded
overscroll even at world overview, and supports county-scale zoom. Drag, wheel,
pinch, keyboard arrows, double-click and explicit controls remain available.
Home returns to the regional view; World overview shows the overseas context.
The modern low-resolution land backdrop is muted at regional historical scales.

## Actual image layers, not empty controls

The five images in `assets/maps/` are **cropped CHGIS V6 map illustrations**:

- 1820: province and prefecture outlines.
- 1911: province, prefecture and county outlines.

Coverage is **108–123°E, 24–35°N**, not the whole country. Some peripheral
jurisdictions are cut by the crop; the crop edges are not drawn as boundaries.
At 1911, automatic detail reveals prefectures below 18 degrees of map width and
counties below 7 degrees. Province outlines remain visible. Manual level
selection is also possible. At 1820 there is **no county polygon layer**: the UI
says so and offers the 1911 reference, rather than inventing counties.

The selector defaults to **1911, explicitly labeled as a reference snapshot**.
It is independent of the narrative year. Reading an event in 1854 or 1878 does
not relabel the map as boundaries for that year. These are not interpolated
boundaries and not modern borders passed off as Qing data. The source-specific
jurisdiction hierarchy remains a separate, partial scholarly assertion layer.

These images support interactive viewing but are not clickable vector polygons.
Sourced journey arcs and city points retain their original meaning. Route lines
are schematic stop-order connections, not reconstructed historical routes.

## Rights and provenance

Dataset landing-page CC0 metadata conflicts with the more specific CHGIS file
EULA. This project follows the **file-level terms**, not the permissive metadata.
EULA §4 permits attributed digital map images and portions in academic use;
§5 prohibits republication of entire datasets and unauthorized redistribution.

Only a geographically limited academic map illustration is published here.
**No SHP, DBF, source ZIP, or CHGIS vector geometry is redistributed.** Input ZIPs
were held in a temporary build directory and discarded after rendering. The
images are not relicensed as MIT or CC0. Full attribution is displayed in the
map's attribution section, copied below, and recorded in the manifest:

> CHGIS Version 6. © Fairbank Center for Chinese Studies and the Institute for
> Chinese Historical Geography at Fudan University, Dec 2016.

Terms: `assets/maps/CHGIS-V6-EULA.txt`, obtained from
https://dataverse.harvard.edu/api/access/datafile/2966703 .

`data/reference-maps.json` records each input URL/file ID and SHA-256, output
hash, snapshot year, crop and rendering modifications. Province labels preserve
the dataset's Chinese forms; they are part of the image, not editorial text.
Further or commercial use must respect the source terms.

Offline preparation used GeoPandas/Pillow; the browser requires neither, nor an
external map service. The published application loads only the derived PNGs.
The import and image-build workflows preserve the inputs or outputs appropriate
to their respective rights, and never change main without explicit promotion.
