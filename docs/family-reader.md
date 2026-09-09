# Family-first reading layout

The desktop reader uses equal left/right columns. The complete text occupies the left
column; the timeline is above the map on the right. Each pane scrolls independently.
The source, timeline year and map camera remain separate state; expanding the timeline
never changes the map's extent. Narrow screens use text, timeline, map in vertical order.

## Hierarchy and focus

`familyHierarchy` reads evidence-bearing `child-of` and spouse assertions from the
catalogue, including references established in another account. It does not infer
kinship from surnames. Rejected/superseded assertions and missing person IDs are excluded.
A two-step parent chain supplies the grandparent tier without adding a new historical
assertion. Grandparents, parents, subject, spouses and children stay in that order.
Spouses are symmetric; a spouse line is not a dated marriage. Missing relatives are
not replaced by invented names or placeholder lifespans. Within a tier, source-record
order is stable and does not purport to establish sibling seniority.

With **隨段落聚焦** enabled, the subject always stays visible. Relatives named in the active
paragraph retain individual rows. Inactive relatives fold into one grey band per tier,
with miniature bars for individually known lifespans and all names available on expansion.
This keeps the family together above the paragraph's other figures while reclaiming
vertical space near the subject. **展開家屬** shows every family member. **其餘人物** exposes
other people from the source without attributing a family relationship to them.

Parent–child lines follow the moving rows. They use a child's birth year only when both
individual rows and compatible lifespan endpoints are available; otherwise the relation
is drawn in the margin. The collapsed family band is not an aggregate lifespan or a new
event. Evidence is available in **親屬關係出處**. The source-wide year scale remains fixed
while rows change, so vertical regrouping cannot move dates horizontally.

## Tests

`node --test tests/family-layout.test.mjs` checks generational ordering, spouses,
evidence filtering, compact tiers, active adjacency and the existing Zeng records.

`python tests/browser_family_layout.py` exercises in-memory local fixtures. The same
script with `--url https://liuyao12.github.io/ren-wen/` checks a real deployment, including
actual paragraph scrolling, family connectors, both languages, unchanged source text,
map dragging/zoom/county layer visibility and desktop/tablet/mobile layout.

Movement respects the operating system's reduced-motion preference:
https://www.w3.org/WAI/WCAG22/Techniques/css/C39
