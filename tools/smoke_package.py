#!/usr/bin/env python3
"""Smoke-test release packages the way a user gets them (#475).

Each archive is unpacked into a fresh directory outside the source tree and run from
there, so nothing resolves against the build tree:

  *-Linux.tar.gz     ./mcrogueface --headless
  *-Windows.zip      wine mcrogueface.exe --headless   (needs wine)
  *-WASM.zip         index.html at the zip root, then tests/wasm/run_wasm_tests.py in
                     headless Chromium (needs the .venv-wasmtest Playwright venv)

Desktop packages must report the expected mcrfpy.__version__, run Python 3.15, import
the networking/async stdlib the package promises (ssl, socket, asyncio, selectors,
sqlite3) and compute FOV with the shipped libtcod. Exit 0 only if every package passes.

    tools/smoke_package.py --version 0.3.1 dist/McRogueFace-0.3.1-*
"""
import argparse
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WASM_VENV_PY = ROOT / ".venv-wasmtest" / "bin" / "python"

PROBE = (
    "import mcrfpy, sys, ssl, socket, asyncio, selectors, sqlite3\n"
    "g = mcrfpy.Grid(grid_size=(10, 10))\n"
    "g.compute_fov((5, 5), radius=4)\n"
    "print('SMOKE', mcrfpy.__version__, sys.version.split()[0], sys.platform)\n"
    "sys.exit(0)\n"
)


def fail(msg):
    raise SystemExit("smoke_package: FAIL: " + msg)


def only_dir(path):
    entries = list(Path(path).iterdir())
    if len(entries) != 1 or not entries[0].is_dir():
        fail("%s should unpack to one top-level folder, got %s"
             % (path, sorted(e.name for e in entries)))
    return entries[0]


def check_probe(label, out, rc, version):
    line = next((l for l in out.splitlines() if l.startswith("SMOKE ")), None)
    if rc != 0 or line is None:
        fail("%s: probe exited %d without its SMOKE line:\n%s" % (label, rc, out[-1500:]))
    _, got, py, plat = line.split()
    if got != version:
        fail("%s: mcrfpy.__version__ is %s, expected %s" % (label, got, version))
    if not py.startswith("3.15"):
        fail("%s: ships Python %s, expected 3.15" % (label, py))
    print("  ok: %s: McRogueFace %s, Python %s, %s; ssl/socket/asyncio/selectors/sqlite3 "
          "import, FOV runs" % (label, got, py, plat))


def smoke_linux(archive, version, work):
    with tarfile.open(archive) as tf:
        # Our own archive; the "data" filter (Python 3.12+, and 3.11.4+) also checks it
        # holds nothing outside its folder.
        tf.extractall(work, **({"filter": "data"} if hasattr(tarfile, "data_filter") else {}))
    pkg = only_dir(work)
    env = dict(os.environ, ALSOFT_DRIVERS="null")
    r = subprocess.run(["./mcrogueface", "--headless", "-c", PROBE], cwd=pkg, env=env,
                       capture_output=True, text=True, timeout=120)
    check_probe(archive.name, r.stdout + r.stderr, r.returncode, version)


def smoke_windows(archive, version, work):
    if shutil.which("wine") is None:
        fail("%s: wine not found; it is needed to run the Windows package" % archive.name)
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(work)
    pkg = only_dir(work)
    env = dict(os.environ, WINEDEBUG="-all")
    r = subprocess.run(["wine", "mcrogueface.exe", "--headless", "-c", PROBE], cwd=pkg, env=env,
                       capture_output=True, text=True, timeout=300)
    check_probe(archive.name, r.stdout + r.stderr, r.returncode, version)


def smoke_wasm(archive, version, work):
    with zipfile.ZipFile(archive) as zf:
        names = zf.namelist()
        if "index.html" not in names or any("/" in n for n in names):
            fail("%s: expected a flat zip with index.html at the root (#474), got %s"
                 % (archive.name, names))
        zf.extractall(work)
    if not WASM_VENV_PY.is_file():
        fail("%s: Playwright venv missing (%s); run 'make test-wasm-setup'"
             % (archive.name, WASM_VENV_PY))
    r = subprocess.run([str(WASM_VENV_PY), str(ROOT / "tests" / "wasm" / "run_wasm_tests.py"),
                        "--build-dir", str(work), "--expect-version", version],
                       capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        fail("%s: browser tests failed:\n%s" % (archive.name, (r.stdout + r.stderr)[-2000:]))
    print("  ok: %s: flat zip with index.html; browser suite passes at %s"
          % (archive.name, version))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--version", required=True, help="the version every package must report")
    ap.add_argument("archives", nargs="+", type=Path)
    a = ap.parse_args()
    for archive in a.archives:
        archive = archive.resolve()
        if not archive.is_file():
            fail("%s not found" % archive)
        name = archive.name
        if ("-%s-" % a.version) not in name:
            fail("%s is not named for version %s" % (name, a.version))
        with tempfile.TemporaryDirectory(prefix="mcrf-smoke-") as work:
            if name.endswith("-Linux.tar.gz"):
                smoke_linux(archive, a.version, work)
            elif name.endswith("-Windows.zip"):
                smoke_windows(archive, a.version, work)
            elif name.endswith("-WASM.zip"):
                smoke_wasm(archive, a.version, work)
            else:
                fail("%s: not a Linux, Windows or WASM release package" % name)
    print("smoke_package: PASS (%d packages)" % len(a.archives))


if __name__ == "__main__":
    main()
