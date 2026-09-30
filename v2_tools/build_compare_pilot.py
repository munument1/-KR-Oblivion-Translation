from __future__ import annotations
import csv, json, hashlib
from pathlib import Path

REPO = Path(r"C:\\오블리비언")
ROOT = REPO / "v2_work"
OLD_CSV = REPO / "applied_translations_v2.csv"
OUT = ROOT / "08_compare_review" / "00_inputs"
OUT.mkdir(parents=True, exist_ok=True)

CATEGORIES = [
    ("generic", ROOT/"03_translation_json", ROOT/"04_gemini_raw", 71),
    ("dialogue", ROOT/"03_translation_json_dialogue_backfill", ROOT/"04_gemini_raw_dialogue_backfill", 40),
    ("dial", ROOT/"03_translation_json_dial_backfill", ROOT/"04_gemini_raw_dial_backfill", 10),
    ("quest", ROOT/"03_translation_json_quest_backfill", ROOT/"04_gemini_raw_quest_backfill", 20),
]

def norm(v):
    return (v or "").strip()

def load_old():
    exact, loose = {}, {}
    with OLD_CSV.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            k = (norm(r["effective_source"]), norm(r["record_type"]), norm(r["raw_formid"]).upper(),
                 norm(r["field"]), norm(r["old_english"]))
            exact[k] = r["new_korean"]
            lk = k[:4]
            loose.setdefault(lk, []).append(r)
    return exact, loose

def load_sources(folder):
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

def load_candidates(folder):
    out = {}
    for p in sorted(folder.glob("*.json")):
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(obj, list):
            rows = obj
        else:
            rows = obj.get("translations") or obj.get("results") or []
        for x in rows:
            if isinstance(x, dict) and x.get("id") and isinstance(x.get("korean"), str):
                out[x["id"]] = x["korean"]
    return out

def old_for(x, exact, loose):
    k = (norm(x.get("source_file")), norm(x.get("record_type")), norm(x.get("formid")).upper(),
         norm(x.get("field")), norm(x.get("source_english")))
    if k in exact:
        return exact[k]
    candidates = loose.get(k[:4], [])
    if len(candidates) == 1:
        return candidates[0]["new_korean"]
    same = [r for r in candidates if norm(r.get("old_english")) == norm(x.get("source_english"))]
    return same[0]["new_korean"] if len(same) == 1 else None

def stable_key(row):
    raw = row["category"] + "|" + row["id"]
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

exact, loose = load_old()
picked, stats = [], {}
for category, src_dir, gem_dir, need in CATEGORIES:
    src = load_sources(src_dir)
    new = load_candidates(gem_dir)
    pool = []
    for rid, x in src.items():
        cand = new.get(rid)
        old = old_for(x, exact, loose)
        eng = x.get("source_english", "")
        if not cand or not old or cand.strip() == old.strip():
            continue
        if len(eng.strip()) < 4 or len(eng) > 1200:
            continue
        pool.append({
            "category": category, "id": rid, "source_english": eng,
            "old_1_0_2": old, "new_gemini": cand,
            "record_type": x.get("record_type", ""), "field": x.get("field", ""),
            "editor_id": x.get("editor_id", ""),
            "context_json": json.dumps(x.get("context", {}), ensure_ascii=False, separators=(",", ":")),
            "glossary_json": json.dumps(x.get("glossary_hits", []), ensure_ascii=False, separators=(",", ":")),
        })
    pool.sort(key=stable_key)
    chosen = pool[:need]
    picked.extend(chosen)
    stats[category] = {"eligible": len(pool), "picked": len(chosen)}

fields = ["category","id","record_type","field","editor_id","source_english",
          "old_1_0_2","new_gemini","context_json","glossary_json"]
csv_path = OUT / "COMPARE_PILOT_100.csv"
with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(picked)

summary = {
    "baseline": "git tag v1.0.2 / applied_translations_v2.csv",
    "candidate": "Gemini v2 raw outputs",
    "total": len(picked),
    "categories": stats,
    "decision_labels": ["KEEP_OLD", "USE_NEW", "REVIEW"],
    "priority": ["meaning fidelity", "locked terminology", "speaker/context tone", "natural Korean"],
}
(OUT/"COMPARE_PILOT_100_REPORT.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
print(csv_path)
