from __future__ import annotations
import csv,json
from pathlib import Path
REPO=Path(r"C:\오블리비언")
OUT=REPO/"v2_work"/"06_build_inputs"
OUT.mkdir(parents=True,exist_ok=True)
rows=[]
with (REPO/"menu_gmst_existing_105.csv").open(encoding="utf-8-sig",newline="") as f:
    for r in csv.DictReader(f):
        rows.append({"formid":r["raw_formid"].upper().removeprefix("0X"),"editor_id":r["editor_id"],
                     "source_english":r["old_english"],"korean":r["new_korean"],
                     "reuse_source":"v1.0.2_existing_gmst"})
with (REPO/"menu_gmst_new_821.csv").open(encoding="utf-8-sig",newline="") as f:
    for r in csv.DictReader(f):
        rows.append({"formid":r["formid"].upper().removeprefix("0X"),"editor_id":r["edid"],
                     "source_english":r["english"],"korean":r["korean"],
                     "reuse_source":"v1.0.2_exe_only_gmst"})
rows.sort(key=lambda r:(r["editor_id"],r["formid"]))
p=OUT/"GMST_REUSE_V1_926.csv"
with p.open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
report={"rows":len(rows),"unique_editor_ids":len({r["editor_id"] for r in rows}),
        "unique_formids":len({r["formid"] for r in rows}),
        "blank_korean":sum(not r["korean"].strip() for r in rows),
        "policy":"Reuse frozen v1.0.2 GMST Korean translations; do not send GMST to Gemini."}
(OUT/"GMST_REUSE_V1_926_REPORT.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(report,ensure_ascii=True,indent=2))