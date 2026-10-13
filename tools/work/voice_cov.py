#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the definitive VA<->scenario coverage matrix from SoundData.cpk voice paths.

Voice path grammar: DATA/sound/Plip/vicNNN/DMMM_LLL_NNN.plip
  vicNNN = voice-actor id, DMMM = scenario/script id (matches DMMM_serif.info),
  LLL = line index.
For each vic dir: distinct D-set (scenarios spoken in) + line counts.
Also list vaIcon ctva ids for the icon<->vic binding, and any missing/gapped ids.
"""
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import cvpatch as C
from cricodecs import cpk

SOUND = r"D:\Video_Game\Emulator\RPCS3\games\CV Casting Voice [BLJS10259]\PS3_GAME\USRDIR\DATA\SoundData.cpk"
RE = re.compile(r"vic(\d+)/D(\d+)_(\d+)_(\d+)\.(plip|acb|awb)")


def main():
    a = cpk.load(SOUND)
    paths = [f.full_path for f in a.files]

    cov = defaultdict(set)      # vic -> {D...}
    lines = defaultdict(int)    # vic -> plip count
    id_re = defaultdict(set)    # vic -> {embedded vic id}
    plip_by_d = defaultdict(set)  # D -> {vic}
    for p in paths:
        m = RE.search(p)
        if not m:
            continue
        vic, scen, line, vid, ext = (int(m.group(1)), int(m.group(2)),
                                     int(m.group(3)), int(m.group(4)), m.group(5))
        cov[vic].add(scen)
        id_re[vic].add(vid)
        plip_by_d[scen].add(vic)
        if ext == "plip":
            lines[vic] += 1

    vics = sorted(cov)
    all_scen = sorted({d for s in cov.values() for d in s})
    print("vic dirs with voice: %d" % len(vics))
    print("vic id range: %d..%d" % (vics[0], vics[-1]))
    gaps = [v for v in range(vics[0], vics[-1] + 1) if v not in cov]
    print("gapped ids: %s" % gaps)
    print("distinct scenarios (D) covered: %d  range %d..%d"
          % (len(all_scen), all_scen[0], all_scen[-1]))
    print("scenarios with NO voice: %s"
          % [d for d in range(all_scen[0], all_scen[-1] + 1) if d not in plip_by_d])
    # embedded id consistency (path vicNNN vs trailing _NNN)
    bad = {v: ids for v, ids in id_re.items() if ids != {v}}
    print("path-vs-embedded id mismatches: %s" % (bad if bad else "none"))

    lines_out = []
    lines_out.append("vic_id  n_scen  n_lines  scenarios(D)")
    for v in vics:
        lines_out.append("%5d  %6d  %7d  %s" %
                         (v, len(cov[v]), lines[v],
                          " ".join("%03d" % d for d in sorted(cov[v]))))
    lines_out.append("")
    lines_out.append("== per-scenario VA count (D -> #vic) ==")
    for d in sorted(plip_by_d):
        lines_out.append("  D%03d: %2d vas  %s" %
                         (d, len(plip_by_d[d]), " ".join(str(v) for v in sorted(plip_by_d[d]))))

    # ctva icons (GameData)
    g = cpk.load(str(C.ORIG))
    ct = sorted(int(m.group(1)) for f in g.files
                for m in [re.match(r"DATA/vaIcon/ctva(\d+)\.pix$", f.full_path)] if m)
    lines_out.append("")
    lines_out.append("ctva icon ids (%d): %s" % (len(ct), ct))

    Path("tools/work/_voice_cov.txt").write_text("\n".join(lines_out), encoding="utf-8")
    print("wrote tools/work/_voice_cov.txt")


if __name__ == "__main__":
    main()
