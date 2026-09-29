from __future__ import annotations
import argparse,json,time
from pathlib import Path
import run_gemini_translation as rg

ROOT=Path(r"C:\오블리비언\v2_work")
IN_DIR=ROOT/"03_translation_json"
OUT_DIR=ROOT/"04_gemini_raw"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("batch",type=int)
    ap.add_argument("--chunk-size",type=int,default=160)
    ap.add_argument("--model",default=rg.DEFAULT_MODEL)
    ap.add_argument("--interval",type=float,default=18.0)
    args=ap.parse_args()

    src=IN_DIR/f"batch_{args.batch:04d}.json"
    batch=json.loads(src.read_text(encoding="utf-8"))
    items=batch["items"]
    keys=rg.load_keys()
    merged=[]
    last=0.0

    for part_no,start in enumerate(range(0,len(items),args.chunk_size),1):
        sub=dict(batch)
        sub["items"]=items[start:start+args.chunk_size]
        ok=False
        for attempt in range(1,6):
            slot=(part_no+attempt-2)%len(keys)
            wait=args.interval-(time.time()-last)
            if wait>0: time.sleep(wait)
            try:
                last=time.time()
                result,usage=rg.call_gemini(keys[slot],args.model,sub)
                paired=rg.validate(sub,result)
                print(json.dumps({"batch":args.batch,"part":part_no,"status":"OK",
                                  "slot":slot+1,"attempt":attempt,"items":len(paired),
                                  "usage":usage},ensure_ascii=True),flush=True)
                merged.extend(paired)
                ok=True
                break
            except Exception as e:
                print(json.dumps({"batch":args.batch,"part":part_no,"status":"ERROR",
                                  "slot":slot+1,"attempt":attempt,
                                  "error_type":type(e).__name__},ensure_ascii=True),flush=True)
                time.sleep(min(30,3*attempt))
        if not ok:
            raise SystemExit(f"failed batch {args.batch} part {part_no}")

    expected=[x["id"] for x in items]
    got=[x["id"] for x in merged]
    if got!=expected:
        raise RuntimeError("merged ID/order mismatch")
    out=OUT_DIR/f"batch_{args.batch:04d}.json"
    out.write_text(json.dumps({"translations":merged},ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"batch":args.batch,"status":"MERGED_OK","items":len(merged)},ensure_ascii=True),flush=True)

if __name__=="__main__":
    main()