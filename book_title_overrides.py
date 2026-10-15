"""Conservative, FormID-scoped corrections for canonical UTF-8 book titles.

The large canonical source remains immutable; these tracked overrides are applied
at build time without altering the book body or the existing volume suffix.
"""
from __future__ import annotations

import csv
from dataclasses import replace
from pathlib import Path


def apply_book_title_overrides(translations, path: Path) -> int:
    total = 0
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            if row["record_type"] != "BOOK" or row["field"] != "FULL":
                raise ValueError("Book title overrides may only affect BOOK/FULL")
            key = (row["effective_source"], b"BOOK", int(row["raw_formid"], 16), b"FULL")
            items = translations.get(key)
            if not items:
                raise ValueError(f"Book title override has no translation records: {key}")
            old_label, new_label = row["find_korean"], row["replace_korean"]
            if not old_label or not new_label or old_label == new_label:
                raise ValueError(f"Invalid book title override: {key}")
            matched = False
            for index, item in enumerate(items):
                if item.english != row["old_english"]:
                    continue
                if not item.korean.endswith(b"\0") or b"\0" in item.korean[:-1]:
                    raise ValueError(f"Invalid book title string: {key}")
                title = item.korean[:-1].decode("utf-8")
                if old_label in title:
                    replacement = title.replace(old_label, new_label).encode("utf-8") + b"\0"
                    items[index] = replace(item, korean=replacement)
                    total += 1
                    matched = True
                elif new_label in title:
                    matched = True
            if not matched:
                raise ValueError(f"Book title override did not match either title spelling: {key}")
    return total
