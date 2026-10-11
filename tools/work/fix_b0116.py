#!/usr/bin/env python3
"""Repair gen_tr_b0116.py: rebuild the T list from tr source order.

Reads the (possibly mangled) generator, extracts every (id, english) tuple via
regex on the literal source, then rewrites the file with a clean, complete
T list for 13920-14039 so nothing is silently dropped.
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
WORK = Path(__file__).resolve().parent
GEN = WORK / "gen_tr_b0116.py"

text = GEN.read_text(encoding="utf-8")
pat = re.compile(r'^\s*\("(\d+)",\s*"((?:[^"\\]|\\.)*)"\),\s*$', re.M)
found = {int(i): s for i, s in pat.findall(text)}
expected = list(range(13920, 14040))
missing = [i for i in expected if i not in found]
print("parsed:", len(found), "missing:", missing)

batch = json.loads((WORK / "batches" / "batch_0116.json")
                   .read_bytes().decode("utf-8", "surrogatepass"))

lines = [
    '#!/usr/bin/env python3',
    '"""Generate tools/work/tr_b0116.json from hand translations + verify budgets.',
    '',
    'Batch 116: Aiba Ken / Hirasawa Ami / Saiguji Mirei / Saotome Toru scenes.',
    '"""',
    'import json',
    'import sys',
    'from pathlib import Path',
    '',
    'sys.stdout.reconfigure(encoding="utf-8", errors="replace")',
    'WORK = Path(__file__).resolve().parent',
    '',
    'T = [',
]
for i in expected:
    if i in found:
        lines.append(f'    ("{i}", "{found[i]}"),')
lines += [
    ']',
    '',
    '',
    'def main():',
    '    batch = json.loads((WORK / "batches" / "batch_0116.json")',
    '                       .read_bytes().decode("utf-8", "surrogatepass"))',
    '    ids = [k for k, _ in T]',
    '    assert len(ids) == len(set(ids)), "duplicate ids"',
    '    missing = set(batch) - set(ids)',
    '    extra = set(ids) - set(batch)',
    '    if missing:',
    '        print("MISSING ids:", sorted(int(x) for x in missing))',
    '    if extra:',
    '        print("EXTRA ids:", sorted(int(x) for x in extra))',
    '',
    '    over = []',
    '    for k, en in T:',
    '        b = batch[k]["b"]',
    '        n = len(en.encode("utf-8"))',
    '        if n > b:',
    '            over.append((k, b, n, en))',
    '    if over:',
    '        print("OVER BUDGET:")',
    '        for k, b, n, en in over:',
    '            print(f"  {k}: {n} > {b}  {en!r}")',
    '        sys.exit(1)',
    '',
    '    out = {k: en for k, en in T}',
    '    path = WORK / "tr_b0116.json"',
    '    path.write_bytes(json.dumps(out, ensure_ascii=False,',
    '                               separators=(",", ":"))',
    '                     .encode("utf-8", "surrogatepass"))',
    '    mx = max(len(en.encode("utf-8")) for _, en in T)',
    '    print(f"wrote {path}  entries={len(T)}  max_used={mx}")',
    '',
    '',
    'if __name__ == "__main__":',
    '    main()',
    '',
]
GEN.write_text("\n".join(lines), encoding="utf-8")
print("rewrote", GEN, "with", len(found), "entries")
if missing:
    sys.exit(1)
