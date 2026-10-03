"""Validate bundled OFL fonts and install them for the current Windows user."""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
BUNDLE = ROOT / 'assets/obcjk_fonts'
REGISTRY_KEY = r'Software\Microsoft\Windows NT\CurrentVersion\Fonts'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bundle_manifest(bundle=BUNDLE):
    bundle = Path(bundle).resolve()
    manifest = json.loads((bundle / 'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('schema') != 1 or {f['id'] for f in manifest['fonts']} != {
            'source_regular', 'source_medium', 'iropke'} or len(manifest['fonts']) != 3:
        raise ValueError('Invalid bundled font manifest')
    for item in [*manifest['fonts'], *manifest['licenses']]:
        path = (bundle / item['file']).resolve()
        if bundle not in path.parents or digest(path) != item['sha256']:
            raise ValueError(f'Bundled font/license checksum mismatch: {item["file"]}')
    for item in manifest['fonts']:
        if (bundle / item['file']).read_bytes()[:4] not in {b'\0\1\0\0', b'OTTO'}:
            raise ValueError('Invalid bundled font format')
    return manifest


def font_check(face, weight, aliases=()):
    """Check actual GDI selection and Hangul/ASCII support, without UI input."""
    if sys.platform != 'win32':
        raise OSError('Font installation requires Windows')
    gdi = ctypes.WinDLL('gdi32', use_last_error=True)
    gdi.CreateCompatibleDC.argtypes = [ctypes.c_void_p]
    gdi.CreateCompatibleDC.restype = ctypes.c_void_p
    gdi.CreateFontW.argtypes = [ctypes.c_int] * 5 + [ctypes.c_uint] * 8 + [ctypes.c_wchar_p]
    gdi.CreateFontW.restype = ctypes.c_void_p
    gdi.SelectObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    gdi.SelectObject.restype = ctypes.c_void_p
    gdi.GetTextFaceW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p]
    gdi.GetGlyphIndicesW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int,
                                   ctypes.POINTER(ctypes.c_ushort), ctypes.c_uint]
    gdi.GetGlyphIndicesW.restype = ctypes.c_uint
    gdi.DeleteObject.argtypes = [ctypes.c_void_p]
    gdi.DeleteDC.argtypes = [ctypes.c_void_p]
    dc = gdi.CreateCompatibleDC(None)
    font = gdi.CreateFontW(-40, 0, 0, 0, weight, 0, 0, 0, 1, 0, 0, 4, 0, face)
    if not dc or not font:
        raise ctypes.WinError(ctypes.get_last_error())
    previous = gdi.SelectObject(dc, font)
    try:
        actual = ctypes.create_unicode_buffer(128)
        if not gdi.GetTextFaceW(dc, len(actual), actual):
            raise ctypes.WinError(ctypes.get_last_error())
        text = ''.join(chr(cp) for cp in range(0xAC00, 0xD7A4)) + ''.join(chr(cp) for cp in range(32, 127))
        glyphs = (ctypes.c_ushort * len(text))()
        if gdi.GetGlyphIndicesW(dc, text, len(text), glyphs, 1) == 0xFFFFFFFF:
            raise ctypes.WinError(ctypes.get_last_error())
        selected = actual.value
        return {'requested_face': face, 'selected_face': selected, 'weight': weight,
                'face_matches': selected.casefold() in {s.casefold() for s in (face, *aliases)},
                'hangul_missing': sum(g == 0xFFFF for g in glyphs[:11172]),
                'ascii_missing': ''.join(ch for ch, g in zip(text[11172:], glyphs[11172:]) if g == 0xFFFF)}
    finally:
        gdi.SelectObject(dc, previous)
        gdi.DeleteObject(font)
        gdi.DeleteDC(dc)


