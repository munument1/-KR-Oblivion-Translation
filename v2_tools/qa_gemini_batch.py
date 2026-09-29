from __future__ import annotations
import json,re,sys
from pathlib import Path
ROOT=Path(r"C:\오블리비언\v2_work")
batch_no=int(sys.argv[1]) if len(sys.argv)>1 else 1
src=json.loads((ROOT/"03_translation_json"/f"batch_{batch_no:04d}.json").read_text(encoding="utf-8"))
out=json.loads((ROOT/"04_gemini_raw"/f"batch_{batch_no:04d}.json").read_text(encoding="utf-8"))
by={x["id"]:x["korean"] for x in out["translations"]}
printf=re.compile(r"%(?:[-+0#]*\d*(?:\.\d+)?[a-zA-Z%])")
tag=re.compile(r"<[^>]+>")
problems=[]
stats={"items":len(src["items"]),"unchanged":0,"placeholder_mismatch":0,"tag_mismatch":0,
       "newline_mismatch":0,"glossary_miss":0}
samples=[]
for item in src["items"]:
    s=item["source_english"]; k=by[item["id"]]
    if s.strip()==k.strip():
        stats["unchanged"]+=1; problems.append((item["id"],"UNCHANGED",s,k))
    if printf.findall(s)!=printf.findall(k):
        stats["placeholder_mismatch"]+=1; problems.append((item["id"],"PRINTF",s,k))
    if tag.findall(s)!=tag.findall(k):
        stats["tag_mismatch"]+=1; problems.append((item["id"],"TAG",s,k))
    if s.count("\n")!=k.count("\n"):
        stats["newline_mismatch"]+=1; problems.append((item["id"],"NEWLINE",s,k))
    for hit in item.get("glossary_hits",[]):
        if hit["source"].casefold() in s.casefold() and hit["target"] not in k:
            stats["glossary_miss"]+=1
            problems.append((item["id"],"GLOSSARY",hit["source"]+"=>"+hit["target"],k))
            break
    if len(samples)<20:
        samples.append({"id":item["id"],"source":s,"korean":k,
                        "record_type":item["record_type"],"field":item["field"]})
print(json.dumps({"stats":stats,"problem_count":len(problems),
                  "problem_samples":[{"id":a,"type":b,"source":c,"korean":d} for a,b,c,d in problems[:20]],
                  "translation_samples":samples},ensure_ascii=True,indent=2))