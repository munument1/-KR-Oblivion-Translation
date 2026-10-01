#!/usr/bin/env python3
"""Add audited Korean CELL/WRLD names to separate UTF-8 test variants."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from build_obcjk_overlay import records, validate
from build_unofficial_release import rewrite
from build_vanilla_overlay import PATCH_TO_OFFICIAL, decode_english, sha256_file


def build(inputs, tables, output):
    output = output.resolve()
    for source in [*inputs, tables]:
        source = source.resolve()
        if output == source or source in output.parents or output in source.parents:
            raise ValueError('Location output must be separate from inputs')
    if output.exists() and any(output.iterdir()):
        raise ValueError('Location output folder must be empty')
    memory = defaultdict(list)
    english_memory = defaultdict(list)
    paths = {}
    for folder in inputs:
        for path in folder.iterdir():
            if path.suffix.lower() in {'.esm', '.esp'}:
                if path.name in paths:
                    raise ValueError(f'Duplicate input filename: {path.name}')
                paths[path.name] = path
    for path in sorted(tables.glob('*.csv')):
        with path.open(encoding='utf-8-sig', newline='') as stream:
            for line, row in enumerate(csv.DictReader(stream), 2):
                if row.get('record_type') not in {'CELL', 'WRLD'} or row.get('field') != 'FULL':
                    continue
                if row.get('obcjk_conversion_status') != 'verified':
                    raise ValueError(f'Unverified location text: {path.name}:{line}')
                target = bytes.fromhex(row['obcjk_utf8_hex'])
                text = target[:-1].decode('utf-8', 'strict')
                if not target.endswith(b'\0') or b'\0' in target[:-1] or text != row['obcjk_unicode_text']:
                    raise ValueError('Invalid audited location target')
                source = row['effective_source']
                item = (source, row['old_english'], target, row.get('editor_id'), path.name, line)
                english_memory[row['old_english']].append(item)
                key = (source, row['record_type'].encode('ascii'), int(row['raw_formid'], 16))
                memory[key].append(item)
                official = PATCH_TO_OFFICIAL.get(source)
                if official:
                    memory[(official, key[1], key[2])].append(item)
    output.mkdir(parents=True, exist_ok=True)
    reports = {}
    for name, source in sorted(paths.items()):
        changes, manifest, unmatched, counts = {}, [], [], Counter()
        for key, header, parts, groups in records(source):
            kind, fid = key
            if kind not in {b'CELL', b'WRLD'}:
                continue
            editor = next((value.rstrip(b'\0').decode('ascii') for field, value, _ in parts if field == b'EDID'), '')
            candidates = memory.get((name, kind, fid), ())
            if not candidates:
                official = PATCH_TO_OFFICIAL.get(name)
                candidates = memory.get((official, kind, fid), ()) if official else ()
            for index, (field, value, raw) in enumerate(parts):
                if field != b'FULL':
                    continue
                english = decode_english(value)
                matches = [x for x in candidates if x[1] == english and (not x[3] or x[3] == editor)]
                direct = [x for x in matches if x[0] == name]
                if direct:
                    matches = direct
                match_kind = 'record_and_source'
                if not matches:
                    matches = english_memory.get(english, ())
                    match_kind = 'exact_english_memory'
                targets = {x[2] for x in matches}
                if len(targets) != 1:
                    if candidates:
                        unmatched.append({'type': kind.decode(), 'formid': f'{fid:08X}',
                                          'editor_id': editor, 'english': english,
                                          'reason': 'ambiguous' if targets else 'source_mismatch'})
                    continue
                target = targets.pop()
                if target == value:
                    continue
                changes.setdefault(key, {})[index] = (field, value, target)
                counts[kind.decode()] += 1
                manifest.append({'type': kind.decode(), 'formid': f'{fid:08X}', 'field': 'FULL',
                                 'editor_id': editor, 'index': index, 'english': english,
                                 'text': target[:-1].decode('utf-8'), 'utf8_hex': target.hex(),
                                 'match_kind': match_kind,
                                 'sources': [{'csv': x[4], 'line': x[5], 'source': x[0]} for x in matches]})
        if changes:
            target = output / name
            temporary = target.with_suffix(target.suffix + '.building')
            applied = rewrite(source, temporary, changes)
            if applied != len(manifest):
                raise ValueError('Location application count mismatch')
            checks = validate(source, temporary, changes)
            temporary.replace(target)
            reports[name] = {'source_sha256': sha256_file(source), 'output_sha256': sha256_file(target),
                             'checks': checks, 'location_counts': dict(counts), 'changes': manifest,
                             'unmatched': unmatched}
            print(name, dict(counts))
        elif unmatched:
            reports[name] = {'location_counts': {}, 'unmatched': unmatched, 'changes': []}
    (output / 'location_validation.json').write_text(
        json.dumps(reports, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, action='append', required=True)
    parser.add_argument('--tables-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    build(args.input_dir, args.tables_dir, args.output)


if __name__ == '__main__':
    main()
