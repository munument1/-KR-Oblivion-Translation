import unittest

from oblivion_korean_codec import decode_legacy, encode_hangul, encode_legacy


class LegacyTextCodecTests(unittest.TestCase):
    def test_all_composed_hangul_roundtrip(self):
        text = "".join(chr(cp) for cp in range(0xAC00, 0xD7A4))
        self.assertEqual(decode_legacy(encode_legacy(text)), text)
        self.assertEqual(len({encode_hangul(ch) for ch in text}), 11172)

    def test_mixed_text_and_line_breaks(self):
        text = "값 꽃 읽음 (A1) 'test' - 50%\r\n“설정” &amp;"
        self.assertEqual(decode_legacy(encode_legacy(text)), text)

    def test_truncated_or_invalid_hangul_fails(self):
        for encoded in (encode_hangul("꽃")[:-1], b"\xb0", b"\xb0\x01"):
            with self.assertRaises(UnicodeDecodeError):
                decode_legacy(encoded)


if __name__ == "__main__":
    unittest.main()
