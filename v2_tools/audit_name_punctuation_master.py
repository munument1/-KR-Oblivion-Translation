import csv, json, re
from pathlib import Path
P=Path(r"C:\오블리비언\v2_work\08_compare_review\00_inputs\MASTER_COMPARE_QUEUE.csv")
rows=list(csv.DictReader(P.open(encoding="utf-8-sig",newline="")))
apos=[]; hy=[]
for r in rows:
    src=r.get("source_english") or ""
    fin=(r.get("sol_final") or "") if r.get("status")=="REVIEWED" else (r.get("new_gemini") or "")
    if re.search(r"[A-Za-z]['’][A-Za-z]",src):
        apos.append({"id":r["id"],"src":src,"old":r.get("old_1_0_2",""),"new":r.get("new_gemini",""),"final":r.get("sol_final",""),"status":r.get("status","")})
    if re.search(r"[A-Za-z]-[A-Za-z]",src):
        hy.append({"id":r["id"],"src":src,"old":r.get("old_1_0_2",""),"new":r.get("new_gemini",""),"final":r.get("sol_final",""),"status":r.get("status","")})
out=Path(r"C:\오블리비언\v2_work\08_compare_review\02_sol_review")
(out/"NAME_APOSTROPHE_AUDIT.json").write_text(json.dumps(apos,ensure_ascii=False,indent=2),encoding="utf-8")
(out/"NAME_HYPHEN_AUDIT.json").write_text(json.dumps(hy,ensure_ascii=False,indent=2),encoding="utf-8")
print("apostrophe",len(apos),"hyphen",len(hy))
print("apostrophe_samples",[(x["src"],x["final"] or x["new"]) for x in apos[:30]])
print("hyphen_samples",[(x["src"],x["final"] or x["new"]) for x in hy[:30]])
