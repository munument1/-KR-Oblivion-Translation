#!/usr/bin/env python3
"""Burn Korean narration subtitles into the user's original intro/outro Bink videos."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile
from pathlib import Path

EXPECTED_SHA256 = {
    "OblivionIntro.bik": "5EB30B0E8F022085A367D282CCB9E8007EECC6EDC4D2F2E10D8625BC92A2830E",
    "OblivionOutro.bik": "6A8086F3B3F98894CC4C36AF6755382315BAC0147DBD5FE2545734F34B5E4583",
}
RAD_CANDIDATES = (
    Path(r"C:\Program Files (x86)\RADVideo\radvideo64.exe"),
    Path(r"C:\Program Files\RADVideo\radvideo64.exe"),
)
FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-9.0.2-essentials_build.zip"
FFMPEG_SHA256 = "60f467265b1e312373dbcd92200c2618a74850f98d3d078e94296bb3fa2047ba"
RAD_URL = "https://www.radgametools.com/down/Bink/RADTools.7z"
RAD_SHA1 = "76e7b8e41c36edf9aba68ebc6d872871f5a1c5c5"
SEVEN_ZR_URL = "https://github.com/ip7z/7zip/releases/download/26.03/7zr.exe"
SEVEN_ZR_SHA256 = "ad4c82fadcbdf93c03b4fc440f300509c7d60c5c2f4d183e35d9d70d6957037d"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _digest(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest().lower()


def _tool_cache() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA") or tempfile.gettempdir())
    return base / "OblivionKRInstaller" / "video-tools"


def _download(url: str, target: Path, expected: str, algorithm: str = "sha256") -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file() and _digest(target, algorithm) == expected.lower():
        return
    partial = target.with_suffix(target.suffix + ".part")
    partial.unlink(missing_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "OblivionKRInstaller/1.0.5"})
    print(f"동영상 도구 자동 준비 중: {target.name}", flush=True)
    try:
        with urllib.request.urlopen(request, timeout=90) as response, partial.open("wb") as stream:
            shutil.copyfileobj(response, stream, length=1 << 20)
        actual = _digest(partial, algorithm)
        if actual != expected.lower():
            raise ValueError(f"{target.name} 다운로드 해시가 다릅니다: {actual}")
        partial.replace(target)
    finally:
        partial.unlink(missing_ok=True)


def _safe_extract_zip(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    with zipfile.ZipFile(archive) as zipped:
        for member in zipped.infolist():
            target = (destination / member.filename).resolve()
            if root != target and root not in target.parents:
                raise ValueError(f"압축 파일 경로가 안전하지 않습니다: {member.filename}")
        zipped.extractall(destination)


def _prepare_ffmpeg(cache: Path):
    folder = cache / "ffmpeg"
    ffmpeg = next(folder.rglob("ffmpeg.exe"), None) if folder.exists() else None
    ffprobe = next(folder.rglob("ffprobe.exe"), None) if folder.exists() else None
    if ffmpeg and ffprobe:
        return str(ffmpeg), str(ffprobe)
    archive = cache / "ffmpeg-release-essentials.zip"
    _download(FFMPEG_URL, archive, FFMPEG_SHA256)
    if folder.exists():
        shutil.rmtree(folder)
    _safe_extract_zip(archive, folder)
    ffmpeg = next(folder.rglob("ffmpeg.exe"), None)
    ffprobe = next(folder.rglob("ffprobe.exe"), None)
    if not ffmpeg or not ffprobe:
        raise FileNotFoundError("자동 준비한 FFmpeg에서 ffmpeg.exe/ffprobe.exe를 찾지 못했습니다.")
    return str(ffmpeg), str(ffprobe)


def _prepare_rad(cache: Path):
    folder = cache / "rad"
    existing = None
    if folder.exists():
        existing = next(folder.rglob("radvideo64.exe"), None) or next(folder.rglob("radvideo.exe"), None)
    if existing:
        return str(existing)
    seven = cache / "7zr.exe"
    archive = cache / "RADTools.7z"
    _download(SEVEN_ZR_URL, seven, SEVEN_ZR_SHA256)
    _download(RAD_URL, archive, RAD_SHA1, "sha1")
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True, exist_ok=True)
    subprocess.run((str(seven), "x", "-y", "-pRAD", f"-o{folder}", str(archive)),
                   check=True, capture_output=True, timeout=120)
    rad = next(folder.rglob("radvideo64.exe"), None) or next(folder.rglob("radvideo.exe"), None)
    if not rad:
        raise FileNotFoundError("자동 준비한 RAD Video Tools에서 radvideo 실행 파일을 찾지 못했습니다.")
    return str(rad)


def find_tools(*, auto_prepare=True):
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    rad = next((str(path) for path in RAD_CANDIDATES if path.is_file()), None)
    if not auto_prepare or all((ffmpeg, ffprobe, rad)):
        return ffmpeg, ffprobe, rad

    cache = _tool_cache()
    try:
        if not ffmpeg or not ffprobe:
            cached_ffmpeg, cached_ffprobe = _prepare_ffmpeg(cache)
            ffmpeg = ffmpeg or cached_ffmpeg
            ffprobe = ffprobe or cached_ffprobe
        if not rad:
            rad = _prepare_rad(cache)
    except (OSError, ValueError, zipfile.BadZipFile, subprocess.SubprocessError) as error:
        print(f"주의: 동영상 도구 자동 준비에 실패했습니다: {error}")
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
        message = "동영상 자막 생성 도구를 자동 준비하지 못했습니다: " + ", ".join(missing)
        if required:
            raise FileNotFoundError(message)
        print("주의: " + message + ". 인터넷 연결을 확인하세요. 인트로·엔딩 자막 영상 생성을 건너뜁니다.")
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
