"""
Packaging test (#505): does the SHIPPED package make a working, pip-capable venv?

Builds the real Linux tarball (`tools/package.sh linux`), extracts it OUTSIDE the
source tree, and from the extracted package:
  1. `./mcrogueface -m venv ENV` (pip comes from the bundled ensurepip wheel; no network).
  2. Installs a local wheel (built here with zipfile) that has a console_scripts entry,
     via `ENV/bin/python -m pip install --no-index --no-deps`.
  3. Runs the console script: exits 0, sys.prefix == ENV, sys.executable is under ENV/bin.
  4. Asserts the extracted package tree is unchanged (nothing is ever installed into the
     engine's own directory). Files by name + size + mtime; directories by name only,
     because importing bumps directory mtimes; __pycache__ is ignored.
Mutations (non-vacuity): renaming `lib/Python/Lib/venv`, and separately
`lib/Python/Lib/ensurepip`, aside in the extracted package must make the probe fail;
restoring each makes it pass again.

Fail Early: any unexpected condition is a loud FAIL + sys.exit(1).
"""
import base64
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import zipfile
from pathlib import Path

THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parent.parent.parent
MAKEFILE = PROJECT_ROOT / "Makefile"
DIST_DIR = PROJECT_ROOT / "dist"

SUCCESS_MARKER = "VENV_PACKAGED_PROBE_OK"

# (what is removed, path relative to the package)
MUTATION_TARGETS = [
    ("venv", "lib/Python/Lib/venv"),
    ("ensurepip", "lib/Python/Lib/ensurepip"),
]

SCRIPT_NAME = "mcrf-venv-probe"
WHEEL_NAME = "mcrfvenvprobe-1.0-py3-none-any.whl"


def fail(msg):
    print("FAIL: %s" % msg)
    sys.exit(1)


def run(cmd, **kwargs):
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)


def engine_version():
    result = run([str(PROJECT_ROOT / "tools" / "version.sh")])
    if result.returncode != 0 or not result.stdout.strip():
        fail("tools/version.sh failed: %s" % result.stderr.strip())
    return result.stdout.strip()


def check_makefile_guard():
    """This test shortcuts to `tools/package.sh linux`; make sure that is still what
    `make package-linux` runs."""
    if not MAKEFILE.is_file():
        fail("Makefile not found at %s" % MAKEFILE)
    m = re.search(r'^package-linux:.*\n((?:\t.*\n?)*)', MAKEFILE.read_text(), re.MULTILINE)
    if not m:
        fail("Could not find a 'package-linux:' target in the Makefile; update this guard.")
    recipe = m.group(1)
    if "tools/package.sh" not in recipe or not re.search(r'\blinux\b', recipe):
        fail("'package-linux:' no longer runs tools/package.sh linux (recipe: %r)" % recipe)


def check_release_build_present():
    exe = PROJECT_ROOT / "build" / "mcrogueface"
    if not exe.is_file():
        fail("Release build not found at %s. tools/package.sh packages build/ "
             "specifically; run `make` from the project root first." % exe)


def extract_tarball(tarball_path, dest_dir):
    with tarfile.open(tarball_path, "r:gz") as tf:
        tf.extractall(dest_dir)
    entries = os.listdir(dest_dir)
    if len(entries) != 1 or not os.path.isdir(os.path.join(dest_dir, entries[0])):
        fail("Expected the tarball to extract one top-level directory, got: %r" % entries)
    return os.path.join(dest_dir, entries[0])


def build_wheel(path):
    """A wheel with one module and a console_scripts entry, no network, no build backend."""
    dist_info = "mcrfvenvprobe-1.0.dist-info"
    files = {
        "mcrfvenvprobe.py": (
            "import os, sys\n"
            "def main():\n"
            "    print('PREFIX', sys.prefix)\n"
            "    print('EXECUTABLE', sys.executable)\n"
            "    print('BASE_PREFIX', sys.base_prefix)\n"
            "    print('%s')\n"
            "    return 0\n" % SUCCESS_MARKER),
        dist_info + "/METADATA":
            "Metadata-Version: 2.1\nName: mcrfvenvprobe\nVersion: 1.0\n",
        dist_info + "/WHEEL":
            "Wheel-Version: 1.0\nGenerator: venv_packaged_test\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
        dist_info + "/entry_points.txt":
            "[console_scripts]\n%s = mcrfvenvprobe:main\n" % SCRIPT_NAME,
    }
    record = []
    for name, text in files.items():
        data = text.encode()
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
        record.append("%s,sha256=%s,%d" % (name, digest, len(data)))
    record.append(dist_info + "/RECORD,,")
    files[dist_info + "/RECORD"] = "\n".join(record) + "\n"
    with zipfile.ZipFile(path, "w") as zf:
        for name, text in files.items():
            zf.writestr(name, text)


def snapshot(pkg_dir):
    """{relative path: None for a dir, (size, mtime_ns) for a file}"""
    snap = {}
    for root, dirs, names in os.walk(pkg_dir):
        # Running Python writes bytecode caches beside the stdlib; that is not an install.
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for d in dirs:
            snap[os.path.relpath(os.path.join(root, d), pkg_dir)] = None
        for n in names:
            p = os.path.join(root, n)
            rel = os.path.relpath(p, pkg_dir)
            if os.path.islink(p):
                snap[rel] = ("link", os.readlink(p))
            else:
                st = os.stat(p)
                snap[rel] = (st.st_size, st.st_mtime_ns)
    return snap


