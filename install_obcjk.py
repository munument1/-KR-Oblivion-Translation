"""Install the obCJK UTF-8 overlay and its bundled OFL fonts on Windows."""
from __future__ import annotations

import argparse
import configparser
import json
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

from obcjk_fonts import BUNDLE, ROOT, bundle_manifest, install_fonts, preset_ini


def update_profile_fonts(path, font_settings, *, dry_run=False):
    """Update only an explicitly chosen profile INI, with an exclusive backup."""
    path = Path(path).resolve()
    if not path.is_file() or path.suffix.lower() != '.ini':
        raise ValueError('Choose an existing MO2 profile Oblivion.ini')
    raw = path.read_bytes()
    text = raw.decode('utf-8-sig')
    parsed = configparser.ConfigParser(interpolation=None, strict=False)
    parsed.read_string(text)
    if not parsed.has_section('Fonts'):
        raise ValueError('Chosen INI has no Fonts section')
    replacements = dict(line.split('=', 1) for line in font_settings.splitlines() if line.startswith('SFontFile_'))
    found = set()
    section = ''
    lines = text.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if line.strip().startswith('['):
            section = line.strip().casefold()
        if section != '[fonts]' or '=' not in line:
            continue
        key = line.split('=', 1)[0].strip()
        if key in replacements:
            lines[index] = key + '=' + replacements[key] + ('\r\n' if line.endswith('\r\n') else '\n')
            found.add(key)
    if found != set(replacements):
        raise ValueError('Chosen INI is missing one or more SFontFile settings')
    changed = ''.join(lines).encode('utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8')
    if dry_run:
        return changed != raw
    if changed == raw:
        return None
    backup = path.with_name(path.name + '.before-obcjk-fonts.bak')
    if not backup.exists():
        with backup.open('xb') as stream:
            stream.write(raw)
    temporary = path.with_name(path.name + '.obcjk-fonts.building')
    with temporary.open('xb') as stream:
        stream.write(changed)
    temporary.replace(path)
    return str(backup)


def main():
    # The frozen UTF-8 builder invokes itself to produce its legacy intermediate.
    if '--text-backend' in sys.argv:
        from build_vanilla_overlay import main as builder_main
        return builder_main()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, help='Original game Data, read only')
    parser.add_argument('--output', type=Path, help='New, empty MO2 mod/output folder')
    parser.add_argument('--profile-ini', type=Path, help='Explicit MO2 profile Oblivion.ini; close MO2 first')
    parser.add_argument('--fonts-only', action='store_true', help='Install bundled fonts without rebuilding plugins')
    parser.add_argument('--report', type=Path, help='Installation report location')
    args = parser.parse_args()
    bundle_manifest()
    if args.fonts_only:
        if args.data_dir or args.output or args.profile_ini:
            parser.error('--fonts-only cannot modify an overlay/profile')
        report = install_fonts()
    else:
        if not args.data_dir or not args.output:
            parser.error('--data-dir and --output are required')
        if args.profile_ini:
            # Preflight before any build or font installation.
            if not args.profile_ini.is_file():
                parser.error('--profile-ini must exist')
            import subprocess
            running = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq ModOrganizer.exe', '/FO', 'CSV', '/NH'],
                                     capture_output=True, text=True, check=True)
            if 'modorganizer.exe' in running.stdout.lower():
                parser.error('Close MO2 before changing its profile INI')
            settings = '[Fonts]\n' + '\n'.join(f'SFontFile_{i}=' for i in range(1, 6))
            update_profile_fonts(args.profile_ini, settings, dry_run=True)
        from build_obcjk_release import build
        output = args.output.resolve()
        # This separate installer never changes the legacy default or Documents INI.
        preset = ROOT / 'assets/obcjk_fonts/obCJK.ini'
        if preset.read_bytes() != preset_ini():
            raise ValueError('Bundled font preset is out of date')
        build(SimpleNamespace(data_dir=args.data_dir, output=output, ini=None, obcjk_ini=preset,
                              csv=ROOT / 'applied_translations_v2.csv', extra_csv=[],
                              video_subtitles='off', korean_locations=True))
        shutil.copytree(BUNDLE, output / 'obCJK_Fonts')
        report = install_fonts()
        report['output'] = str(output)
        report['profile_ini_backup'] = update_profile_fonts(
            args.profile_ini, (output / 'FONT_SETTINGS.txt').read_text(encoding='utf-8')) if args.profile_ini else None
        report['profile_fonts_applied'] = bool(args.profile_ini)
        args.report = args.report or output / 'font_installation.json'
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text, encoding='utf-8')
    print(text)
    print('Fonts installed. Start Oblivion through MO2 with xOBSE and obCJK enabled.')
    if not args.fonts_only and not args.profile_ini:
        print('Profile INI unchanged. Apply the included FONT_SETTINGS.txt to your obCJK test profile.')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as error:
        print(f'Installation failed: {error}', file=sys.stderr)
        raise SystemExit(1)
