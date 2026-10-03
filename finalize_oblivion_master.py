"""Keep native group order while restoring protected rebuilt-master content.

Uses only the project's existing reader/writer. Removes TES4/WRLD OFST and
restores native auto-fixups and ten known original REFR slot normalizations.
"""
import argparse
import json
from pathlib import Path

from build_obcjk_overlay import records, write
from build_vanilla_overlay import sha256_file
from verify_canonical_oblivion import fingerprint, verify

KNOWN_ORIGINAL_REFR_IDS = frozenset((
    0x0100110A, 0x0100110B, 0x0100110C, 0x0100110D,
    0x01001595, 0x01001596, 0x01037A27, 0x01037A33,
    0x01037A40, 0x01037A41,
))


def finalize(before, canonical, output, report_path):
    before, canonical, output, report_path = map(Path, (before, canonical, output, report_path))
    if output.resolve() in {before.resolve(), canonical.resolve()}:
        raise ValueError('Output must be separate from both inputs')
    if report_path.resolve() in {before.resolve(), canonical.resolve(), output.resolve()}:
        raise ValueError('Report must be separate from inputs and output')
    if output.exists():
        raise ValueError('Output already exists')
    before_hash, canonical_hash = sha256_file(before), sha256_file(canonical)
    original, _ = fingerprint(before)
    native, _ = fingerprint(canonical)
    missing, added = original.keys() - native.keys(), native.keys() - original.keys()
    normalized = {}
    for key in missing:
        sig, fid = key
        target = (sig, fid & 0xFFFFFF)
        if sig != b'REFR' or fid not in KNOWN_ORIGINAL_REFR_IDS or target not in added:
            raise ValueError(f'Unexpected native record identity change: {key!r}')
        normalized[target] = key
    if set(normalized) != added:
        raise ValueError('Unexpected added native record identities')
    changed = {key for key in original.keys() & native.keys() if original[key] != native[key]}
    wanted = changed | set(normalized.values())
    overrides = {}
    stripped_ofst = 0
    for key, header, parts, groups in records(before):
        has_ofst = key[0] in {b'TES4', b'WRLD'} and any(f == b'OFST' for f, _, _ in parts)
        if key not in wanted and not has_ofst:
            continue
        body = []
        for field, value, raw in parts:
            if has_ofst and field == b'OFST':
                stripped_ofst += 1
            else:
                body.append(raw)
        input_key = next((target for target, source in normalized.items() if source == key), key)
        overrides[input_key] = (header, b''.join(body))
    if not wanted <= {normalized.get(k, k) for k in overrides}:
        raise ValueError('Required original record content was not recovered')
    del original, native
    write(canonical, output, {}, record_overrides=overrides)
    verification = verify(before, output)
    immutable = before_hash == sha256_file(before) and canonical_hash == sha256_file(canonical)
    report = {
        'before_sha256': before_hash, 'canonical_sha256': canonical_hash,
        'inputs_unchanged': immutable,
        'restored_protected_records': len(changed),
        'restored_original_raw_ids': [(s.decode(), f'{fid:08X}', f'{normalized[s, fid][1]:08X}')
                                     for s, fid in sorted(normalized)],
        'removed_ofst_subrecords': stripped_ofst,
        'record_overrides': len(overrides),
        'verification': verification,
        'passed': immutable and verification['passed'],
        'scope': 'Native canonical group order retained; rebuilt source record headers and fields preserved except OFST removal. Runtime untested.',
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before', type=Path)
    parser.add_argument('canonical', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    result = finalize(args.before, args.canonical, args.output, args.report)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['passed'] else 1)
