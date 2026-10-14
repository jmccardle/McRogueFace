"""Gate for the shipped template programs (docs/templates/*/game.py), #380.

Users copy these as the basis for their own game, so each is run the way a user
gets it: copied to a fresh directory (sibling imports must resolve from there; --exec
does not put the script's directory on sys.path, so _template_prelude.py does),
booted headless, stepped, and driven with keypresses (_template_harness.py).
Templates are discovered by globbing docs/templates/*/game.py, so a new template
is gated without editing this file.

Non-vacuous: each template is ALSO run as a deliberately broken copy (a call to a
nonexistent mcrfpy attribute appended to game.py), which must be rejected. If
the harness ever stops noticing exceptions, that half fails.

Run: ./mcrogueface --headless --exec ../tests/integration/template_programs_test.py
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATES = ROOT / "docs" / "templates"
HARNESS = Path(__file__).resolve().parent / "_template_harness.py"
PRELUDE = Path(__file__).resolve().parent / "_template_prelude.py"
BINARY = Path(os.environ.get("MCRF_BUILD_DIR", ROOT / "build")) / "mcrogueface"
TIMEOUT = 60


def run(game_py):
    r = subprocess.run(
        [str(BINARY), "--headless", "--exec", str(PRELUDE), "--exec", str(game_py),
         "--exec", str(HARNESS)],
        capture_output=True, text=True, timeout=TIMEOUT,
        cwd=str(BINARY.parent),  # templates load assets/... relative to the game dir
        env={**os.environ, "MCRF_TEMPLATE_DIR": str(game_py.parent)})
    out = r.stdout + r.stderr
    ok = (r.returncode == 0 and "TEMPLATE_OK" in out
          and "Traceback (most recent call last)" not in out)
    return ok, out


names = sorted(p.parent.name for p in TEMPLATES.glob("*/game.py"))
if not names:
    print("FAIL: no templates found under", TEMPLATES)
    sys.exit(1)
if not BINARY.exists():
    print("FAIL: engine binary not found:", BINARY)
    sys.exit(1)

failures = []
with tempfile.TemporaryDirectory() as tmp:
    for name in names:
        good = Path(tmp) / "good" / name
        shutil.copytree(TEMPLATES / name, good, ignore=shutil.ignore_patterns("__pycache__"))
        ok, out = run(good / "game.py")
        print(f"{'ok  ' if ok else 'FAIL'} {name}")
        if not ok:
            failures.append(name)
            print(out[-3000:])

        bad = Path(tmp) / "bad" / name
        shutil.copytree(good, bad)
        with open(bad / "game.py", "a") as f:
            f.write("\nmcrfpy.this_does_not_exist()\n")
        ok, _ = run(bad / "game.py")
        if ok:
            failures.append(f"{name} (broken copy was NOT rejected: gate is vacuous)")
            print(f"FAIL {name}: broken copy accepted")

if failures:
    print("FAIL:", failures)
    sys.exit(1)
print(f"PASS: {len(names)} templates: {', '.join(names)}")
sys.exit(0)
