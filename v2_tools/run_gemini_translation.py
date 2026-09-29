from __future__ import annotations
import argparse,json,re,time,urllib.request,urllib.error
from pathlib import Path

REPO=Path(r"C:\오블리비언")
ROOT=REPO/"v2_work"
IN_DIR=ROOT/"03_translation_json"
OUT_DIR=ROOT/"04_gemini_raw"
LOG_DIR=ROOT/"logs"
KEY_FILE=ROOT/"GEMINI_API_KEY.txt"
OUT_DIR.mkdir(parents=True,exist_ok=True); LOG_DIR.mkdir(parents=True,exist_ok=True)
DEFAULT_MODEL="gemini-3.5-flash-lite"

def load_keys():
    text=KEY_FILE.read_text(encoding="utf-8-sig")
    keys=[]
    for line in text.splitlines():
        m=re.search(r"AIza[0-9A-Za-z_-]{20,}",line.strip())
        if m and m.group(0) not in keys:
            keys.append(m.group(0))
    if not keys:
        raise RuntimeError("No valid Gemini API keys detected")
    return keys

def log(obj):
    obj=dict(obj); obj["ts"]=time.strftime("%Y-%m-%dT%H:%M:%S")
    with (LOG_DIR/"gemini_v2.jsonl").open("a",encoding="utf-8") as f:
        f.write(json.dumps(obj,ensure_ascii=False)+"\n")

def call_gemini(key,model,batch,timeout=180):
    wire=dict(batch)
    wire["items"]=[]
    for n,item in enumerate(batch["items"],1):
        x={k:v for k,v in item.items() if k!="id"}
        x["n"]=n
        wire["items"].append(x)
    prompt=(
      "You are translating The Elder Scrolls IV: Oblivion from English to Korean. "
      "Follow the supplied glossary and every per-item constraint. "
      "Return only valid JSON in the exact shape {\"translations\":[{\"n\":1,\"korean\":\"...\"},...]}. "
      "Return exactly one object for every input item. Preserve each integer n exactly and keep ascending order. "
      "Do not invent, omit, duplicate, or reorder n values.\n\n"
      + json.dumps(wire,ensure_ascii=False,separators=(",",":"))
    )
    payload={"contents":[{"role":"user","parts":[{"text":prompt}]}],
             "generationConfig":{"temperature":0.2,"responseMimeType":"application/json",
                                 "maxOutputTokens":65536}}
    url=f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    req=urllib.request.Request(url,data=json.dumps(payload,ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=timeout) as resp:
        raw=json.load(resp)
    candidates=raw.get("candidates") or []
    if not candidates: raise RuntimeError("No Gemini candidate returned")
    parts=candidates[0].get("content",{}).get("parts",[])
    text="".join(p.get("text","") for p in parts)
    if not text: raise RuntimeError("Empty Gemini text response")
    return json.loads(text), raw.get("usageMetadata",{})
def preserve_boundary_newlines(source,korean):
    lead=re.match(r"^[\r\n]+",source)
    tail=re.search(r"[\r\n]+$",source)
    if not lead and not tail:
        return korean
    core=korean.strip("\r\n")
    return (lead.group(0) if lead else "") + core + (tail.group(0) if tail else "")

def validate(batch,result):
    arr=result.get("translations") if isinstance(result,dict) else None
    if not isinstance(arr,list):
        raise ValueError("result.translations is not a list")
    expected=batch["items"]
    if len(arr)!=len(expected):
        raise ValueError(f"translation count mismatch expected={len(expected)} got={len(arr)}")
    paired=[]
    for n,(item,obj) in enumerate(zip(expected,arr),1):
        if not isinstance(obj,dict) or obj.get("n")!=n:
            raise ValueError(f"sequence mismatch at {n}: got={obj.get('n') if isinstance(obj,dict) else type(obj).__name__}")
        korean=obj.get("korean")
        if not isinstance(korean,str) or not korean.strip():
            raise ValueError(f"empty translation at n={n}")
        korean=preserve_boundary_newlines(item["source_english"],korean)
        paired.append({"id":item["id"],"korean":korean})
    return paired

def validate_saved(batch,result):
    arr=result.get("translations") if isinstance(result,dict) else None
    if not isinstance(arr,list) or len(arr)!=len(batch["items"]):
        raise ValueError("saved translation count mismatch")
    for item,obj in zip(batch["items"],arr):
        if not isinstance(obj,dict) or obj.get("id")!=item["id"]:
            raise ValueError("saved ID/order mismatch")
        korean=obj.get("korean")
        if not isinstance(korean,str) or not korean.strip():
            raise ValueError("saved translation is empty")
        if korean!=preserve_boundary_newlines(item["source_english"],korean):
            raise ValueError("saved boundary newline mismatch")
    return arr

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--model",default=DEFAULT_MODEL)
    ap.add_argument("--start",type=int,default=1)
    ap.add_argument("--limit",type=int,default=0)
    ap.add_argument("--interval",type=float,default=18.0)
    args=ap.parse_args()
    keys=load_keys()
    manifest=json.loads((IN_DIR/"manifest.json").read_text(encoding="utf-8"))
    todo=[x for x in manifest if int(x["batch_id"].split("_")[-1])>=args.start]
    if args.limit: todo=todo[:args.limit]
    print(json.dumps({"detected_key_slots":len(keys),"model":args.model,
                      "planned_batches":len(todo)},ensure_ascii=True),flush=True)
    last_call=0.0
    for seq,m in enumerate(todo,1):
        infile=IN_DIR/m["file"]; outfile=OUT_DIR/m["file"]
        if outfile.exists():
            try:
                old=json.loads(outfile.read_text(encoding="utf-8"))
                validate_saved(json.loads(infile.read_text(encoding="utf-8")),old)
                print(json.dumps({"batch":m["batch_id"],"status":"SKIP_VALID"},ensure_ascii=True),flush=True)
                continue
            except Exception: pass
        batch=json.loads(infile.read_text(encoding="utf-8"))
        success=False
        for attempt in range(1,6):
            slot=(int(m["batch_id"].split("_")[-1])+attempt-2)%len(keys)
            wait=args.interval-(time.time()-last_call)
            if wait>0: time.sleep(wait)
            try:
                last_call=time.time()
                result,usage=call_gemini(keys[slot],args.model,batch)
                arr=validate(batch,result)
                outfile.write_text(json.dumps({"translations":arr},ensure_ascii=False,indent=2),encoding="utf-8")
                rec={"batch":m["batch_id"],"status":"OK","slot":slot+1,"attempt":attempt,
                     "items":len(arr),"usage":usage}
                log(rec); print(json.dumps(rec,ensure_ascii=True),flush=True)
                success=True; break
            except urllib.error.HTTPError as e:
                body=e.read().decode("utf-8","replace")[:500]
                rec={"batch":m["batch_id"],"status":"HTTP_ERROR","slot":slot+1,
                     "attempt":attempt,"http":e.code,"detail":body}
                log(rec); print(json.dumps({k:v for k,v in rec.items() if k!="detail"},ensure_ascii=True),flush=True)
                if e.code not in (429,500,502,503,504): break
                time.sleep(min(60,5*attempt))
            except Exception as e:
                rec={"batch":m["batch_id"],"status":"ERROR","slot":slot+1,"attempt":attempt,
                     "error_type":type(e).__name__,"detail":str(e)[:500]}
                log(rec); print(json.dumps({k:v for k,v in rec.items() if k!="detail"},ensure_ascii=True),flush=True)
                time.sleep(min(30,3*attempt))
        if not success:
            raise SystemExit(f"failed batch {m['batch_id']}")
if __name__=="__main__":
    main()