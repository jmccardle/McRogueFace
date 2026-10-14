"""
Packaging test: does the SHIPPED artifact's own filtered stdlib actually work?

`make package-linux` (== `tools/package.sh linux`) copies a filtered
copy of the CPython stdlib into the distribution tarball (`docs/` and CLAUDE.md
promise socket/ssl/asyncio/selectors keep working there). Nothing previously
built the real tarball, extracted it somewhere with NO dev tree in reach, and
proved the packaged binary can still import and USE those modules from its own
copy -- not the dev tree's `__lib/`.

This test drives the real packaging pipeline (`tools/package.sh linux`),
extracts the resulting tarball into a tempdir OUTSIDE the source tree, and:
  1. Runs a probe script through the packaged `mcrogueface` binary with
     PYTHONPATH/PYTHONHOME/PYTHONSTARTUP stripped from the environment, and
     LD_LIBRARY_PATH pointed ONLY at the package's own lib/ dir. The probe
     imports socket/ssl/asyncio/selectors (+ their C extensions), asserts each
     module's __file__ resolves inside the extracted package, and then
     actually uses them (real socket bind/listen, a selector, an SSL context,
     a trivial asyncio event loop).
  2. For EACH of the four modules, independently: renames the shipped stdlib
     file/dir aside, re-runs the probe, and asserts it now FAILS. This is the
     non-vacuity check -- if removing a module does not break the probe, the
     probe was never exercising it, and the whole test has no teeth for that
     module.

Fail Early: any unexpected condition is a loud FAIL + sys.exit(1). No
try/except-to-make-it-pass, no skipping.
"""
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parent.parent.parent
MAKEFILE = PROJECT_ROOT / "Makefile"
DIST_DIR = PROJECT_ROOT / "dist"

SUCCESS_MARKER = "NETWORK_STDLIB_PROBE_OK"

# (module import name, path relative to <package>/lib/Python/Lib)
MUTATION_TARGETS = [
    ("socket", "lib/Python/Lib/socket.py"),
    ("ssl", "lib/Python/Lib/ssl.py"),
    ("asyncio", "lib/Python/Lib/asyncio"),
    ("selectors", "lib/Python/Lib/selectors.py"),
]

PROBE_TEMPLATE = '''
import sys
import os

PKG_DIR = os.path.realpath({pkg_dir!r})

def assert_libpython_inside_pkg(name):
    mapped = set()
    with open("/proc/self/maps") as maps:
        for line in maps:
            parts = line.split()
            if len(parts) >= 6 and "libpython" in os.path.basename(parts[5]):
                mapped.add(os.path.realpath(parts[5]))
    if not mapped:
        print("FAIL: %s is builtin but no libpython is mapped into the process" % name)
        sys.exit(1)
    for path in mapped:
        if os.path.commonpath([path, PKG_DIR]) != PKG_DIR:
            print("FAIL: %s is builtin, but libpython %r is NOT inside package dir %r" % (name, path, PKG_DIR))
            sys.exit(1)

def assert_inside_pkg(mod, name):
    if name in sys.builtin_module_names:
        # CPython 3.15 links some accelerators (e.g. _asyncio) statically into
        # libpython, so there is no __file__; the shipped libpython must be it.
        assert_libpython_inside_pkg(name)
        return
    f = getattr(mod, "__file__", None)
    if f is None:
        print("FAIL: module %s has no __file__" % name)
        sys.exit(1)
    real = os.path.realpath(f)
    if os.path.commonpath([real, PKG_DIR]) != PKG_DIR:
        print("FAIL: module %s __file__ %r is NOT inside package dir %r" % (name, real, PKG_DIR))
        sys.exit(1)

import socket
import ssl
import asyncio
import selectors

for mod, name in ((socket, "socket"), (ssl, "ssl"), (asyncio, "asyncio"), (selectors, "selectors")):
    assert_inside_pkg(mod, name)

import _socket
import _ssl
import _asyncio
import select as _select_mod

for mod, name in ((_socket, "_socket"), (_ssl, "_ssl"), (_asyncio, "_asyncio"), (_select_mod, "select")):
    assert_inside_pkg(mod, name)

# Actually use them, not just import them.
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(("127.0.0.1", 0))
s.listen(1)

sel = selectors.DefaultSelector()
sel.register(s, selectors.EVENT_READ)
sel.unregister(s)
sel.close()

ctx = ssl.create_default_context()
if ctx is None:
    print("FAIL: ssl.create_default_context() returned None")
    sys.exit(1)

loop = asyncio.new_event_loop()
loop.run_until_complete(asyncio.sleep(0))
loop.close()

s.close()

print({marker!r})
sys.exit(0)
'''


