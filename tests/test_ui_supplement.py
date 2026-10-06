import csv
import unittest
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
TABLE = HERE / "canonical_ui_supplement_v1.csv"


class UISupplementTests(unittest.TestCase):
    def test_ui_supplement_integrity(self):
        with TABLE.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))

        self.assertEqual(len(rows), 215)
        self.assertEqual(
            Counter(row["record_type"] for row in rows),
            Counter({"FACT": 116, "SKIL": 84, "INFO": 13, "QUST": 2}),
        )

        identities = {
            (
                row["effective_source"],
                row["record_type"],
                row["raw_formid"],
                row["field"],
                row["editor_id"],
                row["occurrence"],
            )
            for row in rows
        }
        self.assertEqual(len(identities), len(rows))

        for row in rows:
            self.assertTrue(row["old_english"])
            self.assertTrue(row["obcjk_unicode_text"])
            encoded = bytes.fromhex(row["obcjk_utf8_hex"])
            self.assertTrue(encoded.endswith(b"\0"))
            self.assertEqual(
                encoded[:-1].decode("utf-8"),
                row["obcjk_unicode_text"],
            )

    def test_official_chapel_locations_present(self):
        location_table = HERE / "canonical_locations_v2.csv"
        with location_table.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))

        expected = {
            ("000308CD", "AnvilChapelofDibella"): "디벨라 예배당",
            ("00030427", "CheydinhalChapelOfArkay"): "아케이의 대성당",
            ("00030537", "LeyawiinChapelOfZenithar"): "제니타르의 대성당",
            ("0000080A", "ChorrolChapelOfStendarr"): "스텐다르 예배당",
        }
        actual = {
            (r["raw_formid"], r["editor_id"]): r["obcjk_unicode_text"]
            for r in rows
            if r["effective_source"] == "Oblivion.esm"
            and (r["raw_formid"], r["editor_id"]) in expected
        }
        self.assertEqual(actual, expected)

    def test_key_user_visible_rows_present(self):
        with TABLE.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))

        keys = {
            (r["record_type"], r["raw_formid"], r["field"], r["occurrence"]): r
            for r in rows
        }
        self.assertEqual(keys[("SKIL", "00000044", "ANAM", "")]["editor_id"], "SkillAlchemy")
        self.assertEqual(keys[("FACT", "0002F872", "MNAM", "5")]["obcjk_unicode_text"], "사일렌서")
        self.assertEqual(keys[("FACT", "0006A7FC", "MNAM", "7")]["obcjk_unicode_text"], "광기의 신")
        self.assertIn(("QUST", "00081DD5", "CNAM", "0"), keys)
        self.assertEqual(keys[("INFO", "0003E452", "NAM1", "0")]["obcjk_unicode_text"], "그쪽 전리품을 살펴보고 싶구만.")


if __name__ == "__main__":
    unittest.main()