def diff_snapshots(before, after):
    out = []
    for k in sorted(set(before) | set(after)):
        if k not in after:
            out.append("removed: %s" % k)
        elif k not in before:
            out.append("added: %s" % k)
        elif before[k] != after[k]:
            out.append("changed: %s (%r -> %r)" % (k, before[k], after[k]))
    return out


def clean_env(pkg_dir):
    env = os.environ.copy()
    for var in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "VIRTUAL_ENV"):
        env.pop(var, None)
    env["LD_LIBRARY_PATH"] = os.path.join(pkg_dir, "lib")
    env["ALSOFT_DRIVERS"] = "null"
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    return env


def probe(pkg_dir, work_dir, wheel):
    """Returns (ok, log). Makes a venv from the package, installs the wheel, runs the script."""
    env = clean_env(pkg_dir)
    venv_dir = os.path.join(work_dir, "ENV")
    shutil.rmtree(venv_dir, ignore_errors=True)
    log = []

    def step(label, cmd):
        r = run(cmd, cwd=work_dir, env=env, timeout=180)
        log.append("--- %s (rc=%d) ---\n%s%s" % (label, r.returncode, r.stdout, r.stderr))
        return r

    exe = os.path.join(pkg_dir, "mcrogueface")
    if not step("venv", [exe, "-m", "venv", venv_dir]).returncode == 0:
        return False, "\n".join(log)
    py = os.path.join(venv_dir, "bin", "python")
    if step("pip install", [py, "-m", "pip", "install", "--no-index", "--no-deps",
                            "--no-cache-dir", wheel]).returncode != 0:
        return False, "\n".join(log)
    script = os.path.join(venv_dir, "bin", SCRIPT_NAME)
    r = step("console script", [script])
    if r.returncode != 0 or SUCCESS_MARKER not in r.stdout:
        return False, "\n".join(log)
    fields = dict(l.split(" ", 1) for l in r.stdout.splitlines() if l.startswith(("PREFIX ", "EXECUTABLE ")))
    if os.path.realpath(fields.get("PREFIX", "").strip()) != os.path.realpath(venv_dir):
        return False, "\n".join(log) + "\nsys.prefix %r is not %r" % (fields.get("PREFIX"), venv_dir)
    exe_path = fields.get("EXECUTABLE", "").strip()
    if os.path.dirname(exe_path) != os.path.join(venv_dir, "bin"):
        return False, "\n".join(log) + "\nsys.executable %r is not under %s/bin" % (exe_path, venv_dir)
    return True, "\n".join(log)


def main():
    print("=== venv_packaged_test: packaged engine makes a pip-capable venv (#505) ===")
    check_makefile_guard()
    check_release_build_present()

    version = engine_version()
    tarball = DIST_DIR / ("McRogueFace-%s-Linux.tar.gz" % version)
    pre_existed = tarball.exists()
    pre_mtime = tarball.stat().st_mtime if pre_existed else None

    build_start = time.time()
    r = run(["bash", "tools/package.sh", "linux"], cwd=str(PROJECT_ROOT), timeout=180)
    if r.returncode != 0:
        print(r.stdout)
        print(r.stderr)
        fail("tools/package.sh linux exited with code %d" % r.returncode)
    if not tarball.exists():
        fail("Expected tarball not found after packaging: %s" % tarball)
    mtime = tarball.stat().st_mtime
    if (pre_existed and mtime <= pre_mtime) or mtime < build_start - 1:
        fail("Tarball %s was not (re)created by this run" % tarball)
    print("OK: tarball produced: %s" % tarball)

    temp_dir = tempfile.mkdtemp(prefix="mcrf_venvpkg_")
    try:
        pkg_parent = os.path.join(temp_dir, "pkg")
        os.mkdir(pkg_parent)
        work_dir = os.path.join(temp_dir, "work")
        os.mkdir(work_dir)
        pkg_dir = extract_tarball(str(tarball), pkg_parent)
        wheel = os.path.join(work_dir, WHEEL_NAME)
        build_wheel(wheel)

        before = snapshot(pkg_dir)

        # --- POSITIVE CASE ---
        ok, log = probe(pkg_dir, work_dir, wheel)
        if not ok:
            print(log)
            fail("Positive case: the packaged engine could not make a venv, install a "
                 "wheel into it, and run its console script.")
        print("OK: packaged engine -> venv -> pip install wheel -> console script runs in the venv")

        # --- PACKAGE UNTOUCHED ---
        changes = diff_snapshots(before, snapshot(pkg_dir))
        if changes:
            fail("The extracted package changed during the venv round trip (nothing may be "
                 "installed into the engine directory):\n  " + "\n  ".join(changes[:30]))
        print("OK: extracted package tree unchanged (%d entries)" % len(before))

        # --- MUTATIONS ---
        for name, rel in MUTATION_TARGETS:
            target = os.path.join(pkg_dir, rel)
            disabled = target + ".disabled"
            if not os.path.exists(target):
                fail("Expected shipped path missing before mutation: %s" % target)
            os.rename(target, disabled)
            try:
                ok, log = probe(pkg_dir, work_dir, wheel)
            finally:
                os.rename(disabled, target)
            if ok:
                fail("Removing %s did NOT break the probe -- no teeth for %s." % (rel, name))
            print("OK: removing %s breaks the probe" % rel)
            ok, log = probe(pkg_dir, work_dir, wheel)
            if not ok:
                print(log)
                fail("After restoring %s the probe still fails" % rel)
            print("OK: restoring %s brings the probe back to passing" % rel)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        if not pre_existed and tarball.exists():
            tarball.unlink()
            print("Cleaned up freshly-created tarball: %s" % tarball)

    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
