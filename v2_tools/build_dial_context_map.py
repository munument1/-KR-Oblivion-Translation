from pathlib import Path
import csv,json,struct,sys,zlib
sys.path.insert(0,r"C:\오블리비언")
from build_vanilla_overlay import parse_subrecords,decode_english

ESM=Path(r"C:\Program Files (x86)\Steam\steamapps\common\Oblivion\Data\Oblivion.esm")
ROOT=Path(r"C:\오블리비언\v2_work")
OUT=ROOT/"02_source_extract"/"DIAL_CONTEXT_MAP.csv"

TYPE_NAMES={0:"TOPIC",1:"CONVERSATION",2:"COMBAT",3:"PERSUASION",4:"DETECTION",5:"SERVICE",6:"MISC"}
SPECIAL_CONVERSATION={"INFOGENERAL","HELLO","GOODBYE","IdleChatter"}
rows=[]
with ESM.open("rb") as stream:
    def walk(end):
        while stream.tell()<end:
            start=stream.tell()
            h=stream.read(20)
            if len(h)!=20:
                break
            kind,size,flags,formid,_=struct.unpack("<4sIIII",h)
            if kind==b"GRUP":
                walk(start+size)
                continue
            body=stream.read(size)
            if flags & 0x40000:
                body=zlib.decompress(body[4:])
            if kind!=b"DIAL":
                continue
            parts=list(parse_subrecords(body))
            edid=next((v.rstrip(b"\0").decode("ascii","replace") for f,v,_ in parts if f==b"EDID"),"")
            full=next((decode_english(v) for f,v,_ in parts if f==b"FULL"),"")
            data=next((v for f,v,_ in parts if f==b"DATA" and v),b"")
            dtype=data[0] if data else -1
            if dtype==0:
                target_hint="PLAYER_LIKELY"
            elif dtype==1 and edid in SPECIAL_CONVERSATION:
                target_hint="SPECIAL_CONVERSATION_OR_BARK"
            elif dtype==1:
                target_hint="NPC_CONVERSATION_OR_SCRIPTED"
            elif dtype in (3,5):
                target_hint="PLAYER_LIKELY"
            elif dtype in (2,4,6):
                target_hint="SITUATIONAL_TARGET"
            else:
                target_hint="UNKNOWN"
            rows.append({
                "source_file":"Oblivion.esm",
                "dial_formid":f"{formid:08X}",
                "editor_id":edid,
                "full":full,
                "dialogue_type":dtype,
                "dialogue_type_name":TYPE_NAMES.get(dtype,"UNKNOWN"),
                "addressee_hint":target_hint,
            })
    walk(ESM.stat().st_size)
fields=["source_file","dial_formid","editor_id","full","dialogue_type","dialogue_type_name","addressee_hint"]
with OUT.open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
counts={}
for r in rows:
    k=r["dialogue_type_name"]; counts[k]=counts.get(k,0)+1
report={"rows":len(rows),"type_counts":counts,"output":str(OUT)}
(ROOT/"02_source_extract"/"DIAL_CONTEXT_MAP_REPORT.json").write_text(
    json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(report,ensure_ascii=True,indent=2))
