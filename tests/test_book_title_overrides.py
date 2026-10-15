import unittest
from collections import defaultdict
from pathlib import Path

from book_title_overrides import apply_book_title_overrides
from build_vanilla_overlay import Translation

HERE = Path(__file__).resolve().parents[1]
OVERRIDES = HERE / "canonical_book_title_overrides_v1.csv"
TITLE_KEY = ("Oblivion.esm", b"BOOK", 0x00024574, b"FULL")


def book(title, formid=0x00024574):
    return Translation("Oblivion.esm", b"BOOK", formid, b"FULL",
                       "The Real Barenziah, v 5",
                       title.encode("utf-8") + b"\0", 2)


class BookTitleOverridesTests(unittest.TestCase):
    def test_fifth_volume_corrected_without_changing_suffix(self):
        table = defaultdict(list, {TITLE_KEY: [book("진짜 바렌지아, 제 5권")]})
        self.assertEqual(apply_book_title_overrides(table, OVERRIDES), 1)
        self.assertEqual(table[TITLE_KEY][0].korean[:-1].decode("utf-8"),
                         "진정한 바렌지아, 제 5권")

    def test_already_correct_is_idempotent(self):
        table = defaultdict(list, {TITLE_KEY: [book("진정한 바렌지아 5권")]})
        self.assertEqual(apply_book_title_overrides(table, OVERRIDES), 0)

    def test_missing_translation_is_caught(self):
        with self.assertRaises(ValueError):
            apply_book_title_overrides(defaultdict(list), OVERRIDES)


if __name__ == "__main__":
    unittest.main()
