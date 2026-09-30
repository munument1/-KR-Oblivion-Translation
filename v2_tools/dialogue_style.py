from __future__ import annotations
import csv,re,collections
from pathlib import Path

FORMAL_PATTERNS=(r"습니다[.!?…]*$",r"습니까[?!…]*$",r"십시오[.!?…]*$",r"입니다[.!?…]*$",r"입니까[?!…]*$")
POLITE_PATTERNS=(r"요[.!?…]*$",r"세요[.!?…]*$",r"죠[.!?…]*$")
PLAIN_PATTERNS=(r"(?:다|냐|니|라|자|군|네|어|아)[.!?…]*$",)

def classify_korean_tone(text:str)->str:
    s=(text or "").strip()
    if not s: return "UNKNOWN"
    # Inspect final sentence only; quoted dialogue often ends before a quote.
    s=re.sub(r'["”’\']+$',"",s).strip()
    for p in FORMAL_PATTERNS:
        if re.search(p,s): return "FORMAL_HAPSYO"
    for p in POLITE_PATTERNS:
        if re.search(p,s): return "POLITE_HAEYO"
    for p in PLAIN_PATTERNS:
        if re.search(p,s): return "PLAIN"
    return "UNKNOWN"

def build_legacy_style_index(paths):
    by=collections.defaultdict(collections.Counter)
    examples=collections.defaultdict(list)
    for path in paths:
        p=Path(path)
        if not p.exists(): continue
        with p.open(encoding="utf-8-sig",newline="") as f:
            for r in csv.DictReader(f):
                if (r.get("record_type") or "")!="INFO": continue
                en=(r.get("old_english") or r.get("source_english") or "").strip()
                ko=(r.get("new_korean") or r.get("korean") or "").strip()
                if not en or not ko: continue
                tone=classify_korean_tone(ko)
                if tone=="UNKNOWN": continue
                by[en][tone]+=1
                if len(examples[en])<3: examples[en].append(ko)
    out={}
    for en,c in by.items():
        total=sum(c.values()); tone,n=c.most_common(1)[0]
        # Only trust when the same source consistently had one speech level.
        if n>=1 and n/total>=0.8:
            out[en]={"tone":tone,"confidence":round(n/total,3),"count":total}
    return out

STYLE_RULE=(
    "Dialogue style rule: preserve the speaker's social register and attitude, not English word order. "
    "Use surrounding dialogue, titles, commands, hostility, intimacy, rank, and explicit honorific cues. "
    "Do not arbitrarily switch between 반말, 해요체, and 합니다체 within the same conversational voice. "
    "If speaker/relationship is uncertain, prefer neutral natural 존댓말 rather than inventing intimacy or hierarchy. "
    "Hostile or explicitly casual dialogue may use 반말 when the English tone supports it. "
    "Character voice, sarcasm, jokes, and emotional shifts should remain audible in Korean."
)

TONE_HINT_TEXT={
    "FORMAL_HAPSYO":"Legacy style evidence for this exact line consistently used formal 합니다/하십시오체. Treat this only as a speech-level hint, not wording to copy.",
    "POLITE_HAEYO":"Legacy style evidence for this exact line consistently used 해요체. Treat this only as a speech-level hint, not wording to copy.",
    "PLAIN":"Legacy style evidence for this exact line consistently used plain/반말 style. Treat this only as a speech-level hint, not wording to copy.",
}

def load_speaker_map(path):
    out={}
    p=Path(path)
    if not p.exists():
        return out
    with p.open(encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            out[(r.get("source_file",""),r.get("info_formid",""))]=r
    return out

def load_style_profiles(path):
    out={}
    p=Path(path)
    if not p.exists():
        return out
    with p.open(encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            name=(r.get("speaker_name") or "").strip()
            if name:
                out[name.casefold()]=r
    aliases={
        "brother martin":"martin septim",
        "dasheogorathvoice":"sheogorath",
    }
    for alias,canonical in aliases.items():
        if canonical in out:
            out[alias]=out[canonical]
    return out

def speaker_metadata(item,speaker_map,profiles):
    rec=speaker_map.get((item.get("source_file",""),item.get("formid","")))
    if not rec:
        return None,None
    names=[x for x in (rec.get("speaker_names") or "").split("|") if x]
    meta={
        "confidence":rec.get("speaker_confidence",""),
        "speaker_formids":rec.get("speaker_formids",""),
        "speaker_names":names,
        "evidence":rec.get("evidence",""),
    }
    profile=None
    if len(names)==1:
        profile=profiles.get(names[0].casefold())
    return meta,profile

def load_dialog_context_map(path):
    out={}
    p=Path(path)
    if not p.exists():
        return out
    with p.open(encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            out[(r.get("source_file",""),r.get("dial_formid",""))]=r
    return out

def dialogue_context_metadata(item,dialog_map):
    rec=dialog_map.get((item.get("source_file",""),item.get("parent_dialog_formid","")))
    if not rec:
        return None
    return {
        "topic_editor_id":rec.get("editor_id",""),
        "topic_name":rec.get("full",""),
        "dialogue_type":rec.get("dialogue_type_name",""),
        "addressee_hint":rec.get("addressee_hint",""),
    }
