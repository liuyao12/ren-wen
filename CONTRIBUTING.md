# Contributing

Use a branch and pull request for substantial changes. Small evidence-backed data patches are preferable to opaque wholesale rewrites. Describe what changed, its evidence, and any affected interpretations.

## Run and test

```sh
python -m http.server 8000
python scripts/renwen.py validate
python -m unittest discover -s tests -v
npm test
npm run check
python scripts/renwen.py build-db
```

The reader works without installing Python or JavaScript packages. Optional browser tests need Playwright and Chromium:

```sh
python -m pip install playwright
python -m playwright install chromium
python tests/browser_smoke.py http://127.0.0.1:8000
```

`CHROMIUM_EXECUTABLE` selects an existing Chromium executable. `RENWEN_OFFLINE=1` uses an in-memory local fixture instead of navigating to a server; this checks interactions, not HTTP loading. `RENWEN_SCREENSHOT=build/reader.png` saves a desktop screenshot. The normal server-based mode remains the deployment-relevant smoke test.

## Identification proposals

Select an annotated occurrence, inspect its evidence, choose a candidate, and explain the correction. The browser queues a proposal; it does not edit the accepted corpus or publish upstream. Export the queue as JSON.

```sh
python scripts/renwen.py validate-proposals proposals.json
python scripts/renwen.py apply-proposals proposals.json --reviewer "Actual reviewer"
python scripts/renwen.py validate
git diff
```

Only claim a human review when that person actually reviewed it. A source hash, the original identification, existing target ID and meaningful explanation are required. Stale or competing changes are refused. Accepted changes update working HTML, the mention index, checksums and `data/reviews.jsonl`; imported baselines stay untouched. Multi-file writes are not a filesystem transaction: work in a branch and use a reviewed Git commit as the publication boundary.

## Sources, editions and punctuation

Record bibliographical identity, the actual import method, source URL/revision, retrieval date, rights and punctuation provenance. Never label manually prepared excerpts as a raw API export or a complete biography. When the printed base edition is unknown, say so.

Compare incoming source corrections with the saved unannotated baseline and our working version. The `merge` command makes a candidate file, never silently applies it. Different historical editions and quotations are separate witnesses; a biography in another work is another account, not automatically a textual variant.

## Present limits

The seed annotations and events are proposals, not independently human-reviewed facts. No historical jurisdiction geometry is included. ctext XML support is raw staging/inspection only; submit a legally reusable real export fixture and its provenance before adding semantic mapping. Never commit API tokens or third-party data with unresolved redistribution rights.