def install_fonts(bundle=BUNDLE):
    """Persist HKCU font entries, preserving existing files and registry values."""
    if sys.platform != 'win32':
        raise OSError('Font installation requires Windows')
    import winreg
    manifest = bundle_manifest(bundle)
    local = Path(os.environ['LOCALAPPDATA']).resolve()
    destination = local / 'Microsoft/Windows/Fonts'
    gdi = ctypes.WinDLL('gdi32')
    gdi.AddFontResourceExW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint, ctypes.c_void_p]
    gdi.RemoveFontResourceExW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint, ctypes.c_void_p]
    plan = []
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, REGISTRY_KEY, 0,
                           winreg.KEY_READ | winreg.KEY_WRITE) as registry:
        # Preflight every target before copying or registering any font.
        for item in manifest['fonts']:
            suffix = '(TrueType)' if item['file'].endswith('.ttf') else '(OpenType)'
            value_name = item['full_name'] + ' ' + suffix
            try:
                existing, kind = winreg.QueryValueEx(registry, value_name)
            except FileNotFoundError:
                existing = None
            target = destination / ('OblivionKR-' + item['sha256'][:16] + '-' + item['file'])
            if existing is not None:
                existing_path = Path(existing)
                if kind != winreg.REG_SZ or not existing_path.is_absolute() or not existing_path.is_file() or digest(existing_path) != item['sha256']:
                    raise ValueError(f'Existing user font differs; preserved: {value_name}')
                target = existing_path
            if target.exists() and digest(target) != item['sha256']:
                raise ValueError(f'Existing font file differs; preserved: {target}')
            plan.append((item, value_name, target, existing))
        created_files, created_values, loaded = [], [], []
        results = []
        try:
            destination.mkdir(parents=True, exist_ok=True)
            for item, value_name, target, existing in plan:
                if not target.exists():
                    # Exclusive creation also protects against a concurrent installation.
                    with (Path(bundle) / item['file']).open('rb') as src, target.open('xb') as dst:
                        created_files.append(target)
                        shutil.copyfileobj(src, dst)
                if digest(target) != item['sha256']:
                    raise ValueError('Installed font checksum mismatch')
                if not gdi.AddFontResourceExW(str(target), 0, None):
                    raise OSError(f'Windows could not load {item["file"]}')
                loaded.append(target)
                check = font_check(item['family'], item['weight'], item.get('aliases', ()))
                if not check['face_matches'] or check['hangul_missing'] or check['ascii_missing'] != item['ascii_missing']:
                    raise ValueError(f'Windows font substitution/coverage mismatch: {check}')
                if existing is None:
                    winreg.SetValueEx(registry, value_name, 0, winreg.REG_SZ, str(target))
                    created_values.append(value_name)
                results.append({'id': item['id'], 'file': str(target), 'sha256': item['sha256'],
                                'registry_value': value_name, 'reused': existing is not None, 'gdi': check})
        except Exception:
            for target in reversed(loaded):
                gdi.RemoveFontResourceExW(str(target), 0, None)
            for name in reversed(created_values):
                winreg.DeleteValue(registry, name)
            for target in reversed(created_files):
                target.unlink(missing_ok=True)
            raise
    user = ctypes.WinDLL('user32')
    user.SendMessageTimeoutW.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_size_t,
                                        ctypes.c_ssize_t, ctypes.c_uint, ctypes.c_uint,
                                        ctypes.POINTER(ctypes.c_size_t)]
    result = ctypes.c_size_t()
    user.SendMessageTimeoutW(0xFFFF, 0x001D, 0, 0, 2, 1000, ctypes.byref(result))
    return {'scope': 'current Windows user; HKCU and LocalAppData', 'fonts': results}


def preset_ini():
    """Keep the tested geometry and apply the user's chosen typefaces."""
    from build_obcjk_release import default_ini
    lines = default_ini().decode('utf-8').splitlines()
    ascii_index = next(i for i, line in enumerate(lines) if line.startswith('AsciiRenderEnable = '))
    lines[ascii_index] = 'AsciiRenderEnable = 0'
    slots = {1: ('Source Han Serif KR Medium', 'Source Han Serif KR Medium', 500),
             2: ('Source Han Serif KR Medium', 'Source Han Serif KR Medium', 500),
             3: ('Source Han Serif KR Medium', 'Source Han Serif KR Medium', 500),
             5: ('Iropke Batang Medium', 'Iropke Batang Medium', 500)}
    for slot in (7, 8, 33, 34, 35, 36, 37):
        slots[slot] = ('Source Han Serif KR', 'Source Han Serif KR', 400)
    section = None
    for index, line in enumerate(lines):
        if line.startswith('[') and line.endswith(']'):
            section = line
            continue
        if section != '[UTF8]' or not line.startswith('FontParam') or '_Native' in line:
            continue
        key, value = line.split(' = ')
        parts = key.removeprefix('FontParam').split('_')
        if len(parts) != 2 or parts[1] not in {'1', '2'}:
            continue
        slot, region = parts
        half, cjk, weight = slots[int(slot)]
        fields = value.split(',')
        fields[0] = half if region == '1' else cjk
        geometry = {
            1: (0, 38 if region == '1' else 39, 0, 0, 32),
            2: (0, 40, 0, 0, 34), 3: (0, 26, 0, 0, 34),
            5: (0, 34, 0, 0, 34), 7: (0, 24, 1, -3, 30),
            8: (0, 24, 2, 0, 30),
        }.get(int(slot), (0, 32 if region == '1' else 34, 2, 0, 34))
        fields[1:6] = map(str, geometry)
        fields[6] = str(weight)
        lines[index] = key + ' = ' + ','.join(fields)
    return ('\n'.join(lines) + '\n').encode('utf-8')
