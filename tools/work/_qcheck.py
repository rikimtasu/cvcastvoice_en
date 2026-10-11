import json, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
b = sys.argv[1]
d = json.load(open(rf"D:\Documents\CVCastingVoice\tools\work\batches\batch_{int(b):04d}.json", encoding="utf-8"))
en = {}
for p in open(rf"D:\Documents\CVCastingVoice\tools\work\tr\b{int(b):04d}.txt", encoding="utf-8").read().splitlines():
    if not p.strip():
        continue
    i, e = p.split("|", 1)
    en[i] = e
bad = 0
for k in sorted(d, key=int):
    j = d[k]["jp"]
    e = en[k]
    oq = j.startswith("\u300c")
    cq = j.endswith("\u300d")
    eo = e.startswith('"')
    ec = e.endswith('"')
    if oq != eo or cq != ec:
        bad += 1
        print(k, "oq", oq, eo, "cq", cq, ec, repr(j[:14]), repr(e[:24]))
print("mismatch:", bad, "of", len(d))
