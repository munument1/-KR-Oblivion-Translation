import csv
import unittest
from pathlib import Path

from build_obcjk_release import load_utf8_menu_gmsts
from oblivion_korean_codec import encode_legacy


HERE = Path(__file__).resolve().parents[1]
TABLE = HERE / "menu_gmst_new_821.csv"


class ArmorWeightLabelTests(unittest.TestCase):
    def test_armor_category_labels_reach_release_in_both_encodings(self):
        with TABLE.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        release = {key.rstrip(b"\0").decode("ascii"): (fid, english, korean)
                   for fid, key, english, korean in load_utf8_menu_gmsts(TABLE)}
        expected = {
            "sArmorWeightLight": (0x00099EF3, "Light", "경갑"),
            "sArmorWeightHeavy": (0x00099E31, "Heavy", "중갑"),
        }
        for key, (fid, english, korean) in expected.items():
            with self.subTest(key=key):
                matches = [row for row in rows if row["edid"] == key]
                self.assertEqual(len(matches), 1)
                row = matches[0]
                self.assertEqual(row["korean"], korean)
                self.assertEqual(bytes.fromhex(row["encoded_hex"]),
                                 encode_legacy(korean) + b"\0")
                self.assertEqual(release[key],
                                 (fid, english.encode("ascii") + b"\0",
                                  korean.encode("utf-8") + b"\0"))
