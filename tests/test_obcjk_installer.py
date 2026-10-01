import configparser
import json
import tempfile
import unittest
from pathlib import Path

from install_obcjk import update_profile_fonts
from obcjk_fonts import BUNDLE, bundle_manifest, preset_ini


SETTINGS = '[Fonts]\n' + '\n'.join(f'SFontFile_{i}=Data\\Fonts\\Original{i}.fnt' for i in range(1, 6))


class InstallerTests(unittest.TestCase):
    def test_packaged_fonts_and_verified_control_setting(self):
        manifest = bundle_manifest()
        self.assertEqual({f['id'] for f in manifest['fonts']}, {'source_regular', 'source_medium', 'iropke'})
        ini = configparser.ConfigParser(interpolation=None)
        ini.read_string(preset_ini().decode('utf-8'))
        self.assertEqual(ini['obCJK']['AsciiRenderEnable'], '0')
        for slot in (1, 2, 3):
            for half in (1, 2):
                fields = ini['UTF8'][f'FontParam{slot}_{half}'].split(',')
                self.assertEqual((fields[0], fields[6]), ('Source Han Serif KR Medium', '500'))
        self.assertEqual((BUNDLE / 'obCJK.ini').read_bytes(), preset_ini())

    def test_profile_only_fonts_with_bom_and_crlf_and_original_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'Oblivion.ini'
            raw = ('\ufeff[General]\r\nSName=제국 감옥\r\n[Fonts]\r\n' +
                   ''.join(f'SFontFile_{i}=Old{i}\r\n' for i in range(1, 6)) +
                   '[Display]\r\niSize W=1920\r\n').encode('utf-8')
            path.write_bytes(raw)
            self.assertTrue(update_profile_fonts(path, SETTINGS, dry_run=True))
            self.assertEqual(path.read_bytes(), raw)
            self.assertEqual(len(list(Path(tmp).iterdir())), 1)
            backup = Path(update_profile_fonts(path, SETTINGS))
            self.assertEqual(backup.read_bytes(), raw)
            result = path.read_bytes()
            self.assertTrue(result.startswith(b'\xef\xbb\xbf'))
            self.assertIn('SName=제국 감옥\r\n'.encode('utf-8'), result)
            self.assertIn(b'[Display]\r\niSize W=1920\r\n', result)
            self.assertEqual(update_profile_fonts(path, SETTINGS), None)
            self.assertEqual(backup.read_bytes(), raw)

    def test_incomplete_profile_refused_before_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'Oblivion.ini'
            raw = b'[Fonts]\nSFontFile_1=old\n'
            path.write_bytes(raw)
            with self.assertRaisesRegex(ValueError, 'missing'):
                update_profile_fonts(path, SETTINGS, dry_run=True)
            self.assertEqual(path.read_bytes(), raw)
            self.assertEqual(len(list(Path(tmp).iterdir())), 1)


if __name__ == '__main__':
    unittest.main()
