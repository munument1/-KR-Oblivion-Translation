from __future__ import annotations
import csv, json, re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO/"v2_work"
OUT = ROOT/"08_compare_review"/"00_inputs"
OLD_CSV = REPO/"applied_translations_v2.csv"
OUT.mkdir(parents=True, exist_ok=True)

def norm(v):
    return (v or "").strip()

def load_old():
    exact, loose, cross_exact, cross_loose = {}, {}, {}, {}
    with OLD_CSV.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            k = (norm(r["effective_source"]), norm(r["record_type"]),
                 norm(r["raw_formid"]).upper(), norm(r["field"]),
                 norm(r["old_english"]))
            exact[k] = r["new_korean"]
            loose.setdefault(k[:4], []).append(r)
            ck = (k[1], k[2], k[3], k[4])
            cross_exact.setdefault(ck, []).append(r)
            cross_loose.setdefault(ck[:3], []).append(r)
    return exact, loose, cross_exact, cross_loose

def old_for(x, exact, loose, cross_exact, cross_loose):
    k = (norm(x.get("source_file")), norm(x.get("record_type")),
         norm(x.get("formid")).upper(), norm(x.get("field")),
         norm(x.get("source_english")))
    if k in exact:
        return exact[k]
    rows = loose.get(k[:4], [])
    same = [r for r in rows if norm(r.get("old_english")) == k[4]]
    if len(same) == 1:
        return same[0]["new_korean"]
    if len(rows) == 1:
        return rows[0]["new_korean"]
    ck = (k[1], k[2], k[3], k[4])
    rows = cross_exact.get(ck, [])
    if len(rows) == 1:
        return rows[0]["new_korean"]
    rows = cross_loose.get(ck[:3], [])
    same = [r for r in rows if norm(r.get("old_english")) == k[4]]
    if len(same) == 1:
        return same[0]["new_korean"]
    return rows[0]["new_korean"] if len(rows) == 1 else None

def load_items(folder):
    out = {}
    for p in sorted(folder.glob("*.json")):
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        rows = obj if isinstance(obj, list) else obj.get("items", [])
        for x in rows:
            if isinstance(x, dict) and x.get("id"):
                out[x["id"]] = x
    return out

def load_translations(folder):
    out = {}
    for p in sorted(folder.glob("*.json")):
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        rows = obj if isinstance(obj, list) else (obj.get("translations") or obj.get("results") or [])
        for x in rows:
            if isinstance(x, dict) and x.get("id") and isinstance(x.get("korean"), str):
                out[x["id"]] = x["korean"]
    return out

def glossary_hint(old, new, hits):
    targets = [h.get("target","") for h in hits if h.get("target")]
    if not targets:
        return ""
    old_ok = all(t in old for t in targets)
    new_ok = all(t in new for t in targets)
    if new_ok and not old_ok:
        return "NEW_GLOSSARY_MATCH"
    if old_ok and not new_ok:
        return "OLD_GLOSSARY_MATCH"
    if old_ok and new_ok:
        return "BOTH_GLOSSARY_MATCH"
    return "GLOSSARY_UNRESOLVED"

exact, loose, cross_exact, cross_loose = load_old()
categories = [
    ("generic", ROOT/"03_translation_json", ROOT/"04_gemini_raw"),
    ("dialogue", ROOT/"03_translation_json_dialogue_backfill", ROOT/"04_gemini_raw_dialogue_backfill"),
    ("dial", ROOT/"03_translation_json_dial_backfill", ROOT/"04_gemini_raw_dial_backfill"),
    ("quest", ROOT/"03_translation_json_quest_backfill", ROOT/"04_gemini_raw_quest_backfill"),
]
prior_review = {}
prior_review.update(load_translations(ROOT/"05_sol_review"/"dialogue_backfill_sol_reviewed"))

