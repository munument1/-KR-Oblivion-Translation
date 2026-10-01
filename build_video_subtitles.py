#!/usr/bin/env python3
"""Burn Korean narration subtitles into the user's original intro/outro Bink videos."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

EXPECTED_SHA256 = {
    "OblivionIntro.bik": "5EB30B0E8F022085A367D282CCB9E8007EECC6EDC4D2F2E10D8625BC92A2830E",
    "OblivionOutro.bik": "6A8086F3B3F98894CC4C36AF6755382315BAC0147DBD5FE2545734F34B5E4583",
}
RAD_CANDIDATES = (
    Path(r"C:\Program Files (x86)\RADVideo\radvideo64.exe"),
    Path(r"C:\Program Files\RADVideo\radvideo64.exe"),
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def find_tools():
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    rad = next((str(path) for path in RAD_CANDIDATES if path.is_file()), None)
    return ffmpeg, ffprobe, rad


def _probe(ffprobe: str, path: Path):
    result = subprocess.run((ffprobe, "-v", "error", "-show_entries",
                             "format=duration:stream=codec_name,codec_type,width,height",
                             "-of", "json", str(path)), check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def build_videos(data_dir: Path, output_dir: Path, subtitle_dir: Path, *, required=False):
    ffmpeg, ffprobe, rad = find_tools()
    if not all((ffmpeg, ffprobe, rad)):
        missing = [name for name, value in (("FFmpeg", ffmpeg), ("ffprobe", ffprobe), ("RAD Video Tools", rad)) if not value]
        message = "동영상 자막 생성 도구가 없습니다: " + ", ".join(missing)
        if required:
            raise FileNotFoundError(message)
        print("주의: " + message + ". 인트로·엔딩 자막 영상 생성을 건너뜁니다.")
        return {}
    video_dir = data_dir / "Video"
    targets = output_dir / "Video"
    targets.mkdir(parents=True, exist_ok=True)
    report = {}
    for name, expected_hash in EXPECTED_SHA256.items():
        source = video_dir / name
        subtitle = subtitle_dir / (Path(name).stem + ".srt")
        if not source.is_file() or not subtitle.is_file():
            raise FileNotFoundError(f"Video or subtitle missing: {source}, {subtitle}")
        source_hash = _sha256(source)
        if source_hash != expected_hash:
            raise ValueError(f"{name}: original video hash differs; subtitle timing needs review")
        original_info = _probe(ffprobe, source)
        print(f"한국어 자막 영상 생성 중: {name} (시간이 걸릴 수 있습니다.)", flush=True)
        with tempfile.TemporaryDirectory(prefix="oblivion_video_kr_", dir=output_dir) as tmp:
            tmp_path = Path(tmp)
            avi = tmp_path / (Path(name).stem + ".avi")
            bink = tmp_path / name
            filter_text = (f"subtitles=video_subtitles/{Path(name).stem}.srt:"
                           "force_style='FontName=Malgun Gothic,FontSize=24,"
                           "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
                           "Outline=2,Shadow=0,Alignment=2,MarginV=38'")
            subprocess.run((ffmpeg, "-y", "-loglevel", "error", "-i", str(source),
                            "-map", "0:v:0", "-map", "0:a:0", "-vf", filter_text,
                            "-c:v", "mjpeg", "-q:v", "3", "-c:a", "pcm_s16le",
                            str(avi)), cwd=subtitle_dir.parent, check=True, timeout=1200)
            subprocess.run((rad, "binkc", avi.name, bink.name, "/#"),
                           cwd=tmp_path, check=True, timeout=1200)
            if not bink.is_file() or bink.stat().st_size < 100000:
                raise ValueError(f"{name}: RAD did not produce a playable Bink 1 file")
            with bink.open("rb") as stream:
                if stream.read(4) != b"BIKi":
                    raise ValueError(f"{name}: RAD produced an unexpected Bink format")
            output_info = _probe(ffprobe, bink)
            if abs(float(original_info["format"]["duration"]) - float(output_info["format"]["duration"])) > 0.2:
                raise ValueError(f"{name}: duration changed after encoding")
            source_video = next(s for s in original_info["streams"] if s["codec_type"] == "video")
            output_video = next(s for s in output_info["streams"] if s["codec_type"] == "video")
            if (source_video["width"], source_video["height"]) != (output_video["width"], output_video["height"]):
                raise ValueError(f"{name}: frame size changed after encoding")
            if not any(s["codec_type"] == "audio" for s in output_info["streams"]):
                raise ValueError(f"{name}: audio track missing after encoding")
            target = targets / name
            bink.replace(target)
            report[name] = {"source_sha256": source_hash, "output_sha256": _sha256(target),
                            "duration_seconds": float(output_info["format"]["duration"]),
                            "output_bytes": target.stat().st_size}
            print(f"한국어 자막 영상 생성 완료: {name} ({target.stat().st_size:,} bytes)")
    return report
