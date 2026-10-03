from __future__ import annotations
import csv, hashlib, json, re, struct, sys, zlib
from collections import Counter
from pathlib import Path

REPO = Path(r"D:\Codex_Trans\오블리비언")
ROOT = REPO / "v2_work"
OUT_DIR = ROOT / "02_source_extract"
OUT_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR = Path(r"C:\Games\Steam\steamapps\common\Oblivion\Data")
EXE_PATH = DATA_DIR.parent / "Oblivion.exe"
sys.path.insert(0, str(REPO))
from build_vanilla_overlay import OFFICIAL, EXE_GMST_PATTERN, decode_english, parse_subrecords

DESC_TYPES = {b"BOOK", b"CLAS", b"BSGN", b"RACE", b"SKIL", b"MGEF", b"LSCR"}
SKIP_RECORDS = {b"TES4", b"GRAS", b"LAND", b"PGRD", b"SCPT"}
STRING_GMST = re.compile(rb"s[A-Z][A-Za-z0-9_]*")

def is_text_field(kind, field, editor):
    if field == b"FULL":
        return True
    if field == b"DESC" and kind in DESC_TYPES:
        return True
    if kind == b"INFO" and field == b"NAM1":
        return True
    if kind == b"QUST" and field == b"CNAM":
        return True
    if kind == b"GMST" and field == b"DATA" and STRING_GMST.fullmatch(editor):
        return True
    return False

def candidate(value):
    if not value.endswith(b"\0") or not value.rstrip(b"\0"):
        return False
    text = decode_english(value)
    return any(ch.isalpha() for ch in text)
def safety(kind, field, text, editor):
    if kind == b"RACE" and field == b"FULL":
        return "KEEP_ENGLISH_RACE_FULL"
    if kind in (b"CELL", b"WRLD") and field == b"FULL":
        return "REVIEW_LOCATION_UNSAFE"
    if kind == b"DIAL" and field == b"FULL":
        return "TOPIC_STRUCTURE_CHECK"
    if kind == b"GMST" and field == b"DATA":
        return "MENU_GMST"
    if kind == b"MGEF" and field == b"FULL" and text == "Script Effect":
        return "REVIEW_INTERNAL"
    return "TRANSLATE"

def extract_file(path: Path):
    rows = []
    with path.open("rb") as stream:
        def walk(end, parent_dialog=""):
            while stream.tell() < end:
                start = stream.tell()
                header = stream.read(20)
                if len(header) != 20:
                    raise ValueError(f"{path.name}: short record at {start}")
                kind, size, flags, formid, _ = struct.unpack("<4sIIII", header)
                if kind == b"GRUP":
                    if size < 20 or start + size > end:
                        raise ValueError(f"{path.name}: invalid group at {start}")
                    group_type = struct.unpack_from("<I", header, 12)[0]
                    dialog = f"{struct.unpack_from('<I', header, 8)[0]:08X}" if group_type == 7 else parent_dialog
                    yield from walk(start + size, dialog)
                    continue
                if start + 20 + size > end:
                    raise ValueError(f"{path.name}: invalid record at {start}")
                if kind in SKIP_RECORDS:
                    stream.seek(size, 1); continue
                body = stream.read(size)
                if flags & 0x40000:
                    expected = struct.unpack_from("<I", body)[0]
                    body = zlib.decompress(body[4:])
                    if len(body) != expected:
                        raise ValueError(f"{path.name}: decompressed size mismatch")
                parts = list(parse_subrecords(body))
                editor_b = next((v.rstrip(b"\0") for f,v,_ in parts if f == b"EDID"), b"")
                editor = editor_b.decode("ascii", "replace")
                quest_formid = ""
                if kind == b"INFO":
                    qsti = next((v for f,v,_ in parts if f == b"QSTI" and len(v) >= 4), None)
                    if qsti is not None:
                        quest_formid = f"{struct.unpack_from('<I', qsti)[0]:08X}"
                seen = Counter(); stage_seen = Counter(); stage = None
                for field, value, _ in parts:
                    if kind == b"QUST" and field == b"INDX":
                        stage = int.from_bytes(value, "little")
                    if not is_text_field(kind, field, editor_b) or not candidate(value):
                        continue
                    if kind == b"QUST" and field == b"CNAM":
                        occurrence = stage_seen[stage]; stage_seen[stage] += 1
                    else:
                        occurrence = seen[field]; seen[field] += 1
                    text = decode_english(value)
                    yield {
                        "source_file": path.name,
                        "record_type": kind.decode("ascii", "replace"),
                        "formid": f"{formid:08X}",
                        "editor_id": editor,
                        "field": field.decode("ascii"),
                        "occurrence": occurrence,
                        "quest_stage": "" if stage is None or not (kind == b"QUST" and field == b"CNAM") else stage,
                        "parent_dialog_formid": parent_dialog if kind == b"INFO" else "",
                        "quest_formid": quest_formid,
                        "source_english": text,
                        "source_sha256": hashlib.sha256(value).hexdigest(),
                        "source_byte_length": len(value),
                        "safety": safety(kind, field, text, editor_b),
                    }
            if stream.tell() != end:
                raise ValueError(f"{path.name}: group boundary mismatch")
        yield from walk(path.stat().st_size)
