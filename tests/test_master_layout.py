import gzip
import json
import tempfile
import unittest
import struct
import zlib
from pathlib import Path

from master_layout import apply_layout, capture_layout
from build_vanilla_overlay import encode_subrecord


def record(sig, fid, fields, flags=0, vcs=7):
    plain = b''.join(encode_subrecord(f, v) for f, v in fields)
    body = struct.pack('<I', len(plain)) + zlib.compress(plain) if flags & 0x40000 else plain
    return struct.pack('<4sIIII', sig, len(body), flags, fid, vcs) + body


def group(sig, body):
    return struct.pack('<4sI4sII', b'GRUP', 20 + len(body), sig, 0, 12) + body


class MasterLayoutTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.generated, self.reference, self.asset, self.output = [root/n for n in ('generated.esm', 'reference.esm', 'layout.json.gz', 'output.esm')]
        fields = [(b'HEDR', b'123456789012'), (b'CNAM', b'Author\0')]
        ref_fields = [(b'DATA', bytes(range(24)))]
        ref = record(b'REFR', 0x0100110A, ref_fields, flags=0x40000, vcs=99)
        original_world = record(b'WRLD', 0x3C, [(b'EDID', b'Tamriel\0'), (b'OFST', b'old-offsets')], flags=0x40000)
        final_world = record(b'WRLD', 0x3C, [(b'EDID', b'Tamriel\0')], flags=0x40000)
        self.generated.write_bytes(record(b'TES4', 0, fields+[(b'OFST', b'old-header')], flags=1) + group(b'REFR', ref) + group(b'WRLD', original_world))
        self.reference.write_bytes(record(b'TES4', 0, fields, flags=1) + group(b'WRLD', final_world) + group(b'REFR', ref))

    def test_metadata_only_layout_reproduces_exact_reference_bytes(self):
        before = self.generated.read_bytes()
        metadata = capture_layout(self.reference, self.generated, self.asset)
        self.assertEqual(metadata['record_count'], 3)
        self.assertEqual(metadata['group_count'], 2)
        data = json.loads(gzip.decompress(self.asset.read_bytes()))
        self.assertTrue(all(e[0] in {'r', 'g', 'e'} for e in data['events']))
        self.assertNotIn('old-offsets', str(data))
        result = apply_layout(self.generated, self.output, self.asset)
        self.assertTrue(result['passed'])
        self.assertTrue(result['byte_identical_to_native_reference'])
        self.assertEqual(self.output.read_bytes(), self.reference.read_bytes())
        self.assertEqual(self.generated.read_bytes(), before)

    def test_hash_tampering_is_rejected_without_output(self):
        capture_layout(self.reference, self.generated, self.asset)
        data = json.loads(gzip.decompress(self.asset.read_bytes()))
        data['events'][1][1] = data['events'][1][1][:-2] + 'ff'
        self.asset.write_bytes(gzip.compress(json.dumps(data).encode()))
        with self.assertRaisesRegex(ValueError, 'integrity hash'):
            apply_layout(self.generated, self.output, self.asset)
        self.assertFalse(self.output.exists())

    def test_source_hash_and_record_identity_guards(self):
        capture_layout(self.reference, self.generated, self.asset)
        with self.assertRaisesRegex(ValueError, 'source hash mismatch'):
            apply_layout(self.generated, self.output, self.asset, source_sha256='wrong')
        self.generated.write_bytes(
            self.generated.read_bytes() +
            record(b'REFR', 0x0100110B, [(b'DATA', bytes(range(24)))], flags=0x40000, vcs=99)
        )
        with self.assertRaisesRegex(ValueError, 'unused source records'):
            apply_layout(self.generated, self.output, self.asset)
        self.assertFalse(self.output.exists())

    def test_text_update_reuses_pinned_native_layout(self):
        capture_layout(self.reference, self.generated, self.asset)
        self.generated.write_bytes(self.generated.read_bytes().replace(b'Author\0', b'Editor\0'))
        result = apply_layout(self.generated, self.output, self.asset)
        self.assertTrue(result['passed'])
        self.assertFalse(result['matches_captured_translation_bytes'])
        self.assertFalse(result['byte_identical_to_native_reference'])
        self.assertIn(b'Editor\0', self.output.read_bytes())
        self.assertNotIn(b'Author\0', self.output.read_bytes())

    def test_capture_refuses_modified_gameplay_fields(self):
        self.reference.write_bytes(self.reference.read_bytes().replace(b'Author\0', b'EDITOR\0'))
        with self.assertRaisesRegex(ValueError, 'strict source-content'):
            capture_layout(self.reference, self.generated, self.asset)
        self.assertFalse(self.asset.exists())


if __name__ == '__main__':
    unittest.main()
