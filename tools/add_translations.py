#!/usr/bin/env python3
"""Translate the first N batches (highest-frequency Japanese) into English.

Writes work/translated.json so apply_translations.py can merge + build.
Byte budgets are enforced; anything too long is reported and skipped.
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C

BATCH = 120

# ---- English translations for the highest-frequency lines ----------------
# (id -> english).  Ids come from work/batches/batch_0000.json .. 000N.
T = {
    0: "Yes! Perfect, that's it!",
    1: "Hmm... no good. A real shame.",
    2: "Hmm! Maybe a little different.",
    3: "Huh? Not at all like it.",
    4: "Alright, let's give it a demonstration.",
    5: "Please keep it calm and composed.",
    6: "Play it with real depth and maturity.",
    7: "Play it hot and intense.",
    8: "Warm, with real feeling in it.",
    9: "Bright and lively, please.",
    10: "Flat and even, easy to hear.",
    11: "Mind your intonation and make it unique!",
}


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    order = json.loads((C.WORK / "order.json")
                       .read_bytes().decode("utf-8", "surrogatepass"))
    src = {}
    for bi in range(n):
        p = C.WORK / "batches" / f"batch_{bi:04d}.json"
        if not p.exists():
            break
        src.update(json.loads(p.read_bytes().decode("utf-8", "surrogatepass")))
    # auto-fill everything we have a translation for
    out = {}
    over = []
    for k, v in sorted(src.items(), key=lambda kv: int(kv[0])):
        i = int(k)
        if i in T:
            e = T[i]
            if len(e.encode()) > v["b"]:
                over.append((i, v["j"] if "j" in v else v["jp"], v["b"], e))
                continue
            out[k] = e
    (C.WORK / "translated.json").write_bytes(
        json.dumps(out, ensure_ascii=False, indent=0).encode("utf-8"))
    print(f"translated {len(out)} of {len(src)} strings in {n} batch(es)")
    for i, jp, b, e in over:
        print(f"  OVER BUDGET id={i} b={b} en={len(e.encode())} {jp[:30]!r} -> {e!r}")


if __name__ == "__main__":
    main()
