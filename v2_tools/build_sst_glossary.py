from __future__ import annotations
import csv, json, re, unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(r"D:\Codex_Trans\오블리비언\v2_work")
G=ROOT/"01_glossary"
S=ROOT/"02_source_extract"
_ws=re.compile(r"\s+")

def norm(s):
    return _ws.sub(" ",unicodedata.normalize("NFC",s).strip())

def load_sst():
    by=defaultdict(Counter); files=defaultdict(lambda:defaultdict(Counter))
    with (G/"SST_ALL_ROWS.csv").open(encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            src=norm(r["source"]); tr=norm(r["translation"])
            if not src or not tr or src==tr:
                continue
            status=int(r["status_bits"])
            if status & 0x80:  # pending / intentionally untranslated collaborative row
                continue
            by[src][tr]+=1
            files[src][tr][r["source_file"]]+=1
    return by,files

def load_oblivion():
    by=defaultdict(list)
    with (S/"OBLIVION_SOURCE_ALL.csv").open(encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            by[norm(r["source_english"])].append(r)
    return by

def term_like(src, obs):
    if "\n" in src or "\r" in src or len(src)>100:
        return False
    words=src.split()
    if len(words)>10:
        return False
    kinds={r["field"] for r in obs}
    if "FULL" in kinds or any(r["safety"] in ("MENU_GMST","EXE_UI_CANDIDATE") for r in obs):
        return True
    return len(words)<=5 and not src.endswith((".","!","?"))
def main():
    sst,sst_files=load_sst(); obl=load_oblivion()
    matches=[]; conflicts=[]; seed=[]
    matched_occ=0
    for src,obs in obl.items():
        if src not in sst:
            continue
        tc=sst[src]; ranked=sorted(tc.items(),key=lambda x:(-x[1],x[0]))
        saf=Counter(r["safety"] for r in obs)
        combos=Counter(f'{r["record_type"]}/{r["field"]}' for r in obs)
        row={
            "source_english":src,
            "oblivion_occurrences":len(obs),
            "oblivion_record_fields_json":json.dumps(combos,ensure_ascii=False,sort_keys=True),
            "oblivion_safety_json":json.dumps(saf,ensure_ascii=False,sort_keys=True),
            "sst_translation_count":len(ranked),
            "sst_occurrences":sum(tc.values()),
            "preferred_by_frequency":ranked[0][0],
            "preferred_count":ranked[0][1],
            "translations_json":json.dumps(ranked,ensure_ascii=False),
            "sst_source_files_json":json.dumps(
                {t:sst_files[src][t] for t,_ in ranked},ensure_ascii=False,default=dict),
        }
        matches.append(row); matched_occ+=len(obs)
        if len(ranked)>1:
            conflicts.append(row)
        elif term_like(src,obs):
            seed.append({
                "source_english":src,"korean":ranked[0][0],
                "sst_occurrences":sum(tc.values()),
                "oblivion_occurrences":len(obs),
                "record_fields_json":row["oblivion_record_fields_json"],
                "status":"SST_UNAMBIGUOUS_CANDIDATE",
                "override_korean":"","review_notes":""
            })
    fields=list(matches[0].keys()) if matches else []
    for name,rows in [("OBLIVION_SST_EXACT_MATCHES.csv",matches),
                      ("OBLIVION_SST_CONFLICTS.csv",conflicts)]:
        with (G/name).open("w",encoding="utf-8-sig",newline="") as f:
            w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
    seed_fields=["source_english","korean","sst_occurrences","oblivion_occurrences",
                 "record_fields_json","status","override_korean","review_notes"]
    with (G/"OBLIVION_GLOSSARY_SEED.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=seed_fields); w.writeheader(); w.writerows(seed)
    report={
        "oblivion_unique_sources":len(obl),
        "sst_unique_translated_sources":len(sst),
        "exact_matched_unique_sources":len(matches),
        "exact_matched_oblivion_occurrences":matched_occ,
        "matched_conflict_sources":len(conflicts),
        "unambiguous_matches":len(matches)-len(conflicts),
        "term_like_unambiguous_seed":len(seed),
    }
    (G/"OBLIVION_SST_CROSS_REPORT.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=True,indent=2))

if __name__=="__main__":
    main()
