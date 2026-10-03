"""Capture/apply verified Oblivion group layout without shipping record payloads.

Binary traversal stays in build_obcjk_overlay.write's existing walker.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from build_obcjk_overlay import write
from build_vanilla_overlay import sha256_file
from verify_canonical_oblivion import verify

ORIGINAL_SOURCE_SHA256 = 'a26e21ea8c3041f8737ffb3a266129dedb7f8a88590625ecfecd5eb7f66b4a70'


def _event_summary(events):
    digest = hashlib.sha256()
    record_count = group_count = depth = 0
    seen = set()
    for event in events:
        if event[0] == 'g' and len(event) == 2:
            header = bytes.fromhex(event[1])
            if len(header) != 20 or header[:4] != b'GRUP':
                raise ValueError('Invalid group metadata')
            group_count += 1
            depth += 1
        elif event == ['e']:
            depth -= 1
            if depth < 0:
                raise ValueError('Unbalanced group metadata')
        elif event[0] == 'r' and len(event) == 3:
            sig, fid = event[1], event[2]
            if len(sig.encode('ascii')) != 4 or not isinstance(fid, int) or not 0 <= fid <= 0xFFFFFFFF:
                raise ValueError('Invalid record key metadata')
            key = (sig, fid)
            if key in seen:
                raise ValueError('Duplicate layout record key')
            seen.add(key)
            digest.update(sig.encode('ascii') + fid.to_bytes(4, 'little'))
            record_count += 1
        else:
            raise ValueError('Unknown layout metadata event')
    if depth or not events or events[0] != ['r', 'TES4', 0]:
        raise ValueError('Incomplete layout or missing TES4 header key')
    return {'record_count': record_count, 'group_count': group_count,
            'record_key_order_sha256': digest.hexdigest()}


def capture_layout(reference, generated, layout_path, original_source_sha256=ORIGINAL_SOURCE_SHA256):
    reference, generated, layout_path = map(Path, (reference, generated, layout_path))
    if layout_path.resolve() in {reference.resolve(), generated.resolve()}:
        raise ValueError('Layout asset must be separate from inputs')
    reference_hash, generated_hash = sha256_file(reference), sha256_file(generated)
    validation = verify(generated, reference)
    if not validation['passed']:
        raise ValueError('Native reference fails strict source-content verification')
    events = []
    write(reference, None, {}, captured_events=events)
    metadata = {'schema_version': 1, 'original_source_sha256': original_source_sha256,
                'generated_sha256': generated_hash, 'reference_sha256': reference_hash,
                **_event_summary(events)}
    metadata['events_sha256'] = hashlib.sha256(json.dumps(events, separators=(',', ':')).encode('ascii')).hexdigest()
    data = json.dumps({'metadata': metadata, 'events': events}, separators=(',', ':')).encode('ascii')
    if reference_hash != sha256_file(reference) or generated_hash != sha256_file(generated):
        raise ValueError('Input changed during layout capture')
    layout_path.parent.mkdir(parents=True, exist_ok=True)
    layout_path.write_bytes(gzip.compress(data, compresslevel=9, mtime=0))
    return {**metadata, 'gzip_bytes': layout_path.stat().st_size, 'json_bytes': len(data),
            'layout_asset_sha256': sha256_file(layout_path)}


def apply_layout(generated, output, layout_path, *, source_sha256=ORIGINAL_SOURCE_SHA256,
                 report_path=None):
    """Apply pinned layout to an exact rebuilt UTF-8 master; verify byte identity."""
    generated, output, layout_path = map(Path, (generated, output, layout_path))
    if output.resolve() in {generated.resolve(), layout_path.resolve()}:
        raise ValueError('Output must be separate from inputs')
    if output.exists():
        raise ValueError('Output already exists')
    if report_path is not None and Path(report_path).resolve() in {generated.resolve(), output.resolve(), layout_path.resolve()}:
        raise ValueError('Report must be separate from inputs and output')
    data = json.loads(gzip.decompress(layout_path.read_bytes()))
    metadata, events = data['metadata'], data['events']
    if metadata['schema_version'] != 1 or metadata['original_source_sha256'] != source_sha256:
        raise ValueError('Layout schema/source hash mismatch')
    event_hash = hashlib.sha256(json.dumps(events, separators=(',', ':')).encode('ascii')).hexdigest()
    if event_hash != metadata['events_sha256'] or any(metadata[k] != v for k, v in _event_summary(events).items()):
        raise ValueError('Layout counts or integrity hash mismatch')
    before_hash = sha256_file(generated)
    # The pinned native layout is structural metadata, not a translation-content
    # lock. Reuse it across later text-only translation updates as long as the
    # same original source is being rebuilt and the complete pinned record set
    # can be consumed without additions or omissions.
    write(generated, output, {}, layout_events=events, strip_ofst=True)
    validation = verify(generated, output)
    output_hash = sha256_file(output)
    unchanged = sha256_file(generated) == before_hash
    report = {'generated_sha256': before_hash, 'input_hash': before_hash,
              'layout_sha256': sha256_file(layout_path), 'source_sha256': source_sha256,
              'output_sha256': output_hash,
              'reference_sha256': metadata['reference_sha256'], 'input_unchanged': unchanged,
              'matches_captured_translation_bytes': before_hash == metadata['generated_sha256'],
              'byte_identical_to_native_reference': output_hash == metadata['reference_sha256'],
              'verification': validation}
    report['passed'] = unchanged and validation['passed']
    if report_path is not None:
        report_path = Path(report_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    if not report['passed']:
        raise ValueError('Applied layout failed strict content/layout verification')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    capture = sub.add_parser('capture')
    capture.add_argument('reference', type=Path)
    capture.add_argument('generated', type=Path)
    capture.add_argument('--output', type=Path, required=True)
    apply = sub.add_parser('apply')
    apply.add_argument('generated', type=Path)
    apply.add_argument('layout', type=Path)
    apply.add_argument('--output', type=Path, required=True)
    apply.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    result = (capture_layout(args.reference, args.generated, args.output) if args.command == 'capture'
              else apply_layout(args.generated, args.output, args.layout, report_path=args.report))
    print(json.dumps(result, indent=2))