def fail(msg):
    print("FAIL: %s" % msg)
    sys.exit(1)


def run(cmd, **kwargs):
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)


def engine_version():
    # package.sh names archives from the version header (#475), via tools/version.sh.
    result = run([str(PROJECT_ROOT / "tools" / "version.sh")])
    if result.returncode != 0 or not result.stdout.strip():
        fail("tools/version.sh failed: %s" % result.stderr.strip())
    return result.stdout.strip()


def check_makefile_guard():
    """
    Guard against drift from the documented `make package-linux` recipe.
    This test shortcuts straight to `tools/package.sh linux` (avoids a
    re-entrant `make`); if the Makefile target ever stops delegating there,
    this test's shortcut silently diverges from what CI/docs claim to run.
    """
    if not MAKEFILE.is_file():
        fail("Makefile not found at %s" % MAKEFILE)
    text = MAKEFILE.read_text()

    m = re.search(r'^package-linux:.*\n((?:\t.*\n?)*)', text, re.MULTILINE)
    if not m:
        fail("Could not find a 'package-linux:' target in the Makefile. "
             "This test assumes that target exists and delegates to tools/package.sh; "
             "if it was renamed or restructured, update this guard (and re-verify the shortcut is still valid).")

    recipe = m.group(1)
    if "tools/package.sh" not in recipe:
        fail("'package-linux:' target no longer invokes tools/package.sh "
             "(recipe body: %r). This test's shortcut of calling package.sh directly "
             "is no longer equivalent to `make package-linux` -- update both." % recipe)
    if not re.search(r'\blinux\b', recipe):
        fail("'package-linux:' target's tools/package.sh invocation no longer "
             "passes the 'linux' arg (recipe body: %r)." % recipe)


def find_expected_tarball(version):
    return DIST_DIR / ("McRogueFace-%s-Linux.tar.gz" % version)


def check_release_build_present():
    """
    tools/package.sh packages PROJECT_ROOT/build -- the Release build -- no matter
    which build directory the suite itself is being driven from. Say so plainly
    instead of letting package.sh fail with a bare 'Linux build not found'.

    The alternate-build suites (make debug-test / asan-test / tsan-test /
    valgrind-test) point MCRF_BUILD_DIR at build-debug/build-asan/build-tsan and
    pass --exclude=packaging, because packaging the Release artifact is orthogonal
    to sanitizer coverage. If you are seeing this failure from one of those, the
    exclusion was dropped.
    """
    exe = PROJECT_ROOT / "build" / "mcrogueface"
    if not exe.is_file():
        fail("Release build not found at %s. tools/package.sh packages build/ "
             "specifically; run `make` from the project root first." % exe)


def run_packaging():
    result = run(["bash", "tools/package.sh", "linux"], cwd=str(PROJECT_ROOT), timeout=120)
    if result.returncode != 0:
        print("--- tools/package.sh stdout ---")
        print(result.stdout)
        print("--- tools/package.sh stderr ---")
        print(result.stderr)
        fail("tools/package.sh linux exited with code %d" % result.returncode)


def extract_tarball(tarball_path, dest_dir):
    with tarfile.open(tarball_path, "r:gz") as tf:
        tf.extractall(dest_dir)
    entries = os.listdir(dest_dir)
    if len(entries) != 1:
        fail("Expected the tarball to extract a single top-level directory, got: %r" % entries)
    pkg_dir = os.path.join(dest_dir, entries[0])
    if not os.path.isdir(pkg_dir):
        fail("Extracted top-level entry %r is not a directory" % pkg_dir)
    return pkg_dir


def write_probe(probe_path, pkg_dir):
    probe_path.write_text(PROBE_TEMPLATE.format(pkg_dir=pkg_dir, marker=SUCCESS_MARKER))


