#!/usr/bin/env python3
"""Extract only verified Korean text differences from current latest UOP overlays."""

import argparse
import csv
from pathlib import Path

from build_unofficial_release import PAIRS, read_records, TEXT_FIELDS
from build_vanilla_overlay import decode_english


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--prior-kr',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    rows=[]
    for folder,kr_folder in PAIRS:
        for original in sorted((args.source/folder).glob('*.esp')):
            prior=args.prior_kr/kr_folder/original.name
            a=read_records(original);b=read_records(prior)
            if a.keys()!=b.keys():raise ValueError(f'{original.name}: record identities differ')
            for (kind,formid),fields in a.items():
                newer=b[(kind,formid)]
                if [f for f,_ in fields]!=[f for f,_ in newer]:
                    raise ValueError(f'{original.name}: field sequence differs')
                editor=next((v.rstrip(b'\0') for f,v in fields if f==b'EDID'),b'')
                for (field,old),(_,new) in zip(fields,newer):
                    if old==new or field not in TEXT_FIELDS:
                        continue
                    if kind in (b'CELL',b'WRLD') and field==b'FULL':
                        continue
                    if not old.endswith(b'\0') or not new.endswith(b'\0'):
                        raise ValueError(f'{original.name}: bad string at {formid:08X}')
                    rows.append(dict(effective_source=original.name,record_type=kind.decode('ascii'),
                                     raw_formid=f'{formid:08X}',field=field.decode('ascii'),
                                     old_english=decode_english(old),new_korean='',
                                     locres_key='latest_patch_korean_string_reuse',
                                     new_bytes_hex=new.hex(),editor_id=editor.decode('ascii','replace')))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=('effective_source','record_type','raw_formid','field',
                                       'old_english','new_korean','locres_key','new_bytes_hex','editor_id'))
        w.writeheader();w.writerows(rows)
    print('verified patch translation rows',len(rows))


if __name__=='__main__':main()
