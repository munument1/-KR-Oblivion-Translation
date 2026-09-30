from __future__ import annotations
import csv, json, importlib.util
from pathlib import Path

REPO = Path(r"C:\\오블리비언")
ROOT = REPO / "v2_work"
QDIR = ROOT / "08_compare_review" / "00_inputs"
MODPATH = REPO / "v2_tools" / "build_translation_batches.py"
spec = importlib.util.spec_from_file_location("bt", MODPATH)
bt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bt)
exact, override = bt.load_glossary()
index = bt.build_glossary_index(override)

def hits(text):
    return bt.glossary_hits(text or "", exact, index)

def hint(old, cand, hs):
    targets = [h.get("target", "") for h in hs if h.get("target")]
    if not targets:
        return ""
    old_ok = all(t in (old or "") for t in targets)
    new_ok = all(t in (cand or "") for t in targets)
    if new_ok and not old_ok: return "NEW_GLOSSARY_MATCH"
    if old_ok and not new_ok: return "OLD_GLOSSARY_MATCH"
    if old_ok and new_ok: return "BOTH_GLOSSARY_MATCH"
    return "GLOSSARY_UNRESOLVED"

def refresh_master():
    p = QDIR / "MASTER_COMPARE_QUEUE.csv"
    with p.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
        fields = list(rows[0].keys())
    changed = 0
    for r in rows:
        hs = hits(r.get("source_english", ""))
        new_json = json.dumps(hs, ensure_ascii=False, separators=(",", ":"))
        if r.get("glossary_json", "") != new_json:
            changed += 1
        r["glossary_json"] = new_json
        r["glossary_hint"] = hint(r.get("old_1_0_2",""), r.get("prior_sol_candidate") or r.get("new_gemini",""), hs)
    with p.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)
    return len(rows), changed

def refresh_books():
    p = QDIR / "BOOK_COMPARE_QUEUE.csv"
    with p.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
        fields = list(rows[0].keys())
    if "active_glossary_json" not in fields:
        fields.insert(6, "active_glossary_json")
    if "glossary_hint" not in fields:
        fields.insert(7, "glossary_hint")
    for r in rows:
        hs = hits(r.get("source_english", ""))
        r["active_glossary_json"] = json.dumps(hs, ensure_ascii=False, separators=(",", ":"))
        r["glossary_hint"] = hint(r.get("old_1_0_2",""), r.get("prior_sol_candidate") or r.get("new_gemini",""), hs)
    with p.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)
    return len(rows)

if __name__ == "__main__":
    m_total, m_changed = refresh_master()
    b_total = refresh_books()
    print(json.dumps({
        "master_rows": m_total,
        "master_glossary_rows_changed": m_changed,
        "book_rows": b_total,
    }, ensure_ascii=False, indent=2))
