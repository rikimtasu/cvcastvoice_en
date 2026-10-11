#!/usr/bin/env python3
"""Print exact codepoints of the Tono Ken string in segment 5727."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cvpatch as C


def main():
    order = json.loads((C.WORK / "order.json")
                       .read_bytes().decode("utf-8-sig", "surrogatepass"))
    jp = order["5727"]["jp"]
    i = jp.find("遠野")
    frag = jp[i:i + 12]
    print("fragment:", " ".join(f"U+{ord(c):04X}" for c in frag))
    import unicodedata
    for c in frag:
        try:
            print(f"  U+{ord(c):04X} {unicodedata.name(c)}")
        except ValueError:
            print(f"  U+{ord(c):04X} ?")


if __name__ == "__main__":
    main()
