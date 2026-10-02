from contextlib import redirect_stdout
import hashlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from build_video_subtitles import build_videos, find_tools


class VideoSubtitleTests(unittest.TestCase):
    def test_missing_tools_warn_or_fail_without_creating_output(self):
        with tempfile.TemporaryDirectory() as tmp, patch('build_video_subtitles.find_tools', return_value=(None, None, None)):
            root = Path(tmp)
            output = root / 'output'
            log = io.StringIO()
            with redirect_stdout(log):
                self.assertEqual(build_videos(root / 'Data', output, root / 'subtitles'), {})
            self.assertIn('건너뜁니다', log.getvalue())
            with self.assertRaisesRegex(FileNotFoundError, 'FFmpeg'):
                build_videos(root / 'Data', output, root / 'subtitles', required=True)
            self.assertFalse(output.exists())

    def test_find_tools_only_uses_installed_dependencies(self):
        with patch('build_video_subtitles.shutil.which', return_value=None), \
             patch('build_video_subtitles.RAD_CANDIDATES', ()):
            self.assertEqual(find_tools(), (None, None, None))

    def test_changed_original_refused_before_encoding_and_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'Data/Video/OblivionIntro.bik'
            source.parent.mkdir(parents=True)
            source.write_bytes(b'BIKi changed source')
            before = hashlib.sha256(source.read_bytes()).hexdigest()
            subtitles = root / 'subtitles'
            subtitles.mkdir()
            (subtitles / 'OblivionIntro.srt').write_text('fixture', encoding='utf-8')
            with patch('build_video_subtitles.find_tools', return_value=('ffmpeg', 'ffprobe', 'rad')), \
                 patch('build_video_subtitles.subprocess.run') as run:
                with self.assertRaisesRegex(ValueError, 'hash differs'):
                    build_videos(root / 'Data', root / 'output', subtitles, required=True)
                run.assert_not_called()
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), before)
            self.assertFalse(list((root / 'output').rglob('*.bik')))


if __name__ == '__main__':
    unittest.main()
