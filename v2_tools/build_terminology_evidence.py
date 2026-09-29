from __future__ import annotations
import csv,json,re,unicodedata
from collections import Counter,defaultdict
from pathlib import Path

REPO=Path(r"C:\오블리비언")
ROOT=REPO/"v2_work"
G=ROOT/"01_glossary"
S=ROOT/"02_source_extract"
OUT=G/"TERMINOLOGY_EVIDENCE_ALL.csv"
CORE=G/"TERMINOLOGY_EVIDENCE_CORE.csv"

NAMED_TYPES={"NPC_","FACT","CELL","WRLD","RACE","CREA","BSGN","DIAL","BOOK",
             "WEAP","ARMO","CLOT","SPEL","ENCH","SGST","KEYM","ACTI","DOOR","QUST"}

def norm(s):
    return unicodedata.normalize("NFC",(s or "").strip())

def load_project():
    out={}
    p=G/"PROJECT_OVERRIDE_GLOSSARY.csv"
    if p.exists():
        for r in csv.DictReader(p.open(encoding="utf-8-sig",newline="")):
            out[norm(r["source_english"])]=r
    return out

def load_oblivion():
    counts=Counter(); types=defaultdict(set); editors=defaultdict(list)
    for r in csv.DictReader((S/"OBLIVION_SOURCE_ALL.csv").open(encoding="utf-8-sig",newline="")):
        if r["field"]!="FULL" or r["record_type"] not in NAMED_TYPES: continue
        s=norm(r["source_english"])
        if not s or len(s)>100: continue
        counts[s]+=1; types[s].add(r["record_type"])
        if r["editor_id"] and len(editors[s])<4: editors[s].append(r["editor_id"])
    return counts,types,editors

def load_sst():
    exact=defaultdict(Counter); book_rows=[]
    p=G/"SST_ALL_ROWS.csv"
    for r in csv.DictReader(p.open(encoding="utf-8-sig",newline="")):
        s=norm(r["source_norm"]); t=norm(r["translation_norm"])
        if s and t and s!=t and not (int(r["status_bits"]) & 0x80):
            exact[s][t]+=1
        if r["rname"]=="BOOK" and r["fname"] in ("FULL","DESC") and s and t:
            book_rows.append((s,t,r["source_file"],r["fname"]))
    return exact,book_rows

def load_exact_memory(paths):
    out=defaultdict(Counter)
    for p in paths:
        if not p.exists(): continue
        for r in csv.DictReader(p.open(encoding="utf-8-sig",newline="")):
            e=norm(r.get("old_english","")); k=norm(r.get("new_korean",""))
            if e and k and e!=k: out[e][k]+=1
    return out

def ranked_json(c):
    return json.dumps(sorted(c.items(),key=lambda x:(-x[1],x[0])),ensure_ascii=False)

def titleish(s):
    toks=re.findall(r"[A-Za-z][A-Za-z'’-]*",s)
    if not toks: return False
    small={"of","the","and","to","in","on","at","for","a","an","from"}
    significant=[t for t in toks if t.casefold() not in small]
    return bool(significant) and all(t[0].isupper() or t.isupper() for t in significant)

def build_book_hits(candidates,book_rows):
    terms=[s for s in candidates if len(s)>=4]
    terms.sort(key=len,reverse=True)
    hits=defaultdict(list)
    chunks=[terms[i:i+250] for i in range(0,len(terms),250)]
    patterns=[]
    for ch in chunks:
        alts="|".join(re.escape(x) for x in ch)
        patterns.append(re.compile(r"(?<![A-Za-z0-9])("+alts+r")(?![A-Za-z0-9])",re.I))
    canonical={s.casefold():s for s in terms}
    for eng,kor,fn,field in book_rows:
        for pat in patterns:
            for m in pat.finditer(eng):
                term=canonical.get(m.group(1).casefold())
                if not term or len(hits[term])>=5: continue
                pos=m.start()
                es=eng[max(0,pos-100):pos+len(m.group(1))+140].replace("\n"," ")
                ks=kor[:700].replace("\n"," ")
                hits[term].append({"file":fn,"field":field,"source_snip":es,"translation_snip":ks})
    return hits

def main():
    project=load_project(); counts,types,editors=load_oblivion(); sst,books=load_sst()
    rem=load_exact_memory([REPO/"remaster_extended_memory.csv",REPO/"remaster_questlog_memory.csv"])
    v1=load_exact_memory([REPO/"final_review_override.csv"])
    candidates=set(counts)|set(project)
    pre_core=set()
    named_core={"FACT","WRLD","RACE","CREA","BSGN","NPC_","CELL"}
    for s in candidates:
        if s in project or s in sst or s in rem:
            pre_core.add(s); continue
        if titleish(s) and counts[s]>=2 and any(t in named_core for t in types[s]):
            pre_core.add(s); continue
        if titleish(s) and counts[s]>=5 and "DIAL" in types[s]:
            pre_core.add(s)
    bookhits=build_book_hits(pre_core,books)
    rows=[]
    for s in sorted(candidates,key=lambda x:(-counts[x],x.casefold())):
        ss=sst.get(s,Counter()); rr=rem.get(s,Counter()); vv=v1.get(s,Counter())
        proj=project.get(s)
        proposed=""; basis=""; status="REVIEW"
        if proj:
            proposed=proj["korean"]; basis=proj["source_basis"]; status="CONFIRMED_PROJECT"
        elif len(ss)==1:
            proposed=next(iter(ss)); basis="LATEST_SST_EXACT"; status="AUTO_HIGH"
        elif not ss and len(rr)==1 and sum(rr.values())>=2:
            proposed=next(iter(rr)); basis="REMASTER_EXACT_REPEATED"; status="REVIEW_REMASTER"
        row={
          "source_english":s,"oblivion_occurrences":counts[s],
          "record_types":"|".join(sorted(types[s])),"editor_examples":"|".join(editors[s]),
          "project_korean":proj["korean"] if proj else "",
          "project_basis":proj["source_basis"] if proj else "",
          "sst_exact":ranked_json(ss) if ss else "",
          "sst_exact_variants":len(ss),"sst_book_hits":len(bookhits.get(s,[])),
          "sst_book_examples":json.dumps(bookhits.get(s,[]),ensure_ascii=False),
          "remaster_exact":ranked_json(rr) if rr else "",
          "v1_exact":ranked_json(vv) if vv else "",
          "proposed_korean":proposed,"proposal_basis":basis,"status":status,
          "titleish":1 if titleish(s) else 0
        }
        rows.append(row)
    fields=list(rows[0])
    with OUT.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
    core=[r for r in rows if r["project_korean"] or r["sst_book_hits"] or r["sst_exact_variants"] or
          r["remaster_exact"] or (r["titleish"] and any(t in {"FACT","WRLD","RACE","CREA","BSGN"} for t in r["record_types"].split("|")))]
    with CORE.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(core)
    report={"all_candidates":len(rows),"core_candidates":len(core),
            "project_confirmed":sum(r["status"]=="CONFIRMED_PROJECT" for r in rows),
            "sst_exact_auto":sum(r["status"]=="AUTO_HIGH" for r in rows),
            "book_evidence_terms":sum(bool(r["sst_book_hits"]) for r in rows),
            "needs_review_core":sum(r["status"] not in ("CONFIRMED_PROJECT","AUTO_HIGH") for r in core)}
    (G/"TERMINOLOGY_EVIDENCE_REPORT.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=True,indent=2))

if __name__=="__main__": main()