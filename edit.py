#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
edit.py — add the missing `import re` to build.py.

The error
---------
  NameError: name 're' is not defined
  at build.py line 3755 in _render_sidebar

The Firebase/Calendar override uses re.search to splice the Calendar tab
into the sidebar, but build.py never imports `re`. This script inserts
`import re` at module level so the override runs cleanly.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD_PY = ROOT / "build.py"

OVERRIDE_MARKER = "# --- edit.py: Firebase v10 + Calendar + Pricing ---"
IMPORT_LINE = "import re\n"


def patch_build_py() -> None:
    src = BUILD_PY.read_text(encoding="utf-8")

    # Already imported somewhere?
    for line in src.splitlines():
        if line.strip() == "import re":
            print("  [skip] `import re` already present")
            return

    if OVERRIDE_MARKER not in src:
        # No override block; put it at the top.
        BUILD_PY.write_text(IMPORT_LINE + src, encoding="utf-8")
        print("  [ok]   added `import re` at top of build.py")
        return

    # Insert immediately before the override marker so it's a module-level
    # import that runs before the override block.
    src = src.replace(OVERRIDE_MARKER, IMPORT_LINE + "\n" + OVERRIDE_MARKER, 1)
    BUILD_PY.write_text(src, encoding="utf-8")
    print("  [ok]   added `import re` before the override block")


def main() -> int:
    if not BUILD_PY.exists():
        print(f"error: could not find {BUILD_PY}")
        return 1

    print("Patching build.py …\n")
    patch_build_py()

    print("\nRunning build.py …\n")
    return subprocess.run([sys.executable, "build.py"], cwd=ROOT).returncode


if __name__ == "__main__":
    raise SystemExit(main())