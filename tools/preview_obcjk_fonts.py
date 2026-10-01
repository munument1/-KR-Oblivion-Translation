#!/usr/bin/env python3
"""Render local font candidates and inspect Windows GDI glyph availability.

This is an offline comparison, not an Oblivion runtime test or font installer.
Machine paths are supplied in a separate JSON manifest.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def inspect_gdi(face: str, weight: int) -> dict:
    gdi = ctypes.WinDLL("gdi32", use_last_error=True)
    gdi.CreateCompatibleDC.argtypes = [ctypes.c_void_p]
    gdi.CreateCompatibleDC.restype = ctypes.c_void_p
    gdi.CreateFontW.argtypes = [ctypes.c_int] * 5 + [ctypes.c_uint] * 8 + [ctypes.c_wchar_p]
    gdi.CreateFontW.restype = ctypes.c_void_p
    gdi.SelectObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    gdi.SelectObject.restype = ctypes.c_void_p
    gdi.GetTextFaceW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p]
    gdi.GetTextFaceW.restype = ctypes.c_int
    gdi.GetGlyphIndicesW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int, ctypes.POINTER(ctypes.c_ushort), ctypes.c_uint]
    gdi.GetGlyphIndicesW.restype = ctypes.c_uint
    gdi.DeleteObject.argtypes = [ctypes.c_void_p]
    gdi.DeleteDC.argtypes = [ctypes.c_void_p]
    dc = gdi.CreateCompatibleDC(None)
    font = gdi.CreateFontW(-28, 0, 0, 0, weight, 0, 0, 0, 1, 0, 0, 4, 0, face)
    if not dc or not font:
        raise ctypes.WinError(ctypes.get_last_error())
    previous = gdi.SelectObject(dc, font)
    try:
        actual = ctypes.create_unicode_buffer(128)
        if not gdi.GetTextFaceW(dc, len(actual), actual):
            raise ctypes.WinError(ctypes.get_last_error())
        text = "".join(chr(cp) for cp in range(0xAC00, 0xD7A4))
        glyphs = (ctypes.c_ushort * len(text))()
        if gdi.GetGlyphIndicesW(dc, text, len(text), glyphs, 1) == 0xFFFFFFFF:
            raise ctypes.WinError(ctypes.get_last_error())
        missing = [ch for ch, glyph in zip(text, glyphs) if glyph == 0xFFFF]
        return {
            "requested_face": face,
            "selected_face": actual.value,
            "weight": weight,
            "composed_hangul_total": len(text),
            "composed_hangul_missing": len(missing),
            "first_missing_characters": missing[:30],
        }
    finally:
        gdi.SelectObject(dc, previous)
        gdi.DeleteObject(font)
        gdi.DeleteDC(dc)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    specs = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
    width, band = 1360, 177
    canvas = Image.new("RGB", (width, 100 + band * len(specs)), "#efe2c5")
    draw = ImageDraw.Draw(canvas)
    title = ImageFont.truetype(specs[0]["path"], 25)
    draw.text((28, 20), "obCJK 폰트 비교 / 파일 렌더링 미리보기 (게임 화면 아님)", font=title, fill="#392b22")
    results = []
    for index, spec in enumerate(specs):
        path = Path(spec["path"])
        font = ImageFont.truetype(str(path), 29)
        if spec.get("variation"):
            font.set_variation_by_name(spec["variation"])
        result = inspect_gdi(spec["face"], spec.get("weight", 400))
        result.update({"label": spec["label"], "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "pillow_family_style": font.getname()})
        results.append(result)
        top = 85 + index * band
        draw.line((28, top, width - 28, top), fill="#b7a687", width=1)
        draw.text((28, top + 8), spec["label"], font=title, fill="#654531")
        for offset, text in enumerate((
            "새로하기  불러오기  환경설정  종료   —   값·꽃·읽음 (ABC 123)-A",
            "이곳에 오래 머물지 마십시오. 문 너머에서 무슨 일이 벌어질지 모릅니다.",
            "체력 125/200   무게 8.5   저항 50%   “잊힌 왕의 기록”  길흉을 읽는 자",
        )):
            draw.text((28, top + 45 + offset * 37), text, font=font, fill="#392b22")
    args.output.mkdir(parents=True, exist_ok=True)
    canvas.save(args.output / "font-comparison.png")
    report = {"scope": "local file preview and GDI glyph coverage; no game runtime proof", "fonts": results}
    (args.output / "font-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
