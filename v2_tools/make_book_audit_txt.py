import json, re, sys
from pathlib import Path

BASE = Path(r"C:\\오블리비언\\v2_work\\08_compare_review\\02_sol_review")
input_name = sys.argv[1] if len(sys.argv) > 1 else "NEXT_BOOK_BATCH_10.json"
prefix = sys.argv[2] if len(sys.argv) > 2 else "AUDIT"
rows = json.loads((BASE / input_name).read_text(encoding="utf-8"))

def clean(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = s.replace("\\r", " ")
    s = re.sub(r"\\s+", " ", s)
    return s.strip()

for idx, r in enumerate(rows, 1):
    src = [x.strip() for x in r["source_english"].split("\n\n") if x.strip()]
    old = clean(r["old_1_0_2"])
    candidate_raw = r.get("prior_sol_candidate") or r.get("new_gemini", "")
    sol = clean(candidate_raw)
    out = [
        "ID: " + r["id"],
        "EDITOR: " + r["editor_id"],
        f"SOURCE_PARAGRAPHS: {len(src)}",
        f"OLD_LEN: {len(old)} SOL_LEN: {len(sol)}",
        "",
    ]
    for i, p in enumerate(src, 1):
        out.append(f"[SRC {i}] {p}")
    out += ["", "[OLD CLEAN]", old, "", "[SOL CLEAN]", sol]
    (BASE / f"{prefix}_{idx:02d}.txt").write_text("\n".join(out), encoding="utf-8")
print("written", len(rows))
