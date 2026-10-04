#!/usr/bin/env python3
"""
fix_search.py - one small fix for the Number tab.

The server returns {"numbers": [...]} but the page expected a plain list,
so search results would never show. Run from the VP folder:

    python fix_search.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build.py"

OLD = "if (!r.ok) throw new Error(data.error || ('Search failed (' + r.status + ')'));"
NEW = OLD + "\n          data = data.numbers || [];"

src = BUILD.read_text(encoding="utf-8")
if "data = data.numbers || [];" in src:
    print("[skip] already fixed")
elif OLD not in src:
    print("error: couldn't find the search code in build.py")
    sys.exit(1)
else:
    BUILD.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("[ok] fixed number search")

subprocess.run([sys.executable, "build.py"], cwd=ROOT)
