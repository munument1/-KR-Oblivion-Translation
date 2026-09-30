import csv, json, collections
from pathlib import Path

ROOT=Path(r"C:\오블리비언\v2_work\08_compare_review")
P=ROOT/"00_inputs"/"BOOK_COMPARE_QUEUE.csv"
OUT=ROOT/"03_final"
OUT.mkdir(parents=True,exist_ok=True)
with P.open(encoding="utf-8-sig",newline="") as f:
    rows=list(csv.DictReader(f))

fields=["id","editor_id","source_english","old_1_0_2","new_gemini",
        "sol_decision","sol_final","notes"]
with (OUT/"BOOK_FINAL_REVIEWED.csv").open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=fields)
    w.writeheader()
    w.writerows({k:r.get(k,"") for k in fields} for r in rows)

translations=[{"id":r["id"],"korean":r["sol_final"]} for r in rows]
(OUT/"BOOK_FINAL_TRANSLATIONS.json").write_text(
    json.dumps({"translations":translations},ensure_ascii=False,indent=2),encoding="utf-8")

report={
 "total":len(rows),
 "reviewed":sum(r["status"]=="REVIEWED" for r in rows),
 "pending":sum(r["status"]=="PENDING" for r in rows),
 "empty_final":sum(r["status"]=="REVIEWED" and not r["sol_final"] for r in rows),
 "decisions":dict(collections.Counter(r["sol_decision"] for r in rows)),
 "replacement_char":sum("�" in r["sol_final"] for r in rows),
 "triple_question":sum("???" in r["sol_final"] for r in rows),
 "accepted_glossary_exceptions":1,
}
(OUT/"BOOK_FINAL_REPORT.json").write_text(
    json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(report,ensure_ascii=False,indent=2))