def run_probe(pkg_dir, probe_path):
    exe = os.path.join(pkg_dir, "mcrogueface")
    if not os.path.isfile(exe):
        fail("Packaged executable missing: %s" % exe)

    child_env = os.environ.copy()
    for var in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP"):
        child_env.pop(var, None)
    child_env["LD_LIBRARY_PATH"] = os.path.join(pkg_dir, "lib")

    return subprocess.run(
        [exe, "--headless", "--exec", str(probe_path)],
        cwd=pkg_dir,
        env=child_env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def main():
    print("=== network_stdlib_packaged_test: proving packaged stdlib import/use ===")

    check_makefile_guard()
    print("OK: Makefile package-linux delegates to tools/package.sh linux")

    check_release_build_present()

    version = engine_version()
    expected_tarball = find_expected_tarball(version)
    pre_existed = expected_tarball.exists()
    pre_mtime = expected_tarball.stat().st_mtime if pre_existed else None
    if pre_existed:
        print("NOTE: %s already existed before this run (mtime %s); will NOT delete it at cleanup." %
              (expected_tarball, pre_mtime))

    build_start = time.time()
    run_packaging()
    build_elapsed = time.time() - build_start
    print("OK: tools/package.sh linux completed in %.2fs" % build_elapsed)

    if not expected_tarball.exists():
        fail("Expected tarball not found after packaging: %s" % expected_tarball)
    new_mtime = expected_tarball.stat().st_mtime
    if pre_existed and new_mtime <= pre_mtime:
        fail("Tarball %s exists but its mtime (%s) did not advance past the pre-existing "
             "mtime (%s) -- packaging may not have actually re-created it." %
             (expected_tarball, new_mtime, pre_mtime))
    if new_mtime < build_start - 1:
        fail("Tarball %s has mtime %s, which predates this packaging run (started %s)." %
             (expected_tarball, new_mtime, build_start))
    print("OK: tarball produced/updated: %s" % expected_tarball)

    temp_dir = tempfile.mkdtemp(prefix="mcrf_pkgtest_")
    print("Extracting into tempdir (outside source tree): %s" % temp_dir)

    try:
        pkg_dir = extract_tarball(str(expected_tarball), temp_dir)
        print("OK: extracted package dir: %s" % pkg_dir)

        probe_path = Path(temp_dir) / "probe.py"
        write_probe(probe_path, pkg_dir)

        # --- POSITIVE CASE ---
        result = run_probe(pkg_dir, probe_path)
        if result.returncode != 0 or SUCCESS_MARKER not in result.stdout:
            print("--- probe stdout ---")
            print(result.stdout)
            print("--- probe stderr ---")
            print(result.stderr)
            fail("Positive-case probe failed (returncode=%d) against the freshly packaged binary. "
                 "The packaged stdlib should support socket/ssl/asyncio/selectors." % result.returncode)
        print("OK: positive case -- packaged binary imports+uses socket/ssl/asyncio/selectors")

        # --- MUTATION / NON-VACUITY CASE ---
        for module_name, rel_path in MUTATION_TARGETS:
            target_path = os.path.join(pkg_dir, rel_path)
            disabled_path = target_path + ".disabled"

            if not os.path.exists(target_path):
                fail("Expected shipped stdlib path missing before mutation: %s" % target_path)

            os.rename(target_path, disabled_path)
            try:
                mutated_result = run_probe(pkg_dir, probe_path)
            finally:
                os.rename(disabled_path, target_path)

            if mutated_result.returncode == 0:
                fail("Removing %s (module %r) did NOT break the probe -- this test has "
                     "no teeth for that module. Probe stdout:\n%s\nstderr:\n%s" %
                     (rel_path, module_name, mutated_result.stdout, mutated_result.stderr))

            # Best-effort check that the failure actually mentions the missing module.
            # The binding assertion is the non-zero returncode above; we do not weaken
            # that if this text match is imprecise.
            combined_output = mutated_result.stdout + mutated_result.stderr
            if module_name not in combined_output:
                print("NOTE: mutation of %s failed the probe (returncode=%d) but the module "
                      "name %r was not found verbatim in its output -- returncode is still "
                      "the binding assertion here." % (rel_path, mutated_result.returncode, module_name))

            print("OK: removing %s breaks the probe (returncode=%d) as expected" %
                  (rel_path, mutated_result.returncode))

            # Confirm restoring it un-breaks the probe (proves the mutation, not some
            # sticky side effect, caused the failure).
            restored_result = run_probe(pkg_dir, probe_path)
            if restored_result.returncode != 0 or SUCCESS_MARKER not in restored_result.stdout:
                print("--- restored probe stdout ---")
                print(restored_result.stdout)
                print("--- restored probe stderr ---")
                print(restored_result.stderr)
                fail("After restoring %s, the probe still fails (returncode=%d) -- "
                     "expected a clean pass again." % (rel_path, restored_result.returncode))
            print("OK: restoring %s brings the probe back to passing" % rel_path)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        if not pre_existed and expected_tarball.exists():
            expected_tarball.unlink()
            print("Cleaned up freshly-created tarball: %s" % expected_tarball)

    print("=" * 60)
    print("Proven: `tools/package.sh linux` (== `make package-linux`) produces")
    print("a tarball whose OWN packaged stdlib -- not the dev tree's __lib/ -- provides")
    print("working socket, ssl, asyncio, and selectors modules (Python source AND C")
    print("extensions), each independently load-bearing (removing any one breaks the")
    print("packaged binary's ability to use the networking stack).")
    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
