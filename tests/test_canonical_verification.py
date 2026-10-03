import struct
import tempfile
import unittest
from pathlib import Path

from build_vanilla_overlay import encode_subrecord
from verify_canonical_oblivion import verify


def record(signature, fid, parts):
    payload = b''.join(encode_subrecord(field, value) for field, value in parts)
    return struct.pack('<4sIIII', signature, len(payload), 0, fid, 0) + payload


class CanonicalVerificationTests(unittest.TestCase):
    def test_ofst_removal_and_record_reorder_are_allowed(self):
        with tempfile.TemporaryDirectory() as folder:
            a, b = Path(folder) / 'before.esm', Path(folder) / 'after.esm'
            world = [(b'EDID', b'Tamriel\0'), (b'OFST', b'old offsets')]
            script = record(b'SCPT', 0x1234, [(b'SCDA', b'\xff\x00\x10')])
            a.write_bytes(record(b'WRLD', 0x3C, world) + script)
            b.write_bytes(script + record(b'WRLD', 0x3C, world[:1]))
            report = verify(a, b)
            self.assertTrue(report['passed'])
            self.assertEqual(report['input_ofst'], 1)

    def test_translated_text_and_compiled_script_changes_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            a, b = Path(folder) / 'before.esm', Path(folder) / 'after.esm'
            parts = [(b'FULL', '한글'.encode('utf8') + b'\0'), (b'SCDA', b'\x01\x02')]
            a.write_bytes(record(b'SCPT', 0x1234, parts))
            for index, replacement in [(0, b'changed\0'), (1, b'\x01\x03')]:
                changed = list(parts)
                changed[index] = (parts[index][0], replacement)
                b.write_bytes(record(b'SCPT', 0x1234, changed))
                self.assertFalse(verify(a, b)['passed'])
