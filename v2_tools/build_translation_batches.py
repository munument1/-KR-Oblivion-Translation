from __future__ import annotations
import csv,json,re,unicodedata
from collections import defaultdict
from pathlib import Path

REPO=Path(r"C:\오블리비언")
ROOT=REPO/"v2_work"
SRC=ROOT/"02_source_extract"
G=ROOT/"01_glossary"
OUT=ROOT/"03_translation_json"
OUT.mkdir(parents=True,exist_ok=True)

def norm(s):
    return unicodedata.normalize("NFC",s)

def load_glossary():
    exact={}
    override={}
    p=G/"OBLIVION_GLOSSARY_V2_ACTIVE.csv"
    with p.open(encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            if r["application"]=="PHRASE_CONTEXT":
                override[r["source_english"]]=r["korean"]
            else:
                exact[r["source_english"].casefold()]=(r["source_english"],r["korean"])
    return exact,override

def build_glossary_index(g):
    index=defaultdict(list)
    for en,ko in g.items():
        if len(en)<3:
            continue
        words=re.findall(r"[A-Za-z0-9]+",en.casefold())
        if not words:
            continue
        tail = r"(?:'s|s)?" if not en.casefold().endswith("s") else ""
        # Core proper-noun phrases are case-sensitive on purpose.
        # This prevents Anvil/Bliss/Split/etc. from overriding ordinary lowercase words.
        pat=re.compile(r"(?<![A-Za-z0-9])"+re.escape(en)+tail+r"(?![A-Za-z0-9])")
        index[words[0]].append((en,ko,pat))
    return index

def glossary_hits(text,exact,index):
    hits=[]; seen=set()
    pair=exact.get(text.casefold().strip())
    if pair:
        en,ko=pair
        hits.append({"source":en,"target":ko,"basis":"SST_EXACT"})
        seen.add(en)
    words=set(re.findall(r"[A-Za-z0-9]+",text.casefold()))
    for word in words:
        for en,ko,pat in index.get(word,()):
            if en in seen:
                continue
            seen.add(en)
            if pat.search(text):
                hits.append({"source":en,"target":ko,"basis":"PROJECT_OVERRIDE"})
    hits.sort(key=lambda x:(0 if x.get("basis")=="PROJECT_OVERRIDE" else 1,-len(x["source"]),x["source"]))
    return hits[:20]
def load_rows():
    rows=[]
    with (SRC/"OBLIVION_SOURCE_ALL.csv").open(encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            if r["source_file"] in ("MENU_GMST_MASTER","Oblivion.exe"):
                continue
            if r["safety"] in ("KEEP_ENGLISH_RACE_FULL","REVIEW_LOCATION_UNSAFE","REVIEW_INTERNAL","MENU_GMST"):
                continue
            if r["safety"] not in ("TRANSLATE","TOPIC_STRUCTURE_CHECK"):
                continue
            rows.append(r)
    # GMST is intentionally excluded from Gemini translation.
    # All 926 player-facing menu GMST translations are reused from the frozen v1 set.
    return rows

def constraints(r):
    c=[
      "Preserve meaning and tone in natural Korean.",
      "Use glossary terms exactly when semantically applicable.",
      "Do not add unnecessary English in parentheses.",
      "Preserve placeholders, markup, tags, and line breaks exactly.",
      "Do not translate editor IDs, FormIDs, file paths, or internal identifiers."
    ]
    if r["record_type"]=="DIAL":
        c.append("This is a dialogue topic label; keep it concise and verify topic-system meaning.")
    if r["record_type"]=="INFO":
        c.append("This is spoken dialogue; use surrounding dialogue context.")
    if r["record_type"]=="BOOK" and r["field"]=="DESC":
        c.append("This is the full book/note body; translate as one coherent document, not line-by-line.")
    if r["record_type"]=="QUST" and r["field"]=="CNAM":
        c.append("This is a quest journal stage; preserve chronological narrative continuity.")
    if r["source_file"]=="MENU_GMST_MASTER":
        c.append("This is player-facing UI text; keep wording concise and functional.")
    return c
def enrich(rows,exact,index):
    by_dialog=defaultdict(list)
    by_quest_stage=defaultdict(list)
    for i,r in enumerate(rows):
        if r["record_type"]=="INFO" and r["parent_dialog_formid"]:
            by_dialog[(r["source_file"],r["parent_dialog_formid"])].append(i)
        if r["record_type"]=="QUST" and r["field"]=="CNAM":
            by_quest_stage[(r["source_file"],r["formid"])].append(i)
    dialog_pos={}
    for key,idxs in by_dialog.items():
        for p,i in enumerate(idxs): dialog_pos[i]=(idxs,p)
    quest_pos={}
    for key,idxs in by_quest_stage.items():
        idxs.sort(key=lambda i:(int(rows[i]["quest_stage"] or 0),int(rows[i]["occurrence"] or 0)))
        for p,i in enumerate(idxs): quest_pos[i]=(idxs,p)

    out=[]
    for i,r in enumerate(rows):
        ctx={}
        if i in dialog_pos:
            idxs,p=dialog_pos[i]
            ctx["dialogue_before"]=[rows[j]["source_english"] for j in idxs[max(0,p-2):p]]
            ctx["dialogue_after"]=[rows[j]["source_english"] for j in idxs[p+1:p+3]]
        if i in quest_pos:
            idxs,p=quest_pos[i]
            ctx["quest_before"]=[{"stage":rows[j]["quest_stage"],"text":rows[j]["source_english"]} for j in idxs[max(0,p-2):p]]
            ctx["quest_after"]=[{"stage":rows[j]["quest_stage"],"text":rows[j]["source_english"]} for j in idxs[p+1:p+3]]
        item={
          "id":f'{r["source_file"]}|{r["record_type"]}|{r["formid"]}|{r["field"]}|{r["quest_stage"]}|{r["occurrence"]}',
          "source_file":r["source_file"],"record_type":r["record_type"],"formid":r["formid"],
          "editor_id":r["editor_id"],"field":r["field"],"occurrence":r["occurrence"],
          "quest_stage":r["quest_stage"],"parent_dialog_formid":r["parent_dialog_formid"],
          "quest_formid":r["quest_formid"],"source_english":r["source_english"],
          "glossary_hits":glossary_hits(r["source_english"],exact,index),
          "context":ctx,"constraints":constraints(r)
        }
        out.append(item)
    return out
def main():
    exact,override=load_glossary()
    index=build_glossary_index(override)
    items=enrich(load_rows(),exact,index)
    # Keep request bodies comfortably below the user's TPM ceiling.
    max_chars=210000
    batches=[]; cur=[]; chars=0
    for item in items:
        n=len(json.dumps(item,ensure_ascii=False))
        if cur and chars+n>max_chars:
            batches.append(cur); cur=[]; chars=0
        cur.append(item); chars+=n
    if cur: batches.append(cur)

    manifest=[]
    for i,b in enumerate(batches,1):
        obj={"schema_version":1,"batch_id":f"obl_v2_{i:04d}",
             "instructions":{
               "task":"Translate each source_english into Korean.",
               "output":"Runner will assign integer n values; return JSON only as {translations:[{n,korean}]} in ascending n order.",
               "rules":["Obey per-item constraints.","Use glossary_hits exactly when applicable.",
                        "Do not omit, duplicate, or reorder n values.","Do not add commentary outside JSON."]},
             "items":b}
        p=OUT/f"batch_{i:04d}.json"
        p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8")
        manifest.append({"batch_id":obj["batch_id"],"file":p.name,"items":len(b),
                         "chars":len(json.dumps(obj,ensure_ascii=False))})
    (OUT/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    report={"work_items":len(items),"batches":len(batches),
            "max_batch_chars":max(x["chars"] for x in manifest),
            "min_batch_chars":min(x["chars"] for x in manifest),
            "menu_items":sum(x["source_file"]=="MENU_GMST_MASTER" for x in items),
            "dialogue_items":sum(x["record_type"]=="INFO" for x in items),
            "topic_items":sum(x["record_type"]=="DIAL" for x in items),
            "quest_stage_items":sum(x["record_type"]=="QUST" and x["field"]=="CNAM" for x in items),
            "book_body_items":sum(x["record_type"]=="BOOK" and x["field"]=="DESC" for x in items)}
    (OUT/"BATCH_REPORT.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=True,indent=2))

if __name__=="__main__":
    main()