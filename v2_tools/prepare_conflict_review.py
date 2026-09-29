from __future__ import annotations
import csv,json
from collections import defaultdict
from pathlib import Path
ROOT=Path(r"C:\오블리비언\v2_work")
G=ROOT/"01_glossary"; S=ROOT/"02_source_extract"
srcrows=defaultdict(list)
with (S/"OBLIVION_SOURCE_ALL.csv").open(encoding="utf-8-sig",newline="") as f:
    for r in csv.DictReader(f):
        srcrows[r["source_english"].strip()].append(r)
out=[]
with (G/"OBLIVION_SST_CONFLICTS.csv").open(encoding="utf-8-sig",newline="") as f:
    for r in csv.DictReader(f):
        obs=srcrows[r["source_english"].strip()]
        fields={f'{x["record_type"]}/{x["field"]}' for x in obs}
        is_dialog=any(x["record_type"] in ("INFO","DIAL") for x in obs)
        is_menu=any(x["safety"] in ("MENU_GMST","EXE_UI_CANDIDATE") for x in obs)
        # Do not force one global translation for dialogue: speaker/context must decide later.
        if is_dialog:
            bucket="CONTEXTUAL_DIALOGUE"
        elif is_menu:
            bucket="MENU_REVIEW"
        else:
            bucket="TERM_REVIEW"
        ranked=json.loads(r["translations_json"])
        top_count=ranked[0][1]; total=sum(x[1] for x in ranked)
        dominance=top_count/total if total else 0
        auto = bucket=="TERM_REVIEW" and dominance>=0.80 and top_count>=3
        out.append({
            "source_english":r["source_english"],
            "bucket":bucket,
            "record_fields":"; ".join(sorted(fields)),
            "oblivion_occurrences":r["oblivion_occurrences"],
            "sst_occurrences":r["sst_occurrences"],
            "translations_json":r["translations_json"],
            "frequency_candidate":ranked[0][0],
            "frequency_share":f"{dominance:.3f}",
            "decision":ranked[0][0] if auto else "",
            "status":"AUTO_HIGH_CONFIDENCE" if auto else "REVIEW",
            "notes":""
        })
fields=list(out[0].keys())
with (G/"OBLIVION_SST_CONFLICT_REVIEW.csv").open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(out)
from collections import Counter
print(json.dumps({"rows":len(out),"buckets":Counter(x["bucket"] for x in out),
 "auto_high_confidence":sum(x["status"]=="AUTO_HIGH_CONFIDENCE" for x in out)},ensure_ascii=True,default=dict))