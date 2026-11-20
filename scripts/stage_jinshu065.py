"""Stage Ren-Wen's edited Jinshu 65 against the CBR release being published."""

import json
from pathlib import Path
import sys


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def stage(site, renwen):
    name = "jinshu/065.json"
    output = site / "data/corpus" / name
    editorial = read(renwen / "corpus" / name)
    baseline = read(output)
    for key in ("id", "work_id", "book_id", "source_id", "source", "text_sha256"):
        require(editorial[key] == baseline[key], f"CBR and Ren-Wen disagree on {key}")
    baseline_passages = {p["id"]: p["text"] for p in baseline["paragraphs"]}
    require([(p["id"], p["text"]) for p in editorial["paragraphs"]] == list(baseline_passages.items()),
            "The fixed volume text or paragraph order changed")
    mentions = {}
    for paragraph in editorial["paragraphs"]:
        end = 0
        for mention in paragraph["mentions"]:
            start, stop = mention["start"], mention["end"]
            require(mention["id"] not in mentions and end <= start < stop <= len(paragraph["text"])
                    and paragraph["text"][start:stop] == mention["surface"],
                    f"Invalid Ren-Wen mention {mention['id']}")
            person = mention.get("person_id")
            if person:
                require((site / "data/corpus/profiles" / f"{person}.json").is_file(), f"Missing CBR profile {person}")
            mentions[mention["id"]] = mention
            end = stop

    works = {w["id"]: w for w in read(site / "data/corpus/works.json")["works"]}
    routes = read(renwen / "corpus/jinshu/065-biographies.json")
    require(routes, "Confirm at least one biography link")
    for route in routes:
        source = mentions[route["mention_id"]]
        require(source["kind"] == "person" and source["person_id"] == route["person_id"], "Biography source identity mismatch")
        target = route["target"]
        index = read(site / works[target["work_id"]]["catalog_path"])
        entry, = [ch for ch in index["chapters"] if ch["chapter_id"] == target["chapter_id"] and ch["book_id"] == target["book_id"]]
        chapter = read(site / entry["path"])
        passage, = [p for p in chapter["paragraphs"] if p["id"] == target["paragraph_id"]]
        target_mention, = [m for m in passage["mentions"] if m["id"] == target["mention_id"]]
        require(target_mention["person_id"] == route["person_id"], f"Biography target identity mismatch: {route['label']}")
        source.setdefault("editorial_biographies", []).append({"label": route["label"], "target": target})
    output.write_text(json.dumps(editorial, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Ren-Wen: {len(baseline_passages)} paragraphs, {len(mentions)} mentions, {len(routes)} biography links")


if __name__ == "__main__":
    stage(Path(sys.argv[1]), Path(__file__).resolve().parents[1])
