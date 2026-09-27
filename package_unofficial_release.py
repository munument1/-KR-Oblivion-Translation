#!/usr/bin/env python3
"""Package verified latest-patch Korean ESPs for a separate Nexus upload."""

import argparse
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

OPTIONAL = {"Oblivion Citadel Door Fix.esp", "DLCThievesDen - Unofficial Patch - SSSB.esp"}
NO_TRANSLATION = {"UOP Vampire Aging & Face Fix.esp"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    audit = json.loads((args.stage / "release_audit.json").read_text(encoding="utf-8"))
    esp_files = sorted(args.stage.rglob("*.esp"))
    if len(esp_files) != 14 or set(audit) != {p.name for p in esp_files}:
        raise ValueError("Expected all 14 latest original patch ESPs and audit entries")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(args.output, "w", compression=ZIP_DEFLATED, compresslevel=6) as archive:
        main_count = optional_count = 0
        for path in esp_files:
            name = path.name
            if name in NO_TRANSLATION:
                if audit[name]["translated_fields"] != 0:
                    raise ValueError(f"Expected no translations for {name}")
                continue
            if audit[name]["translated_fields"] == 0:
                raise ValueError(f"Untranslated ESP unexpectedly included: {name}")
            if name in OPTIONAL:
                arcname = "Optional/" + name
                optional_count += 1
            else:
                arcname = name
                main_count += 1
            archive.write(path, arcname)
        archive.write("README_UOP_KR.md", "README_KR.md")
        archive.write(args.stage / "release_audit.json", "release_audit.json")
    if (main_count, optional_count) != (11, 2):
        raise ValueError(f"Unexpected package layout: {main_count} main, {optional_count} optional")
    print(args.output.resolve(), args.output.stat().st_size, "bytes,", main_count, "main ESPs,", optional_count, "optional ESPs")


if __name__ == "__main__":
    main()
