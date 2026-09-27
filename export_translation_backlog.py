#!/usr/bin/env python3
"""Export exact untranslated text fields from verified Original and UOP builds.

The CSV files are translation work queues. A Korean text cell is not directly
patchable until it is encoded with the project's custom Hangul byte map and
checked against the exact source hash and field identity.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import struct
import zlib
from collections import Counter
from pathlib import Path

from build_vanilla_overlay import EXE_GMST_PATTERN, OFFICIAL, decode_english, parse_subrecords

FIELDS = ("scope", "file", "record_type", "formid", "editor_id", "field",
          "occurrence", "quest_stage", "parent_dialog_formid", "source_english",
          "source_sha256", "source_byte_length", "korean_translation", "review_status", "notes")
FIELD_KINDS = {b"FULL", b"DESC", b"NAM1", b"CNAM", b"DATA"}


def text_field(kind: bytes, field: bytes, editor: bytes) -> bool:
    return (field in (b"FULL", b"DESC") or
            (kind == b"INFO" and field == b"NAM1") or
            (kind == b"QUST" and field == b"CNAM") or
            (kind == b"GMST" and field == b"DATA" and re.fullmatch(rb"s[A-Z][A-Za-z0-9_]*", editor)))


def records(path: Path):
    """Yield candidate text subrecords with exact occurrence and stage keys."""
    with path.open("rb") as stream:
        def walk(end: int, parent_dialog: str = ""):
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
                if kind in (b"TES4", b"GRAS", b"LAND", b"PGRD", b"SCPT"):
                    stream.seek(size, 1)
                    continue
                body = stream.read(size)
                if flags & 0x40000:
                    if len(body) < 4:
                        raise ValueError(f"{path.name}: short compressed record")
                    expected = struct.unpack_from("<I", body)[0]
                    body = zlib.decompress(body[4:])
                    if len(body) != expected:
                        raise ValueError(f"{path.name}: wrong decompressed size")
                parts = list(parse_subrecords(body))
                editor = next((value.rstrip(b"\0") for field, value, _ in parts if field == b"EDID"), b"")
                seen = Counter()
                stage = None
                stage_seen = Counter()
                for field, value, _ in parts:
                    if kind == b"QUST" and field == b"INDX":
                        stage = int.from_bytes(value, "little")
                    if field not in FIELD_KINDS or not text_field(kind, field, editor):
                        continue
                    if kind == b"QUST" and field == b"CNAM":
                        occurrence = stage_seen[stage]
                        stage_seen[stage] += 1
                    else:
                        occurrence = seen[field]
                        seen[field] += 1
                    yield ((kind.decode("ascii"), formid, field.decode("ascii"), stage if kind == b"QUST" and field == b"CNAM" else None, occurrence),
                           editor.decode("ascii", errors="replace"), parent_dialog if kind == b"INFO" else "", value)
            if stream.tell() != end:
                raise ValueError(f"{path.name}: group boundary mismatch")
        yield from walk(path.stat().st_size)


def candidate(value: bytes) -> bool:
    if not value.endswith(b"\0") or not value.rstrip(b"\0"):
        return False
    text = decode_english(value)
    return any("A" <= char <= "Z" or "a" <= char <= "z" for char in text)


def audit_pair(scope: str, source: Path, output: Path, writer: csv.DictWriter,
               summary: Counter, duplicate_hashes: set[str]):
    result = {}
    for key, editor, parent, value in records(output):
        if key in result:
            raise ValueError(f"{output.name}: duplicate field key {key}")
        result[key] = value
    for key, editor, parent, value in records(source):
        if not candidate(value):
            continue
        kind, formid, field, stage, occurrence = key
        category = f"{kind}/{field}"
        summary[(scope, "all", category)] += 1
        actual = result.get(key)
        if actual is None:
            raise ValueError(f"{output.name}: missing field {key}")
        if actual != value:
            summary[(scope, "translated", category)] += 1
            continue
        if kind in ("CELL", "WRLD") and field == "FULL":
            summary[(scope, "intentional_location", category)] += 1
            continue
        digest = hashlib.sha256(value).hexdigest()
        duplicate_hashes.add(digest)
        row = dict(zip(FIELDS, (scope, source.name, kind, f"{formid:08X}", editor, field,
                                      occurrence, stage if stage is not None else "", parent,
                                      decode_english(value), digest, len(value), "", "TODO", "")))
        if (kind, field, row["source_english"]) in (("DIAL", "FULL", "GREETING"),
                                                     ("MGEF", "FULL", "Script Effect")):
            row["review_status"] = "REVIEW_INTERNAL"
        writer.writerow(row)
        summary[(scope, "todo", category)] += 1


def exe_candidates(exe_path: Path, esm_output: Path, output_csv: Path):
    existing = {}
    for key, editor, _, value in records(esm_output):
        if key[0] == "GMST" and key[2] == "DATA":
            existing[editor] = value
    defaults = {}
    data = exe_path.read_bytes()
    for match in EXE_GMST_PATTERN.finditer(data):
        key = match[1].decode("ascii")
        english = match[2].decode("ascii")
        defaults[(key, english)] = match.start()
    total = covered = 0
    with output_csv.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=("gmst", "exe_english", "source_sha256",
                                                    "exe_offset_hex", "korean_translation", "review_status", "notes"))
        writer.writeheader()
        for (key, english), offset in sorted(defaults.items()):
            if not any(char.isalpha() for char in english):
                continue
            total += 1
            effective = existing.get(key)
            if effective is not None and effective != english.encode("ascii") + b"\0":
                covered += 1
                continue
            writer.writerow({"gmst": key, "exe_english": english,
                             "source_sha256": hashlib.sha256(english.encode("ascii") + b"\0").hexdigest(),
                             "exe_offset_hex": f"{offset:X}", "korean_translation": "",
                             "review_status": "REVIEW_UI_CANDIDATE", "notes": "게임 화면 노출 여부 확인 필요"})
    return {"exe_default_candidates": total, "covered_by_output_gmst": covered,
            "remaining_review_candidates": total - covered}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--vanilla-output", type=Path, required=True)
    parser.add_argument("--patch-source", type=Path, required=True)
    parser.add_argument("--patch-output", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    summary = Counter()
    unique = {}
    pairs = {
        "vanilla": [(args.data_dir / name, args.vanilla_output / name) for name in OFFICIAL
                    if (args.vanilla_output / name).is_file()],
        "unofficial": [],
    }
    for source_folder, output_folder in (("UOP", "Unofficial Oblivion Patch-KR"),
                                          ("USIP", "Unofficial Shivering Isles Patch-KR"),
                                          ("UODP", "Unofficial Oblivion DLC Patches-KR")):
        for source in sorted((args.patch_source / source_folder).glob("*.esp")):
            output = args.patch_output / output_folder / source.name
            if not output.is_file():
                raise FileNotFoundError(output)
            pairs["unofficial"].append((source, output))
    for scope, items in pairs.items():
        hashes = set()
        with (args.output / f"{scope}_translation_todo.csv").open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader()
            for source, output in items:
                audit_pair(scope, source, output, writer, summary, hashes)
        unique[scope] = len(hashes)
    exe = exe_candidates(args.data_dir.parent / "Oblivion.exe", args.vanilla_output / "Oblivion.esm",
                         args.output / "exe_gmst_review.csv")
    report = {"method": "Compare exact source and built output subrecord bytes, including field occurrence and quest stage. Only nonempty NUL-terminated strings containing ASCII letters are counted.",
              "included_fields": ["FULL", "DESC", "INFO/NAM1", "QUST/CNAM", "string GMST/DATA"],
              "counts_by_scope_status_type": {scope: {status: dict(sorted((category, count) for (s, t, category), count in summary.items() if s == scope and t == status))
                                                       for status in ("all", "translated", "todo", "intentional_location")}
                                              for scope in pairs},
              "unique_source_strings_in_todo": unique,
              "exe": exe,
              "notes": ["Source field occurrences are work units; identical English source strings can repeat in different contexts.",
                        "CELL/WRLD FULL remain English intentionally because translated location names caused manual save failures.",
                        "EXE GMST rows are candidates requiring an in-game visibility check; do not assume every row appears in menus.",
                        "A completed Korean cell must be encoded with the custom byte map and validated against source hash before plugin insertion."]}
    (args.output / "translation_backlog_summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for scope in pairs:
        print(scope, {status: sum(count for (s, t, _), count in summary.items() if s == scope and t == status)
                      for status in ("all", "translated", "todo", "intentional_location")},
              "unique_todo_sources", unique[scope])
    print("exe", exe)


if __name__ == "__main__":
    main()
