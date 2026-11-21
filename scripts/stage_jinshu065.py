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
    reviewed = baseline.get("annotation", {}).get("status") == "reviewed"
    fixed_fields = ("id", "work_id", "book_id", "source_id", "source", "text_sha256")
    if reviewed and any(editorial[key] != baseline[key] for key in fixed_fields):
        print("Ren-Wen: preserving the reviewed CBR chapter with its updated source.")
        return
    for key in fixed_fields:
        require(editorial[key] == baseline[key], f"CBR and Ren-Wen disagree on {key}")
    baseline_passages = [(p["id"], p["text"]) for p in baseline["paragraphs"]]
    require([(p["id"], p["text"]) for p in editorial["paragraphs"]] == baseline_passages,
            "The fixed volume text or paragraph order changed")
    published = baseline if reviewed else editorial
    mentions = {}
    for paragraph in published["paragraphs"]:
        end = 0
        for mention in paragraph["mentions"]:
            start, stop = mention["start"], mention["end"]
            require(mention["id"] not in mentions and end <= start < stop <= len(paragraph["text"])
                    and paragraph["text"][start:stop] == mention["surface"],
                    f"Invalid Jinshu mention {mention['id']}")
            person = mention.get("person_id")
            if person:
                require((site / "data/corpus/profiles" / f"{person}.json").is_file(), f"Missing CBR profile {person}")
            mentions[mention["id"]] = mention
            end = stop

    works = {w["id"]: w for w in read(site / "data/corpus/works.json")["works"]}
    routes = read(renwen / "corpus/jinshu/065-biographies.json")
    require(routes, "Confirm at least one biography link")
    accepted = 0
    for route in routes:
        source = mentions.get(route["mention_id"])
        if not source or source["kind"] != "person" or source["person_id"] != route["person_id"]:
            require(reviewed, f"Biography source identity mismatch: {route['label']}")
            continue
        target = route["target"]
        index = read(site / works[target["work_id"]]["catalog_path"])
        entry = next((ch for ch in index["chapters"] if ch["chapter_id"] == target["chapter_id"]
                      and ch["book_id"] == target["book_id"]), None)
        chapter = read(site / entry["path"]) if entry else {}
        passage = next((p for p in chapter.get("paragraphs", []) if p["id"] == target["paragraph_id"]), {})
        target_mention = next((m for m in passage.get("mentions", []) if m["id"] == target["mention_id"]), {})
        if target_mention.get("person_id") != route["person_id"]:
            require(reviewed, f"Biography target identity mismatch: {route['label']}")
            continue
        link = {"label": route["label"], "target": target}
        links = source.setdefault("editorial_biographies", [])
        if link not in links:
            links.append(link)
        accepted += 1
    output.write_text(json.dumps(published, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    version = "reviewed CBR" if reviewed else "Ren-Wen pilot"
    print(f"{version}: {len(baseline_passages)} paragraphs, {len(mentions)} mentions, {accepted}/{len(routes)} biography links")



if __name__ == "__main__":
    stage(Path(sys.argv[1]), Path(__file__).resolve().parents[1])
