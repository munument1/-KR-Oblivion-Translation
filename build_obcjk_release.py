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

ORIGINAL_FONT_SETTINGS = ('[Fonts]\nSFontFile_1=Data\\Fonts\\Kingthings_Regular.fnt\n'
                          'SFontFile_2=Data\\Fonts\\Kingthings_Shadowed.fnt\n'
                          'SFontFile_3=Data\\Fonts\\Tahoma_Bold_Small.fnt\n'
                          'SFontFile_4=Data\\Fonts\\Daedric_Font.fnt\n'
                          'SFontFile_5=Data\\Fonts\\Handwritten.fnt\n')


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
        csv_report = audit(HERE / 'docs/obcjk/release_csv_inventory.json', tables)
        if csv_report['failed']:
            raise ValueError('Unresolved translation text; refusing UTF-8 output')
        # Release translation and location tables are already canonicalized and
        # carry their verified UTF-8 targets. Legacy/remaster CSVs stay archival.
        for name in ('canonical_translation_v2.csv', 'canonical_locations_v2.csv'):
            shutil.copyfile(HERE / name, tables / name)
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
        (output / 'FONT_SETTINGS.txt').write_text(ORIGINAL_FONT_SETTINGS, encoding='utf-8')
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
        # Record ordering comes from the canonical TES4Edit save, while this
        # builder retains the user's original record data and translated text.
        from master_layout import apply_layout
        master = output / 'Oblivion.esm'
        native_report = apply_layout(
            master, stage / 'Oblivion.ordered.esm',
            HERE / 'assets/oblivion_native_layout.json.gz',
            source_sha256=sha256_file(source / 'Oblivion.esm'))
        ordered = master.with_suffix('.esm.native-building')
        shutil.copyfile(stage / 'Oblivion.ordered.esm', ordered)
        if sha256_file(ordered) != native_report['output_sha256']:
            raise ValueError('Native layout copy checksum mismatch')
        ordered.replace(master)
        legacy_audit['files']['Oblivion.esm']['before_native_layout_sha256'] = legacy_audit['files']['Oblivion.esm']['output_sha256']
        legacy_audit['files']['Oblivion.esm']['output_sha256'] = native_report['output_sha256']
        legacy_audit['native_master_layout'] = native_report
        reports['Oblivion.esm']['before_native_layout_sha256'] = reports['Oblivion.esm']['output_sha256']
        reports['Oblivion.esm']['output_sha256'] = native_report['output_sha256']
        reports['Oblivion.esm']['native_master_layout'] = native_report
        (output / 'obcjk_validation.json').write_text(
            json.dumps(reports, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        (output / 'translation_audit.json').write_text(
            json.dumps(legacy_audit, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return 0
