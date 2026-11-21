import json
from pathlib import Path
import tempfile
import unittest

from scripts.stage_jinshu065 import stage


class ReviewedJinshuTest(unittest.TestCase):
    def test_reviewed_names_survive_staging_and_stale_links_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = Path(tmp) / "site"
            editorial = Path(tmp) / "renwen"

            def write(root, path, payload):
                output = root / path
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(json.dumps(payload), encoding="utf-8")

            def mention(id, person_id, start, surface):
                return dict(id=id, person_id=person_id, start=start,
                            end=start + len(surface), surface=surface, kind="person")

            mentions = [mention("m1", "person1", 0, "甲"), mention("m2", "person2", 1, "乙")]
            chapter = {
                "id": "c-jinshu-065-x", "work_id": "w-jinshu", "book_id": "b-jinshu-065",
                "source_id": "s0", "source": {}, "text_sha256": "fixture",
                "annotation": {"status": "reviewed"},
                "paragraphs": [{"id": "p0", "text": "甲乙", "mentions": mentions[:1]}],
            }
            write(site, "data/corpus/jinshu/065.json", chapter)
            old = dict(chapter, annotation={"status": "in_progress"},
                       paragraphs=[dict(chapter["paragraphs"][0], mentions=mentions)])
            write(editorial, "corpus/jinshu/065.json", old)
            write(site, "data/corpus/profiles/person1.json", {})
            write(site, "data/corpus/works.json", {"works": [{"id": "w-target", "catalog_path": "catalog.json"}]})
            target = dict(work_id="w-target", chapter_id="c-target", book_id="b-target",
                          paragraph_id="p1", mention_id="target1")
            write(site, "catalog.json", {"chapters": [dict(target, path="target.json")]})
            write(site, "target.json", {"paragraphs": [{"id": "p1", "mentions": [{"id": "target1", "person_id": "person1"}]}]})
            write(editorial, "corpus/jinshu/065-biographies.json", [
                dict(mention_id=mid, person_id=person, label=mid, target=target)
                for mid, person in (("m1", "person1"), ("m2", "person2"))
            ])

            stage(site, editorial)
            output = json.loads((site / "data/corpus/jinshu/065.json").read_text())
            kept = output["paragraphs"][0]["mentions"]
            self.assertEqual([m["id"] for m in kept], ["m1"])
            self.assertEqual(kept[0].pop("editorial_biographies"), [{"label": "m1", "target": target}])
            self.assertEqual(output, chapter)
