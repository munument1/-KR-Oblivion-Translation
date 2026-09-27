#!/usr/bin/env python3
"""Build a Korean Oblivion mod overlay from the user's original game files.

The patcher edits existing string subrecords after exact source checks and adds
verified executable string settings. It never creates gameplay records.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import struct
import sys
import zlib
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

HERE = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
MASTER = "Oblivion.esm"
# The executable supplies these default GMSTs, but the original ESM has no
# records for them. The question's Hangul bytes come from verified CSV strings;
# "취소" uses the existing translated menus/strings.xml entry.
BASE_MENU_GMSTS = (
    (0x00F00001, b"sExitGameAffirm\0", b"Exit Game\0",
     bytes.fromhex("b08bd7a90520c8a408c38500")),
    (0x00F00002, b"sExitGameQuestion\0", b"Exit the game?\0",
     bytes.fromhex("b08bd7a905c7a80420c8a408c385bd80b689d0ab14c6a806b189be803f00")),
    (0x00F00003, b"sCancel\0", b"Cancel\0",
     bytes.fromhex("d997c68400")),
)
EXE_GMST_PATTERN = re.compile(rb"(?<![A-Za-z0-9_])(s[A-Z][A-Za-z0-9_]{2,60})\x00{1,4}([\x20-\x7e]{1,180})\x00")
PRINTF_PATTERN = re.compile(r"%(?:[-+0#]*\d*(?:\.\d+)?[a-zA-Z%])")
OFFICIAL = (
    MASTER, "Knights.esp", "DLCBattlehornCastle.esp", "DLCFrostcrag.esp",
    "DLCThievesDen.esp", "DLCSpellTomes.esp", "DLCMehrunesRazor.esp",
    "DLCVileLair.esp", "DLCOrrery.esp", "DLCHorseArmor.esp",
    "DLCShiveringIsles.esp",
)
PATCH_TO_OFFICIAL = {
    "Unofficial Oblivion Patch.esp": MASTER,
    "Unofficial Shivering Isles Patch.esp": MASTER,
    **{f"{name[:-4]} - Unofficial Patch.esp": name for name in OFFICIAL[1:]},
}
SOURCE_RANK = {name: 0 for name in OFFICIAL}
SOURCE_RANK.update({"Unofficial Shivering Isles Patch.esp": 1,
                    "Unofficial Oblivion Patch.esp": 2})


@dataclass(frozen=True)
class Translation:
    source: str
    record_type: bytes
    formid: int
    field: bytes
    english: str
    korean: bytes
    line: int


def load_translations(path: Path):
    table = defaultdict(list)
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for line, row in enumerate(csv.DictReader(stream), 2):
            source = row["effective_source"]
            target = source if source in OFFICIAL else PATCH_TO_OFFICIAL.get(source)
            if target is None:
                continue
            # Oblivion uses the current cell/world name in menu save filenames.
            # Legacy Korean byte strings can contain control bytes and make a
            # menu save silently fail, even while autosaves and console saves work.
            if row["record_type"] in ("CELL", "WRLD") and row["field"] == "FULL":
                continue
            formid = int(row["raw_formid"], 16)
            # The original audit used 01 as the isolated official DLC's slot.
            if (formid >> 24) != (0 if target == MASTER else 1):
                continue
            korean = bytes.fromhex(row["new_bytes_hex"])
            if not korean.endswith(b"\0") or b"\0" in korean[:-1]:
                raise ValueError(f"CSV line {line}: invalid encoded string")
            item = Translation(source, row["record_type"].encode("ascii"),
                               formid, row["field"].encode("ascii"),
                               row["old_english"], korean, line)
            table[(target, item.record_type, formid & 0xFFFFFF, item.field)].append(item)
    return table


def decode_english(data: bytes) -> str:
    raw = data.rstrip(b"\0")
    try:
        return raw.decode("cp1252")
    except UnicodeDecodeError:
        return raw.decode("latin1")


def parse_subrecords(data: bytes):
    pos = 0
    while pos < len(data):
        start = pos
        if pos + 6 > len(data):
            raise ValueError("truncated subrecord header")
        kind = data[pos:pos + 4]
        size = struct.unpack_from("<H", data, pos + 4)[0]
        pos += 6
        if kind == b"XXXX":
            if size != 4 or pos + 10 > len(data):
                raise ValueError("invalid XXXX subrecord")
            size = struct.unpack_from("<I", data, pos)[0]
            pos += 4
            kind = data[pos:pos + 4]
            pos += 6
        if pos + size > len(data):
            raise ValueError("subrecord extends past record")
        yield kind, data[pos:pos + size], data[start:pos + size]
        pos += size


def existing_gmst_keys(path: Path) -> set[bytes]:
    keys = set()
    with path.open("rb") as stream:
        def walk(end):
            while stream.tell() < end:
                start = stream.tell()
                header = stream.read(20)
                if len(header) != 20:
                    raise ValueError(f"{path.name}: truncated record at {start}")
                kind, size = struct.unpack_from("<4sI", header)
                if kind == b"GRUP":
                    if size < 20 or start + size > end:
                        raise ValueError(f"{path.name}: invalid group at {start}")
                    walk(start + size)
                elif kind == b"GMST":
                    body = stream.read(size)
                    for field, value, _ in parse_subrecords(body):
                        if field == b"EDID":
                            keys.add(value.rstrip(b"\0"))
                            break
                else:
                    stream.seek(size, 1)
            if stream.tell() != end:
                raise ValueError(f"{path.name}: group boundary mismatch")
        walk(path.stat().st_size)
    return keys


def load_exe_menu_gmsts(csv_path: Path, exe_path: Path, esm_path: Path):
    if not exe_path.is_file():
        raise ValueError(f"Oblivion.exe is required beside the Data folder: {exe_path}")
    defaults = {(match[1], match[2]) for match in EXE_GMST_PATTERN.finditer(exe_path.read_bytes())}
    existing = existing_gmst_keys(esm_path)
    result = list(BASE_MENU_GMSTS)
    seen = {row[1].rstrip(b"\0") for row in result}
    with csv_path.open(encoding="utf-8-sig", newline="") as stream:
        for line, row in enumerate(csv.DictReader(stream), 2):
            key = row["gmst"].encode("ascii")
            english = row["exe_english"].encode("ascii")
            korean = bytes.fromhex(row["encoded_hex"])
            if (key, english) not in defaults:
                raise ValueError(f"EXE default differs from translation CSV line {line}: {row['gmst']}")
            if key in seen or not re.fullmatch(rb"s[A-Z][A-Za-z0-9_]*", key):
                raise ValueError(f"duplicate or invalid GMST key at CSV line {line}")
            if not korean.endswith(b"\0") or b"\0" in korean[:-1]:
                raise ValueError(f"invalid GMST translation bytes at CSV line {line}")
            if PRINTF_PATTERN.findall(row["exe_english"]) != PRINTF_PATTERN.findall(row["korean"]):
                raise ValueError(f"GMST placeholder mismatch at CSV line {line}")
            if key not in existing:
                formid = 0x00F00001 + len(result)
                result.append((formid, key + b"\0", english + b"\0", korean))
            seen.add(key)
    return tuple(result)


def load_quest_loading_translations(path: Path):
    quest = {}
    loading = {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for line, row in enumerate(csv.DictReader(stream), 2):
            kind = row["record_type"]
            formid = int(row["formid"], 16)
            editor_id = row["editor_id"].encode("ascii")
            source = bytes.fromhex(row["source_hex"])
            target = bytes.fromhex(row["encoded_hex"])
            if not source.endswith(b"\0") or not target.endswith(b"\0") or b"\0" in target[:-1]:
                raise ValueError(f"invalid journal/loading text at CSV line {line}")
            if kind == "QUST":
                key = (formid, int(row["stage"]), int(row["occurrence"]))
                dest = quest
            elif kind == "LSCR":
                key = formid
                dest = loading
            else:
                raise ValueError(f"invalid journal/loading record type at CSV line {line}")
            if key in dest:
                raise ValueError(f"duplicate journal/loading key at CSV line {line}")
            dest[key] = (editor_id, source, target, line)
    return quest, loading


def encode_subrecord(kind: bytes, value: bytes) -> bytes:
    if len(value) <= 0xFFFF:
        return kind + struct.pack("<H", len(value)) + value
    return b"XXXX\x04\x00" + struct.pack("<I", len(value)) + kind + b"\0\0" + value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def structure_signature(path: Path, skip_formids=frozenset()):
    """Check container bounds and preserve record identity and compiled scripts."""
    digest = hashlib.sha256()
    scripts = hashlib.sha256()
    records = groups = 0
    with path.open("rb") as stream:
        def walk(end):
            nonlocal records, groups
            while stream.tell() < end:
                start = stream.tell()
                header = stream.read(20)
                if len(header) != 20:
                    raise ValueError(f"{path.name}: short header at {start}")
                kind, size = struct.unpack_from("<4sI", header)
                if kind == b"GRUP":
                    if size < 20 or start + size > end:
                        raise ValueError(f"{path.name}: bad GRUP at {start}")
                    groups += 1
                    digest.update(header[:4] + header[8:])
                    walk(start + size)
                else:
                    if start + 20 + size > end:
                        raise ValueError(f"{path.name}: bad record at {start}")
                    formid = struct.unpack_from("<I", header, 12)[0]
                    if formid in skip_formids:
                        stream.seek(size, 1)
                        continue
                    records += 1
                    digest.update(header[:4] + header[8:])
                    if kind == b"SCPT":
                        scripts.update(header[:4] + header[8:])
                        remaining = size
                        while remaining:
                            block = stream.read(min(remaining, 1 << 20))
                            scripts.update(block)
                            remaining -= len(block)
                    elif kind in (b"QUST", b"INFO"):
                        body = stream.read(size)
                        if struct.unpack_from("<I", header, 8)[0] & 0x00040000:
                            body = zlib.decompress(body[4:])
                        scripts.update(header[:4] + header[8:])
                        for field, _, original in parse_subrecords(body):
                            if field in (b"SCHR", b"SCDA", b"SCTX", b"SCRO"):
                                scripts.update(original)
                    else:
                        stream.seek(size, 1)
            if stream.tell() != end:
                raise ValueError(f"{path.name}: container mismatch")

        walk(path.stat().st_size)
    return {"records": records, "groups": groups,
            "identity_sha256": digest.hexdigest(), "scripts_sha256": scripts.hexdigest()}


def patch_record(data: bytes, filename: str, record_type: bytes, formid: int,
                 translations, counts: Counter, audit: list[dict],
                 quest_texts=None, loading_texts=None) -> bytes:
    parts = list(parse_subrecords(data))
    editor_id = next((value.rstrip(b"\0") for field, value, _ in parts if field == b"EDID"), b"")
    changed = False
    output = []
    stage = None
    stage_occurrences = Counter()
    for field, value, original in parts:
        if record_type == b"QUST" and field == b"INDX":
            stage = int.from_bytes(value, "little")
        special = None
        if record_type == b"QUST" and field == b"CNAM" and stage is not None and quest_texts:
            occurrence = stage_occurrences[stage]
            stage_occurrences[stage] += 1
            special = quest_texts.get((formid, stage, occurrence))
        elif record_type == b"LSCR" and field == b"DESC" and loading_texts:
            special = loading_texts.get(formid)
        if special is not None:
            expected_editor, expected_source, replacement, line = special
            if editor_id != expected_editor or value != expected_source:
                raise ValueError(f"journal/loading source mismatch: {filename} {formid:08X} CSV line {line}")
            output.append(encode_subrecord(field, replacement))
            changed = True
            counts["journal_loading"] += 1
            counts["applied"] += 1
            audit.append({"file": filename, "type": record_type.decode("ascii"),
                          "formid": f"{formid:08X}", "field": field.decode("ascii"),
                          "source_sha256": hashlib.sha256(value).hexdigest(),
                          "source": decode_english(value),
                          "translation_sources": ["legacy original Korean patch journal/loading"]})
            continue
        candidates = translations.get((filename, record_type, formid & 0xFFFFFF, field), ())
        if not candidates:
            output.append(original)
            continue
        english = decode_english(value)
        matches = [x for x in candidates if x.english == english]
        if not matches:
            output.append(original)
            continue
        # The same English string may occur in duplicate CSV rows. Apply only
        # if all matching rows agree on the encoded replacement.
        replacements = {x.korean for x in matches}
        if len(replacements) != 1:
            counts["ambiguous"] += 1
            output.append(original)
            continue
        replacement = replacements.pop()
        if replacement == value:
            output.append(original)
            continue
        output.append(encode_subrecord(field, replacement))
        changed = True
        counts["applied"] += 1
        audit.append({"file": filename, "type": record_type.decode("ascii"),
                      "formid": f"{formid:08X}", "field": field.decode("ascii"),
                      "source_sha256": hashlib.sha256(value).hexdigest(),
                      "source": english, "translation_sources": sorted({x.source for x in matches})})
    return b"".join(output) if changed else data


def patch_plugin(source: Path, destination: Path, filename: str, translations,
                 counts: Counter, audit: list[dict], menu_gmsts=(),
                 quest_texts=None, loading_texts=None):
    destination.parent.mkdir(parents=True, exist_ok=True)
    menu_formids = frozenset(item[0] for item in menu_gmsts)
    with source.open("rb") as src, destination.open("w+b") as dst:
        limit = source.stat().st_size

        def walk(end: int):
            while src.tell() < end:
                start = src.tell()
                header = src.read(20)
                if len(header) != 20:
                    raise ValueError(f"{filename}: truncated record at {start}")
                kind, size = struct.unpack_from("<4sI", header)
                if kind == b"GRUP":
                    if size < 20 or start + size > end:
                        raise ValueError(f"{filename}: invalid group at {start}")
                    out_start = dst.tell()
                    dst.write(header)
                    walk(start + size)
                    if filename == MASTER and header[8:12] == b"GMST" and header[12:16] == b"\0\0\0\0":
                        for menu_formid, editor_id, english, korean in menu_gmsts:
                            menu_body = (encode_subrecord(b"EDID", editor_id) +
                                         encode_subrecord(b"DATA", korean))
                            dst.write(struct.pack("<4sIIII", b"GMST", len(menu_body), 0,
                                                  menu_formid, 0))
                            dst.write(menu_body)
                            counts["new_menu_gmst"] += 1
                            audit.append({"file": filename, "type": "GMST",
                                          "formid": f"{menu_formid:08X}", "field": "DATA",
                                          "source_sha256": hashlib.sha256(english).hexdigest(),
                                          "source": english[:-1].decode("ascii"),
                                          "translation_sources": ["menu GMST"]})
                    out_end = dst.tell()
                    dst.seek(out_start + 4)
                    dst.write(struct.pack("<I", out_end - out_start))
                    dst.seek(out_end)
                    continue
                if start + 20 + size > end:
                    raise ValueError(f"{filename}: invalid record at {start}")
                flags, formid = struct.unpack_from("<II", header, 8)
                if filename == MASTER and formid in menu_formids:
                    raise ValueError("menu GMST FormID collides with source record")
                if filename == MASTER and kind == b"TES4":
                    body = bytearray(src.read(size))
                    if body[:6] != b"HEDR\x0c\x00":
                        raise ValueError("unexpected TES4 HEDR layout")
                    old_count = struct.unpack_from("<I", body, 10)[0]
                    struct.pack_into("<I", body, 10, old_count + len(menu_gmsts))
                    dst.write(header)
                    dst.write(body)
                    continue
                has_special = (filename == MASTER and
                               ((kind == b"QUST" and quest_texts and formid in quest_texts["formids"]) or
                                (kind == b"LSCR" and loading_texts and formid in loading_texts)))
                if not has_special and not translations.get((filename, kind, formid & 0xFFFFFF, b"FULL")) and not any(
                        translations.get((filename, kind, formid & 0xFFFFFF, field))
                        for field in (b"DESC", b"NAM1", b"DATA")):
                    dst.write(header)
                    remaining = size
                    while remaining:
                        block = src.read(min(remaining, 1 << 20))
                        if not block:
                            raise ValueError(f"{filename}: truncated record data")
                        dst.write(block)
                        remaining -= len(block)
                    continue
                body = src.read(size)
                compressed = bool(flags & 0x00040000)
                if compressed:
                    if len(body) < 4:
                        raise ValueError(f"{filename}: short compressed record")
                    expected = struct.unpack_from("<I", body)[0]
                    plain = zlib.decompress(body[4:])
                    if len(plain) != expected:
                        raise ValueError(f"{filename}: bad compressed record")
                else:
                    plain = body
                updated = patch_record(plain, filename, kind, formid, translations, counts, audit,
                                       quest_texts["entries"] if has_special and kind == b"QUST" else None,
                                       loading_texts if has_special and kind == b"LSCR" else None)
                if updated != plain:
                    body = struct.pack("<I", len(updated)) + zlib.compress(updated) if compressed else updated
                    header = header[:4] + struct.pack("<I", len(body)) + header[8:]
                    counts["changed_records"] += 1
                dst.write(header)
                dst.write(body)
            if src.tell() != end:
                raise ValueError(f"{filename}: container size mismatch")

        walk(limit)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True, help="Original game Data directory (read only)")
    parser.add_argument("--output", type=Path, required=True, help="Destination MO2 mod or staging folder")
    parser.add_argument("--csv", type=Path, default=HERE / "applied_translations_v2.csv")
    parser.add_argument("--ini", type=Path, help="Optional active Oblivion.ini to update with a backup")
    args = parser.parse_args()
    source_dir = args.data_dir.resolve()
    output_dir = args.output.resolve()
    if source_dir == output_dir or source_dir in output_dir.parents or output_dir in source_dir.parents:
        parser.error("output must be separate from the source Data directory")
    table = load_translations(args.csv)
    if not (source_dir / MASTER).is_file():
        parser.error(f"{MASTER} is missing from {source_dir}")
    menu_gmsts = load_exe_menu_gmsts(HERE / "exe_gmst_translations.csv",
                                      source_dir.parent / "Oblivion.exe", source_dir / MASTER)
    menu_formids = frozenset(item[0] for item in menu_gmsts)
    quest_entries, loading_entries = load_quest_loading_translations(
        HERE / "quest_loading_translations.csv")
    quest_texts = {"entries": quest_entries,
                   "formids": frozenset(key[0] for key in quest_entries)}
    output_dir.mkdir(parents=True, exist_ok=True)
    audit = []
    report = {}
    for name in OFFICIAL:
        src = source_dir / name
        if not src.is_file():
            print(f"SKIP missing {name}")
            continue
        counts = Counter()
        target = output_dir / name
        temporary = output_dir / (name + ".building")
        try:
            patch_plugin(src, temporary, name, table, counts, audit,
                         menu_gmsts if name == MASTER else (),
                         quest_texts if name == MASTER else None,
                         loading_entries if name == MASTER else None)
            if name == MASTER and counts["applied"] < 9000:
                raise ValueError("Oblivion.esm does not match the expected original English source")
            original_structure = structure_signature(src)
            output_structure = structure_signature(
                temporary, menu_formids if name == MASTER else frozenset())
            if original_structure != output_structure:
                raise ValueError(f"{name}: record structure or compiled script changed")
            if name == MASTER and counts["new_menu_gmst"] != len(menu_gmsts):
                raise ValueError("unexpected menu GMST count")
            if name == MASTER and counts["journal_loading"] != len(quest_entries) + len(loading_entries):
                raise ValueError("journal/loading translation coverage mismatch")
            if counts["applied"]:
                temporary.replace(target)
            else:
                temporary.unlink()
                target.unlink(missing_ok=True)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        report[name] = {"source_sha256": sha256_file(src),
                        "applied_strings": counts["applied"],
                        "changed_records": counts["changed_records"],
                        "ambiguous": counts["ambiguous"],
                        "new_menu_gmst": counts["new_menu_gmst"],
                        "journal_loading": counts["journal_loading"],
                        "structure": original_structure,
                        "output_sha256": sha256_file(target) if target.exists() else None}
        print(f"{name}: {counts['applied']} strings in {counts['changed_records']} records")
    for asset in (HERE / "assets").rglob("*"):
        if asset.is_file():
            target = output_dir / asset.relative_to(HERE / "assets")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(asset, target)
    font_lines = {
        "SFontFile_1": r"Data\Fonts\TheGreatestKorean.fnt",
        "SFontFile_2": r"Data\Fonts\TheGreatestKorean_shadowed.fnt",
        "SFontFile_3": r"Data\Fonts\TheGreatestKorean_Small_FIXED.fnt",
    }
    snippet = "[Fonts]\n" + "".join(f"{key}={value}\n" for key, value in font_lines.items())
    (output_dir / "FONT_SETTINGS.txt").write_text(snippet, encoding="utf-8")
    if args.ini:
        ini = args.ini.resolve()
        if not ini.is_file():
            raise FileNotFoundError(f"INI not found: {ini}")
        raw = ini.read_bytes()
        content = raw.decode("cp1252")
        newline = "\r\n" if b"\r\n" in raw else "\n"
        lines = content.splitlines()
        section = None
        found = set()
        for i, line in enumerate(lines):
            stripped = line.strip()
            if re.fullmatch(r"\[[^\]]+\]", stripped):
                section = stripped[1:-1].lower()
            if section == "fonts":
                match = re.match(r"\s*(SFontFile_[123])\s*=", line, re.IGNORECASE)
                if match:
                    key = "SFontFile_" + match.group(1)[-1]
                    lines[i] = f"{key}={font_lines[key]}"
                    found.add(key)
        if len(found) != len(font_lines):
            try:
                pos = next(i for i, line in enumerate(lines) if line.strip().lower() == "[fonts]")
            except StopIteration:
                lines.extend(["", "[Fonts]"])
                pos = len(lines) - 1
            lines[pos + 1:pos + 1] = [f"{key}={value}" for key, value in font_lines.items() if key not in found]
        updated = (newline.join(lines) + newline).encode("cp1252")
        if updated != raw:
            backup = ini.with_name(ini.name + ".before_oblivion_kr.bak")
            if not backup.exists():
                shutil.copy2(ini, backup)
            ini.write_bytes(updated)
            print(f"Font INI updated (backup: {backup})")
    (output_dir / "translation_audit.json").write_text(
        json.dumps({"files": report, "applied": audit}, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
