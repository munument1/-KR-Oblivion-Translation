import csv,json,re
from pathlib import Path
from collections import Counter

ROOT=Path(r"C:\오블리비언\v2_work\08_compare_review")
P=ROOT/"00_inputs"/"MASTER_COMPARE_QUEUE.csv"
OUT=ROOT/"03_final"

with P.open(encoding="utf-8-sig",newline="") as f:
    rows=list(csv.DictReader(f))
issues=[]
def add(r,k,d=""): issues.append((r["id"],r["record_type"],k,d))

for r in rows:
    fin=r.get("sol_final") or ""; src=r.get("source_english") or ""; eid=r.get("editor_id") or ""
    if r.get("status")!="REVIEWED": add(r,"STATUS",r.get("status",""))
    if not fin.strip(): add(r,"EMPTY_FINAL","")
    if "\ufffd" in fin: add(r,"REPLACEMENT_CHAR","")
    if "???" in fin: add(r,"TRIPLE_QUESTION","")
    if r["record_type"]!="DIAL":
        try: hits=json.loads(r.get("glossary_json") or "[]")
        except: hits=[]
        miss=[]
        for h in hits:
            tgt=h.get("target")
            if not tgt or tgt in fin: continue
            # Blade skill item names can falsely hit the Blades-organization glossary entry.
            if h.get("source")=="Blades" and eid.startswith("EnchRingFortifyBlade") and "검술" in fin:
                continue
            miss.append(h)
        if miss: add(r,"GLOSSARY_MISS",json.dumps(miss,ensure_ascii=False))
    if r["record_type"]=="NPC_":
        hy=re.findall(r"\b[A-Za-z]+-[A-Za-z]+\b",src)
        if hy and "-" not in fin: add(r,"NPC_HYPHEN_LOST",", ".join(hy))
        ap=[]
        for t in re.findall(r"\b[A-Za-z]+['’][A-Za-z]+\b",src):
            if re.split(r"['’]",t,maxsplit=1)[1].lower()!="s": ap.append(t)
        if ap and "'" not in fin and "’" not in fin: add(r,"NPC_APOSTROPHE_LOST",", ".join(ap))
    if r["record_type"]=="DIAL" and re.fullmatch(r"[A-Za-z0-9_]+",src) and len(fin)>100:
        add(r,"DIAL_INFO_LEAK",fin[:180])

    words=re.findall(r"\b[A-Za-z][A-Za-z'-]{2,}\b",fin)
    bad=[]
    for w in words:
        if r["id"]=="Oblivion.esm|QUST|000CD300|FULL||0" and w.lower()=="mtv": continue
        if re.fullmatch(r"[A-Z]{2,}[A-Z0-9_-]*",w): continue
        if re.fullmatch(r"(DLC|SE|TG|MS|MQ|ND|DA|NPC|TEMP|IC|CG)\d*[A-Za-z0-9_-]*",w): continue
        if w in {"Dark","Light"} and re.search(r"\b(?:Dark|Light)\d+",fin): continue
        bad.append(w)
    if bad: add(r,"ASCII_RESIDUE",", ".join(sorted(set(bad))[:20]))

for r in rows:
    if r["record_type"]=="NPC_" and r["source_english"]=="M'aiq the Liar" and r["sol_final"]!="거짓말쟁이 마'이크":
        add(r,"MAIQ_OVERRIDE","expected 거짓말쟁이 마'이크")

with (OUT/"MASTER_FINAL_VALIDATION_ISSUES_V2.csv").open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.writer(f); w.writerow(["id","record_type","issue","detail"]); w.writerows(issues)
rep={
 "total":len(rows),
 "reviewed":sum(r.get("status")=="REVIEWED" for r in rows),
 "pending":sum(r.get("status")=="PENDING" for r in rows),
 "nonempty_final":sum(bool((r.get("sol_final") or "").strip()) for r in rows),
 "issue_counts":dict(Counter(x[2] for x in issues)),
 "issue_rows":len(set(x[0] for x in issues)),
}
(OUT/"MASTER_FINAL_VALIDATION_REPORT_V2.json").write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(rep,ensure_ascii=False,indent=2))
