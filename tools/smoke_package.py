#!/usr/bin/env python3
"""Smoke-test release packages the way a user gets them (#475).

Each archive is unpacked into a fresh directory outside the source tree and run from
there, so nothing resolves against the build tree:

  *-Linux.tar.gz     ./mcrogueface --headless; then, in clean Debian 13 and Ubuntu 24.04
                     containers with only CLEAN_DISTRO_PACKAGES installed, the same probe
                     run directly (no run.sh, no LD_LIBRARY_PATH) and `ldd` finding every
                     dependency of every ELF in the package (#525; needs podman or docker, --no-clean-distro skips it)
  *-Windows.zip      wine mcrogueface.exe --headless   (needs wine)
  *-WASM.zip         index.html at the zip root, then tests/wasm/run_wasm_tests.py in
                     headless Chromium (needs the .venv-wasmtest Playwright venv)

Desktop packages must report the expected mcrfpy.__version__, run Python 3.15, import
the networking/async stdlib the package promises (ssl, socket, asyncio, selectors,
sqlite3), venv and ensurepip (#505) and compute FOV with the shipped libtcod. Exit 0 only if every package passes.

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

# The Linux floor (#525): Debian 13 / Ubuntu 24.04 and newer (glibc >= 2.38). Every image
# is a clean install plus exactly these packages, which README.md documents: the first list
# is what the engine needs to start, the second what some stdlib modules need (the Python
# extension modules under lib/Python/). The package ships everything else, libFLAC included.
CLEAN_DISTRO_IMAGES = ("docker.io/library/debian:13-slim", "docker.io/library/ubuntu:24.04")
ENGINE_PACKAGES = ("libopenal1 libvorbisfile3 libvorbisenc2 libfreetype6 libx11-6 libxrandr2 "
                   "libxcursor1 libudev1 libopengl0 libgl1")
STDLIB_PACKAGES = ("libsqlite3-0 libssl3t64 libffi8 libreadline8t64 libgdbm6t64 libncursesw6 "
                   "libuuid1 libbz2-1.0 liblzma5 libzstd1")
# Test-only, installed after the dependency check: the probe builds a Grid, which needs a
# display (#451), so it runs under Xvfb.
TEST_PACKAGES = "xvfb libgl1-mesa-dri"
CONTAINER_TOOLS = ("podman", "docker")

# Runs inside the container, in the unpacked package (mounted read-only at /pkg). The
# documented packages are installed first and alone, so the ldd check proves they suffice.
CLEAN_DISTRO_SCRIPT = """set -e
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq >/dev/null || {{ echo "APT-FAILED update"; exit 5; }}
apt-get install -y -qq --no-install-recommends {packages} >/dev/null \\
    || {{ echo "APT-FAILED install of the documented packages"; exit 5; }}
cd /pkg
missing=$(for f in mcrogueface $(find lib -type f \\( -name '*.so' -o -name '*.so.*' \\)); do ldd "$f" 2>&1 | grep 'not found' | sed "s|^|$f: |"; done)
if [ -n "$missing" ]; then echo "DEPS-NOT-FOUND"; echo "$missing"; exit 3; fi
echo "DEPS-OK"
apt-get install -y -qq --no-install-recommends {test_packages} >/dev/null \\
    || {{ echo "APT-FAILED install of the test-only packages"; exit 5; }}
Xvfb :99 -nolisten tcp >/dev/null 2>&1 &
for i in $(seq 100); do [ -e /tmp/.X11-unix/X99 ] && break; sleep 0.1; done
[ -e /tmp/.X11-unix/X99 ] || {{ echo "XVFB-FAILED"; exit 4; }}
rc=0
DISPLAY=:99 ALSOFT_DRIVERS=null timeout 120 ./mcrogueface --headless -c "$PROBE" || rc=$?
kill %1 2>/dev/null || true
exit $rc
"""

PROBE = (
    "import mcrfpy, sys, ssl, socket, asyncio, selectors, sqlite3, pydoc, sysconfig, venv, ensurepip\n"
    "sysconfig.get_path('stdlib')\n"
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
    print("  ok: %s: McRogueFace %s, Python %s, %s; ssl/socket/asyncio/selectors/sqlite3/venv/ensurepip "
          "import, FOV runs" % (label, got, py, plat))


def container_tool():
    for tool in CONTAINER_TOOLS:
        if shutil.which(tool):
            return tool
    fail("neither podman nor docker found; the Linux package is tested in clean containers "
         "(pass --no-clean-distro to skip, for development only)")


def smoke_clean_distro(archive, pkg, version):
    tool = container_tool()
    script = CLEAN_DISTRO_SCRIPT.format(packages=ENGINE_PACKAGES + " " + STDLIB_PACKAGES,
                                         test_packages=TEST_PACKAGES)
    for image in CLEAN_DISTRO_IMAGES:
        label = "%s on %s" % (archive.name, image.rsplit("/", 1)[-1])
        try:
            r = subprocess.run([tool, "run", "--rm", "-v", "%s:/pkg:ro" % pkg,
                                "-e", "PROBE=" + PROBE, image, "bash", "-c", script],
                               capture_output=True, text=True, timeout=900)
        except subprocess.TimeoutExpired:
            fail("%s: container run exceeded 900s" % label)
        out = r.stdout + r.stderr
        if "DEPS-NOT-FOUND" in out:
            fail("%s: unresolved dependencies (run directly, no LD_LIBRARY_PATH):\n%s"
                 % (label, out.split("DEPS-NOT-FOUND", 1)[1][:1500]))
        if "APT-FAILED" in out or "DEPS-OK" not in out:
            fail("%s: container setup failed (image pull or apt-get, not the package) (rc %d):\n%s"
                 % (label, r.returncode, out[-1500:]))
        check_probe(label, out, r.returncode, version)


def smoke_linux(archive, version, work, clean_distro=True):
    with tarfile.open(archive) as tf:
        # Our own archive; the "data" filter (Python 3.12+, and 3.11.4+) also checks it
        # holds nothing outside its folder.
        tf.extractall(work, **({"filter": "data"} if hasattr(tarfile, "data_filter") else {}))
    pkg = only_dir(work)
    env = dict(os.environ, ALSOFT_DRIVERS="null")
    r = subprocess.run(["./mcrogueface", "--headless", "-c", PROBE], cwd=pkg, env=env,
                       capture_output=True, text=True, timeout=120)
    check_probe(archive.name, r.stdout + r.stderr, r.returncode, version)
    if clean_distro:
        smoke_clean_distro(archive, pkg, version)


def smoke_windows(archive, version, work):
    if shutil.which("wine") is None:
        fail("%s: wine not found; it is needed to run the Windows package" % archive.name)
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(work)
    pkg = only_dir(work)
    if list(pkg.glob("python3*.zip")):
        fail("%s: ships a python3NN.zip; the engine imports the stdlib from lib/Python/Lib, "
             "so it is dead weight" % archive.name)
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
    ap.add_argument("--no-clean-distro", action="store_true",
                    help="skip the clean-container run of the Linux package (development only; "
                         "tools/release.sh never passes it)")
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
                smoke_linux(archive, a.version, work, not a.no_clean_distro)
            elif name.endswith("-Windows.zip"):
                smoke_windows(archive, a.version, work)
            elif name.endswith("-WASM.zip"):
                smoke_wasm(archive, a.version, work)
            else:
                fail("%s: not a Linux, Windows or WASM release package" % name)
    print("smoke_package: PASS (%d packages)" % len(a.archives))


if __name__ == "__main__":
    main()
