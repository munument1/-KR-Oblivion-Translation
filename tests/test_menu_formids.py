import csv
import struct
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from build_vanilla_overlay import load_menu_gmsts, patch_plugin


class MenuFormIDTests(unittest.TestCase):
    def test_release_menu_ids_are_legal_and_unique(self):
        root = Path(__file__).resolve().parents[1]
        items = load_menu_gmsts(root / 'menu_gmst_existing_105.csv',
                                root / 'menu_gmst_new_821.csv', {})
        self.assertEqual(len(items), 821)
        self.assertEqual(len({item[0] for item in items}), 821)
        self.assertTrue(all(0 < item[0] <= 0xFFFFFF for item in items))

    def test_terrain_incident_37_ids_stay_in_reserved_slot00_range(self):
        root = Path(__file__).resolve().parents[1]
        with (root / 'menu_gmst_new_821.csv').open(encoding='utf-8-sig', newline='') as stream:
            ids = [int(row['formid'], 16) for row in csv.DictReader(stream)]
        repaired = {fid for fid in ids if 0x00F10001 <= fid <= 0x00F10025}
        self.assertEqual(repaired, set(range(0x00F10001, 0x00F10026)))
        self.assertEqual(len(repaired), 37)
        self.assertFalse(any((fid >> 24) == 0x01 for fid in ids))

    def test_invalid_slot_is_rejected_before_output_creation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            output = root / 'out.esm'
            with self.assertRaisesRegex(ValueError, 'file slot'):
                patch_plugin(root / 'absent.esm', output, 'Oblivion.esm', {},
                             Counter(), [], ((0x01000809, b'sAge\0', b'Age\0', b'Age\0'),))
            self.assertFalse(output.exists())

    def test_source_ids_are_normalized_for_collision_check(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'source.esm'
            source.write_bytes(struct.pack('<4sIIII', b'CELL', 0, 0, 0x01000809, 0))
            with self.assertRaisesRegex(ValueError, 'collides'):
                patch_plugin(source, root / 'out.esm', 'Oblivion.esm', {},
                             Counter(), [], ((0x809, b'sAge\0', b'Age\0', b'Age\0'),))


if __name__ == '__main__':
    unittest.main()
