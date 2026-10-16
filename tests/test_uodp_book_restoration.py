"""Prevent UODP book bodies from regressing to translated title labels."""
import csv
import hashlib
import struct
import tempfile
import unittest
from pathlib import Path

from build_unofficial_release import collect_changes, load_patch_canonical, read_records, rewrite
from build_vanilla_overlay import encode_subrecord
from package_obcjk_unofficial import PATCHES
from uop_book_restoration import suspicious_book_body

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / 'canonical_unofficial_translation_v2.csv'
REPAIRED = {
    ('DLCSpellTomes - Unofficial Patch.esp', '02001281'),
    ('Knights - Unofficial Patch.esp', '02000ED2'),
    ('Knights - Unofficial Patch.esp', '02000ED4'),
    ('Knights - Unofficial Patch.esp', '02000ED8'),
}


class UODPBookRestorationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with TABLE.open(encoding='utf-8-sig', newline='') as stream:
            cls.rows = [r for r in csv.DictReader(stream)
                        if r['effective_source'] in PATCHES['UODP']
                        and r['record_type'] == 'BOOK' and r['field'] == 'DESC']
        cls.table = load_patch_canonical(TABLE)

    def test_all_15_bodies_have_valid_utf8_and_are_not_title_only(self):
        self.assertEqual(len(self.rows), 15)
        identities = set()
        for row in self.rows:
            with self.subTest(plugin=row['effective_source'], formid=row['raw_formid']):
                identity = (row['effective_source'], row['raw_formid'], row['occurrence'])
                self.assertNotIn(identity, identities)
                identities.add(identity)
                encoded = bytes.fromhex(row['obcjk_utf8_hex'])
                self.assertTrue(encoded.endswith(b'\0'))
                self.assertNotIn(b'\0', encoded[:-1])
                body = encoded[:-1].decode('utf-8')
                self.assertEqual(body, row['new_korean'])
                self.assertFalse(suspicious_book_body(row['old_english'], body))
                self.assertEqual(hashlib.sha256(row['old_english'].encode('cp1252') + b'\0').hexdigest(),
                                 row['source_sha256'])

    def test_restored_source_details_and_final_paragraphs(self):
        bodies = {(r['effective_source'], r['raw_formid']): r['new_korean'] for r in self.rows}
        self.assertTrue(REPAIRED <= bodies.keys())
        spell = bodies[('DLCSpellTomes - Unofficial Patch.esp', '02001281')]
        self.assertIn('잠금 해제 중급', spell)
        self.assertNotIn('잠금 해제 상급', spell)
        knights = bodies[('Knights - Unofficial Patch.esp', '02000ED2')]
        self.assertIn('제3시대 111년', knights)
        self.assertIn('거지를', knights)
        self.assertIn('제3시대 150년', knights)
        shezarr = bodies[('Knights - Unofficial Patch.esp', '02000ED4')]
        self.assertIn('알레시안 교단', shezarr)
        self.assertIn('글렌눔브리아', shezarr)
        pelinal = bodies[('Knights - Unofficial Patch.esp', '02000ED8')]
        self.assertIn('사랑을 통해 세상을 바꾸지', pelinal)
        self.assertIn('불가능한 일입니다', pelinal)

    def test_patch_writer_restores_desc_and_preserves_other_subrecords(self):
        def record(kind, fid, fields):
            body = b''.join(encode_subrecord(k, v) for k, v in fields)
            return struct.pack('<4sIIII', kind, len(body), 0, fid, 0) + body

        with tempfile.TemporaryDirectory() as folder:
            for row in self.rows:
                if (row['effective_source'], row['raw_formid']) not in REPAIRED:
                    continue
                with self.subTest(formid=row['raw_formid']):
                    source = Path(folder) / row['effective_source']
                    fid = int(row['raw_formid'], 16)
                    fields = [(b'EDID', row['editor_id'].encode('ascii') + b'\0'),
                              (b'FULL', b'Book title\0'),
                              (b'DESC', row['old_english'].encode('cp1252') + b'\0'),
                              (b'DATA', b'\x01\x02')]
                    source.write_bytes(record(b'TES4', 0, []) + record(b'BOOK', fid, fields))
                    changes, counts = collect_changes(source, None, patch_table=self.table)
                    self.assertEqual(counts['translated_fields'], 1)
                    target = Path(folder) / 'output.esp'
                    self.assertEqual(rewrite(source, target, changes), 1)
                    expected = list(fields)
                    expected[2] = (b'DESC', bytes.fromhex(row['obcjk_utf8_hex']))
                    self.assertEqual(read_records(target)[(b'BOOK', fid)], expected)


if __name__ == '__main__':
    unittest.main()
