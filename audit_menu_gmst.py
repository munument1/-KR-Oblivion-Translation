#!/usr/bin/env python3
"""Find executable string GMST defaults absent from the original Oblivion.esm.

This is a candidate audit, not a safe-to-install translation list. An English
default must be verified in game before adding an ESM override.
"""

from __future__ import annotations

import argparse
import csv
import re
import struct
from pathlib import Path

from build_vanilla_overlay import parse_subrecords


PAIR = re.compile(rb"(?<![A-Za-z0-9_])(s[A-Z][A-Za-z0-9_]{2,60})\x00{1,4}([\x20-\x7e]{1,180})\x00")


def esm_game_settings(path: Path) -> set[str]:
    result = set()
    with path.open("rb") as stream:
        def walk(end: int) -> None:
            while stream.tell() < end:
                start = stream.tell()
                header = stream.read(20)
                if len(header) != 20:
                    raise ValueError(f"truncated record at {start}")
                kind, size = struct.unpack_from("<4sI", header)
                if kind == b"GRUP":
                    if size < 20 or start + size > end:
                        raise ValueError(f"invalid group at {start}")
                    walk(start + size)
                elif kind == b"GMST":
                    if start + 20 + size > end:
                        raise ValueError(f"invalid GMST at {start}")
                    for field, value, _ in parse_subrecords(stream.read(size)):
                        if field == b"EDID":
                            result.add(value.rstrip(b"\0").decode("ascii"))
                else:
                    stream.seek(size, 1)
            if stream.tell() != end:
                raise ValueError("group boundary mismatch")

        walk(path.stat().st_size)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--esm", type=Path, required=True)
    parser.add_argument("--locres-csv", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    existing = esm_game_settings(args.esm)
    translated = {}
    if args.locres_csv:
        with args.locres_csv.open(encoding="utf-8-sig", newline="") as stream:
            for row in csv.DictReader(stream):
                if row["key"].startswith("LOC_HC_MenuGamesettings_s"):
                    translated.setdefault(row["key"].removeprefix("LOC_HC_MenuGamesettings_"), []).append(row["localized"])

    candidates = {}
    for match in PAIR.finditer(args.exe.read_bytes()):
        key = match[1].decode("ascii")
        english = match[2].decode("ascii")
        if key in existing or re.fullmatch(r"[sifb][A-Z][A-Za-z0-9_]+", english):
            continue
        candidates.setdefault((key, english), match.start())

    def category(value: str) -> str:
        if "\\" in value or "/" in value or re.search(r"\.(?:dds|nif|wav|mp3|xml|bik)$", value, re.I):
            return "asset_or_path"
        return "text_candidate"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("gmst", "exe_english_candidate", "exe_offset_hex", "candidate_kind", "remastered_korean_by_key", "review_status"))
        for (key, english), offset in sorted(candidates.items()):
            writer.writerow((key, english, f"{offset:08X}", category(english), " | ".join(translated.get(key, [])), "unverified"))
    print(f"Original ESM string GMST keys: {sum(name.startswith('s') for name in existing)}")
    print(f"Executable candidates absent from ESM: {len(candidates)}")
    print(f"Text candidates (paths excluded): {sum(category(english) == 'text_candidate' for _, english in candidates)}")
    print(f"Text candidates with Remastered Korean by key: {sum(category(english) == 'text_candidate' and key in translated for key, english in candidates)}")
    print(f"Audit: {args.output}")


if __name__ == "__main__":
    main()
