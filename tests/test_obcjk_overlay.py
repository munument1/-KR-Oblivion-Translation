import csv
import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from build_obcjk_overlay import records, validate, write
from build_vanilla_overlay import encode_subrecord
from obcjk_text_backend import encode_text, load_exceptions, recover_legacy

ROOT = Path(__file__).resolve().parents[1]


class OverlayIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source.esp'
        self.output = self.root / 'output.esp'
        self.old = encode_text('값 꽃 읽음 ABC 123')
        self.new = encode_text('값 꽃 읽음 ABC 123\r\n' * 4000, 'obcjk')
        plain = (encode_subrecord(b'EDID', b'TestBook\0') +
                 encode_subrecord(b'DESC', self.old) +
                 encode_subrecord(b'DATA', b'\x01\x02\x00\xff') +
                 encode_subrecord(b'SCDA', b'\x00\x08\x15\x00\xff'))
        packed = struct.pack('<I', len(plain)) + zlib.compress(plain)
        record = struct.pack('<4sIIII', b'BOOK', len(packed), 0x40000, 0x1234, 7) + packed
        group = struct.pack('<4sI4sII', b'GRUP', 20 + len(record), b'BOOK', 0, 12)
        self.source.write_bytes(group + record)
        self.changes = {(b'BOOK', 0x1234): {1: (b'DESC', self.old, self.new)}}

    def test_compressed_extended_text_preserves_other_bytes(self):
        write(self.source, self.output, self.changes)
        report = validate(self.source, self.output, self.changes)
        self.assertEqual(report['changed_text_fields'], 1)
        self.assertEqual(report['unchanged_subrecords'], 3)
        parts = next(records(self.output))[2]
        self.assertTrue(parts[1][2].startswith(b'XXXX'))
        self.assertEqual(parts[2][1], b'\x01\x02\x00\xff')
        self.assertEqual(parts[3][1], b'\x00\x08\x15\x00\xff')

    def test_unlisted_script_change_is_rejected(self):
        extra = {(b'BOOK', 0x1234): {**self.changes[(b'BOOK', 0x1234)],
                                   3: (b'SCDA', b'\x00\x08\x15\x00\xff', b'\x00BAD')}}
        write(self.source, self.output, extra)
        with self.assertRaisesRegex(ValueError, 'Non-allowlisted'):
            validate(self.source, self.output, self.changes)

    def test_header_and_parent_bounds_are_checked(self):
        write(self.source, self.output, self.changes)
        raw = bytearray(self.output.read_bytes())
        raw[28] ^= 1
        self.output.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, 'identity, flags'):
            validate(self.source, self.output, self.changes)
        self.output.write_bytes(self.source.read_bytes()[:-1])
        with self.assertRaisesRegex(ValueError, 'bounds'):
            list(records(self.output))

    def test_target_termination_is_checked(self):
        bad = {(b'BOOK', 0x1234): {1: (b'DESC', self.old, b'UTF8\0hidden\0')}}
        write(self.source, self.output, bad)
        with self.assertRaisesRegex(ValueError, 'NUL'):
            validate(self.source, self.output, bad)

    def test_empty_groups_are_preserved(self):
        empty = struct.pack('<4sI4sII', b'GRUP', 20, b'NPC_', 0, 3)
        self.source.write_bytes(self.source.read_bytes() + empty)
        write(self.source, self.output, self.changes)
        report = validate(self.source, self.output, self.changes)
        self.assertEqual(report['structure']['groups'], 2)


class PinnedRecoveryTests(unittest.TestCase):
    def test_all_six_recoveries_and_changed_source_rejection(self):
        exceptions = load_exceptions(ROOT / 'docs/obcjk/legacy_text_exceptions.json')
        with (ROOT / 'legacy_full_recovery.csv').open(encoding='utf-8-sig', newline='') as stream:
            rows = list(csv.DictReader(stream))
        for entry in exceptions.values():
            raw = bytes.fromhex(rows[entry['row'] - 2]['new_bytes_hex'])[:-1]
            text = recover_legacy(raw, exceptions)
            self.assertNotIn('\ufffd', text)
            for token in entry.get('tokens', []):
                self.assertIn(token['unicode'], text)
            # The exception is not a permissive fallback for arbitrary damage.
            with self.assertRaises(UnicodeError):
                recover_legacy(raw + b'\xd0', exceptions)


if __name__ == '__main__':
    unittest.main()
