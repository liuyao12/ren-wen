# ctext adapter: contract and current status

## Implemented now

The browser can open a local UTF-8 XML file, reject DTD/entity declarations and malformed XML, report its element counts, display it inertly and download the **original bytes unchanged**. The Python tool can stage those bytes with a source URL, rights note, checksum and `unverified` semantic status:

```sh
python scripts/renwen.py inspect-xml exported.xml
python scripts/renwen.py ctext-stage exported.xml --output imports/local/example \
  --source-url 'https://ctext.org/...' --rights-note 'Record actual applicable permission here'
```

Files in `imports/local/` are ignored by Git. Raw staging/inspection is not semantic compatibility, an annotation editor for ctext XML, or an upstream publishing mechanism.

## First integration test

ctext's annotation client documents XML export: https://ctext.org/instructions/annotation/client . Donald Sturgeon's course page links a real sample that can be opened locally in that client: https://dsturgeon.net/esscs/ and https://dsturgeon.net/textfiles/qidan-guozhi1.xml . The sample was identified, but its actual XML bytes were **not retrieved/inspected during repository setup**. No substitute fixture is presented as a genuine ctext export.

Obtain a permitted actual export; record its provenance; inventory the schema and mixed-content structure. Establish tests for dates, entities, confirmed/proposed state, unknown attributes/elements, source IDs, whitespace and punctuation. An unchanged round trip must preserve the original bytes. An edited round trip must preserve unrelated content and unknown fields, and reopen correctly in ctext's own client. Retain raw XML alongside any reader projection.

Do not define or guess ctext XML tags from the categories visible in its interface. Reader-side HTML spans are not a claim about ctext's interchange language.

## Upstream contribution queue

Future contributions should separate text/punctuation edits, occurrence annotations and shared Data Wiki entity changes. Record imported baseline, proposed patch, evidence and review. Check for intervening upstream edits before submission. Local acceptance does not imply ctext acceptance.

A supported authenticated submission interface and applicable permissions remain to be verified. The browser contains no ctext credentials and currently makes no upstream writes. A contribution package must not be described as published until the remote service confirms it.
