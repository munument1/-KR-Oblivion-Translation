#!/usr/bin/env python3
"""Recover Unicode from the inventoried legacy CSVs; never open game plugins."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from oblivion_korean_codec import decode_legacy, encode_legacy

ROOT = Path(__file__).resolve().parent

# The legacy CSVs normalized these punctuation characters for their font.
# Require an exact byte match after this documented normalization; retain the
# existing Unicode punctuation in the new output rather than rewriting it.
LEGACY_PUNCTUATION = str.maketrans({
    "“": '"', "”": '"', "‘": "'", "’": "'",
    "—": "-", "–": "-", "―": "-", "…": "...", "\u00a0": " ",
})


def audit(inventory: Path, output: Path) -> dict:
    if output.resolve() == ROOT.resolve():
        raise ValueError("Output must be separate from the source CSV directory")
    output.mkdir(parents=True, exist_ok=True)
    results = []
    for spec in json.loads(inventory.read_text(encoding="utf-8")):
        source = ROOT / spec["file"]
        column = spec.get("hex_column")
        if not column:
            continue
        counts = Counter()
        failures = []
        prepared = []
        with source.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            fields = list(reader.fieldnames or [])
            for row_number, row in enumerate(reader, 2):
                counts["rows"] += 1
                value = row.get(column, "")
                try:
                    legacy = bytes.fromhex(value)
                    if not legacy.endswith(b"\0") or b"\0" in legacy[:-1]:
                        raise ValueError("Expected exactly one terminal NUL")
                    text = decode_legacy(legacy[:-1])
                    original_text = row.get(spec.get("text_column") or "", "")
                    if original_text:
                        try:
                            original_encoded = encode_legacy(original_text)
                        except UnicodeEncodeError:
                            original_encoded = None
                        if original_encoded != legacy[:-1]:
                            normalized = original_text.translate(LEGACY_PUNCTUATION)
                            if encode_legacy(normalized) != legacy[:-1]:
                                raise ValueError("Existing Unicode text differs from legacy bytes")
                            counts["verified_legacy_punctuation_normalization"] += 1
                        text = original_text
                    counts["decoded"] += 1
                    if not original_text:
                        counts["recovered_without_unicode"] += 1
                    row["obcjk_unicode_text"] = text
                    row["obcjk_utf8_hex"] = (text.encode("utf-8") + b"\0").hex()
                    row["obcjk_conversion_status"] = "verified"
                except (UnicodeError, ValueError) as error:
                    counts["failed"] += 1
                    failures.append({"row": row_number, "reason": str(error)})
                    row["obcjk_unicode_text"] = ""
                    row["obcjk_utf8_hex"] = ""
                    row["obcjk_conversion_status"] = "blocked"
                prepared.append(row)
        with (output / source.name).open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fields + ["obcjk_unicode_text", "obcjk_utf8_hex", "obcjk_conversion_status"])
            writer.writeheader()
            writer.writerows(prepared)
        results.append({
            "file": source.name,
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            **counts,
            "failures": failures,
        })
    report = {
        "scope": "CSV text only; duplicates are not effective plugin-record counts",
        "sources_unchanged": True,
        "rows": sum(item["rows"] for item in results),
        "decoded": sum(item.get("decoded", 0) for item in results),
        "failed": sum(item.get("failed", 0) for item in results),
        "recovered_without_unicode": sum(item.get("recovered_without_unicode", 0) for item in results),
        "files": results,
    }
    (output / "audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, default=ROOT / "docs/obcjk/csv_inventory.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.inventory, args.output)
    print(json.dumps({key: value for key, value in report.items() if key != "files"}, ensure_ascii=False, indent=2))
    if report["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
