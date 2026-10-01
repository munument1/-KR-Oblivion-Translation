"""Create a verified UTF-8 unofficial-patch ZIP for a separate Nexus upload."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

OPTIONAL = {'Oblivion Citadel Door Fix.esp', 'DLCThievesDen - Unofficial Patch - SSSB.esp'}
OMIT = 'UOP Vampire Aging & Face Fix.esp'


def package(inputs, locations, output):
    sources, reports = {}, {}
    location_reports = json.loads((locations / 'location_validation.json').read_text(encoding='utf-8'))
    for folder in inputs:
        data = json.loads((folder / 'obcjk_validation.json').read_text(encoding='utf-8'))
        for name, report in data.items():
            path = folder / name
            if path.suffix.lower() != '.esp' or name in sources:
                raise ValueError('Expected unique unofficial ESP files')
            if hashlib.sha256(path.read_bytes()).hexdigest() != report['output_sha256']:
                raise ValueError(f'UTF-8 source checksum mismatch: {name}')
            sources[name] = path
            reports[name] = report
    if len(sources) != 14 or OMIT not in sources or reports[OMIT]['changes']:
        raise ValueError('Expected 14 verified patch ESPs including the untranslated optional fix')
    del sources[OMIT]
    entries, audit = [], {}
    for name, path in sorted(sources.items()):
        report = reports[name]
        lr = location_reports.get(name, {})
        if lr.get('changes'):
            if lr['source_sha256'] != report['output_sha256']:
                raise ValueError(f'Location input differs from validated UTF-8 source: {name}')
            path = locations / name
            if hashlib.sha256(path.read_bytes()).hexdigest() != lr['output_sha256']:
                raise ValueError(f'Location output checksum mismatch: {name}')
        target = ('Optional/' if name in OPTIONAL else '') + name
        entries.append((path, target))
        audit[name] = {'archive_path': target, 'original_sha256': report['original_sha256'],
                       'utf8_sha256': report['output_sha256'],
                       'output_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                       'utf8_validation': report['checks'], 'korean_location_counts': lr.get('location_counts', {}),
                       'location_validation': lr.get('checks'), 'unmatched_locations': lr.get('unmatched', [])}
    if sum('/' not in n for _, n in entries) != 11 or sum('/' in n for _, n in entries) != 2:
        raise ValueError('Expected 11 main and 2 optional translated ESPs')
    output.parent.mkdir(parents=True, exist_ok=True)
    readme = Path(__file__).resolve().parent / 'README_UOP_obCJK_KR.md'
    with output.open('xb') as stream, ZipFile(stream, 'w', ZIP_DEFLATED, compresslevel=6) as archive:
        for path, name in entries:
            archive.write(path, name)
        archive.write(readme, 'README_KR.md')
        archive.writestr('validation.json', json.dumps(audit, ensure_ascii=False, indent=2) + '\n')
        archive.writestr('SHA256SUMS.txt', ''.join(
            f'{audit[p.name]["output_sha256"]}  {name}\n' for p, name in entries))
    with ZipFile(output) as archive:
        if archive.testzip():
            raise ValueError('ZIP integrity check failed')
    sha = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(output.suffix + '.sha256').write_text(f'{sha}  {output.name}\n', encoding='ascii')
    print(output.resolve(), output.stat().st_size, sha)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, action='append', required=True)
    parser.add_argument('--locations', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    package(args.input_dir, args.locations, args.output)
