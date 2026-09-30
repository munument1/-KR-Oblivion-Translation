import csv, json, re
from pathlib import Path
from collections import Counter

P = Path(r"C:\오블리비언\v2_work\08_compare_review\00_inputs\BOOK_COMPARE_QUEUE.csv")
OUT = Path(r"C:\오블리비언\v2_work\08_compare_review\03_final")
with P.open(encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

tag_re = re.compile(r"<[^>]+>")
residue_patterns = [
    r"\bpoints? on\b", r"\bon (Self|Target|Touch)\b", r"\bfor \d+ seconds?\b",
    r"\bSchool of\b", r"\bSkill:\b", r"\bRange:\b", r"\bEffects?:\b",
    r"\bpoints? for\b"
]
issues=[]

def base_text(r):
    d=r.get("sol_decision","")
    if d in {"KEEP_OLD","REWRITE_OLD"}: return r.get("old_1_0_2","")
    if d in {"USE_PRIOR_SOL","REWRITE_PRIOR_SOL"}: return r.get("prior_sol_candidate","")
    return r.get("new_gemini","")

for r in rows:
    rid=r["id"]; fin=r.get("sol_final",""); base=base_text(r)
    if r.get("status")!="REVIEWED": issues.append((rid,"STATUS",r.get("status","")))
    if not fin.strip(): issues.append((rid,"EMPTY_FINAL",""))
    bt=tag_re.findall(base or ""); ft=tag_re.findall(fin)
    if bt != ft:
        issues.append((rid,"BASE_TAG_MISMATCH",json.dumps({"base":bt,"final":ft},ensure_ascii=False)))
    hits=json.loads(r.get("active_glossary_json") or "[]")
    miss=[h for h in hits if h.get("target") and h["target"] not in fin]
    if miss: issues.append((rid,"GLOSSARY_MISS",json.dumps(miss,ensure_ascii=False)))
    if "\ufffd" in fin: issues.append((rid,"REPLACEMENT_CHAR",""))
    if "???" in fin: issues.append((rid,"TRIPLE_QUESTION",""))
    for pat in residue_patterns:
        m=re.search(pat,fin,re.I)
        if m:
            issues.append((rid,"ENGLISH_RESIDUE",m.group(0))); break

with (OUT/"BOOK_FINAL_VALIDATION_ISSUES_V2.csv").open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.writer(f); w.writerow(["id","issue","detail"]); w.writerows(issues)
rep={
 "total":len(rows),"reviewed":sum(r.get("status")=="REVIEWED" for r in rows),
 "nonempty":sum(bool((r.get("sol_final") or "").strip()) for r in rows),
 "decision_counts":dict(Counter(r.get("sol_decision","") for r in rows)),
 "issue_counts":dict(Counter(x[1] for x in issues)),
 "issue_rows":len(set(x[0] for x in issues))
}
(OUT/"BOOK_FINAL_VALIDATION_REPORT_V2.json").write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(rep,ensure_ascii=False,indent=2))
