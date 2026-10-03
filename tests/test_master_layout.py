import gzip
import json
import tempfile
import unittest
from pathlib import Path

from master_layout import apply_layout, capture_layout
from tests.test_finalize_oblivion_master import group, record


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

    def test_source_and_generated_hash_guards(self):
        capture_layout(self.reference, self.generated, self.asset)
        with self.assertRaisesRegex(ValueError, 'source hash mismatch'):
            apply_layout(self.generated, self.output, self.asset, source_sha256='wrong')
        self.generated.write_bytes(self.generated.read_bytes()+b'X')
        with self.assertRaisesRegex(ValueError, 'differs from'):
            apply_layout(self.generated, self.output, self.asset)
        self.assertFalse(self.output.exists())

    def test_capture_refuses_modified_gameplay_fields(self):
        self.reference.write_bytes(self.reference.read_bytes().replace(b'Author\0', b'EDITOR\0'))
        with self.assertRaisesRegex(ValueError, 'strict source-content'):
            capture_layout(self.reference, self.generated, self.asset)
        self.assertFalse(self.asset.exists())


if __name__ == '__main__':
    unittest.main()
