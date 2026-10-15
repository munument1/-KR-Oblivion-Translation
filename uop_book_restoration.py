"""UOP BOOK/DESC restoration using the audited Oblivion UTF-8 canonical source.

The 2026-10-15 audit identified 112 long English book bodies which an older
UOP Korean table had reduced to a short title. Preserve UOP identity and all
unrelated record data; replace only explicitly enumerated, source-hash-pinned
fields. Do not use a translated BOOK/FULL title as BOOK/DESC.
"""
from __future__ import annotations

import csv
import hashlib
import re
from pathlib import Path

UOP_PLUGIN = "Unofficial Oblivion Patch.esp"
BARZ_FIVE = 0x00024574
WILD_ELVES = 0x00024594
CLAUDIUS_JOURNAL = 0x00072296
EXPECTED_REPAIRS = 112
MARKUP = re.compile(r"<\s*(?:font|div|br|img|p)\b", re.IGNORECASE)


def suspicious_book_body(source: str, translated: str) -> bool:
    """Catch severe book-body -> single-label regressions, not short pamphlets."""
    return (len(source) >= 250
            and len(translated) <= max(110, round(len(source) * 0.20))
            and not MARKUP.search(translated)
            and (bool(MARKUP.search(source)) or len(translated) < len(source) * 0.08))


def _special_uop_changes(formid: int, text: str) -> str:
    if formid == WILD_ELVES:
        # Carry forward the UOP's corrected historical-date spacing.
        if "1E2790-2E227" not in text:
            raise ValueError("Unexpected Wild Elves canonical body")
        return text.replace("1E2790-2E227", "1E 2790-2E 227").replace("2E12", "2E 12")
    if formid == CLAUDIUS_JOURNAL:
        # Canonical already correctly translates "skin" as "가죽".
        if "심장과 가죽" not in text or text.count("\r\n\r\n") != 2:
            raise ValueError("Unexpected Claudius journal body")
        return ("<font face=5><BR>\r\n"
                + text.replace("\r\n\r\n", "<BR>\r\n<BR>\r\n")
                + "<BR>\r\n</font>")
    return text


def load_restorations(manifest_path: Path, canonical_path: Path,
                      expected_count: int = EXPECTED_REPAIRS) -> dict[int, tuple[str, bytes]]:
    """Return {FormID: (SHA-256 of exact UOP source DESC, validated UTF-8 DESC)}."""
    expected = {}
    with manifest_path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            fid = int(row["formid"], 16)
            source_sha = row["source_sha256"]
            if fid in expected or not re.fullmatch(r"[a-f0-9]{64}", source_sha):
                raise ValueError(f"Duplicate/invalid UOP book restoration: {fid:08X}")
            expected[fid] = source_sha
    if len(expected) != expected_count:
        raise ValueError(f"UOP book restoration count {len(expected)} != {expected_count}")

    found = {}
    with canonical_path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            if (row["effective_source"] != "Oblivion.esm"
                    or row["record_type"] != "BOOK"
                    or row["field"] != "DESC"):
                continue
            fid = int(row["raw_formid"], 16)
            if fid not in expected:
                continue
            if fid in found:
                raise ValueError(f"Duplicated canonical BOOK/DESC: {fid:08X}")
            target_hex = row["obcjk_utf8_hex"]
            if not target_hex:
                raise ValueError(f"Missing canonical UTF-8 book body: {fid:08X}")
            target = bytes.fromhex(target_hex)
            if not target.endswith(b"\0") or b"\0" in target[:-1]:
                raise ValueError(f"Corrupted canonical BOOK/DESC: {fid:08X}")
            body = target[:-1].decode("utf-8", errors="strict")
            if not body.strip() or not re.search("[가-힣]", body) or len(body) < 80:
                raise ValueError(f"Too-short canonical BOOK/DESC: {fid:08X}")
            if suspicious_book_body(row["old_english"], body):
                raise ValueError(f"Canonical BOOK/DESC itself appears truncated: {fid:08X}")
            if fid in (WILD_ELVES, CLAUDIUS_JOURNAL):
                body = _special_uop_changes(fid, body)
                target = body.encode("utf-8") + b"\0"
            found[fid] = (expected[fid], target)

    missing = set(expected) - set(found)
    if missing:
        raise ValueError(f"Missing canonical BOOK/DESC values: {[f'{x:08X}' for x in sorted(missing)]}")
    return found


def restore_book_body(formid: int, raw_source: bytes,
                      restorations: dict[int, tuple[str, bytes]]) -> bytes | None:
    item = restorations.get(formid)
    if item is None:
        return None
    expected_sha, replacement = item
    if hashlib.sha256(raw_source).hexdigest() != expected_sha:
        raise ValueError(f"Changed UOP BOOK/DESC source hash: {formid:08X}")
    try:
        old = raw_source.rstrip(b"\0").decode("cp1252")
        new = replacement[:-1].decode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise ValueError(f"Invalid UOP BOOK/DESC encoding: {formid:08X}") from exc
    if len(new) < 80 or suspicious_book_body(old, new):
        raise ValueError(f"Restored BOOK/DESC is still truncated: {formid:08X}")
    return replacement


def normalize_volume_five_title(value: bytes) -> bytes:
    if not value.endswith(b"\0"):
        raise ValueError("BOOK/FULL title is not NUL-terminated")
    title = value[:-1].decode("utf-8", errors="strict")
    if "진짜 바렌지아" in title:
        return title.replace("진짜 바렌지아", "진정한 바렌지아").encode("utf-8") + b"\0"
    if "진정한 바렌지아" in title:
        return value
    raise ValueError(f"Unexpected Real Barenziah vol 5 title: {title!r}")
