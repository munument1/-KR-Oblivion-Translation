"""Regression coverage for canonical Gray Prince dialogue translations."""
import csv
import hashlib
import struct
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from build_unofficial_release import collect_changes, read_records, rewrite
from build_vanilla_overlay import (
    encode_subrecord,
    load_translations,
    parse_subrecords,
    patch_record,
)
from oblivion_korean_codec import decode_legacy

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "canonical_translation_v2.csv"
EXPECTED = (
    "까마귀의 안식처는 여기서 서쪽으로 한참 떨어진 폐허가 된 요새라네. "
    "나도 직접 가고 싶지만, 훈련 일정 때문에 그렇게 먼 곳까지 다녀올 여유가 없군."
)


class DialogueFixesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with CANONICAL.open(encoding="utf-8-sig", newline="") as stream:
            cls.rows = [row for row in csv.DictReader(stream)
                        if (row["effective_source"], row["record_type"],
                            row["raw_formid"], row["field"]) ==
                        ("Oblivion.esm", "INFO", "00038ED7", "NAM1")]
        cls.table = load_translations(CANONICAL, encoded_column="obcjk_utf8_hex")

    def test_scoped_crowhaven_fix_integrity(self):
        self.assertEqual([row["occurrence"] for row in self.rows], ["0", "1", "2", "3"])
        row = self.rows[1]
        self.assertEqual(
            row["old_english"],
            "Crowhaven is a ruined fort far to the west of here. I'd go myself, "
            "but my training regiment doesn't allow for the luxury of such an excursion.",
        )
        self.assertEqual(row["obcjk_unicode_text"], EXPECTED)
        self.assertEqual(row["new_korean"], EXPECTED)
        self.assertEqual(bytes.fromhex(row["obcjk_utf8_hex"]), EXPECTED.encode("utf-8") + b"\0")
        self.assertEqual(decode_legacy(bytes.fromhex(row["new_bytes_hex"])[:-1]), EXPECTED)
        matches = self.table[("Oblivion.esm", b"INFO", 0x38ED7, b"NAM1")]
        self.assertEqual(len(matches), 4)
        self.assertEqual([item.occurrence for item in matches], [0, 1, 2, 3])

        # The actual release also loads UI data after the main table. Ensure
        # that no supplement can reintroduce an alternative Crowhaven target.
        release = load_translations(
            CANONICAL, (ROOT / "canonical_ui_supplement_v1.csv",),
            encoded_column="obcjk_utf8_hex")
        targets = [item for item in release[("Oblivion.esm", b"INFO", 0x38ED7, b"NAM1")]
                   if item.english == row["old_english"]
                   and item.occurrence in (None, 1)]
        self.assertEqual(len(targets), 1)
        self.assertEqual(targets[0].korean, EXPECTED.encode("utf-8") + b"\0")

    def test_build_translates_all_canonical_responses(self):
        body = b"".join(encode_subrecord(b"NAM1", row["old_english"].encode("cp1252") + b"\0")
                        for row in self.rows)
        result = patch_record(body, "Oblivion.esm", b"INFO", 0x38ED7,
                              self.table, Counter(), [])
        responses = [value for field, value, _ in parse_subrecords(result) if field == b"NAM1"]
        self.assertEqual(responses, [bytes.fromhex(row["obcjk_utf8_hex"]) for row in self.rows])

    def test_fix_does_not_leak_to_other_occurrences_or_records(self):
        english = self.rows[1]["old_english"].encode("cp1252") + b"\0"
        body = encode_subrecord(b"NAM1", english) * 3
        result = patch_record(body, "Oblivion.esm", b"INFO", 0x38ED7,
                              self.table, Counter(), [])
        responses = [value for field, value, _ in parse_subrecords(result)]
        self.assertEqual(responses, [english, EXPECTED.encode("utf-8") + b"\0", english])
        self.assertEqual(patch_record(body, "Oblivion.esm", b"INFO", 0x38ED8,
                                      self.table, Counter(), []), body)
        other_field = encode_subrecord(b"FULL", english)
        self.assertEqual(patch_record(other_field, "Oblivion.esm", b"INFO", 0x38ED7,
                                      self.table, Counter(), []), other_field)

    def test_unofficial_forwarding_uses_canonical_responses(self):
        def record(kind, formid, body):
            return struct.pack("<4sIIII", kind, len(body), 0, formid, 0) + body

        body = b"".join(encode_subrecord(b"NAM1", row["old_english"].encode("cp1252") + b"\0")
                        for row in self.rows)
        audit = {("Oblivion.esm", "INFO", "00038ED7", "NAM1",
                  hashlib.sha256(row["old_english"].encode("cp1252") + b"\0").hexdigest())
                 for row in self.rows}
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "Unofficial Oblivion Patch.esp"
            source.write_bytes(record(b"TES4", 0, encode_subrecord(b"MAST", b"Oblivion.esm\0"))
                               + record(b"INFO", 0x38ED7, body))
            changes, counts = collect_changes(source, None, audit, self.table)
            self.assertEqual(counts["reviewed_base_translation"], 4)
            output = Path(folder) / "translated.esp"
            self.assertEqual(rewrite(source, output, changes), 4)
            self.assertEqual(read_records(output)[(b"INFO", 0x38ED7)],
                             [(b"NAM1", bytes.fromhex(row["obcjk_utf8_hex"])) for row in self.rows])


if __name__ == "__main__":
    unittest.main()
