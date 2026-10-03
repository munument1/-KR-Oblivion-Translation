import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from build_obcjk_overlay import records, write
from build_vanilla_overlay import encode_subrecord
from finalize_oblivion_master import finalize


def record(sig, fid, fields, flags=0, vcs=7):
    plain = b''.join(encode_subrecord(f, v) for f, v in fields)
    body = struct.pack('<I', len(plain)) + zlib.compress(plain) if flags & 0x40000 else plain
    return struct.pack('<4sIIII', sig, len(body), flags, fid, vcs) + body


def group(sig, body):
    return struct.pack('<4sI4sII', b'GRUP', 20 + len(body), sig, 0, 12) + body


class FinalizeMasterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.before, self.native, self.output, self.report = [root/n for n in ('before.esm', 'native.esm', 'final.esm', 'report.json')]
        header = record(b'TES4', 0, [(b'HEDR', struct.pack('<fII', 1., 2, 0xF00000)), (b'OFST', b'stale')], flags=1)
        world = record(b'WRLD', 0x3C, [(b'EDID', b'Tamriel\0'), (b'OFST', b'stale-world')])
        source_ref = record(b'REFR', 0x0100110A, [(b'FULL', b'\0'), (b'DATA', bytes(range(24)))], flags=0x40000, vcs=99)
        self.before.write_bytes(header + group(b'REFR', source_ref) + group(b'WRLD', world))
        native_ref = record(b'REFR', 0x0000110A, [(b'DATA', bytes(range(24)))], vcs=99)
        self.native.write_bytes(header + group(b'WRLD', world) + group(b'REFR', native_ref))

    def test_restores_fields_raw_ids_and_compression_preserving_native_order(self):
        before_bytes, native_bytes = self.before.read_bytes(), self.native.read_bytes()
        result = finalize(self.before, self.native, self.output, self.report)
        self.assertTrue(result['passed'])
        self.assertEqual(result['removed_ofst_subrecords'], 2)
        actual = list(records(self.output))
        self.assertEqual([key[0] for key, *_ in actual], [b'TES4', b'WRLD', b'REFR'])
        ref = actual[2]
        self.assertEqual(ref[0], (b'REFR', 0x0100110A))
        self.assertEqual(struct.unpack_from('<I', ref[1], 8)[0], 0x40000)
        self.assertEqual(struct.unpack_from('<I', ref[1], 16)[0], 99)
        self.assertEqual([(f, v) for f, v, _ in ref[2]][0], (b'FULL', b'\0'))
        self.assertFalse(any(f == b'OFST' for _, _, parts, _ in actual for f, _, _ in parts))
        self.assertEqual(self.before.read_bytes(), before_bytes)
        self.assertEqual(self.native.read_bytes(), native_bytes)
        self.assertTrue(json.loads(self.report.read_text())['verification']['passed'])

    def test_rejects_unknown_identity_normalization_before_writing(self):
        raw = self.before.read_bytes().replace(struct.pack('<I', 0x0100110A), struct.pack('<I', 0x010011FF))
        self.before.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, 'Unexpected native record identity'):
            finalize(self.before, self.native, self.output, self.report)
        self.assertFalse(self.output.exists())

    def test_refuses_input_overwrite_and_existing_output(self):
        with self.assertRaisesRegex(ValueError, 'separate'):
            finalize(self.before, self.native, self.before, self.report)
        self.output.write_bytes(b'keep')
        with self.assertRaisesRegex(ValueError, 'already exists'):
            finalize(self.before, self.native, self.output, self.report)
        self.assertEqual(self.output.read_bytes(), b'keep')

    def test_writer_refuses_missing_override_without_creating_output(self):
        header = struct.pack('<4sIIII', b'REFR', 0, 0, 0x123, 0)
        with self.assertRaisesRegex(ValueError, 'missing or excluded'):
            write(self.native, self.output, {}, record_overrides={(b'REFR', 0xBAD): (header, b'')})
        self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
