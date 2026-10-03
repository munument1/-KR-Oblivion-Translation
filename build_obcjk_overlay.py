#!/usr/bin/env python3
"""Convert a separate, validated legacy build to UTF-8 for obCJK.

Uses the project's existing Oblivion record helpers. Original and legacy inputs
are read only. Every rewritten field is recorded and checked on readback.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import struct
import zlib
from collections import Counter
from pathlib import Path

from build_unofficial_release import read_records
from build_vanilla_overlay import HERE, encode_subrecord, parse_subrecords, sha256_file, structure_signature
from oblivion_korean_codec import decode_legacy
from obcjk_text_backend import load_exceptions, recover_legacy

EXCEPTIONS = load_exceptions(HERE / 'docs/obcjk/legacy_text_exceptions.json')


def records(path):
    """Yield record headers, uncompressed fields and their complete group path."""
    with path.open('rb') as stream:
        def walk(end, groups=()):
            while stream.tell() < end:
                start = stream.tell()
                header = stream.read(20)
                if len(header) != 20:
                    raise ValueError(f'{path}: truncated header at {start}')
                kind, size, flags, fid, _ = struct.unpack('<4sIIII', header)
                if kind == b'GRUP':
                    if size < 20 or start + size > end:
                        raise ValueError(f'{path}: invalid GRUP bounds')
                    yield from walk(start + size, groups + (header[:4] + header[8:],))
                else:
                    if start + 20 + size > end:
                        raise ValueError(f'{path}: record crosses parent bounds')
                    body = stream.read(size)
                    if flags & 0x40000:
                        if len(body) < 4:
                            raise ValueError('Short compressed record')
                        plain = zlib.decompress(body[4:])
                        if len(plain) != struct.unpack_from('<I', body)[0]:
                            raise ValueError('Uncompressed length mismatch')
                    else:
                        plain = body
                    yield (kind, fid), header, list(parse_subrecords(plain)), groups
            if stream.tell() != end:
                raise ValueError(f'{path}: parent boundary mismatch')
        yield from walk(path.stat().st_size)


def unicode_memory(folder):
    targets = {}
    for path in sorted(folder.glob('*.csv')):
        with path.open(encoding='utf-8-sig', newline='') as stream:
            for row in csv.DictReader(stream):
                if row.get('obcjk_conversion_status') != 'verified':
                    continue
                for column in ('new_bytes_hex', 'encoded_hex', 'target_hex'):
                    if row.get(column):
                        raw = bytes.fromhex(row[column])
                        target = bytes.fromhex(row['obcjk_utf8_hex'])
                        targets.setdefault(raw, set()).add(target)
                        break
    return targets


def convert_text(raw, memory):
    if not raw.endswith(b'\0') or b'\0' in raw[:-1]:
        raise ValueError('Expected exactly one terminal NUL')
    candidates = memory.get(raw, set())
    # An unambiguous audited Unicode source retains its original punctuation.
    # When multiple sources disagree, preserve the actual legacy text instead.
    if len(candidates) == 1:
        result = next(iter(candidates))
    else:
        result = recover_legacy(raw[:-1], EXCEPTIONS).encode('utf-8') + b'\0'
    result[:-1].decode('utf-8', errors='strict')
    if b'\0' in result[:-1] or not result.endswith(b'\0'):
        raise ValueError('Invalid UTF-8 target termination')
    return result


def is_text(kind, field, editor):
    return (field == b'FULL' or
            field == b'DESC' or
            field == b'NAM1' and kind == b'INFO' or
            field == b'CNAM' and kind == b'QUST' or
            field == b'DATA' and kind == b'GMST' and editor.startswith(b's'))


def prepare(legacy, original, memory, smoke=False):
    originals = read_records(original)
    menu_additions = {}
    if legacy.name == 'Oblivion.esm':
        with (HERE / 'menu_gmst_new_821.csv').open(encoding='utf-8-sig', newline='') as stream:
            menu_additions = {int(row['formid'], 16): row['edid'].encode('ascii') + b'\0'
                              for row in csv.DictReader(stream)}
    changes, manifest, chosen = {}, [], set()
    seen = set()
    smoke_kinds = {b'GMST', b'WEAP', b'BOOK', b'SPEL', b'MGEF', b'INFO'}
    found = set()
    for key, header, parts, groups in records(legacy):
        kind, fid = key
        if smoke and (kind not in smoke_kinds or kind in found):
            continue
        if key in seen:
            raise ValueError(f'Duplicate legacy record: {key}')
        seen.add(key)
        old_parts = originals.get(key)
        if old_parts is None:
            if (kind != b'GMST' or fid not in menu_additions or
                    [p[0] for p in parts] != [b'EDID', b'DATA'] or
                    parts[0][1] != menu_additions[fid] or header[8:] != struct.pack('<III', 0, fid, 0)):
                raise ValueError(f'Unexpected extra record {key}')
        elif [x[0] for x in old_parts] != [x[0] for x in parts]:
            raise ValueError(f'Subrecord sequence changed: {key}')
        editor = next((value.rstrip(b'\0') for field, value, _ in parts if field == b'EDID'), b'')
        replacements = {}
        for index, (field, value, raw) in enumerate(parts):
            baseline = old_parts[index][1] if old_parts is not None else None
            translated = baseline is not None and baseline != value
            if translated and not is_text(kind, field, editor):
                # TES4's HEDR count is the documented 821 menu-record addition.
                if kind == b'TES4' and field == b'HEDR':
                    expected_header = bytearray(baseline)
                    struct.pack_into('<I', expected_header, 4,
                                     struct.unpack_from('<I', baseline, 4)[0] + len(menu_additions))
                    if value != expected_header:
                        raise ValueError('Unexpected TES4 HEDR change')
                    continue
                raise ValueError(f'Non-text legacy difference: {key} {field!r}')
            if not is_text(kind, field, editor):
                continue
            if kind in {b'CELL', b'WRLD', b'RACE'} and field == b'FULL':
                if translated:
                    raise ValueError(f'Protected location/race name changed: {key}')
                continue
            if not value.endswith(b'\0') or b'\0' in value[:-1]:
                raise ValueError(f'Invalid text termination: {key} {field!r}')
            if translated or old_parts is None:
                if smoke and (kind not in smoke_kinds or kind in found):
                    continue
                try:
                    target = convert_text(value, memory)
                except (UnicodeError, ValueError) as error:
                    raise ValueError(f'{legacy.name} {kind.decode()} {fid:08X} {field.decode()} index {index}: {error}') from error
            else:
                # Untranslated western text also needs UTF-8 in global UTF8 mode.
                target = value[:-1].decode('cp1252').encode('utf-8') + b'\0'
            if target != value:
                replacements[index] = (field, value, target)
        if smoke and replacements:
            # A smoke override includes its complete source record and all of its
            # translated text fields, not just the first label in that record.
            if kind not in smoke_kinds or kind in found:
                continue
            found.add(kind)
            chosen.add(key)
            if kind == b'INFO':
                for group in groups:
                    if struct.unpack_from('<I', group, 8)[0] == 7:
                        chosen.add((b'DIAL', struct.unpack_from('<I', group, 4)[0]))
        if replacements:
            changes[key] = replacements
            for index, (field, before, after) in replacements.items():
                manifest.append({'type': kind.decode('ascii'), 'formid': f'{fid:08X}',
                                 'editor_id': editor.decode('ascii'), 'field': field.decode('ascii'),
                                 'index': index, 'source_sha256': hashlib.sha256(before).hexdigest(),
                                 'utf8_hex': after.hex(), 'text': after[:-1].decode('utf-8')})
    if not smoke:
        expected = set(originals) | {(b'GMST', fid) for fid in menu_additions}
        if seen != expected:
            raise ValueError('Original records or documented menu additions are missing')
    if smoke and found != smoke_kinds:
        raise ValueError(f'Missing smoke categories: {smoke_kinds - found}')
    if smoke:
        for key, header, parts, groups in records(legacy):
            if key not in chosen or key[0] != b'DIAL':
                continue
            editor = next((v.rstrip(b'\0') for f, v, _ in parts if f == b'EDID'), b'')
            for index, (field, value, raw) in enumerate(parts):
                if field != b'FULL':
                    continue
                target = convert_text(value, memory)
                if target != value:
                    changes.setdefault(key, {})[index] = (field, value, target)
                    manifest.append({'type': 'DIAL', 'formid': f'{key[1]:08X}',
                                     'editor_id': editor.decode('ascii'), 'field': 'FULL', 'index': index,
                                     'source_sha256': hashlib.sha256(value).hexdigest(),
                                     'utf8_hex': target.hex(), 'text': target[:-1].decode('utf-8')})
    return changes, manifest, chosen


def write(legacy, destination, changes, chosen=None, record_overrides=None,
          layout_events=None, captured_events=None, strip_ofst=False):
    """Write existing group order, optionally replacing complete record content.

    Overrides map input (signature, FormID) to (20-byte header, plain body).
    Replacement headers supply flags, identity and VCS; size is recalculated.
    """
    record_overrides = record_overrides or {}
    used_overrides = set()
    layout_records = {}
    special_layout = layout_events is not None or captured_events is not None
    if special_layout and chosen is not None:
        raise ValueError('Layout mode cannot select a subset')

    def emit_record(header, body, output):
        kind = header[:4]
        fid = struct.unpack_from('<I', header, 12)[0]
        if captured_events is not None:
            captured_events.append(['r', kind.decode('ascii'), fid])
        if layout_events is not None:
            key = (kind, fid)
            if key in layout_records:
                raise ValueError('Duplicate layout source record')
            layout_records[key] = header + body
        if not special_layout:
            output.append(header + body)
    with legacy.open('rb') as src:
        def walk(end):
            output = []
            while src.tell() < end:
                start = src.tell()
                header = src.read(20)
                if len(header) != 20:
                    raise ValueError('Truncated writer input header')
                kind, size, flags, fid, _ = struct.unpack('<4sIIII', header)
                if kind == b'GRUP':
                    if size < 20 or start + size > end:
                        raise ValueError('Invalid writer input group bounds')
                    if captured_events is not None:
                        captured_events.append(['g', header.hex()])
                    children = walk(start + size)
                    if captured_events is not None:
                        captured_events.append(['e'])
                    if not special_layout and (children or chosen is None):
                        output.append(header[:4] + struct.pack('<I', len(children) + 20) + header[8:] + children)
                    continue
                if start + 20 + size > end:
                    raise ValueError('Writer input record crosses group bounds')
                body = src.read(size)
                if chosen is not None and (kind, fid) not in chosen:
                    continue
                override = record_overrides.get((kind, fid))
                if override is not None:
                    if changes.get((kind, fid)):
                        raise ValueError('Record override conflicts with field changes')
                    replacement_header, plain = override
                    if len(replacement_header) != 20 or replacement_header[:4] != kind:
                        raise ValueError('Invalid replacement record header')
                    replacement_flags = struct.unpack_from('<I', replacement_header, 8)[0]
                    body = (struct.pack('<I', len(plain)) + zlib.compress(plain)
                            if replacement_flags & 0x40000 else plain)
                    header = replacement_header[:4] + struct.pack('<I', len(body)) + replacement_header[8:]
                    used_overrides.add((kind, fid))
                    emit_record(header, body, output)
                    continue
                replacements = changes.get((kind, fid), {})
                if replacements or (strip_ofst and kind in {b'TES4', b'WRLD'}):
                    plain = zlib.decompress(body[4:]) if flags & 0x40000 else body
                    updated = []
                    changed_body = bool(replacements)
                    for index, (field, value, raw) in enumerate(parse_subrecords(plain)):
                        if strip_ofst and kind in {b'TES4', b'WRLD'} and field == b'OFST':
                            changed_body = True
                            continue
                        replacement = replacements.get(index)
                        if replacement:
                            if replacement[:2] != (field, value):
                                raise ValueError('Replacement source mismatch')
                            updated.append(encode_subrecord(field, replacement[2]))
                        else:
                            updated.append(raw)
                    plain = b''.join(updated)
                    if changed_body:
                        body = struct.pack('<I', len(plain)) + zlib.compress(plain) if flags & 0x40000 else plain
                        header = header[:4] + struct.pack('<I', len(body)) + header[8:]
                emit_record(header, body, output)
            return b''.join(output)
        payload = walk(legacy.stat().st_size)
    if used_overrides != record_overrides.keys():
        raise ValueError('Record override source is missing or excluded')
    if layout_events is not None:
        stack = [(None, [])]
        for event in layout_events:
            if event[0] == 'g':
                group_header = bytes.fromhex(event[1])
                if len(group_header) != 20 or group_header[:4] != b'GRUP':
                    raise ValueError('Invalid layout group header')
                stack.append((group_header, []))
            elif event[0] == 'e':
                if len(stack) == 1:
                    raise ValueError('Unbalanced layout group end')
                group_header, chunks = stack.pop()
                children = b''.join(chunks)
                stack[-1][1].append(group_header[:4] + struct.pack('<I', len(children) + 20) + group_header[8:] + children)
            elif event[0] == 'r':
                key = (event[1].encode('ascii'), event[2])
                if key not in layout_records:
                    raise ValueError('Layout record missing or repeated')
                stack[-1][1].append(layout_records.pop(key))
            else:
                raise ValueError('Unknown layout event')
        if len(stack) != 1 or layout_records:
            raise ValueError('Unbalanced layout or unused source records')
        payload = b''.join(stack[0][1])
    if destination is None:
        if captured_events is None:
            raise ValueError('Missing writer destination')
        return
    if chosen is not None:
        body = (encode_subrecord(b'HEDR', struct.pack('<fII', 1.0, len(chosen), 0x800)) +
                encode_subrecord(b'CNAM', b'obCJK Korean encoding smoke test\0') +
                encode_subrecord(b'MAST', b'Oblivion.esm\0') + encode_subrecord(b'DATA', b'\0' * 8))
        payload = struct.pack('<4sIIII', b'TES4', len(body), 0, 0, 0) + body + payload
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)


def validate(legacy, destination, changes, chosen=None):
    before = records(legacy)
    if chosen is not None:
        before = (r for r in before if r[0] in chosen)
    after = records(destination)
    if chosen is not None:
        tes4 = next(after)
        if tes4[0] != (b'TES4', 0):
            raise ValueError('Smoke TES4 missing')
    counts = Counter()
    sentinel = object()
    from itertools import zip_longest
    for left, right in zip_longest(before, after, fillvalue=sentinel):
        if left is sentinel or right is sentinel:
            raise ValueError('Record count mismatch')
        key, header, parts, groups = left
        key2, header2, parts2, groups2 = right
        if key != key2 or header[:4] + header[8:] != header2[:4] + header2[8:] or groups != groups2:
            raise ValueError(f'Record identity, flags, header or group path changed: {key}')
        if len(parts) != len(parts2):
            raise ValueError(f'Subrecord count mismatch: {key}')
        for index, (left_part, right_part) in enumerate(zip(parts, parts2)):
            field, value, raw = left_part
            field2, value2, raw2 = right_part
            if field != field2:
                raise ValueError('Subrecord order mismatch')
            expected = changes.get(key, {}).get(index)
            if expected:
                if expected != (field, value, value2):
                    raise ValueError('Target differs from allowlist')
                value2[:-1].decode('utf-8', 'strict')
                if not value2.endswith(b'\0') or b'\0' in value2[:-1]:
                    raise ValueError('Target NUL mismatch')
                counts['changed_text_fields'] += 1
            else:
                if raw != raw2:
                    raise ValueError(f'Non-allowlisted bytes changed: {key} {field!r}')
                counts['unchanged_subrecords'] += 1
        counts['records'] += 1
    expected_count = sum(len(v) for k, v in changes.items() if chosen is None or k in chosen)
    if counts['changed_text_fields'] != expected_count:
        raise ValueError('Allowlist coverage mismatch')
    result = dict(counts)
    if chosen is None:
        before_signature = structure_signature(legacy)
        if before_signature != structure_signature(destination):
            raise ValueError('Container identity or compiled-script signature mismatch')
        result['structure'] = before_signature
    return result


def build_directory(original_dir, legacy_dir, tables_dir, output_dir, smoke=False):
    output = output_dir.resolve()
    for source in (original_dir.resolve(), legacy_dir.resolve(), tables_dir.resolve()):
        if output == source or source in output.parents or output in source.parents:
            raise ValueError('Output must be separate from every input folder')
    memory = unicode_memory(tables_dir)
    reports = {}
    paths = [legacy_dir / 'Oblivion.esm'] if smoke else sorted(
        p for p in legacy_dir.iterdir() if p.suffix.lower() in {'.esp', '.esm'})
    for legacy in paths:
        original = original_dir / legacy.name
        changes, manifest, chosen = prepare(legacy, original, memory, smoke)
        target = output / ('ObCJK_KR_Smoke.esp' if smoke else legacy.name)
        temporary = target.with_suffix(target.suffix + '.building')
        write(legacy, temporary, changes, chosen if smoke else None)
        checks = validate(legacy, temporary, changes, chosen if smoke else None)
        temporary.replace(target)
        reports[target.name] = {'source_sha256': sha256_file(legacy), 'original_sha256': sha256_file(original),
                               'output_sha256': sha256_file(target), 'checks': checks, 'changes': manifest,
                               'scope': 'Selected complete override records' if smoke else 'Complete legacy plugin'}
        print(target.name, checks)
    output.mkdir(parents=True, exist_ok=True)
    (output / 'obcjk_validation.json').write_text(json.dumps(reports, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original-dir', type=Path, required=True)
    parser.add_argument('--legacy-dir', type=Path, required=True)
    parser.add_argument('--tables-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--smoke', action='store_true')
    args = parser.parse_args()
    build_directory(args.original_dir, args.legacy_dir, args.tables_dir, args.output, args.smoke)


if __name__ == '__main__':
    main()