def menu_master_rows():
    rows = []
    for name, mode in [("menu_gmst_existing_105.csv", "existing"), ("menu_gmst_new_821.csv", "new")]:
        p = REPO / name
        with p.open(encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                if mode == "existing":
                    fid, edid, eng = r["raw_formid"], r["editor_id"], r["old_english"]
                else:
                    fid, edid, eng = r["formid"], r["edid"], r["english"]
                rows.append({"source_file":"MENU_GMST_MASTER","record_type":"GMST",
                             "formid":fid.upper().removeprefix("0X"),"editor_id":edid,
                             "field":"DATA","occurrence":0,"quest_stage":"",
                             "parent_dialog_formid":"","quest_formid":"",
                             "source_english":eng,"source_sha256":"",
                             "source_byte_length":len(eng.encode("cp1252","replace"))+1,
                             "safety":"MENU_GMST"})
    return rows

def exe_rows():
    rows = []
    data = EXE_PATH.read_bytes()
    for m in EXE_GMST_PATTERN.finditer(data):
        edid = m[1].decode("ascii"); eng = m[2].decode("ascii")
        if not any(ch.isalpha() for ch in eng):
            continue
        rows.append({"source_file":"Oblivion.exe","record_type":"GMST_EXE",
                     "formid":"","editor_id":edid,"field":"DATA","occurrence":0,
                     "quest_stage":"","parent_dialog_formid":"","quest_formid":"",
                     "source_english":eng,
                     "source_sha256":hashlib.sha256(m[2]+b"\0").hexdigest(),
                     "source_byte_length":len(m[2])+1,"safety":"EXE_UI_CANDIDATE"})
    return rows
def main():
    rows=[]; stats={}
    for name in OFFICIAL:
        p=DATA_DIR/name
        if not p.is_file():
            continue
        rr=list(extract_file(p)); rows.extend(rr); stats[name]=len(rr)
    menu=menu_master_rows(); exe=exe_rows()
    rows.extend(menu); rows.extend(exe)
    fields=["source_file","record_type","formid","editor_id","field","occurrence",
            "quest_stage","parent_dialog_formid","quest_formid","source_english",
            "source_sha256","source_byte_length","safety"]
    with (OUT_DIR/"OBLIVION_SOURCE_ALL.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
    with (OUT_DIR/"MENU_GMST_MASTER_926.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(menu)
    safety_counts=Counter(r["safety"] for r in rows)
    combo_counts=Counter((r["record_type"],r["field"]) for r in rows)
    report={"official_files":stats,"plugin_rows":sum(stats.values()),
            "menu_master_rows":len(menu),"exe_candidates":len(exe),
            "all_rows":len(rows),"safety_counts":dict(safety_counts),
            "record_field_counts":{f"{a}/{b}":n for (a,b),n in combo_counts.most_common()}}
    (OUT_DIR/"OBLIVION_SOURCE_REPORT.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=True,indent=2))

if __name__=="__main__":
    main()
