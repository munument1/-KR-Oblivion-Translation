from __future__ import annotations
import csv, json, re, struct, sys, unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(r"D:\Codex_Trans\오블리비언\v2_work")
IN_DIR = ROOT / "00_incoming_sst"
OUT_DIR = ROOT / "01_glossary"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def read_i32(b, p):
    return struct.unpack_from("<i", b, p)[0], p + 4

def read_u32(b, p):
    return struct.unpack_from("<I", b, p)[0], p + 4

def read_u16(b, p):
    return struct.unpack_from("<H", b, p)[0], p + 2

def read_wstr(b, p):
    size, p = read_i32(b, p)
    if size < 0 or size % 2 or p + size > len(b):
        raise ValueError(f"invalid UTF-16 byte length {size} at {p-4}")
    return b[p:p+size].decode("utf-16le"), p + size
def parse_record(b, p, version):
    start = p
    if p >= len(b):
        raise EOFError
    list_index = b[p]; p += 1
    if list_index > 2:
        raise ValueError(f"bad list index {list_index} at {start}")
    data = dict(list_index=list_index, str_id=0, formid=0, rname="", fname="",
                index=0, index_max=0, record_hash=0, colab_id=0, status_bits=0)
    if version > 1:
        data["str_id"], p = read_i32(b, p)
        data["formid"], p = read_u32(b, p)
        if version > 4:
            data["rname"] = b[p:p+4].decode("ascii", "replace"); p += 4
            data["fname"] = b[p:p+4].decode("ascii", "replace"); p += 4
        if version > 2:
            data["index"], p = read_u16(b, p)
        if version > 3:
            data["index_max"], p = read_u16(b, p)
            data["record_hash"], p = read_u32(b, p)
        if version > 5:
            data["colab_id"] = b[p]; p += 1
    data["status_bits"] = b[p]; p += 1
    data["source"], p = read_wstr(b, p)
    data["translation"], p = read_wstr(b, p)
    return data, p

def parse_records_to_end(b, p, version):
    rows = []
    while p < len(b):
        row, p = parse_record(b, p, version)
        rows.append(row)
    if p != len(b):
        raise ValueError("record parse did not end at EOF")
    return rows
def parse_sst(path: Path):
    b = path.read_bytes()
    if len(b) < 9 or b[:3] != b"SSU" or not chr(b[3]).isdigit():
        raise ValueError("unsupported SST header")
    version = int(chr(b[3]))
    p = 4
    if version > 3:
        flag = b[p]; p += 1
    else:
        flag = 0
    masters = []
    if version > 7:
        master_count, p = read_i32(b, p)
        if not (0 <= master_count <= 10000):
            raise ValueError(f"implausible master count {master_count}")
        for _ in range(master_count):
            s, p = read_wstr(b, p)
            masters.append(s)

    # Some distributed SSU8 dictionaries omit the v7 collab-label table.
    candidates = [(p, [])]
    if version > 6 and p + 4 <= len(b):
        try:
            q = p
            collab_count, q = read_i32(b, q)
            labels = []
            if 0 <= collab_count <= 4096:
                for _ in range(collab_count):
                    cid, q = read_i32(b, q)
                    label, q = read_wstr(b, q)
                    labels.append((cid, label))
                candidates.insert(0, (q, labels))
        except Exception:
            pass
    errors = []
    for record_start, labels in candidates:
        try:
            rows = parse_records_to_end(b, record_start, version)
            return {"version": version, "flag": flag, "masters": masters,
                    "collab_labels": labels, "rows": rows, "record_start": record_start}
        except Exception as e:
            errors.append(f"{record_start}: {e}")
    raise ValueError("could not parse records; " + " | ".join(errors))

_ws = re.compile(r"\s+")
def norm_source(s):
    return _ws.sub(" ", unicodedata.normalize("NFC", s).strip())

def norm_translation(s):
    return _ws.sub(" ", unicodedata.normalize("NFC", s).strip())

def main():
    files = sorted(IN_DIR.glob("*.sst"))
    all_rows, file_stats, failures = [], [], []
    for path in files:
        try:
            parsed = parse_sst(path)
            for r in parsed["rows"]:
                r = dict(r)
                r["source_file"] = path.name
                r["sst_version"] = parsed["version"]
                r["source_norm"] = norm_source(r["source"])
                r["translation_norm"] = norm_translation(r["translation"])
                all_rows.append(r)
            file_stats.append((path.name, parsed["version"], len(parsed["rows"]),
                               len(parsed["masters"]), len(parsed["collab_labels"]),
                               parsed["record_start"], path.stat().st_size))
        except Exception as e:
            failures.append((path.name, str(e)))
    fields = ["source_file","sst_version","list_index","str_id","formid","rname","fname",
              "index","index_max","record_hash","colab_id","status_bits",
              "source","translation","source_norm","translation_norm"]
    with (OUT_DIR/"SST_ALL_ROWS.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(all_rows)

    by_source = defaultdict(Counter)
    occ = Counter()
    for r in all_rows:
        if r["source_norm"] and r["translation_norm"]:
            by_source[r["source_norm"]][r["translation_norm"]] += 1
            occ[(r["source_norm"], r["translation_norm"])] += 1

    unique_rows = []
    conflict_rows = []
    for src, trans_counts in by_source.items():
        ranked = sorted(trans_counts.items(), key=lambda x: (-x[1], x[0]))
        unique_rows.append({
            "source_english": src, "translation_count": len(ranked),
            "total_occurrences": sum(trans_counts.values()),
            "preferred_by_frequency": ranked[0][0],
            "preferred_count": ranked[0][1],
            "translations_json": json.dumps(ranked, ensure_ascii=False)
        })
        if len(ranked) > 1:
            conflict_rows.append(unique_rows[-1])

    for name, rows in [("SST_NORMALIZED_UNIQUE.csv", unique_rows),
                       ("SST_CONFLICTS.csv", conflict_rows)]:
        with (OUT_DIR/name).open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else
                               ["source_english","translation_count","total_occurrences",
                                "preferred_by_frequency","preferred_count","translations_json"])
            w.writeheader(); w.writerows(rows)
    report = {
        "sst_files": len(files),
        "parsed_files": len(file_stats),
        "failed_files": failures,
        "total_rows": len(all_rows),
        "unique_sources": len(by_source),
        "conflict_sources": len(conflict_rows),
        "exact_unique_pairs": len(occ),
        "versions": dict(Counter(v for _,v,*_ in file_stats)),
        "file_stats": [
            {"file":a,"version":b,"rows":c,"masters":m,"collab_labels":cl,
             "record_start":rs,"bytes":sz}
            for a,b,c,m,cl,rs,sz in file_stats
        ],
    }
    (OUT_DIR/"SST_PARSE_REPORT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k != "file_stats"},
                     ensure_ascii=True, indent=2))
    if failures:
        sys.exit(2)

if __name__ == "__main__":
    main()