master = {}
for category, src_dir, cand_dir in categories:
    items = load_items(src_dir)
    candidates = load_translations(cand_dir)
    for rid, x in items.items():
        new = candidates.get(rid)
        old = old_for(x, exact, loose, cross_exact, cross_loose)
        # New v2 work must not be dropped merely because the frozen v1 table
        # has no baseline row (QUST/CNAM is the major case).  v1 is only a
        # comparison aid, never a prerequisite for accepting new translation.
        if not new or (old is not None and old.strip() == new.strip()):
            continue
        prior = prior_review.get(rid, "")
        hits = x.get("glossary_hits", [])
        master[rid] = {
            "category": category, "id": rid, "record_type": x.get("record_type",""),
            "field": x.get("field",""), "editor_id": x.get("editor_id",""),
            "source_english": x.get("source_english",""), "old_1_0_2": old or "",
            "new_gemini": new, "prior_sol_candidate": prior,
            "glossary_hint": glossary_hint(old or "", prior or new, hits),
            "context_json": json.dumps(x.get("context",{}), ensure_ascii=False, separators=(",",":")),
            "glossary_json": json.dumps(hits, ensure_ascii=False, separators=(",",":")),
            "status": "PENDING", "sol_decision": "", "sol_final": "", "notes": "",
        }

fields = ["category","id","record_type","field","editor_id","source_english",
          "old_1_0_2","new_gemini","prior_sol_candidate","glossary_hint",
          "context_json","glossary_json","status","sol_decision","sol_final","notes"]
master_path = OUT/"MASTER_COMPARE_QUEUE.csv"
with master_path.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(sorted(master.values(), key=lambda r:(r["category"], r["id"])))

# BOOK queue: compare v1.0.2 against reconstructed Gemini, preserving prior Sol reviews.
book_sources = {}
for p in sorted((ROOT/"03_translation_json_books").glob("*.json")):
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        continue
    books = obj.get("books", []) if isinstance(obj, dict) else []
    if not isinstance(books, list):
        continue
    for b in books:
        source = "\n\n".join(seg.get("text","") for seg in b.get("segments", []))
        parts = b["id"].split("|")
        book_sources[b["id"]] = {
            "id": b["id"], "source_file": parts[0], "record_type": parts[1],
            "formid": parts[2], "field": parts[3], "source_english": source,
            "editor_id": b.get("editor_id","")
        }

book_new = load_translations(ROOT/"05_sol_review"/"books_reconstructed")
book_prior = load_translations(ROOT/"05_sol_review"/"books_sol_reviewed")
book_rows = []
for rid, x in book_sources.items():
    new = book_new.get(rid)
    old = old_for(x, exact, loose, cross_exact, cross_loose)
    # BOOK/DESC may also have no v1 baseline; keep new v2 work for review.
    if not new or (old is not None and old.strip() == new.strip()):
        continue
    book_rows.append({
        "id": rid, "editor_id": x["editor_id"], "source_english": x["source_english"],
        "old_1_0_2": old or "", "new_gemini": new,
        "prior_sol_candidate": book_prior.get(rid, ""),
        "status": "PENDING", "sol_decision": "", "sol_final": "", "notes": "",
    })

book_fields = ["id","editor_id","source_english","old_1_0_2","new_gemini",
               "prior_sol_candidate","status","sol_decision","sol_final","notes"]
book_path = OUT/"BOOK_COMPARE_QUEUE.csv"
with book_path.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=book_fields)
    w.writeheader()
    w.writerows(sorted(book_rows, key=lambda r:r["id"]))

report = {
    "master_compare_rows": len(master),
    "book_compare_rows": len(book_rows),
    "prior_dialogue_sol_candidates": sum(1 for r in master.values() if r["prior_sol_candidate"]),
    "prior_book_sol_candidates": sum(1 for r in book_rows if r["prior_sol_candidate"]),
    "baseline": "git tag v1.0.2",
}
(OUT/"MASTER_COMPARE_REPORT.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
print(master_path)
print(book_path)
