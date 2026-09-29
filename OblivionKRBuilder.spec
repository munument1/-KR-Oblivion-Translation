# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['build_vanilla_overlay.py'],
    pathex=[],
    binaries=[],
    datas=[('applied_translations_v2.csv', '.'), ('vanilla_completion.csv', '.'), ('patch_translation_memory.csv', '.'), ('legacy_carrier_completion.csv', '.'), ('legacy_full_recovery.csv', '.'), ('remaster_exact_memory.csv', '.'), ('remaster_info_memory.csv', '.'), ('remaster_info_dlc_memory.csv', '.'), ('remaster_questlog_memory.csv', '.'), ('remaster_desc_memory.csv', '.'), ('remaster_book_safe_memory.csv', '.'), ('remaster_extended_memory.csv', '.'), ('source_memory_recovery.csv', '.'), ('quest_unique_stage_memory.csv', '.'), ('manual_visible_memory.csv', '.'), ('exe_gmst_existing.csv', '.'), ('final_review_override.csv', '.'), ('menu_gmst_existing_105.csv', '.'), ('menu_gmst_new_821.csv', '.'), ('exe_gmst_translations.csv', '.'), ('exe_gmst_extra.csv', '.'), ('quest_loading_translations.csv', '.'), ('assets', 'assets'), ('video_subtitles', 'video_subtitles')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='OblivionKRBuilder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
