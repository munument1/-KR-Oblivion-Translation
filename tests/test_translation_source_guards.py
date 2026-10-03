import csv
import tempfile
import unittest
from pathlib import Path
from collections import Counter
from build_vanilla_overlay import load_translations, patch_record, encode_subrecord, parse_subrecords
from oblivion_korean_codec import encode_legacy

class TranslationSourceGuards(unittest.TestCase):
    def test_name_keys_are_full_only_and_real_text_is_kept(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'source.csv'
            fields=['effective_source','record_type','raw_formid','field','old_english','new_bytes_hex','locres_key','occurrence']
            rows=[['Oblivion.esm','QUST','00000001','CNAM','Long journal text',encode_legacy('잘못된 제목').hex()+'00','LOC_FN_Test','0'],
                  ['Oblivion.esm','QUST','00000001','CNAM','Long journal text',encode_legacy('정상 일지 설명').hex()+'00','LOC_LE_Test_STAGE10_LOG0','0'],
                  ['Oblivion.esm','BOOK','00000002','DESC','Book body',encode_legacy('잘못된 책 제목').hex()+'00','LOC_FN_Book','0'],
                  ['Oblivion.esm','QUST','00000001','FULL','Quest title',encode_legacy('퀘스트 제목').hex()+'00','LOC_FN_Test','0']]
            with p.open('w',encoding='utf-8',newline='') as f:
                w=csv.writer(f);w.writerow(fields);w.writerows(rows)
            table=load_translations(p)
            self.assertEqual(len(table[('Oblivion.esm',b'QUST',1,b'CNAM')]),1)
            self.assertNotIn(('Oblivion.esm',b'BOOK',2,b'DESC'),table)
            body=encode_subrecord(b'FULL',b'Quest title\0')+encode_subrecord(b'CNAM',b'Long journal text\0')
            out=patch_record(body,'Oblivion.esm',b'QUST',1,table,Counter(),[])
            values={k:v for k,v,_ in parse_subrecords(out)}
            self.assertEqual(values[b'CNAM'],encode_legacy('정상 일지 설명')+b'\0')
            self.assertEqual(values[b'FULL'],encode_legacy('퀘스트 제목')+b'\0')
