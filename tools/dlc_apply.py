#!/usr/bin/env python3
"""DLC patch pipeline: merge DLC translations, patch each inner CPK with the
surgical patcher, re-encrypt to EDAT, and prove the round-trip.

  dlc_apply.py --audit              # budgets + review scan on tr_dlc files
  dlc_apply.py --build              # patch + verify + re-encrypt + round-trip
  dlc_apply.py --install            # backup originals, deploy patched EDATs

Base-game translations (tr_*.json) also cover 167 DLC segments; those merge
automatically. vinfo \\n line breaks are preserved (never spaced).
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C

ROOT = C.ROOT
DLC = ROOT / "dlc"
DEC = DLC / "dec"
PATCHED = DLC / "patched"


def _rpcs3_root() -> Path | None:
    v = os.environ.get("CVC_RPCS3")
    if v:
        return Path(v).expanduser()
    # Legacy local default (kept for existing runs; set CVC_RPCS3 to override).
    return Path(r"D:\Video_Game\Emulator\RPCS3")


RPCS3 = _rpcs3_root()
DLCDATA = RPCS3 / "dev_hdd0" / "game" / "NPJB00558" / "USRDIR" / "DATA"
EXDATA = RPCS3 / "dev_hdd0" / "home" / "00000001" / "exdata"
NP = Path(__file__).resolve().parent / "npdata_src" / "make_npdata.exe"

PACKS = [
    ("DLC_S276", "JP0700-NPJB00558_00-DRMCONTENTCVS276"),
    ("DLC_S287", "JP0700-NPJB00558_00-DRMCONTENTCVS287"),
    ("DLC_S295", "JP0700-NPJB00558_00-DRMCONTENTCVS295"),
    ("DLC_S297", "JP0700-NPJB00558_00-DRMCONTENTCVS297"),
    ("DLC_S305", "JP0700-NPJB00558_00-DRMCONTENTCVS305"),
    ("DLC_D009", "JP0700-NPJB00558_00-DRMCONTENTCVD009"),
    ("DLC_D012", "JP0700-NPJB00558_00-DRMCONTENTCVD012"),
    ("DLC_D015", "JP0700-NPJB00558_00-DRMCONTENTCVD015"),
]
HONOR = re.compile(r"\b([A-Za-z]+)-(san|chan|sama|kun|dono|chin|sensei)\b")
NONASCII = re.compile(r"[^\x00-\x7F]")


def load_json(p):
    return json.loads(p.read_bytes().decode("utf-8-sig", "surrogatepass"))


def clean_vinfo(en: str) -> str:
    en = en.replace("\u3000", " ")
    en = en.replace("@n", " ")
    en = en.replace("\r", " ")
    return en  # \n PRESERVED (rule 15)


def clean_std(en: str) -> str:
    en = en.replace("\u3000", " ")
    en = en.replace("@n", " ")
    en = en.replace("\n", " ").replace("\r", " ")
    return en


def load_translations():
    """en_by_jp from DLC batches + base corpus (for covered segments)."""
    en_by_jp = {}
    for p in sorted((C.WORK / "dlc_batches").glob("dlc_batch_*.json")):
        batch = load_json(p)
        tid = "tr_dlc" + p.stem.split("_")[-1] + ".json"
        tr = load_json(C.WORK / tid)
        for k, v in tr.items():
            if k in batch:
                en_by_jp[batch[k]["jp"]] = v
    order = load_json(C.WORK / "order.json")
    for p in sorted(C.WORK.glob("tr_*.json")):
        if p.name.startswith("tr_dlc"):
            continue
        tr = load_json(p)
        for k, v in tr.items():
            if k in order:
                en_by_jp[order[k]["jp"]] = v
    return en_by_jp


def cmd_audit(args):
    en_by_jp = load_translations()
    seg = load_json(C.WORK / "dlc_segments.json")
    n_hit = n_miss = n_over = 0
    probs = []
    for key, rec in seg.items():
        clean = clean_vinfo if rec["kind"] == "vinfo" else clean_std
        for s in rec["seg"]:
            e = en_by_jp.get(s["jp"])
            if e is None:
                n_miss += 1
                continue
            e = clean(e)
            n_hit += 1
            if len(e.encode()) > s["b"]:
                n_over += 1
                probs.append(f"OVER {key} [{s['s']},{s['e']}) "
                             f"{len(e.encode())}>{s['b']} {e[:50]!r}")
                continue
            m = NONASCII.search(e)
            if m:
                probs.append(f"NONASCII {key} {m.group()!r} {e[:50]!r}")
            if "@n" in e:
                probs.append(f"ATN {key} {e[:50]!r}")
            if HONOR.search(e):
                probs.append(f"HONOR {key} {e[:60]!r}")
    print(f"dlc segments covered: {n_hit}  still JP: {n_miss}  "
          f"over budget: {n_over}")
    for p_ in probs[:20]:
        print("  " + p_)
    (C.WORK / "dlc_audit.txt").write_text(
        f"hit={n_hit} miss={n_miss} over={n_over}\n"
        + "\n".join(probs[:50]), encoding="utf-8")
    return 0


def build_overlay(en_by_jp):
    seg = load_json(C.WORK / "dlc_segments.json")
    per_cpk = {}
    n_hit = n_miss = n_over = 0
    for key, rec in seg.items():
        clean = clean_vinfo if rec["kind"] == "vinfo" else clean_std
        runs = []
        for s in rec["seg"]:
            e = en_by_jp.get(s["jp"])
            if e is None:
                n_miss += 1
                continue
            e = clean(e)
            if len(e.encode()) > s["b"]:
                n_over += 1
                continue
            n_hit += 1
            runs.append({"span": [s["s"], s["e"]], "text": e})
        if runs:
            per_cpk.setdefault(rec["cpk"], {})[rec["path"]] = {
                "kind": rec["kind"], "runs": runs}
    print(f"overlay: hit={n_hit} miss={n_miss} over={n_over}")
    return per_cpk


def run(exe_args):
    r = subprocess.run(exe_args, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    print(r.stdout[-1500:])
    if r.stderr:
        print(r.stderr[-500:])
    return r.returncode


def cmd_build(args):
    PATCHED.mkdir(parents=True, exist_ok=True)
    en_by_jp = load_translations()
    per_cpk = build_overlay(en_by_jp)
    py = sys.executable
    cvp = str(Path(__file__).with_name("cvpatch.py"))
    for name, cid in PACKS:
        short = name.replace("DLC_", "DLC_")
        edat = f"{name}_cpk.EDAT"
        rap = EXDATA / f"{cid}.rap"
        src = DEC / f"{name}.cpk"
        ov_path = C.WORK / f"overlay_dlc_{name}.json"
        out_cpk = PATCHED / f"{name}.cpk"
        out_edat = PATCHED / edat
        ov = {"files": per_cpk.get(name + ".cpk", {})}
        ov_path.write_bytes(json.dumps(ov, ensure_ascii=False)
                            .encode("utf-8"))
        print(f"===== {name}: {len(ov['files'])} files =====")
        rc = run([py, cvp, "build", "--orig", str(src),
                  "--overlay", str(ov_path), "--out", str(out_cpk)])
        if rc:
            return rc
        rc = run([py, cvp, "verify", "--orig", str(src),
                  "--file", str(out_cpk), "--overlay", str(ov_path),
                  "--deep"])
        if rc:
            return rc
        # Preserve Sony's NPD digest/dev_hash: dev_hash feeds block-key
        # derivation and license-2 never recomputes it, so copying keeps
        # every downstream key identical (proven by RPCS3 source).
        # Source of truth is the BACKUP (install dir may hold test files).
        orig_edat = (DLC / "backup_edat" / f"{name}_cpk.EDAT").read_bytes()
        digest_hex = orig_edat[0x40:0x50].hex()
        dev_hex = orig_edat[0x60:0x70].hex()
        rc = run([str(NP), "-e", str(out_cpk), str(out_edat),
                  "4", "2", "0", "0", cid, "2", str(rap),
                  digest_hex, dev_hex])
        if rc:
            return rc
        # round-trip: decrypt output, compare to patched plaintext
        rt = PATCHED / f"{name}.rt.cpk"
        rc = run([str(NP), "-d", str(out_edat), str(rt), "2", str(rap)])
        if rc:
            return rc
        h1 = __import__("hashlib").sha256(
            out_cpk.read_bytes()).hexdigest()[:16]
        h2 = __import__("hashlib").sha256(rt.read_bytes()).hexdigest()[:16]
        print(f"round-trip {name}: {h1} vs {h2} "
              f"{'IDENTICAL' if h1 == h2 else 'MISMATCH'}")
        if h1 != h2:
            return 1
        rt.unlink()
    print("ALL DLC PACKS BUILT + ROUND-TRIP VERIFIED")
    return 0


def cmd_install(args):
    bdir = DLC / "backup_edat"
    bdir.mkdir(parents=True, exist_ok=True)
    for name, cid in PACKS:
        edat = f"{name}_cpk.EDAT"
        src = PATCHED / edat
        dst = DLCDATA / edat
        if not src.exists():
            print(f"SKIP {edat}: no patched output (run --build first)")
            continue
        bak = bdir / edat
        if not bak.exists():
            bak.write_bytes(dst.read_bytes())
            print(f"backup {edat} ({bak.stat().st_size})")
        dst.write_bytes(src.read_bytes())
        print(f"installed {edat} ({dst.stat().st_size})")
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("audit")
    sub.add_parser("build")
    sub.add_parser("install")
    args = ap.parse_args()
    return {"audit": cmd_audit, "build": cmd_build,
            "install": cmd_install}[args.cmd](args)


if __name__ == "__main__":
    main()
