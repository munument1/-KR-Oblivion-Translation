from __future__ import annotations
import csv,json
from pathlib import Path

ROOT=Path(r"C:\오블리비언\v2_work")
G=ROOT/"01_glossary"
REVIEW=G/"OBLIVION_SST_CONFLICT_REVIEW.csv"

DECISIONS={
"Travel to":("이동하기","SOL_CONFIRMED","Oblivion sTravelQuestion UI"),
"Imperial Legion":("제국군","SOL_CONFIRMED","Faction name; reject generic Imperial"),
"Frenzy":("광분","SOL_CONFIRMED","Magic effect/spell name"),
"Cure Poison":("독 치료","SOL_CONFIRMED","Magic effect/spell name"),
"Turn Undead":("언데드 퇴치","SOL_CONFIRMED","Magic effect/spell name"),
"Bone Break Fever":("골절열","SOL_CONFIRMED","Disease name"),
"Gold Necklace":("금 목걸이","SOL_CONFIRMED","Item name"),
"Boar Meat":("멧돼지 고기","SOL_CONFIRMED","Correct Korean spelling; reject 맷돼지"),
"Diamond":("다이아몬드","SOL_CONFIRMED","Remove Skyrim category prefix"),
"Emerald":("에메랄드","SOL_CONFIRMED","Remove Skyrim category prefix"),
"Sapphire":("사파이어","SOL_CONFIRMED","Remove Skyrim category prefix"),
"Ruby":("루비","SOL_CONFIRMED","Remove Skyrim category prefix"),
"Planter":("화분","SOL_CONFIRMED","EditorIDs are Upper/MiddleClassPlanter objects"),
"Weight":("저울추","SOL_OVERRIDE","EditorID UpperScaleWeight01; object, not body weight"),
"Dread Zombie":("공포의 좀비","SOL_OVERRIDE","Creature name; reject unrelated necromancy tier"),
"Soul Tomato":("영혼 토마토","SOL_CONFIRMED","Same English name for both Oblivion records"),
"Poison":("독","SOL_CONFIRMED","sMagicTypePoison UI"),
"Feed":("흡혈","SOL_CONTEXT_CONFIRMED","Oblivion editor ID sVampireFeed"),
"Reanimate":("시체 부활","SOL_CONFIRMED","Magic effect/spell; reject Skyrim tier label"),
"Absorb Health":("체력 흡수","SOL_CONFIRMED","Magic effect/spell"),
"Bound Dagger":("마법 단검","SOL_CONFIRMED","Magic effect/spell/weapon"),
"Ice Storm":("얼음 폭풍","SOL_CONFIRMED","Spell name"),
"Bench":("긴 의자","SOL_CONFIRMED","Furniture name"),
"Spellbreaker":("스펠브레이커","SOL_CONFIRMED","Established artifact transliteration"),
"Steel Arrow":("강철 화살","SOL_OVERRIDE","Remove Skyrim inventory category prefix"),
}
CONTEXT_SPECIFIC={
"Common":"Khajiit hair and soul-level UI use different senses; resolve per record/editor ID.",
"Light":"Armor weight and light magic effect use different senses; resolve per record/editor ID.",
}
def main():
    with REVIEW.open(encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f))
    for r in rows:
        src=r["source_english"]
        if r["bucket"]=="CONTEXTUAL_DIALOGUE":
            r["decision"]=""
            r["status"]="CONTEXTUAL_DIALOGUE"
            r["notes"]="Do not force global glossary; translate with speaker/quest/topic context."
        elif src in CONTEXT_SPECIFIC:
            r["decision"]=""
            r["status"]="CONTEXT_SPECIFIC"
            r["notes"]=CONTEXT_SPECIFIC[src]
        elif src in DECISIONS:
            decision,status,note=DECISIONS[src]
            r["decision"]=decision; r["status"]=status; r["notes"]=note
        else:
            raise RuntimeError(f"Unresolved non-dialogue conflict: {src}")
    fields=list(rows[0])
    with REVIEW.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

    final=[]
    with (G/"OBLIVION_GLOSSARY_SEED.csv").open(encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            final.append({"source_english":r["source_english"],"korean":r["korean"],
                          "provenance":"SST_UNAMBIGUOUS","review_status":"SEED",
                          "notes":""})
    for r in rows:
        if r["decision"]:
            final.append({"source_english":r["source_english"],"korean":r["decision"],
                          "provenance":"SST_CONFLICT_SOL_REVIEW",
                          "review_status":r["status"],"notes":r["notes"]})
    final.sort(key=lambda x:x["source_english"].casefold())
    with (G/"OBLIVION_GLOSSARY_V2_DRAFT.csv").open("w",encoding="utf-8-sig",newline="") as f:
        fields=["source_english","korean","provenance","review_status","notes"]
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(final)
    report={
        "seed_unambiguous":sum(x["provenance"]=="SST_UNAMBIGUOUS" for x in final),
        "sol_resolved_conflicts":sum(x["provenance"]=="SST_CONFLICT_SOL_REVIEW" for x in final),
        "draft_glossary_rows":len(final),
        "context_specific_non_dialogue":len(CONTEXT_SPECIFIC),
        "contextual_dialogue_deferred":sum(r["bucket"]=="CONTEXTUAL_DIALOGUE" for r in rows),
        "unresolved_non_dialogue":sum(r["bucket"]!="CONTEXTUAL_DIALOGUE" and not r["decision"] and r["status"]!="CONTEXT_SPECIFIC" for r in rows)
    }
    (G/"OBLIVION_GLOSSARY_V2_DRAFT_REPORT.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=True,indent=2))

if __name__=="__main__":
    main()