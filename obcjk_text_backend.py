"""Text backends and narrowly pinned recovery for historical mixed encodings."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from oblivion_korean_codec import decode_legacy, encode_legacy


def remove_english_name_glosses(text: str, original_english: str):
    """Remove added English name glosses; retain original parentheses and syntax."""
    removed = []
    pattern = re.compile(r'(?<=[가-힣])\(([A-Za-z][A-Za-z0-9 .,\x27\x22:&/\-]*)\)')
    def replace(match):
        gloss = match.group(1)
        if gloss not in original_english or match.group(0) in original_english:
            return match.group(0)
        removed.append(gloss)
        return ''
    return pattern.sub(replace, text), removed


def encode_text(text: str, backend: str = 'legacy') -> bytes:
    if '\0' in text:
        raise ValueError('Text contains an embedded NUL')
    if backend == 'legacy':
        return encode_legacy(text) + b'\0'
    if backend == 'obcjk':
        return text.encode('utf-8', errors='strict') + b'\0'
    raise ValueError(f'Unknown text backend: {backend}')


def load_exceptions(path: Path):
    entries = json.loads(path.read_text(encoding='utf-8'))
    result = {entry['legacy_text_sha256']: entry for entry in entries}
    if len(result) != len(entries):
        raise ValueError('Duplicate legacy recovery hash')
    return result


def recover_legacy(data: bytes, exceptions: dict) -> str:
    entry = exceptions.get(hashlib.sha256(data).hexdigest())
    if entry is None:
        return decode_legacy(data)
    if entry['mode'] == 'cp1252':
        text = data.decode('cp1252', errors='strict')
        if text.encode('cp1252') != data:
            raise ValueError('Western alphabet test failed byte roundtrip')
        return text
    if entry['mode'] != 'mixed_cp949':
        raise ValueError('Unknown historical recovery mode')
    spans, cursor = [], 0
    for token in entry['tokens']:
        offset, raw = token['offset'], bytes.fromhex(token['hex'])
        if offset < cursor or data[offset:offset + len(raw)] != raw:
            raise ValueError('Pinned CP949 token does not match source')
        if token['unicode'].encode('cp949') != raw:
            raise ValueError('Pinned CP949 token failed byte roundtrip')
        spans.append(decode_legacy(data[cursor:offset]))
        spans.append(token['unicode'])
        cursor = offset + len(raw)
    spans.append(decode_legacy(data[cursor:]))
    return ''.join(spans)
