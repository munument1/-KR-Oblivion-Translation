"""Verify a native xEdit save using the project's existing record reader."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from build_obcjk_overlay import records
from build_vanilla_overlay import sha256_file


def fingerprint(path, formid_remap=None):
    result, counts = {}, Counter()
    for key, header, parts, groups in records(path):
        if formid_remap and key in formid_remap:
            key = (key[0], formid_remap[key])
            header = header[:12] + key[1].to_bytes(4, 'little') + header[16:]
        if key in result:
            raise ValueError(f'Duplicate record {key} in {path}')
        digest = hashlib.sha256(header[:4] + header[8:])
        for group in groups:
            digest.update(group)
        for field, value, raw in parts:
            if field == b'OFST' and key[0] in {b'TES4', b'WRLD'}:
                counts['ofst'] += 1
                continue
            # Native PrepareSave recounts HEDR. All other header bytes remain
            # protected, including Next Object ID.
            if key[0] == b'TES4' and field == b'HEDR':
                value = value[:4] + b'\0' * 4 + value[8:]
            digest.update(field)
            digest.update(len(value).to_bytes(4, 'little'))
            digest.update(value)
        result[key] = digest.digest()
        counts[key[0].decode('ascii')] += 1
    return result, counts


def verify(before, after):
    a, ca = fingerprint(before)
    b, cb = fingerprint(after)
    missing, added = a.keys() - b.keys(), b.keys() - a.keys()
    changed = [key for key in a.keys() & b.keys() if a[key] != b[key]]
    report = {
        'input_sha256': sha256_file(before), 'output_sha256': sha256_file(after),
        'input_records': len(a), 'output_records': len(b),
        'input_ofst': ca['ofst'], 'output_ofst': cb['ofst'],
        'missing_records': [(s.decode(), f'{i:08X}') for s, i in sorted(missing)],
        'added_records': [(s.decode(), f'{i:08X}') for s, i in sorted(added)],
        'changed_protected_records': [(s.decode(), f'{i:08X}') for s, i in sorted(changed)],
        'scope': 'Record identity, flags, version control, parent group path and all subrecord bytes, excluding TES4/WRLD OFST and HEDR record recount. In-game behavior unverified.',
    }
    report['passed'] = not missing and not added and not changed and cb['ofst'] == 0
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before', type=Path)
    parser.add_argument('after', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    report = verify(args.before, args.after)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report['passed'] else 1)
