# UTF-8 installer built from the existing translation backend.
tables = [
    'canonical_translation_v2.csv',
    'canonical_locations_v2.csv',
    'menu_gmst_existing_105.csv',
    'menu_gmst_new_821.csv',
]
a = Analysis(['install_obcjk.py'], pathex=[], binaries=[],
    datas=[(name, '.') for name in tables] + [
        ('assets', 'assets'), ('video_subtitles', 'video_subtitles'),
        ('docs/obcjk/release_csv_inventory.json', 'docs/obcjk'),
        ('docs/obcjk/legacy_text_exceptions.json', 'docs/obcjk')],
    hiddenimports=['build_vanilla_overlay', 'build_obcjk_release', 'winreg'],
    hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False, optimize=0)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name='OblivionKRBuilder',
    debug=False, bootloader_ignore_signals=False, strip=False, upx=False, upx_exclude=[],
    runtime_tmpdir=None, console=True, disable_windowed_traceback=False,
    argv_emulation=False, target_arch=None, codesign_identity=None, entitlements_file=None)
