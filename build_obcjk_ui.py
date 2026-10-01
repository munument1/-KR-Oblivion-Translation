#!/usr/bin/env python3
"""Build a UTF-8 menu-text overlay, without reading or writing ESP/ESM files."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree

from oblivion_korean_codec import decode_legacy, encode_legacy

ROOT = Path(__file__).resolve().parent


def build(source: Path, output: Path) -> dict:
    if source.resolve() == output.resolve():
        raise ValueError("Output must be separate from the legacy menu source")
    legacy = source.read_bytes()
    text = decode_legacy(legacy)
    if encode_legacy(text) != legacy:
        raise ValueError("Source menu text failed exact legacy round-trip")
    if "\0" in text:
        raise ValueError("Menu XML contains an embedded NUL")
    # The legacy font used DEL around menu labels. GDI draws a missing-glyph
    # box for it; it carries no translated text and must not enter UTF-8 UI.
    legacy_del_markers = text.count("\x7f")
    text = text.replace("\x7f", "")
    root = ElementTree.fromstring(text)
    utf8 = text.encode("utf-8")
    if utf8.startswith(b"\xef\xbb\xbf"):
        raise ValueError("Menu XML must not contain a UTF-8 BOM")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(utf8)
    return {
        "scope": "menu XML only; no game plugin conversion",
        "source_sha256": hashlib.sha256(legacy).hexdigest(),
        "output_sha256": hashlib.sha256(utf8).hexdigest(),
        "legacy_bytes": len(legacy),
        "utf8_bytes": len(utf8),
        "xml_elements": sum(1 for _ in root.iter()),
        "hangul_characters": sum(0xAC00 <= ord(ch) <= 0xD7A3 for ch in text),
        "exact_legacy_roundtrip": True,
        "removed_legacy_del_markers": legacy_del_markers,
        "utf8_bom": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "assets/menus/strings.xml")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = build(args.source, args.output)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
