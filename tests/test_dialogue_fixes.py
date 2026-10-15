"""Regression coverage for scoped Gray Prince dialogue correction."""
import csv
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from build_vanilla_overlay import (
    encode_subrecord,
    load_translations,
    parse_subrecords,
    patch_record,
)

ROOT = Path(__file__).resolve().parents[1]
FIXES = ROOT / "canonical_dialogue_fixes_v1.csv"


class DialogueFixesTests(unittest.TestCase):
    def test_scoped_crowhaven_fix_integrity(self):
        with FIXES.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(
            (row["effective_source"], row["record_type"], row["raw_formid"],
             row["field"], row["occurrence"]),
            ("Oblivion.esm", "INFO", "00038ED7", "NAM1", "1"),
        )
        self.assertTrue(row["old_english"].startswith("Crowhaven is a ruined fort"))
        self.assertEqual(
            bytes.fromhex(row["obcjk_utf8_hex"]).rstrip(b"\0").decode("utf-8"),
            row["obcjk_unicode_text"],
        )
        self.assertTrue(row["obcjk_utf8_hex"].endswith("00"))
        self.assertIn("까마귀의 안식처", row["obcjk_unicode_text"])
        self.assertNotIn("Crowhaven", row["obcjk_unicode_text"])

    def test_build_prefers_fix_and_preserves_other_responses(self):
        with FIXES.open(encoding="utf-8-sig", newline="") as stream:
            row = next(csv.DictReader(stream))
        english = row["old_english"]
        stale = "Crowhaven는 여기서 서쪽 멀리 있는 폐허라네."
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder) / "base.csv"
            with base.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(
                    stream, fieldnames=("effective_source", "record_type",
                                        "raw_formid", "field", "old_english",
                                        "obcjk_utf8_hex", "occurrence"))
                writer.writeheader()
                writer.writerow({
                    "effective_source": "Oblivion.esm",
                    "record_type": "INFO",
                    "raw_formid": "00038ED7",
                    "field": "NAM1",
                    "old_english": english,
                    "obcjk_utf8_hex": (stale.encode("utf-8") + b"\0").hex(),
                    "occurrence": "1",
                })
            table = load_translations(base, (FIXES,), encoded_column="obcjk_utf8_hex")
            body = (
                encode_subrecord(b"NAM1", b"Previous response\0")
                + encode_subrecord(b"NAM1", english.encode("cp1252") + b"\0")
            )
            result = patch_record(
                body, "Oblivion.esm", b"INFO", 0x00038ED7,
                table, Counter(), [],
            )
            responses = [value for field, value, _ in parse_subrecords(result)
                         if field == b"NAM1"]
            self.assertEqual(responses[0], b"Previous response\0")
            self.assertEqual(
                responses[1],
                row["obcjk_unicode_text"].encode("utf-8") + b"\0",
            )


if __name__ == "__main__":
    unittest.main()
