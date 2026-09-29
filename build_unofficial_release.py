#!/usr/bin/env python3
"""Rebuild the permitted Korean UOP/USIP/UODP ESP overlay from latest originals.

The existing Korean ESPs are translation memory only. This tool copies the
latest original records and changes verified text subrecords, preserving every
other field and compiled script. CELL/WRLD names stay English for manual saves.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import struct
import zlib
from collections import Counter
from pathlib import Path

from build_vanilla_overlay import (decode_english, encode_subrecord, load_quest_loading_translations,
                                   load_translations, parse_subrecords, sha256_file,
                                   structure_signature)

PAIRS = (
    ("UOP", "Unofficial Oblivion Patch-KR"),
    ("USIP", "Unofficial Shivering Isles Patch-KR"),
    ("UODP", "Unofficial Oblivion DLC Patches-KR"),
)
TEXT_FIELDS = {b"FULL", b"DESC", b"NAM1", b"CNAM", b"DATA"}


def read_records(path: Path):
    result = {}
    with path.open("rb") as stream:
        def walk(end):
            while stream.tell() < end:
                start = stream.tell()
                header = stream.read(20)
                if len(header) != 20:
                    raise ValueError(f"{path.name}: short header at {start}")
                kind, size, flags, formid, _ = struct.unpack("<4sIIII", header)
                if kind == b"GRUP":
                    if size < 20 or start + size > end:
                        raise ValueError(f"{path.name}: invalid group")
                    walk(start + size)
                else:
                    if start + 20 + size > end:
                        raise ValueError(f"{path.name}: invalid record")
                    body = stream.read(size)
                    if flags & 0x40000:
                        expected = struct.unpack_from("<I", body)[0]
                        body = zlib.decompress(body[4:])
                        if len(body) != expected:
                            raise ValueError(f"{path.name}: bad compression")
                    key = (kind, formid)
                    if key in result:
                        raise ValueError(f"{path.name}: duplicate record {kind!r} {formid:08X}")
                    result[key] = [(field, value) for field, value, _ in parse_subrecords(body)]
            if stream.tell() != end:
                raise ValueError(f"{path.name}: group boundary mismatch")
        walk(path.stat().st_size)
    return result


def collect_changes(original: Path, prior: Path, vanilla_audit=None, vanilla_table=None, final_table=None,
                    quest_entries=None, loading_entries=None, completions=None, nexus_completions=None):
    old_records = read_records(original)
    kr_records = read_records(prior)
    if old_records.keys() != kr_records.keys():
        raise ValueError(f"{original.name}: record identities differ from Korean reference")
    changes = {}
    counts = Counter()
    if original.name in ("Unofficial Oblivion Patch.esp", "Unofficial Shivering Isles Patch.esp"):
        official = "Oblivion.esm"
    elif " - Unofficial Patch" in original.name:
        official = original.name.split(" - Unofficial Patch")[0] + ".esp"
    else:
        official = "Oblivion.esm"
    for key, old_fields in old_records.items():
        kr_fields = kr_records[key]
        if [field for field, _ in old_fields] != [field for field, _ in kr_fields]:
            raise ValueError(f"{original.name}: subrecord sequence differs at {key}")
        old_editor = next((value for field, value in old_fields if field == b"EDID"), b"")
        kr_editor = next((value for field, value in kr_fields if field == b"EDID"), b"")
        if old_editor != kr_editor:
            raise ValueError(f"{original.name}: EditorID differs at {key}")
        stage = None
        stage_occurrences = Counter()
        field_occurrences = Counter()
        for index, ((field, old), (_, new)) in enumerate(zip(old_fields, kr_fields)):
            field_occurrence = field_occurrences[field]
            field_occurrences[field] += 1
            if key[0] == b"QUST" and field == b"INDX":
                stage = int.from_bytes(old, "little")
            occurrence = None
            if key[0] == b"QUST" and field == b"CNAM" and stage is not None:
                occurrence = stage_occurrences[stage]
                stage_occurrences[stage] += 1
            if field not in TEXT_FIELDS:
                if old != new:
                    raise ValueError(f"{original.name}: non-text difference at {key} field {field!r}")
                continue
            if key[0] in (b"CELL", b"WRLD") and field == b"FULL":
                if old != new:
                    counts["save_unsafe_location_skipped"] += 1
                continue
            if not old.endswith(b"\0"):
                if old != new:
                    raise ValueError(f"{original.name}: non-text difference at {key} field {field!r}")
                continue
            if old != new and not new.endswith(b"\0"):
                raise ValueError(f"{original.name}: non-text difference at {key} field {field!r}")
            if b"\0" in old[:-1]:
                if old != new:
                    raise ValueError(f"{original.name}: embedded NUL at {key} field {field!r}")
                continue
            if old != new and b"\0" in new[:-1]:
                raise ValueError(f"{original.name}: embedded NUL at {key} field {field!r}")

            # Existing KR is the fallback for patch-specific text.
            replacement = new if old != new else None
            reviewed = None
            if vanilla_audit is not None:
                audit_key = (official, key[0].decode("ascii"), f"{key[1]:08X}",
                             field.decode("ascii"), hashlib.sha256(old).hexdigest())
                if audit_key in vanilla_audit:
                    candidates = vanilla_table.get((official, key[0], key[1], field), ())
                    targets = {x.korean for x in candidates if x.english == decode_english(old) and
                               (x.editor_id is None or x.editor_id == old_editor.rstrip(b"\0"))}
                    if len(targets) == 1:
                        reviewed = targets.pop()
                        replacement = reviewed
            # Final reviewed override has priority over all legacy translation memories.
            if final_table is not None:
                candidates = final_table.get((official, key[0], key[1], field), ())
                targets = {x.korean for x in candidates if x.english == decode_english(old) and
                           (x.editor_id is None or x.editor_id == old_editor.rstrip(b"\0"))}
                if len(targets) == 1:
                    reviewed = targets.pop()
                    replacement = reviewed
            if official == "Oblivion.esm" and quest_entries is not None:
                special = None
                if key[0] == b"QUST" and field == b"CNAM" and occurrence is not None:
                    special = quest_entries.get((key[1], stage, occurrence))
                elif key[0] == b"LSCR" and field == b"DESC":
                    special = loading_entries.get(key[1])
                if special and special[0] == old_editor.rstrip(b"\0") and special[1] == old:
                    reviewed = special[2]
                    replacement = reviewed
            completion = (completions or {}).get((original.name, key[0], key[1], field))
            if completion:
                if old != completion[0]:
                    raise ValueError(f"{original.name}: completion source mismatch at {key}")
                replacement = completion[1]
                counts["manual_completion"] += 1
            nx_occurrence = occurrence if (key[0] == b"QUST" and field == b"CNAM" and occurrence is not None) else field_occurrence
            nx_stage = stage if (key[0] == b"QUST" and field == b"CNAM") else None
            nx = (nexus_completions or {}).get((original.name, key[0], key[1], field, nx_occurrence, nx_stage))
            if nx:
                if old != nx[0]:
                    raise ValueError(f"{original.name}: nexus completion source mismatch at {key} {field!r} occ {nx_occurrence}")
                replacement = nx[1]
                counts["nexus_completion"] += 1
            if replacement is not None and replacement != old:
                changes.setdefault(key, {})[index] = (field, old, replacement)
                counts["translated_fields"] += 1
                if reviewed is not None:
                    counts["reviewed_base_translation"] += 1
                    if old != new and replacement != new:
                        counts["reviewed_base_overrode_prior_kr"] += 1
                elif old == new:
                    counts["restored_base_translation"] += 1
    return changes, counts

def rewrite(original: Path, destination: Path, changes):
    destination.parent.mkdir(parents=True, exist_ok=True)
    applied = 0
    with original.open("rb") as src, destination.open("w+b") as dst:
        def walk(end):
            nonlocal applied
            while src.tell() < end:
                start = src.tell()
                header = src.read(20)
                if len(header) != 20:
                    raise ValueError(f"{original.name}: truncated record")
                kind, size, flags, formid, _ = struct.unpack("<4sIIII", header)
                if kind == b"GRUP":
                    out_start = dst.tell()
                    dst.write(header)
                    walk(start + size)
                    out_end = dst.tell()
                    dst.seek(out_start + 4)
                    dst.write(struct.pack("<I", out_end - out_start))
                    dst.seek(out_end)
                    continue
                body = src.read(size)
                if len(body) != size:
                    raise ValueError(f"{original.name}: truncated body")
                replacements = changes.get((kind, formid))
                if replacements:
                    compressed = bool(flags & 0x40000)
                    plain = zlib.decompress(body[4:]) if compressed else body
                    parts = list(parse_subrecords(plain))
                    updated = []
                    for index, (field, value, raw) in enumerate(parts):
                        expected = replacements.get(index)
                        if expected:
                            if (field, value) != expected[:2]:
                                raise ValueError(f"{original.name}: source mismatch at {kind!r} {formid:08X}")
                            updated.append(encode_subrecord(field, expected[2]))
                            applied += 1
                        else:
                            updated.append(raw)
                    plain = b"".join(updated)
                    body = struct.pack("<I", len(plain)) + zlib.compress(plain) if compressed else plain
                    header = header[:4] + struct.pack("<I", len(body)) + header[8:]
                dst.write(header)
                dst.write(body)
            if src.tell() != end:
                raise ValueError(f"{original.name}: container mismatch")
        walk(original.stat().st_size)
    return applied


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="Folder with UOP/USIP/UODP original subfolders")
    parser.add_argument("--prior-kr", type=Path, required=True, help="Folder containing existing three *-KR MO2 mods")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--vanilla-audit", type=Path, help="Final vanilla build translation_audit.json")
    args = parser.parse_args()
    if args.vanilla_audit:
        data = json.loads(args.vanilla_audit.read_text(encoding="utf-8"))
        vanilla_audit = {(a["file"], a["type"], a["formid"], a["field"], a["source_sha256"])
                         for a in data["applied"]}
        root = Path(__file__).resolve().parent
        vanilla_table = load_translations(root / "applied_translations_v2.csv",
                                          (root / "vanilla_completion.csv",
                                           root / "patch_translation_memory.csv",
                                           root / "legacy_carrier_completion.csv",
                                           root / "legacy_full_recovery.csv",
                                           root / "remaster_exact_memory.csv",
                                           root / "remaster_info_memory.csv",
                                           root / "remaster_info_dlc_memory.csv",
                                           root / "remaster_questlog_memory.csv",
                                           root / "remaster_desc_memory.csv",
                                           root / "remaster_book_safe_memory.csv",
                                           root / "remaster_extended_memory.csv",
                                           root / "source_memory_recovery.csv",
                                           root / "quest_unique_stage_memory.csv",
                                           root / "manual_visible_memory.csv",
                                           root / "exe_gmst_existing.csv"))
        final_table = load_translations(root / "final_review_override.csv")
        quest_entries, loading_entries = load_quest_loading_translations(root / "quest_loading_translations.csv")
    else:
        vanilla_audit = vanilla_table = final_table = quest_entries = loading_entries = None
    completions = {}
    with (Path(__file__).resolve().parent / "patch_completion.csv").open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            key = (row["file"], row["record_type"].encode("ascii"),
                   int(row["formid"], 16), row["field"].encode("ascii"))
            if key in completions:
                raise ValueError(f"duplicate patch completion {key}")
            completions[key] = (bytes.fromhex(row["source_hex"]), bytes.fromhex(row["target_hex"]))
    nexus_completions = {}
    nexus_path = Path(__file__).resolve().parent / "_build" / "nexus_patch_completion.csv"
    if nexus_path.is_file():
        with nexus_path.open(encoding="utf-8-sig", newline="") as stream:
            for row in csv.DictReader(stream):
                key = (row["file"], row["record_type"].encode("ascii"), int(row["formid"], 16),
                       row["field"].encode("ascii"), int(row["occurrence"]),
                       int(row["quest_stage"]) if row["quest_stage"] else None)
                if key in nexus_completions:
                    raise ValueError(f"duplicate nexus completion {key}")
                nexus_completions[key] = (bytes.fromhex(row["source_hex"]), bytes.fromhex(row["target_hex"]))
    report = {}
    for source_folder, kr_folder in PAIRS:
        originals = sorted((args.source / source_folder).glob("*.esp"))
        if not originals:
            raise ValueError(f"No original ESPs in {args.source / source_folder}")
        for original in originals:
            prior = args.prior_kr / kr_folder / original.name
            if not prior.is_file():
                raise FileNotFoundError(prior)
            changes, counts = collect_changes(original, prior, vanilla_audit, vanilla_table, final_table,
                                              quest_entries, loading_entries, completions, nexus_completions)
            destination = args.output / kr_folder / original.name
            applied = rewrite(original, destination, changes)
            if applied != counts["translated_fields"]:
                raise ValueError(f"{original.name}: applied count mismatch")
            before = structure_signature(original)
            after = structure_signature(destination)
            if before != after:
                raise ValueError(f"{original.name}: structure or script differs")
            report[original.name] = {
                "source_sha256": sha256_file(original),
                "output_sha256": sha256_file(destination),
                "translated_fields": applied,
                "restored_base_translation": counts["restored_base_translation"],
                "reviewed_base_translation": counts["reviewed_base_translation"],
                "reviewed_base_overrode_prior_kr": counts["reviewed_base_overrode_prior_kr"],
                "manual_completion": counts["manual_completion"],
                "nexus_completion": counts["nexus_completion"],
                "location_fields_preserved_english": counts["save_unsafe_location_skipped"],
                "structure": before,
            }
            print(f"{original.name}: {applied} Korean fields; reviewed-base {counts['reviewed_base_translation']} (overrode prior KR {counts['reviewed_base_overrode_prior_kr']}), restored legacy-base {counts['restored_base_translation']}; {counts['save_unsafe_location_skipped']} location names kept English")
    (args.output / "release_audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
