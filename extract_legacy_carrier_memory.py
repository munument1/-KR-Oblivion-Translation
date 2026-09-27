#!/usr/bin/env python3
"""Recover Korean text from old UOP carrier records absent in latest English UOP.

Only a matching original Oblivion.esm record and EditorID can contribute text.
The legacy record itself and all its non-text fields are never copied.
"""

import argparse
import csv
import struct
import zlib
from pathlib import Path

from build_unofficial_release import TEXT_FIELDS, read_records
from build_vanilla_overlay import decode_english, parse_subrecords


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--legacy-uop',type=Path,required=True)
    p.add_argument('--latest-uop',type=Path,required=True)
    p.add_argument('--original-esm',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    legacy=read_records(args.legacy_uop)
    latest_keys=read_records(args.latest_uop).keys()
    carriers={key:legacy[key] for key in legacy.keys()-latest_keys if key[1]>>24==0}
    rows=[]
    with args.original_esm.open('rb') as stream:
        def walk(end):
            while stream.tell()<end:
                start=stream.tell();header=stream.read(20)
                if len(header)!=20:raise ValueError('truncated ESM')
                kind,size,flags,formid,_=struct.unpack('<4sIIII',header)
                if kind==b'GRUP':walk(start+size);continue
                old_fields=carriers.get((kind,formid))
                if not old_fields:stream.seek(size,1);continue
                body=stream.read(size)
                if flags&0x40000:body=zlib.decompress(body[4:])
                source_fields=[(f,v) for f,v,_ in parse_subrecords(body)]
                source_editor=next((v.rstrip(b'\0') for f,v in source_fields if f==b'EDID'),b'')
                legacy_editor=next((v.rstrip(b'\0') for f,v in old_fields if f==b'EDID'),b'')
                if source_editor!=legacy_editor:continue
                source_by_field={}
                legacy_by_field={}
                for field,value in source_fields:source_by_field.setdefault(field,[]).append(value)
                for field,value in old_fields:legacy_by_field.setdefault(field,[]).append(value)
                for field,source_values in source_by_field.items():
                    if field not in TEXT_FIELDS or (kind in (b'CELL',b'WRLD') and field==b'FULL'):
                        continue
                    targets=legacy_by_field.get(field,[])
                    if len(source_values)!=1 or len(targets)!=1:
                        continue
                    english,korean=source_values[0],targets[0]
                    if english==korean or not english.endswith(b'\0') or not korean.endswith(b'\0'):
                        continue
                    if b'\0' in english[:-1] or b'\0' in korean[:-1] or not any(n>=128 for n in korean):
                        continue
                    rows.append(dict(effective_source='Unofficial Oblivion Patch.esp',
                                     record_type=kind.decode('ascii'),raw_formid=f'{formid:08X}',
                                     field=field.decode('ascii'),old_english=decode_english(english),
                                     new_korean='',locres_key='legacy_v3_carrier_string_only',
                                     new_bytes_hex=korean.hex(),editor_id=source_editor.decode('ascii','replace')))
            if stream.tell()!=end:raise ValueError('group mismatch')
        walk(args.original_esm.stat().st_size)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=('effective_source','record_type','raw_formid','field',
                                       'old_english','new_korean','locres_key','new_bytes_hex','editor_id'))
        w.writeheader();w.writerows(rows)
    print('carriers',len(carriers),'matched translated strings',len(rows))


if __name__=='__main__':main()
