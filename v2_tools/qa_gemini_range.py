import json,re,sys
from pathlib import Path
R=Path(r"C:\오블리비언\v2_work")
start=int(sys.argv[1]) if len(sys.argv)>1 else 1
end=int(sys.argv[2]) if len(sys.argv)>2 else start
printf=re.compile(r"%(?:[-+0#]*\d*(?:\.\d+)?[a-zA-Z%])")
tag=re.compile(r"<[^>]+>")
stats={"batches":0,"items":0,"unchanged":0,"printf":0,"tag":0,"newline":0,"glossary_miss":0}
probs=[]; key_samples=[]
watch={"Vitharn","Blackwood Company","Order of the Virtuous Blood","Raminus Polus","Tar-Meena","Raven Camoran","Ruma Camoran","Jyggalag","Pelinal"}
for n in range(start,end+1):
    sp=R/"03_translation_json"/f"batch_{n:04d}.json"
    op=R/"04_gemini_raw"/f"batch_{n:04d}.json"
    s=json.loads(sp.read_text(encoding="utf-8"))
    o=json.loads(op.read_text(encoding="utf-8"))
    by={x["id"]:x["korean"] for x in o["translations"]}
    stats["batches"]+=1
    for x in s["items"]:
        e=x["source_english"]; k=by[x["id"]]; stats["items"]+=1
        if e.strip()==k.strip():
            stats["unchanged"]+=1
            if len(probs)<30: probs.append({"batch":n,"type":"UNCHANGED","source":e,"korean":k})
        if printf.findall(e)!=printf.findall(k):
            stats["printf"]+=1
            if len(probs)<30: probs.append({"batch":n,"type":"PRINTF","source":e,"korean":k})
        if tag.findall(e)!=tag.findall(k):
            stats["tag"]+=1
            if len(probs)<30: probs.append({"batch":n,"type":"TAG","source":e,"korean":k})
        if e.count("\n")!=k.count("\n"):
            stats["newline"]+=1
            if len(probs)<30: probs.append({"batch":n,"type":"NEWLINE","source":e,"korean":k})
        for h in x.get("glossary_hits",[]):
            if h["target"] not in k:
                stats["glossary_miss"]+=1
                if len(probs)<30: probs.append({"batch":n,"type":"GLOSSARY","source":e,"expected":h["target"],"korean":k})
                break
        if any(t in e for t in watch) and len(key_samples)<30:
            key_samples.append({"batch":n,"source":e[:300],"korean":k[:300],"hits":x.get("glossary_hits",[])})
print(json.dumps({"stats":stats,"problems":probs,"key_samples":key_samples},ensure_ascii=True,indent=2))