#!/usr/bin/env python3
"""
cvpatch - surgical English translation patcher for "CV Casting Voice" [BLJS10259].

WHY THIS IS SURGICAL (and not a cricodecs rebuild)
--------------------------------------------------
* Calling `cricodecs.cpk.save()` re-lays-out the archive (re-sorts the TOC by
  name, shrinks the ETOC).  That made the game HANG, twice, even with
  byte-identical content.  We never call save().
* We copy the pristine original and change only:
    - TOC  col4 (row k)  : stored file size  (raw storage of the new payload)
    - TOC  col5 (row k)  : extract size      (unchanged, same length)
    - TOC  col0 (row k+1): `file_offset[k] = col0[k+1] + 2048`  (verified 8399/8399)
    - INFO EtocOffset @0x107 / DataSize @0xEF (u64be, big endian)
  Every other byte of the original archive is copied verbatim.
* Modified files are re-stored UNCOMPRESSED (150 files in the original are
  already stored raw, so raw storage is supported by the runtime) inside a tail
  block inserted at the current ETOC offset.  This keeps the invariant
  `filesize == ContentOffset + DataSize + EtocSize`.
* Run text is replaced 1:1 with the *same* UTF-8 byte length, so no internal
  .srt/.info table field (which caches offsets/lengths) ever changes.

USAGE
  cvpatch.py scan                            -> work/master.json + report
  cvpatch.py build --overlay O.json --out P   (dry-run with --dry)
  cvpatch.py verify --file P [--expect E.json]
  cvpatch.py restore

PATHS (portable: repo works from any checkout location)
  All game paths default to repo-relative locations and can be overridden
  with environment variables (or --orig / --install flags on each command):
    CVC_ORIG     pristine GameData.cpk
                 (default: <repo>/_backup/GameData.original.cpk)
    CVC_SOUND    pristine SoundData.cpk
                 (default: <repo>/_backup/SoundData.cpk)
    CVC_INSTALL  deployed GameData.cpk inside the game folder
                 (no default; required only by `restore`)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent

WORK = TOOLS / "work"
WORK.mkdir(parents=True, exist_ok=True)


def _env_path(name: str, default: Path | None) -> Path | None:
    val = os.environ.get(name)
    if val:
        return Path(val).expanduser()
    return default


ORIG = _env_path("CVC_ORIG", ROOT / "_backup" / "GameData.original.cpk")
SOUND = _env_path("CVC_SOUND", ROOT / "_backup" / "SoundData.cpk")
INSTALL = _env_path("CVC_INSTALL", None)

# ---- CPK layout constants (all independently verified) ----
ROW0 = 0x84F            # first TOC row
STRIDE = 28             # 7 x u32be
NROWS = 8400
COL_FILE, COL_EXTR, COL_ZERO = 4, 5, 6          # constant columns
COL_PREV = 0                                     # file_offset[i-1] - 2048
ALIGN = 2048

INFO_CONTENT_OFF = 0xE7      # u64be
INFO_DATA_SIZE = 0xEF        # u64be
INFO_ETOC_OFF = 0x107        # u64be
INFO_ETOC_SIZE = 0x10F       # u64be

ATN = b"@n"
CRLF = b"\x0d\x0a"


def log(msg=""):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(msg)


# --------------------------------------------------------------------------
# UTF-8 aware helpers
# --------------------------------------------------------------------------
def _utf8_len(b: int):
    if b < 0x80:
        return 1
    if 0xC2 <= b <= 0xDF:
        return 2
    if 0xE0 <= b <= 0xEF:
        return 3
    if 0xF0 <= b <= 0xF4:
        return 4
    return 0


def _is_plain(cp: int) -> bool:
    """Chars that make up on-screen text (ASCII, kana, kanji, CJK punct)."""
    return (0x20 <= cp <= 0x7E
            or 0x2010 <= cp <= 0x203B     # …… – — ‘ “ ’ ” etc
            or 0x3000 <= cp <= 0x30FF
            or 0x4E00 <= cp <= 0x9FFF
            or 0xFF01 <= cp <= 0xFF60
            or cp in (0x00B7,))


def scan_spans(data: bytes, want_japanese: bool = True):
    """Maximal byte spans of on-screen text, keeping @n / ⊥ / ⊿ separators.

    Walks the buffer as UTF-8, never splitting a multibyte character, so an
    `@n` sequence embedded inside a Japanese character is never mistaken for a
    line break.
    """
    spans = []
    i = 0
    n = len(data)
    while i < n:
        b = data[i]
        if not (b == 0x0A or 0x20 <= b <= 0x7E or 0xC2 <= b <= 0xF4):
            i += 1
            continue
        j = i
        good = 0
        jp = 0
        while j < n:
            b = data[j]
            if data[j:j + 2] == ATN:
                j += 2
                good += 1
                continue
            if b == 0x0A:
                j += 1
                good += 1
                continue
            ln = _utf8_len(b)
            if ln == 0 or j + ln > n:
                break
            try:
                cp = ord(data[j:j + ln].decode("utf-8"))
            except Exception:
                break
            if not _is_plain(cp):
                break
            if cp >= 0x2E80:
                jp += 1
            j += ln
            good += 1
        if good >= 4 and (jp > 0 if want_japanese else good >= 4):
            spans.append((i, j))
            i = j
        else:
            i += 1
    return spans


def split_lines(data: bytes, s: int, e: int):
    """Split text span [s,e) into line spans on `@n` at character boundaries."""
    out = []
    cur = s
    i = s
    while i < e:
        if data[i:i + 2] == ATN:
            if i > cur:
                out.append((cur, i))
            i += 2
            cur = i
            continue
        ln = _utf8_len(data[i])
        if ln == 0 or i + ln > e:
            i += 1
            continue
        i += ln
    if e > cur:
        out.append((cur, e))
    return out


def parse_dialogue(data: bytes):
    """All dialogue line spans in an FSRT/.srt file (both layouts)."""
    seen = set()
    lines = []
    for s, e in scan_spans(data):
        for (ls, le) in split_lines(data, s, e):
            if (ls, le) not in seen:
                seen.add((ls, le))
                lines.append((ls, le))
    return lines


def parse_info_segments(data: bytes):
    """The trailing CRLF-separated string block of a .info file."""
    segs = []
    start = 0
    while True:
        i = data.find(CRLF, start)
        if i < 0:
            break
        segs.append((start, i))
        start = i + 2
    return segs


def is_srt(path: str) -> bool:
    return path.lower().endswith(".srt")


def row_cols(buf: bytes, i: int):
    o = ROW0 + i * STRIDE
    return [int.from_bytes(buf[o + 4 * k:o + 4 * k + 4], "big") for k in range(7)]


def cmd_scan(args):
    from cricodecs import cpk
    a = cpk.load(str(ORIG))
    master = {}
    n_files = n_runs = n_bytes = 0
    n_info_files = n_info_segs = n_info_bytes = 0
    for f in a.files:
        lp = f.full_path.lower()
        if lp.endswith(".srt"):
            data = a.file_bytes(f.toc_index)
            if data[:4] != b"FSRT":
                continue
            spans = parse_dialogue(data)
            n_files += 1
            n_runs += len(spans)
            n_bytes += sum(e - s for s, e in spans)
            master[f.full_path] = {
                "toc_index": f.toc_index, "extract_size": f.extract_size,
                "file_size": f.file_size, "kind": "srt",
                "runs": [[s, e] for s, e in spans]}
        elif lp.endswith(".info"):
            data = a.file_bytes(f.toc_index)
            spans = parse_info_segments(data)
            if not spans:
                continue
            n_info_files += 1
            n_info_segs += len(spans)
            n_info_bytes += sum(e - s for s, e in spans)
            master[f.full_path] = {
                "toc_index": f.toc_index, "extract_size": f.extract_size,
                "file_size": f.file_size, "kind": "info",
                "runs": [[s, e] for s, e in spans]}
    (WORK / "master.json").write_text(
        json.dumps(master, ensure_ascii=False), encoding="utf-8")
    msg = [f".srt files          : {n_files}",
           f".srt runs           : {n_runs}",
           f".srt text bytes     : {n_bytes} ({n_bytes/1048576:.2f} MiB)",
           f"  avg run           : {n_bytes/max(1,n_runs):.1f} bytes (Japanese UTF-8)",
           f".info files         : {n_info_files}",
           f".info segments      : {n_info_segs}",
           f".info text bytes    : {n_info_bytes} ({n_info_bytes/1048576:.2f} MiB)",
           f"total translatable  : {n_runs + n_info_segs} segments",
           f"master.json         : {WORK / 'master.json'}"]
    (WORK / "scan.txt").write_text("\n".join(msg), encoding="utf-8")
    log("\n".join(msg))
    return 0


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------
def encode_run(text: str, budget: int, pad_char: str = " ") -> bytes:
    """Encode `text` into exactly `budget` bytes of UTF-8 (padded with spaces)."""
    raw = text.encode("utf-8", "surrogateescape")
    if len(raw) > budget:
        raise ValueError(f"text too long: {len(raw)} > {budget} ({text[:40]!r})")
    if len(raw) < budget:
        raw = raw + (pad_char * (budget - len(raw))).encode("ascii")
    return raw


def build_payload(orig_bytes: bytes, spans, ov, kind) -> bytes:
    """Return a new content buffer of the SAME total length."""
    buf = bytearray(orig_bytes)
    rep = {tuple(r["span"]): r for r in ov.get("runs", [])}
    for (s, e) in spans:
        key = (s, e)
        r = rep.get(key)
        if r is None:
            continue
        budget = e - s
        buf[s:e] = encode_run(r["text"], budget,
                              r.get("pad", " "))
    if len(buf) != len(orig_bytes):
        raise ValueError("payload length changed")
    return bytes(buf)


def cmd_build(args):
    from cricodecs import cpk

    a = cpk.load(str(ORIG))
    buf = bytearray(ORIG.read_bytes())
    bytoc = {f.full_path: f for f in a.files}

    overlay = json.loads(Path(args.overlay).read_text(encoding="utf-8"))
    root = overlay["files"] if "files" in overlay else overlay

    # ---- plan -------------------------------------------------------------
    # The overlay already carries the exact spans it wants to replace (they came
    # from parse_dialogue/parse_info_segments on these same original bytes), so
    # there is no need to re-walk every file in pure Python (~8s at scale).
    plan = []                       # (toc_index, path, payload)
    problems = []
    for path, ov in root.items():
        f = bytoc.get(path)
        if f is None:
            problems.append(f"unknown path: {path}")
            continue
        runs = ov.get("runs", [])
        spans = [tuple(r["span"]) for r in runs]
        if not spans:
            continue
        data = a.file_bytes(f.toc_index)
        bad = [s for s in spans if not (0 <= s[0] < s[1] <= len(data))]
        if bad:
            problems.append(f"{path}: {len(bad)} span(s) outside file")
            continue
        try:
            payload = build_payload(data, spans, ov, None)
        except ValueError as ex:
            problems.append(f"{path}: {ex}")
            continue
        if payload == data:
            continue
        plan.append([f.toc_index, path, payload])

    if problems:
        log("PROBLEMS:")
        for p_ in problems[:20]:
            log("  " + p_)
        if not args.force:
            return 2

    toc = {}
    for ti, path, payload in plan:
        toc.setdefault(ti, []).append((path, payload))

    # ---- layout -----------------------------------------------------------
    etoc = int.from_bytes(buf[INFO_ETOC_OFF:INFO_ETOC_OFF + 8], "big")
    etoc_size = int.from_bytes(buf[INFO_ETOC_SIZE:INFO_ETOC_SIZE + 8], "big")
    etoc_bytes = bytes(buf[etoc:etoc + etoc_size])
    cursor = etoc                                     # 2048-aligned already
    placements = []
    for ti, path, payload in plan:
        if ti == NROWS - 1:
            problems.append(f"cannot relocate last row {ti} ({path})")
            continue
        if cursor % ALIGN:
            cursor = (cursor + ALIGN - 1) & ~(ALIGN - 1)
        placements.append([ti, cursor, len(payload), path])
        cursor += len(payload)
    new_etoc = (cursor + ALIGN - 1) & ~(ALIGN - 1)
    new_size = new_etoc + etoc_size

    if problems:
        log("LAYOUT PROBLEMS:")
        for p_ in problems[:20]:
            log("  " + p_)
        if not args.force:
            return 2

    log(f"files to patch      : {len(placements)}")
    log(f"payload bytes       : {cursor - etoc} ({(cursor-etoc)/1048576:.1f} MiB)")
    log(f"original archive    : {len(buf)} ({len(buf)/1048576:.1f} MiB)")
    log(f"new archive         : {new_size} ({new_size/1048576:.1f} MiB)")
    log(f"ETOC moves          : {etoc:#x} -> {new_etoc:#x}")

    if args.dry:
        (WORK / "build_plan.json").write_text(json.dumps(
            {"placements": [[t, o, n, p] for t, o, n, p in placements],
             "old_etoc": etoc, "new_etoc": new_etoc, "new_size": new_size,
             "problems": problems}, indent=1), encoding="utf-8")
        log("dry-run: plan written, no file written")
        return 0

    # ---- apply: 1) patch TOC fields IN PLACE, 2) assemble file -------------
    # NOTE: patching a bytearray in place is O(field).  Building each patch as
    # `hdr[:o] + b + hdr[o+4:]` re-copies the whole ~300 MB header per field,
    # which measured 1491 s vs 2.9 s for 10,284 patches (503x).  Keep the
    # in-place form.
    out = bytearray(buf[:etoc])                   # header + data, verbatim
    for ti, off, n, path in placements:
        o4 = ROW0 + ti * STRIDE + 4 * COL_FILE     # stored size
        out[o4:o4 + 4] = n.to_bytes(4, "big")
        o5 = ROW0 + ti * STRIDE + 4 * COL_EXTR     # extract size
        out[o5:o5 + 4] = n.to_bytes(4, "big")
        on = ROW0 + (ti + 1) * STRIDE + 4 * COL_PREV   # offset - 2048
        out[on:on + 4] = (off - ALIGN).to_bytes(4, "big")

    # 2) assemble [patched header+data][new payloads][pad][relocated ETOC]
    for ti, off, n, path in placements:
        if len(out) < off:
            out.extend(b"\x00" * (off - len(out)))
        assert len(out) == off, (hex(len(out)), hex(off))
        out.extend(payload_of(toc, ti, path))
    if len(out) < new_etoc:
        out.extend(b"\x00" * (new_etoc - len(out)))
    assert len(out) == new_etoc, (hex(len(out)), hex(new_etoc))
    out.extend(etoc_bytes)
    assert len(out) == new_size, (len(out), new_size)

    # 3) INFO: DataSize + EtocOffset (ContentOffset / EtocSize / Files unchanged)
    content_off = int.from_bytes(buf[INFO_CONTENT_OFF:INFO_CONTENT_OFF + 8], "big")
    out[INFO_DATA_SIZE:INFO_DATA_SIZE + 8] = (new_etoc - content_off).to_bytes(8, "big")
    out[INFO_ETOC_OFF:INFO_ETOC_OFF + 8] = new_etoc.to_bytes(8, "big")

    dest = Path(args.out)
    dest.write_bytes(bytes(out))
    log(f"written             : {dest} ({dest.stat().st_size} bytes)")

    (WORK / "last_build.json").write_text(json.dumps(
        {"out": str(dest), "placements": [[t, o, n, p] for t, o, n, p in placements],
         "old_etoc": etoc, "new_etoc": new_etoc}, indent=1), encoding="utf-8")
    return 0


def payload_of(toc, ti, path):
    for p2, pl in toc[ti]:
        if p2 == path:
            return pl
    raise KeyError(path)


# --------------------------------------------------------------------------
# verify
# --------------------------------------------------------------------------
def cmd_verify(args):
    """Confirm the patched archive is the original with only the intended
    changes.

    Content is compared as RAW ARCHIVE REGIONS rather than by decompressing
    each file.  That is strictly stronger for our purpose (it proves the bytes
    were copied verbatim, not merely that they decompress to the same thing)
    and it measured 68 s -> ~1 s.  Use --deep to also decompress-compare.
    """
    from cricodecs import cpk
    target = Path(args.file)
    log(f"verifying {target} ({target.stat().st_size} bytes)")
    import time as _time
    T_START = _time.perf_counter()
    marks = []
    t0 = _time.perf_counter()
    a = cpk.load(str(target))
    b = cpk.load(str(ORIG))
    log(f"loaded: {len(a.files)} files (original {len(b.files)})")
    marks.append(("cpk.load x2", _time.perf_counter() - t0))
    assert len(a.files) == len(b.files)

    t0 = _time.perf_counter()
    na = target.read_bytes()
    nb = ORIG.read_bytes()
    marks.append(("read_bytes x2", _time.perf_counter() - t0))
    log(f"archive bytes read: {len(na)} / {len(nb)}")

    # NOTE: `.files` is a property that rebuilds the whole 8400-element list on
    # every access.  Indexing it inside the loop cost 56 s; hoisting it into a
    # local makes that phase ~0.1 s.  Always bind these once.
    fa, fb = a.files, b.files

    t0 = _time.perf_counter()
    bad = 0
    moved = same = 0
    diff = 0
    first_diffs = []
    for ti in range(len(fa)):
        f1, f0 = fa[ti], fb[ti]
        if f1.full_path != f0.full_path:
            bad += 1
            if len(first_diffs) < 10:
                first_diffs.append(f"  PATH MISMATCH {ti}: "
                                   f"{f1.full_path} vs {f0.full_path}")
        if f1.extract_size != f0.extract_size:
            bad += 1
            if len(first_diffs) < 10:
                first_diffs.append(f"  EXTRACTSIZE {ti} {f1.full_path}: "
                                   f"{f1.extract_size} vs {f0.extract_size}")
        if f1.file_offset == f0.file_offset:
            # ---- UNMOVED: must be byte-verbatim, stored identically ----
            same += 1
            if f1.file_size != f0.file_size:
                bad += 1
                if len(first_diffs) < 10:
                    first_diffs.append(f"  FILESIZE {ti} {f1.full_path}: "
                                       f"{f1.file_size} vs {f0.file_size}")
            elif na[f1.file_offset:f1.file_offset + f1.file_size] != \
                    nb[f0.file_offset:f0.file_offset + f0.file_size]:
                diff += 1
                if len(first_diffs) < 10:
                    first_diffs.append(f"  CONTENT DIFF {ti} {f1.full_path}")
        else:
            # ---- RELOCATED: stored raw (file_size == extract_size) ----
            moved += 1
            if not (f1.file_size == f1.extract_size == f0.extract_size):
                bad += 1
                if len(first_diffs) < 10:
                    first_diffs.append(
                        f"  RELOC SIZE {ti} {f1.full_path}: "
                        f"stored {f1.file_size} extract {f1.extract_size} "
                        f"orig-extract {f0.extract_size}")
                continue
            if not args.deep:
                continue
            # --deep: prove the only changed bytes are inside text spans
            orig = b.file_bytes(ti)                 # decompressed original
            new = na[f1.file_offset:f1.file_offset + f1.file_size]
            if len(orig) != len(new):
                bad += 1
                if len(first_diffs) < 10:
                    first_diffs.append(f"  RELOC LENGTH {ti} {f1.full_path}")
                continue
            spans = (parse_dialogue(orig)
                     if f0.full_path.lower().endswith(".srt")
                     else parse_info_segments(orig))
            p = 0
            ok = True
            for s, e in spans:
                if s > p and orig[p:s] != new[p:s]:
                    ok = False
                    break
                p = max(p, e)
            if ok and orig[p:] != new[p:]:
                ok = False
            if not ok:
                diff += 1
                if len(first_diffs) < 10:
                    first_diffs.append(
                        f"  NON-TEXT DIFF {ti} {f1.full_path}")
    marks.append(("compare loop", _time.perf_counter() - t0))
    for m in first_diffs:
        log(m)
    log(f"paths/size mismatches    : {bad}")
    log(f"files at original offsets: {same}")
    log(f"files relocated          : {moved}")
    log(f"content diffs outside text spans: {diff}")
    log(f"content_offset           : {a.content_offset} "
        f"(orig {b.content_offset})")
    log(f"file_count               : {len(a.files)}")

    # header diff vs expected
    ob = nb
    etoc_o = int.from_bytes(ob[INFO_ETOC_OFF:INFO_ETOC_OFF + 8], "big")
    etoc_n = int.from_bytes(na[INFO_ETOC_OFF:INFO_ETOC_OFF + 8], "big")
    log(f"EtocOffset {etoc_o:#x} -> {etoc_n:#x}   "
        f"DataSize {int.from_bytes(ob[INFO_DATA_SIZE:INFO_DATA_SIZE+8],'big'):#x} -> "
        f"{int.from_bytes(na[INFO_DATA_SIZE:INFO_DATA_SIZE+8],'big'):#x}")
    etoc_size = int.from_bytes(na[INFO_ETOC_SIZE:INFO_ETOC_SIZE + 8], "big")
    log(f"filesize {len(ob)} -> {len(na)} ; "
        f"EtocOffset+EtocSize == filesize? {etoc_n + etoc_size == len(na)}")
    total = _time.perf_counter() - T_START
    for nm, dt in marks:
        log(f"  {nm:22s} {dt:7.2f} s")
    log(f"elapsed {total:.1f} s")
    log("VERIFY OK" if (bad == 0 and diff == 0) else "VERIFY FAILED")
    return 0 if (bad == 0 and diff == 0) else 1


def resolve_orig(args) -> Path:
    """ORIG with a per-run --orig override (falls back to CVC_ORIG env / default)."""
    global ORIG
    if getattr(args, "orig", None):
        ORIG = Path(args.orig).expanduser()
    if ORIG is None or not ORIG.exists():
        sys.exit(
            f"pristine GameData.cpk not found at {ORIG}.\n"
            "Provide it with --orig PATH or the CVC_ORIG environment variable "
            "(default: <repo>/_backup/GameData.original.cpk).")
    return ORIG


def resolve_install(args) -> Path:
    """INSTALL with a per-run --install override (falls back to CVC_INSTALL env)."""
    global INSTALL
    if getattr(args, "install", None):
        INSTALL = Path(args.install).expanduser()
    if INSTALL is None:
        sys.exit(
            "no deployed GameData.cpk configured. Provide it with --install PATH "
            "or the CVC_INSTALL environment variable "
            "(e.g. <RPCS3 games>/CV Casting Voice [BLJS10259]/"
            "PS3_GAME/USRDIR/DATA/GameData.cpk).")
    return INSTALL


def cmd_restore(args):
    import shutil
    src = resolve_orig(args)
    dest = resolve_install(args)
    shutil.copyfile(src, dest)
    log(f"restored {dest} from {src} "
        f"({dest.stat().st_size} bytes)")
    return 0


def _add_path_flags(p):
    p.add_argument("--orig", default=None,
                   help="pristine GameData.cpk (overrides CVC_ORIG; "
                        "default: <repo>/_backup/GameData.original.cpk)")
    return p


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    _add_path_flags(sub.add_parser("scan"))
    bg = sub.add_parser("build")
    bg.add_argument("--overlay", required=True)
    bg.add_argument("--out", required=True)
    bg.add_argument("--dry", action="store_true")
    bg.add_argument("--force", action="store_true")
    _add_path_flags(bg)
    vg = sub.add_parser("verify")
    vg.add_argument("--file", required=True)
    vg.add_argument("--expect")
    vg.add_argument("--deep", action="store_true",
                    help="also decompress-compare every file (slow)")
    _add_path_flags(vg)
    rg = sub.add_parser("restore")
    _add_path_flags(rg)
    rg.add_argument("--install", default=None,
                    help="deployed GameData.cpk to overwrite (overrides CVC_INSTALL)")
    args = ap.parse_args()
    if args.cmd is not None:
        resolve_orig(args)   # honor --orig / CVC_ORIG before any command runs
    return {"scan": cmd_scan, "build": cmd_build,
            "verify": cmd_verify, "restore": cmd_restore}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
