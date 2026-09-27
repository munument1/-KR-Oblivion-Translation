#!/usr/bin/env python3
"""Audit/recover all legacy Korean text carried by the old integrated UOP.

Unlike extract_legacy_carrier_memory.py this does NOT exclude records that also
exist in the latest UOP and does NOT discard repeated text fields. Matching is
record type + base FormID + EditorID + text-field occurrence against the
original Oblivion.esm. Output is translation-memory CSV only; gameplay records
are never copied.
"""
from __future__ import annotations
import argparse, csv
from collections import Counter, defaultdict
from pathlib import Path
from build_unofficial_release import TEXT_FIELDS, read_records
from build_vanilla_overlay import decode_english

UNSAFE = {(b"CELL", b"FULL"), (b"WRLD", b"FULL")}

def indexed_fields(fields):
    seen=Counter()
    out=[]
    stage=None
    stage_seen=Counter()
    for field,value in fields:
        if field==b"INDX":
            stage=int.from_bytes(value,"little")
        if field not in TEXT_FIELDS:
            continue
        occurrence=seen[field]; seen[field]+=1
        stage_occurrence=None
        if field==b"CNAM" and stage is not None:
            stage_occurrence=stage_seen[stage]; stage_seen[stage]+=1
        out.append((field,occurrence,stage,stage_occurrence,value))
    return out

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--legacy-uop",type=Path,required=True)
    p.add_argument("--original-esm",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--summary",type=Path)
    args=p.parse_args()
    legacy=read_records(args.legacy_uop)
    original=read_records(args.original_esm)
    rows=[]; counts=Counter(); by_type=Counter()
    for key,source_fields in original.items():
        kind,formid=key
        target_fields=legacy.get(key)
        if target_fields is None:
            continue
        source_editor=next((v.rstrip(b"\0") for f,v in source_fields if f==b"EDID"),b"")
        target_editor=next((v.rstrip(b"\0") for f,v in target_fields if f==b"EDID"),b"")
        if source_editor!=target_editor:
            counts["editorid_mismatch"]+=1
            continue
        src=indexed_fields(source_fields)
        dst=indexed_fields(target_fields)
        dst_map=defaultdict(list)
        for item in dst:
            dst_map[(item[0],item[1])].append(item)
        for field,occ,stage,stage_occ,english in src:
            counts["source_text_fields"]+=1
            candidates=dst_map.get((field,occ),())
            if len(candidates)!=1:
                counts["missing_or_ambiguous_occurrence"]+=1
                continue
            korean=candidates[0][4]
            if english==korean:
                counts["unchanged"]+=1
                continue
            if not english.endswith(b"\0") or not korean.endswith(b"\0"):
                counts["non_string"]+=1; continue
            if b"\0" in english[:-1] or b"\0" in korean[:-1]:
                counts["embedded_nul"]+=1; continue
            if not any(x>=128 for x in korean[:-1]):
                counts["changed_ascii_only"]+=1; continue
            unsafe=(kind,field) in UNSAFE
            rows.append({
                "effective_source":"Unofficial Oblivion Patch.esp",
                "record_type":kind.decode("ascii"),"raw_formid":f"{formid:08X}",
                "field":field.decode("ascii"),"occurrence":occ,
                "quest_stage":"" if stage is None else stage,
                "stage_occurrence":"" if stage_occ is None else stage_occ,
                "old_english":decode_english(english),"new_korean":"",
                "locres_key":"legacy_full_occurrence_recovery",
                "new_bytes_hex":korean.hex(),
                "editor_id":source_editor.decode("ascii","replace"),
                "apply_allowed":"no" if unsafe else "yes",
            })
            counts["recovered_candidates"]+=1
            if unsafe: counts["save_unsafe_audit_only"]+=1
            else: counts["recoverable_apply"]+=1
            by_type[(kind.decode("ascii"),field.decode("ascii"))]+=1
    args.output.parent.mkdir(parents=True,exist_ok=True)
    fields=("effective_source","record_type","raw_formid","field","occurrence",
            "quest_stage","stage_occurrence","old_english","new_korean",
            "locres_key","new_bytes_hex","editor_id","apply_allowed")
    with args.output.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
    summary=args.summary or args.output.with_suffix(".summary.txt")
    lines=[f"{k}={v}" for k,v in sorted(counts.items())]
    lines+=["", "[record_type/field]"]
    lines += [f"{kind}/{field}={n}" for (kind,field),n in sorted(by_type.items())]
    summary.write_text("\n".join(lines)+"\n",encoding="utf-8")
    print("recovered",counts["recovered_candidates"],
          "apply",counts["recoverable_apply"],
          "audit-only locations",counts["save_unsafe_audit_only"])

if __name__=="__main__":
    main()
