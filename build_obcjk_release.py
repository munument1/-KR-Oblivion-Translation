"""Build the UTF-8 variant through an unchanged legacy intermediate build."""
from __future__ import annotations

import configparser
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from audit_obcjk_texts import audit
from build_obcjk_overlay import build_directory
from build_obcjk_ui import build as build_ui
from build_vanilla_overlay import HERE, sha256_file


def default_ini():
    lines = ['[obCJK]', 'ActiveCodePage = UTF8', 'UILang = ko',
             'AsciiRenderEnable = 1', 'DebugLogEnable = 0', '', '[UTF8]']
    sizes = {1: 38, 2: 40, 3: 26, 5: 34, 7: 24, 8: 24,
             33: 32, 34: 32, 35: 32, 36: 32, 37: 32}
    for slot, size in sizes.items():
        for language in (1, 2):
            lines.append(f'FontParam{slot}_{language} = Malgun Gothic,0,{size},0,0,34,400,0,0')
        lines.append(f'FontParam{slot}_1_Native = 0')
    return ('\n'.join(lines) + '\n').encode('utf-8')


def build(args):
    output = args.output.resolve()
    source = args.data_dir.resolve()
    if output == source or source in output.parents or output in source.parents:
        raise ValueError('Output must be separate from original Data')
    if output.exists() and any(output.iterdir()):
        raise ValueError('obCJK output folder must be empty; keep variants separate')
    if args.ini:
        raise ValueError('--ini is for legacy installation; use profile-local original fonts for obCJK')
    ini_bytes = args.obcjk_ini.read_bytes() if args.obcjk_ini else default_ini()
    config = configparser.ConfigParser(interpolation=None)
    config.read_string(ini_bytes.decode('utf-8-sig'))
    if config.get('obCJK', 'ActiveCodePage', fallback='').upper() != 'UTF8':
        raise ValueError('obCJK INI must explicitly select ActiveCodePage = UTF8')
    with tempfile.TemporaryDirectory(prefix='obcjk-build-') as temporary:
        stage = Path(temporary)
        legacy = stage / 'legacy'
        # Frozen executables invoke themselves in legacy mode; Python invokes
        # the existing script. Arguments remain structured, with no shell.
        command = [sys.executable]
        if not getattr(sys, 'frozen', False):
            command.append(str(HERE / 'build_vanilla_overlay.py'))
        command += ['--text-backend', 'legacy', '--data-dir', str(source), '--output', str(legacy),
                    '--csv', str(args.csv.resolve()), '--video-subtitles', args.video_subtitles]
        for path in args.extra_csv:
            command += ['--extra-csv', str(path.resolve())]
        subprocess.run(command, check=True)
        tables = stage / 'tables'
        csv_report = audit(HERE / 'docs/obcjk/csv_inventory.json', tables)
        if csv_report['failed']:
            raise ValueError('Unresolved translation text; refusing UTF-8 output')
        # Additional caller-supplied CSVs are decoded strictly on actual use.
        reports = build_directory(source, legacy, tables, output)
        location_reports = {}
        if getattr(args, 'korean_locations', False):
            from build_obcjk_locations import build as build_locations
            locations = stage / 'locations'
            location_reports = build_locations([output], tables, locations)
            for name, report in location_reports.items():
                if not report.get('changes'):
                    continue
                # Temp and output may be on different Windows volumes. Copy
                # into the output volume before replacing its staged UTF-8 file.
                target = output / name
                copied = target.with_suffix(target.suffix + '.location-building')
                shutil.copyfile(locations / name, copied)
                if sha256_file(copied) != report['output_sha256']:
                    raise ValueError('Location copy checksum mismatch')
                copied.replace(target)
                reports[name]['utf8_before_locations_sha256'] = reports[name]['output_sha256']
                reports[name]['output_sha256'] = sha256_file(output / name)
                reports[name]['location_validation'] = 'location_validation.json'
            shutil.copyfile(locations / 'location_validation.json', output / 'location_validation.json')
            (output / 'obcjk_validation.json').write_text(
                json.dumps(reports, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        ui_report = build_ui(HERE / 'assets/menus/strings.xml', output / 'menus/strings.xml')
        for folder in ('Video',):
            if (legacy / folder).is_dir():
                shutil.copytree(legacy / folder, output / folder)
        font_settings = ('[Fonts]\nSFontFile_1=Data\\Fonts\\Kingthings_Regular.fnt\n'
                         'SFontFile_2=Data\\Fonts\\Kingthings_Shadowed.fnt\n'
                         'SFontFile_3=Data\\Fonts\\Tahoma_Bold_Small.fnt\n'
                         'SFontFile_4=Data\\Fonts\\Daedric_Font.fnt\n'
                         'SFontFile_5=Data\\Fonts\\Handwritten.fnt\n')
        (output / 'FONT_SETTINGS.txt').write_text(font_settings, encoding='utf-8')
        ini_path = output / 'OBSE/plugins/obCJK/obCJK.ini'
        ini_path.parent.mkdir(parents=True, exist_ok=True)
        ini_path.write_bytes(ini_bytes)
        legacy_audit = json.loads((legacy / 'translation_audit.json').read_text(encoding='utf-8'))
        legacy_audit['text_backend'] = 'obcjk'
        for name, report in legacy_audit['files'].items():
            target = output / name
            report['legacy_intermediate_sha256'] = report['output_sha256']
            report['output_sha256'] = sha256_file(target) if target.exists() else None
        legacy_audit['utf8_validation'] = 'obcjk_validation.json'
        legacy_audit['csv_texts'] = {key: value for key, value in csv_report.items() if key != 'files'}
        legacy_audit['menu_xml'] = ui_report
        legacy_audit['obcjk_ini_sha256'] = sha256_file(ini_path)
        legacy_audit['runtime_verified'] = False
        legacy_audit['korean_locations'] = bool(getattr(args, 'korean_locations', False))
        if location_reports:
            legacy_audit['location_validation'] = 'location_validation.json'
        (output / 'translation_audit.json').write_text(
            json.dumps(legacy_audit, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return 0
