from __future__ import annotations
import csv,json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from dialogue_style import build_legacy_style_index,classify_korean_tone,load_speaker_map,load_dialog_context_map

REPO=Path(r"C:\오블리비언")
ROOT=REPO/"v2_work"
IN_DIR=ROOT/"03_translation_json"
OUT_DIR=ROOT/"04_gemini_raw"
REVIEW=ROOT/"05_sol_review"
REVIEW.mkdir(parents=True,exist_ok=True)

STYLE_INDEX=build_legacy_style_index([
    REPO/"remaster_info_memory.csv",
    REPO/"patch_translation_memory.csv",
])
SPEAKER_MAP=load_speaker_map(ROOT/"02_source_extract"/"INFO_SPEAKER_MAP.csv")
DIALOG_MAP=load_dialog_context_map(ROOT/"02_source_extract"/"DIAL_CONTEXT_MAP.csv")

CUE_PATTERNS={
    "sir":re.compile(r"\bsir\b",re.I),
    "maam":re.compile(r"\bma['’]?am\b",re.I),
    "lord":re.compile(r"\b(?:my )?lord\b",re.I),
    "lady":re.compile(r"\b(?:my )?lady\b",re.I),
    "master":re.compile(r"\bmaster\b",re.I),
    "commander":re.compile(r"\bcommander\b",re.I),
    "emperor":re.compile(r"\bemperor\b",re.I),
    "your_majesty":re.compile(r"\byour majesty\b",re.I),
    "please":re.compile(r"\bplease\b",re.I),
}

def cues(text):
    return "|".join(k for k,p in CUE_PATTERNS.items() if p.search(text or ""))

rows=[]
for ip in sorted(IN_DIR.glob("batch_[0-9][0-9][0-9][0-9].json")):
    op=OUT_DIR/ip.name
    if not op.exists():
        continue
    try:
        inp=json.loads(ip.read_text(encoding="utf-8"))
        out=json.loads(op.read_text(encoding="utf-8"))
    except Exception:
        continue
    by={x.get("id"):x.get("korean","") for x in out.get("translations",[])}
    for item in inp.get("items",[]):
        if item.get("record_type")!="INFO" or item.get("field")!="NAM1":
            continue
        k=by.get(item.get("id"))
        if not k:
            continue
        src=item.get("source_english","")
        hint=STYLE_INDEX.get(src.strip(),{})
        ctx=item.get("context") or {}
        srec=SPEAKER_MAP.get((item.get("source_file",""),item.get("formid","")), {})
        drec=DIALOG_MAP.get((item.get("source_file",""),item.get("parent_dialog_formid","")), {})
        rows.append({
            "id":item.get("id",""),
            "source_file":item.get("source_file",""),
            "formid":item.get("formid",""),
            "speaker_formid":srec.get("speaker_formids",""),
            "speaker_name":srec.get("speaker_names",""),
            "speaker_confidence":srec.get("speaker_confidence",""),
            "parent_dialog_formid":item.get("parent_dialog_formid",""),
            "dialogue_type":drec.get("dialogue_type_name",""),
            "addressee_hint":drec.get("addressee_hint",""),
            "topic_editor_id":drec.get("editor_id",""),
            "quest_formid":item.get("quest_formid",""),
            "source_english":src,
            "korean":k,
            "current_tone":classify_korean_tone(k),
            "legacy_tone_hint":hint.get("tone",""),
            "legacy_hint_confidence":hint.get("confidence",""),
            "legacy_hint_count":hint.get("count",""),
            "social_cues":cues(src),
            "dialogue_before":" || ".join(ctx.get("dialogue_before") or []),
            "dialogue_after":" || ".join(ctx.get("dialogue_after") or []),
            "review_reason":"",
            "review_status":"MAPPED" if srec.get("speaker_formids") else "PENDING_SPEAKER_MAP",
        })

# Flag direct disagreement with high-confidence historical speech-level evidence.
for r in rows:
    h=r["legacy_tone_hint"]; cur=r["current_tone"]
    if h and cur!="UNKNOWN" and h!=cur and float(r["legacy_hint_confidence"] or 0)>=0.8:
        r["review_reason"]="LEGACY_TONE_DISAGREEMENT"
        r["review_status"]="REVIEW"

fields=list(rows[0].keys()) if rows else []
outp=REVIEW/"DIALOGUE_TONE_REVIEW.csv"
with outp.open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

summary={
    "rows":len(rows),
    "with_legacy_hint":sum(bool(r["legacy_tone_hint"]) for r in rows),
    "tone_disagreements":sum(r["review_reason"]=="LEGACY_TONE_DISAGREEMENT" for r in rows),
    "speaker_mapped":sum(bool(r["speaker_formid"]) for r in rows),
    "output":str(outp),
}
(REVIEW/"DIALOGUE_TONE_REVIEW_REPORT.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(summary,ensure_ascii=True,indent=2))
