from __future__ import annotations
import csv,json
from pathlib import Path
ROOT=Path(r"C:\오블리비언\v2_work")
G=ROOT/"01_glossary"

def main():
    merged={}
    draft=G/"OBLIVION_GLOSSARY_V2_DRAFT.csv"
    for r in csv.DictReader(draft.open(encoding="utf-8-sig",newline="")):
        en=r["source_english"]
        merged[en.casefold()]={"source_english":en,"korean":r["korean"],
            "application":"EXACT_ONLY","source_basis":r["provenance"],
            "status":r["review_status"],"notes":r.get("notes","")}
    core=G/"OBLIVION_CORE_TERMINOLOGY_V2.csv"
    core_count=0; overlap=0
    for r in csv.DictReader(core.open(encoding="utf-8-sig",newline="")):
        core_count+=1; key=r["source_english"].casefold()
        if key in merged: overlap+=1
        merged[key]={"source_english":r["source_english"],"korean":r["korean"],
            "application":"PHRASE_CONTEXT","source_basis":r["source_basis"],
            "status":r["status"],"notes":r["notes"]}
    rows=sorted(merged.values(),key=lambda x:x["source_english"].casefold())
    out=G/"OBLIVION_GLOSSARY_V2_ACTIVE.csv"
    fields=["source_english","korean","application","source_basis","status","notes"]
    with out.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
    report={
      "active_unique_terms":len(rows),
      "draft_exact_rows":sum(1 for _ in csv.DictReader(draft.open(encoding="utf-8-sig",newline=""))),
      "core_phrase_terms":core_count,
      "core_overrides_of_draft":overlap,
      "exact_only":sum(r["application"]=="EXACT_ONLY" for r in rows),
      "phrase_context":sum(r["application"]=="PHRASE_CONTEXT" for r in rows),
    }
    (G/"OBLIVION_GLOSSARY_V2_ACTIVE_REPORT.json").write_text(
      json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=True,indent=2))
if __name__=="__main__": main()