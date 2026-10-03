import hashlib
from dataclasses import replace
import struct
import tempfile
import unittest
from pathlib import Path

from build_unofficial_release import collect_changes, has_localizable_text, read_records, reviewed_identity
from build_vanilla_overlay import Translation, encode_subrecord


def record(kind, formid, fields):
    body = b''.join(encode_subrecord(field, value) for field, value in fields)
    return struct.pack('<4sIIII', kind, len(body), 0, formid, 0) + body


class UnofficialForwardingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.original = self.root / 'DLCFrostcrag - Unofficial Patch.esp'
        self.prior = self.root / 'prior.esp'
        self.owner = 'DLCFrostcrag.esp'
        self.key = (b'QUST', 0x02001234)
        self.fields = [(b'EDID', b'TestQuest\0'), (b'INDX', b'\x0a\x00'),
                       (b'CNAM', b'Source\0'), (b'CNAM', b'Source\0')]
        self.header = record(b'TES4', 0, [(b'MAST', b'Oblivion.esm\0'),
                                        (b'MAST', b'OtherMaster.esm\0'),
                                        (b'MAST', b'DLCFrostcrag.esp\0')])
        self.write()

    def write(self, rawid=0x02001234):
        self.original.write_bytes(self.header + record(b'QUST', rawid, self.fields))
        self.prior.write_bytes(self.original.read_bytes())

    def table(self, targets=(b'Reviewed\0',), source=None):
        return {(self.owner, b'QUST', 0x01001234, b'CNAM'): [
            Translation(source or self.owner, b'QUST', 0x01001234, b'CNAM',
                        'Source', value, index + 2, b'TestQuest', index)
            for index, value in enumerate(targets)]}

    def audit(self):
        return {(self.owner, 'QUST', '01001234', 'CNAM', hashlib.sha256(b'Source\0').hexdigest())}

    def test_missing_kr_reference_is_safe_only_without_visible_text(self):
        metadata_only = self.root / 'metadata-only.esp'
        metadata_only.write_bytes(
            record(b'TES4', 0, [(b'CNAM', b'Author\0')]) +
            record(b'GMST', 0x02000CE6, [(b'DATA', b'\0\0\0')])
        )
        self.assertFalse(has_localizable_text(metadata_only))
        visible = self.root / 'visible.esp'
        visible.write_bytes(
            record(b'TES4', 0, [(b'CNAM', b'Author\0')]) +
            record(b'QUST', 0x02000001, [(b'CNAM', b'Visible quest text\0')])
        )
        self.assertTrue(has_localizable_text(visible))

    def test_master_slot_maps_to_source_identity(self):
        records = read_records(self.original)
        self.assertEqual(reviewed_identity(records, 0x02001234), (self.owner, 0x01001234))
        self.assertEqual(reviewed_identity(records, 0x00001234), ('Oblivion.esm', 0x00001234))
        self.assertIsNone(reviewed_identity(records, 0x03001234))

    def test_normalized_audit_forwards_each_occurrence(self):
        changes, counts = collect_changes(self.original, self.prior, self.audit(),
                                         self.table((b'First\0', b'Second\0')))
        self.assertEqual(changes[self.key][2][2], b'First\0')
        self.assertEqual(changes[self.key][3][2], b'Second\0')
        self.assertEqual(counts['reviewed_base_translation'], 2)

    def test_patch_owned_id_does_not_receive_master_translation(self):
        self.write(0x03001234)
        changes, _ = collect_changes(self.original, self.prior, self.audit(), self.table())
        self.assertEqual(changes, {})

    def test_reviewed_translation_beats_old_completion(self):
        completion = {(self.original.name, b'QUST', self.key[1], b'CNAM'):
                      (b'Source\0', b'Old bilingual\0')}
        nexus = {(self.original.name, b'QUST', self.key[1], b'CNAM', 0, 10):
                 (b'Source\0', b'Old nexus\0')}
        changes, _ = collect_changes(self.original, self.prior, self.audit(), self.table(),
                                     completions=completion, nexus_completions=nexus)
        self.assertEqual(changes[self.key][2][2], b'Reviewed\0')

    def test_final_review_beats_reviewed_base_and_completions(self):
        changes, _ = collect_changes(self.original, self.prior, self.audit(), self.table(),
                                     self.table((b'Final\0',)))
        self.assertEqual(changes[self.key][2][2], b'Final\0')

    def test_wrong_english_or_editor_cannot_forward(self):
        table = self.table()
        key = next(iter(table))
        table[key][0] = replace(table[key][0], english='Other text')
        changes, _ = collect_changes(self.original, self.prior, self.audit(), table)
        self.assertEqual(changes, {})
        table = self.table()
        table[key][0] = replace(table[key][0], editor_id=b'OtherQuest')
        changes, _ = collect_changes(self.original, self.prior, self.audit(), table)
        self.assertEqual(changes, {})

    def test_latest_direct_source_refinement_matches_main_builder(self):
        table = self.table()
        table[next(iter(table))].append(Translation(self.owner, b'QUST', 0x01001234, b'CNAM',
                                                   'Source', b'Latest\0', 99, b'TestQuest', 0))
        changes, _ = collect_changes(self.original, self.prior, self.audit(), table)
        self.assertEqual(changes[self.key][2][2], b'Latest\0')


if __name__ == '__main__':
    unittest.main()
