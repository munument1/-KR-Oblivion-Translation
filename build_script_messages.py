"""Translate the verified sewer-exit literals at their original byte lengths.

The complete original script is pinned. Only literal payloads in SCDA and SCTX
change; trailing ASCII spaces preserve all compiled lengths and offsets.
"""
from __future__ import annotations

import hashlib
import shutil
import struct
from pathlib import Path

from build_vanilla_overlay import parse_subrecords, sha256_file

SCRIPT_FORMID = 0x0000A396
SCRIPT_EDID = b'CGSewerExitScript\0'
ORIGINAL_BODY_SHA256 = 'f3a9e221255d7b562ac0b67820cc32adbeaf37519aefb589e1a40853e2ef8c8d'
TRANSLATIONS = (
    (b'Before exiting the sewers, you may revise your character.', '탈출 전에 캐릭터를 수정할 수 있습니다.'),
    (b'Edit Race', '종족'),
    (b'Edit Birthsign', '별자리'),
    (b'Edit Class', '직업'),
    (b'Finished - Exit Sewers', '완료 - 탈출'),
)


def translate_body(body):
    if hashlib.sha256(body).hexdigest() != ORIGINAL_BODY_SHA256:
        raise ValueError('Sewer-exit script differs from the verified original')
    parts = list(parse_subrecords(body))
    if next((v for k, v, r in parts if k == b'EDID'), None) != SCRIPT_EDID:
        raise ValueError('Sewer-exit script identity mismatch')
    output = bytearray(body)
    changes = []
    offset = 0
    for field, value, raw in parts:
        if field in (b'SCDA', b'SCTX'):
            for english, korean in TRANSLATIONS:
                translated = korean.encode('utf-8')
                if len(translated) > len(english):
                    raise ValueError('Translation exceeds reserved literal length')
                translated = translated.ljust(len(english), b' ')
                if value.count(english) != 1:
                    raise ValueError('Expected one source literal in each script field')
                literal = value.index(english)
                if field == b'SCDA' and (
                    literal < 2 or struct.unpack_from('<H', value, literal - 2)[0] != len(english)
                ):
                    raise ValueError('Compiled string length mismatch')
                at = offset + len(raw) - len(value) + literal
                output[at:at + len(english)] = translated
                changes.append({'field': field.decode(), 'body_offset': at,
                                'bytes': len(english), 'english': english.decode(), 'korean': korean})
        offset += len(raw)
    if len(changes) != 10 or len(output) != len(body):
        raise ValueError('Expected five SCDA and five SCTX literals of unchanged size')
    # Reversing only the allowlisted text must recover the entire pinned script,
    # including opcodes, variable/reference data, SCHR and byte-count metadata.
    restored = bytearray(output)
    for change in changes:
        at = change['body_offset']
        restored[at:at + change['bytes']] = change['english'].encode('ascii')
    if bytes(restored) != body:
        raise ValueError('Non-literal script bytes changed')
    return bytes(output), changes


def find_script(path):
    found = []
    with path.open('rb') as stream:
        def walk(end):
            while stream.tell() < end:
                start = stream.tell()
                header = stream.read(20)
                if len(header) != 20:
                    raise ValueError('Truncated record header')
                kind, size, flags, fid, _ = struct.unpack('<4sIIII', header)
                limit = start + size if kind == b'GRUP' else start + 20 + size
                if limit > end or limit < start + 20:
                    raise ValueError('Invalid record bounds')
                if kind == b'GRUP':
                    walk(limit)
                elif kind == b'SCPT' and fid == SCRIPT_FORMID:
                    if flags & 0x40000:
                        raise ValueError('Expected uncompressed vanilla sewer-exit script')
                    found.append((start + 20, stream.read(size)))
                else:
                    stream.seek(size, 1)
            if stream.tell() != end:
                raise ValueError('Record boundary mismatch')
        walk(path.stat().st_size)
    if len(found) != 1:
        raise ValueError('Expected exactly one sewer-exit script')
    return found[0]


def build(source: Path, output: Path):
    source, output = Path(source), Path(output)
    if source.resolve() == output.resolve() or output.exists():
        raise ValueError('Script-message output must be new and separate from input')
    before_sha256 = sha256_file(source)
    offset, body = find_script(source)
    translated, changes = translate_body(body)
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, output)
    with output.open('r+b') as stream:
        stream.seek(offset)
        stream.write(translated)

    # Verify every output byte against the input plus this one approved body.
    source_hash, output_hash = hashlib.sha256(), hashlib.sha256()
    with source.open('rb') as left, output.open('rb') as right:
        position = 0
        while original := left.read(1 << 20):
            actual = right.read(len(original))
            expected = bytearray(original)
            start = max(position, offset)
            end = min(position + len(original), offset + len(translated))
            if start < end:
                expected[start - position:end - position] = translated[start - offset:end - offset]
            if actual != expected:
                raise ValueError('Script-message output differs outside the approved literals')
            source_hash.update(original)
            output_hash.update(actual)
            position += len(original)
        if right.read(1) or source_hash.hexdigest() != before_sha256:
            raise ValueError('Source changed or output size differs')
    return {'script_formid': f'{SCRIPT_FORMID:08X}', 'script_editor_id': SCRIPT_EDID[:-1].decode(),
            'display_strings': 5, 'literal_replacements': len(changes),
            'source_sha256': before_sha256, 'output_sha256': output_hash.hexdigest(),
            'original_script_sha256': ORIGINAL_BODY_SHA256,
            'translated_script_sha256': hashlib.sha256(translated).hexdigest(),
            'file_size_unchanged': True, 'only_allowlisted_literal_bytes_changed': True,
            'bytecode_lengths_and_control_flow_unchanged': True, 'changes': changes}
