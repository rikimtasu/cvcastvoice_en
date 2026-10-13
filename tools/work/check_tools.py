import importlib.util as u
for m in ("capstone", "pyelftools", "lief", "angr", "r2pipe"):
    print("%-12s %s" % (m, "OK" if u.find_spec(m) else "MISSING"))
