#!/usr/bin/env python3
"""Find unpatched vanilla FULL names with a uniquely translated identical name."""

import argparse
import csv
import json
import struct
import zlib
from collections import Counter, defaultdict
from pathlib import Path

from build_vanilla_overlay import OFFICIAL, decode_english, parse_subrecords


def scan(path):
    with path.open("rb") as stream:
        def walk(end):
            while stream.tell() < end:
                start = stream.tell()
                header = stream.read(20)
                if len(header) != 20:
                    raise ValueError((path, start))
                kind, size, flags, formid, _ = struct.unpack("<4sIIII", header)
                if kind == b"GRUP":
                    yield from walk(start + size)
                    continue
                if kind in (b"CELL", b"WRLD"):
                    stream.seek(size, 1)
                    continue
                body = stream.read(size)
                if flags & 0x40000:
                    body = zlib.decompress(body[4:])
                edid = b""
                full = None
                for field, value, _ in parse_subrecords(body):
                    if field == b"EDID":
                        edid = value.rstrip(b"\0")
                    if field == b"FULL":
                        full = value
                if full and full.endswith(b"\0") and all(32 <= n < 127 for n in full[:-1]):
                    yield kind.decode("ascii"), formid, edid.decode("ascii", "replace"), decode_english(full)
            if stream.tell() != end:
                raise ValueError((path, end))
        yield from walk(path.stat().st_size)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", type=Path, required=True)
    p.add_argument("--audit", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    translated = defaultdict(set)
    for csv_name in ("applied_translations_v2.csv", "vanilla_completion.csv"):
        with Path(csv_name).open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                if row["field"] == "FULL" and row["record_type"] not in ("CELL", "WRLD"):
                    translated[(row["record_type"], row["old_english"])].add(row["new_bytes_hex"])
    applied = {(a["file"], a["type"], a["formid"], a["field"])
               for a in json.loads(args.audit.read_text(encoding="utf-8"))["applied"]}
    candidates = []
    for file in OFFICIAL:
        source = args.data_dir / file
        if not source.is_file():
            continue
        for kind, formid, edid, english in scan(source):
            choices = translated.get((kind, english), set())
            if len(choices) != 1:
                continue
            if (file, kind, f"{formid:08X}", "FULL") in applied:
                continue
            candidates.append((file, kind, f"{formid:08X}", edid, english, next(iter(choices))))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(("file", "record_type", "formid", "editor_id", "english", "candidate_hex"))
        w.writerows(candidates)
    print("Candidates", len(candidates), "by file", Counter(row[0] for row in candidates))
    for row in candidates[:80]:
        print(*row[:5], sep=" | ")


if __name__ == "__main__":
    main()
