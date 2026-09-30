from pathlib import Path
import csv, json, struct, sys, zlib
from collections import defaultdict
sys.path.insert(0, r"C:\오블리비언")
from build_vanilla_overlay import parse_subrecords, decode_english

ESM = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Oblivion\Data\Oblivion.esm")
ROOT = Path(r"C:\오블리비언\v2_work")
OUT = ROOT / "02_source_extract" / "INFO_SPEAKER_MAP.csv"
npc = {}
info_candidates = defaultdict(list)

def decode_body(flags, body):
    return zlib.decompress(body[4:]) if flags & 0x40000 else body
with ESM.open("rb") as stream:
    def walk(end):
        while stream.tell() < end:
            start = stream.tell()
            header = stream.read(20)
            if len(header) != 20:
                break
            kind, size, flags, formid, _ = struct.unpack("<4sIIII", header)
            if kind == b"GRUP":
                walk(start + size)
                continue
            parts = list(parse_subrecords(decode_body(flags, stream.read(size))))
            if kind == b"NPC_":
                edid = next((v.rstrip(b"\0").decode("ascii","replace") for f,v,_ in parts if f == b"EDID"), "")
                full = next((decode_english(v) for f,v,_ in parts if f == b"FULL"), "")
                npc[formid] = (edid, full)
            elif kind == b"INFO":
                for field, raw, _ in parts:
                    if field != b"CTDA" or len(raw) < 16:
                        continue
                    func = struct.unpack_from("<I", raw, 8)[0]
                    if func == 72:
                        info_candidates[formid].append(struct.unpack_from("<I", raw, 12)[0])
    walk(ESM.stat().st_size)
rows=[]
for info_formid, vals in sorted(info_candidates.items()):
    uniq=[]
    for x in vals:
        if x not in uniq:
            uniq.append(x)
    candidates=[]
    for fid in uniq:
        edid, name = npc.get(fid, ("",""))
        candidates.append({"formid":f"{fid:08X}","editor_id":edid,"name":name})
    exact=[x for x in candidates if x["editor_id"] or x["name"]]
    if len(exact)==1:
        confidence="EXACT_SINGLE"
    elif len(exact)>1:
        confidence="EXACT_SET"
    else:
        confidence="UNRESOLVED_ID"
    rows.append({
        "source_file":"Oblivion.esm",
        "info_formid":f"{info_formid:08X}",
        "speaker_confidence":confidence,
        "speaker_count":len(exact),
        "speaker_formids":"|".join(x["formid"] for x in exact),
        "speaker_names":"|".join(x["name"] or x["editor_id"] for x in exact),
        "speaker_editor_ids":"|".join(x["editor_id"] for x in exact),
        "evidence":"CTDA:GetIsID",
    })
fields=["source_file","info_formid","speaker_confidence","speaker_count",
        "speaker_formids","speaker_names","speaker_editor_ids","evidence"]
with OUT.open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

report={
    "npc_records":len(npc),
    "info_with_getisid":len(rows),
    "exact_single":sum(r["speaker_confidence"]=="EXACT_SINGLE" for r in rows),
    "exact_set":sum(r["speaker_confidence"]=="EXACT_SET" for r in rows),
    "unresolved_id":sum(r["speaker_confidence"]=="UNRESOLVED_ID" for r in rows),
    "output":str(OUT),
}
(ROOT/"02_source_extract"/"INFO_SPEAKER_MAP_REPORT.json").write_text(
    json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(report,ensure_ascii=True,indent=2))
