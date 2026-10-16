"""Bundle the game-verified, unofficial obCJK xOBSE UTF-8 correction."""
import hashlib
import json
from pathlib import Path

from obcjk_fonts import ROOT

BUNDLE = ROOT / 'assets/obcjk_runtime'
VERIFIED_SHA256 = 'ac215af221e680e03e3bbab03e890c34f7dcdfae422d7b82b21256f261b73d06'


def bundle_manifest(bundle=BUNDLE):
    bundle = Path(bundle)
    manifest = json.loads((bundle / 'manifest.json').read_text(encoding='utf-8'))
    data = (bundle / 'obCJK.dll').read_bytes()
    if (manifest.get('schema') != 1 or manifest.get('release') != 'temporary-fix-2'
            or manifest.get('sha256') != VERIFIED_SHA256
            or hashlib.sha256(data).hexdigest() != VERIFIED_SHA256):
        raise ValueError('Bundled obCJK runtime checksum mismatch')
    return manifest


def install_runtime(output, bundle=BUNDLE):
    manifest = bundle_manifest(bundle)
    target = Path(output) / 'OBSE/plugins/obCJK.dll'
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as stream:
        stream.write((Path(bundle) / 'obCJK.dll').read_bytes())
    if hashlib.sha256(target.read_bytes()).hexdigest() != VERIFIED_SHA256:
        raise ValueError('Installed obCJK runtime checksum mismatch')
    return {'file': 'OBSE/plugins/obCJK.dll', 'sha256': VERIFIED_SHA256,
            'release': manifest['release'], 'upstream_author': manifest['upstream_author'],
            'supported_xobse': '22.13; PE timestamp 684B4FE5; SizeOfImage 125000',
            'game_verified': manifest['game_verified'],
            'save_reload_verified': manifest['save_reload_verified']}
