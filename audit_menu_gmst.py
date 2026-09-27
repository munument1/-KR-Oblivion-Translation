#!/usr/bin/env python3
"""Inventory candidate string GMST defaults in the original Oblivion.exe.

This is a candidate audit, not a safe-to-install translation list. An English
default must be verified in game before adding a translation override.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

PAIR = re.compile(rb"(?<![A-Za-z0-9_])(s[A-Z][A-Za-z0-9_]{2,60})\x00{1,4}([\x20-\x7e]{1,180})\x00")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    candidates = {}
    for match in PAIR.finditer(args.exe.read_bytes()):
        key = match[1].decode("ascii")
        english = match[2].decode("ascii")
        if re.fullmatch(r"[sifb][A-Z][A-Za-z0-9_]+", english):
            continue
        candidates.setdefault((key, english), match.start())

    def category(value: str) -> str:
        if "\\" in value or "/" in value or re.search(r"\.(?:dds|nif|wav|mp3|xml|bik)$", value, re.I):
            return "asset_or_path"
        return "text_candidate"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("gmst", "exe_english_candidate", "exe_offset_hex", "candidate_kind", "review_status"))
        for (key, english), offset in sorted(candidates.items()):
            writer.writerow((key, english, f"{offset:08X}", category(english), "unverified"))
    print(f"Executable string-setting candidates: {len(candidates)}")
    print(f"Text candidates (paths excluded): {sum(category(english) == 'text_candidate' for _, english in candidates)}")
    print(f"Audit: {args.output}")


if __name__ == "__main__":
    main()
