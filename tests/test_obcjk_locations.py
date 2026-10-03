import csv
import struct
import tempfile
import unittest
from pathlib import Path

from build_obcjk_locations import build
from build_obcjk_overlay import records
from build_vanilla_overlay import encode_subrecord


class LocationOverlayTests(unittest.TestCase):
    def test_marker_names_and_region_names_preserve_nonmarker_and_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, tables, output = root/'source', root/'tables', root/'output'
            source.mkdir(); tables.mkdir()
            chunks = []
            for kind, fid, field, marker in [(b'REFR', 1, b'FULL', True), (b'REFR', 2, b'FULL', False), (b'REGN', 3, b'RDMP', False)]:
                body = encode_subrecord(field, b'Matched Hall\0')
                if marker:
                    body += encode_subrecord(b'XMRK', b'')
                body += encode_subrecord(b'DATA', b'\x01\x00\xff')
                chunks.append(struct.pack('<4sIIII', kind, len(body), 0, fid, 9)+body)
            (source/'Oblivion.esm').write_bytes(b''.join(chunks))
            fields = ['effective_source', 'record_type', 'raw_formid', 'field', 'old_english', 'obcjk_conversion_status', 'obcjk_unicode_text', 'obcjk_utf8_hex']
            with (tables/'memory.csv').open('w', encoding='utf-8', newline='') as stream:
                writer = csv.writer(stream); writer.writerow(fields)
                writer.writerow(['Oblivion.esm','CELL','00000009','FULL','Matched Hall','verified','일치하는 전당',('일치하는 전당'.encode()+b'\0').hex()])
            # Release table folders can also contain unrelated CSV schemas
            # such as the injected menu GMST table; those are not locations.
            with (tables/'menu.csv').open('w', encoding='utf-8', newline='') as stream:
                writer = csv.writer(stream); writer.writerow(['formid','edid','english','korean'])
                writer.writerow(['00000010','sExample','Example','예시'])
            report = build([source], tables, output)['Oblivion.esm']
            self.assertEqual(report['location_counts'], {'REFR':1,'REGN':1})
            actual = {key:parts for key,_,parts,_ in records(output/'Oblivion.esm')}
            self.assertEqual(actual[(b'REFR',1)][0][1], '일치하는 전당'.encode()+b'\0')
            self.assertEqual(actual[(b'REFR',2)][0][1], b'Matched Hall\0')
            self.assertEqual(actual[(b'REGN',3)][0][1], '일치하는 전당'.encode()+b'\0')
            self.assertTrue(all(parts[-1][1] == b'\x01\x00\xff' for parts in actual.values()))

    def test_exact_source_matching_ambiguity_and_binary_preservation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, tables, output = root / 'source', root / 'tables', root / 'output'
            source.mkdir()
            tables.mkdir()
            chunks = []
            for fid, name in [(1, 'Matched Hall'), (2, 'Changed by upstream'), (3, 'Ambiguous Hall')]:
                body = (encode_subrecord(b'EDID', f'Cell{fid}'.encode() + b'\0') +
                        encode_subrecord(b'FULL', name.encode() + b'\0') +
                        encode_subrecord(b'DATA', b'\x01\x00\xff'))
                chunks.append(struct.pack('<4sIIII', b'CELL', len(body), 0, fid, 9) + body)
            (source / 'Oblivion.esm').write_bytes(b''.join(chunks))
            fields = ['effective_source', 'record_type', 'raw_formid', 'field', 'old_english',
                      'obcjk_conversion_status', 'obcjk_unicode_text', 'obcjk_utf8_hex']
            with (tables / 'memory.csv').open('w', encoding='utf-8', newline='') as stream:
                writer = csv.DictWriter(stream, fields)
                writer.writeheader()
                for fid, english, korean in [(1, 'Matched Hall', '일치하는 전당'),
                                             (2, 'Old name', '옛 이름'),
                                             (3, 'Ambiguous Hall', '전당'),
                                             (3, 'Ambiguous Hall', '홀')]:
                    writer.writerow(dict(zip(fields, ['Oblivion.esm', 'CELL', f'{fid:08X}', 'FULL',
                                                       english, 'verified', korean,
                                                       (korean.encode('utf-8') + b'\0').hex()])))
            report = build([source], tables, output)['Oblivion.esm']
            self.assertEqual(report['location_counts'], {'CELL': 1})
            self.assertEqual(len(report['unmatched']), 2)
            fields_by_id = {key[1]: parts for key, header, parts, groups in records(output / 'Oblivion.esm')}
            self.assertEqual(fields_by_id[1][1][1], '일치하는 전당'.encode('utf-8') + b'\0')
            self.assertEqual(fields_by_id[2][1][1], b'Changed by upstream\0')
            self.assertEqual(fields_by_id[3][1][1], b'Ambiguous Hall\0')
            self.assertTrue(all(parts[2][1] == b'\x01\x00\xff' for parts in fields_by_id.values()))


if __name__ == '__main__':
    unittest.main()
