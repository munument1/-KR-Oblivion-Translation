import hashlib
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build_script_messages as messages
from build_vanilla_overlay import encode_subrecord, parse_subrecords


class ScriptMessageTests(unittest.TestCase):
    def setUp(self):
        # Synthetic fixture; no proprietary original bytecode is stored.
        self.scda = b'\x16\x00\x01\x00' + b''.join(
            struct.pack('<H', len(english)) + english + b'\x19\x00'
            for english, korean in messages.TRANSLATIONS)
        self.sctx = b'messagebox ' + b', '.join(
            b'"' + english + b'"' for english, korean in messages.TRANSLATIONS) + b'\0'
        self.body = (
            encode_subrecord(b'EDID', messages.SCRIPT_EDID) +
            encode_subrecord(b'SCHR', struct.pack('<IIIII', 0, 6, len(self.scda), 1, 0)) +
            encode_subrecord(b'SCDA', self.scda) + encode_subrecord(b'SCTX', self.sctx) +
            encode_subrecord(b'SCRO', struct.pack('<I', 0x58)))
        self.pin = hashlib.sha256(self.body).hexdigest()

    def plugin(self, body=None):
        body = self.body if body is None else body
        script = struct.pack('<4sIIII', b'SCPT', len(body), 0, messages.SCRIPT_FORMID, 7) + body
        return struct.pack('<4sI4sII', b'GRUP', 20 + len(script), b'SCPT', 0, 0) + script

    def test_literals_translate_with_metadata_and_non_text_bytes_preserved(self):
        with patch.object(messages, 'ORIGINAL_BODY_SHA256', self.pin):
            translated, changes = messages.translate_body(self.body)
        self.assertEqual(len(changes), 10)
        self.assertEqual(len(translated), len(self.body))
        for (a, old, raw), (b, new, new_raw) in zip(parse_subrecords(self.body), parse_subrecords(translated)):
            self.assertEqual(a, b)
            self.assertEqual(len(old), len(new))
            if a not in (b'SCDA', b'SCTX'):
                self.assertEqual(raw, new_raw)
            else:
                for english, korean in messages.TRANSLATIONS:
                    padded = korean.encode('utf-8').ljust(len(english), b' ')
                    self.assertEqual(new.count(padded), 1)
                    self.assertNotIn(english, new)
                    if a == b'SCDA':
                        self.assertEqual(struct.unpack_from('<H', new, new.index(padded) - 2)[0], len(english))

    def test_modified_source_is_rejected(self):
        with patch.object(messages, 'ORIGINAL_BODY_SHA256', self.pin):
            for modified in (self.body.replace(b'Edit Race', b'Edit Face'), self.body[:-1] + b'\x01'):
                with self.assertRaisesRegex(ValueError, 'verified original'):
                    messages.translate_body(modified)

    def test_compiled_length_mismatch_is_rejected(self):
        bad = self.body.replace(struct.pack('<H', len(messages.TRANSLATIONS[0][0])), b'\xff\x00', 1)
        with patch.object(messages, 'ORIGINAL_BODY_SHA256', hashlib.sha256(bad).hexdigest()):
            with self.assertRaisesRegex(ValueError, 'Compiled string length'):
                messages.translate_body(bad)

    def test_real_file_writer_preserves_input_and_all_other_records(self):
        with tempfile.TemporaryDirectory() as temporary:
            source, output = Path(temporary) / 'original.esm', Path(temporary) / 'translated.esm'
            other_body = encode_subrecord(b'EDID', b'Unrelated\0')
            other = struct.pack('<4sIIII', b'BOOK', len(other_body), 0, 0x55, 3) + other_body
            original = self.plugin() + other
            source.write_bytes(original)
            with patch.object(messages, 'ORIGINAL_BODY_SHA256', self.pin):
                report = messages.build(source, output)
            self.assertEqual(source.read_bytes(), original)
            self.assertEqual(output.stat().st_size, len(original))
            self.assertTrue(output.read_bytes().endswith(other))
            self.assertEqual(hashlib.sha256(output.read_bytes()).hexdigest(), report['output_sha256'])
            self.assertTrue(report['only_allowlisted_literal_bytes_changed'])
            with self.assertRaisesRegex(ValueError, 'new and separate'):
                messages.build(source, source)
            with self.assertRaisesRegex(ValueError, 'new and separate'):
                messages.build(source, output)

    def test_missing_duplicate_compressed_and_truncated_scripts_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / 'test.esm'
            compressed = bytearray(self.plugin())
            struct.pack_into('<I', compressed, 28, 0x40000)
            for raw in (b'', self.plugin() * 2, compressed, self.plugin()[:-1]):
                source.write_bytes(raw)
                with self.assertRaises(ValueError):
                    messages.find_script(source)


if __name__ == '__main__':
    unittest.main()
