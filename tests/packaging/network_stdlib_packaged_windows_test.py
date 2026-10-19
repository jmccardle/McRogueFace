"""
Packaging test (Windows, under Wine): does the SHIPPED Windows package's own stdlib and
extension modules provide the networking set?

The Windows twin of network_stdlib_packaged_test.py. Until 0.3.0 the Windows zip had no
.pyd files at all, so socket/ssl/asyncio did not import there (3be5cb5); nothing but a
manual Wine run kept them working since. This drives the real pipeline
(`tools/package.sh windows`), extracts the zip OUTSIDE the source tree, and runs a probe
through the packaged `mcrogueface.exe` under Wine. The probe imports socket / ssl /
asyncio / selectors and their extension modules (_socket, _ssl, _hashlib, _asyncio,
select), asserts every `__file__` is inside the extracted package, and uses them (a real
socket bind/listen, a selector, an SSL context, an asyncio loop plus a loopback TCP round
trip).

Non-vacuity: each Python module and each extension file / DLL the networking set needs is
renamed aside in turn (including libssl-3.dll and libcrypto-3.dll, which only Windows
ships beside the .pyd files), and the probe must then FAIL. A final run after everything is
restored must pass again, which proves the mutations, not a sticky side effect, broke it.

Inputs outside git (see EXTERNAL_INPUTS in run_tests.py): a `make windows` build
(build-windows/mcrogueface.exe) and `wine`. Where they are absent the runner reports SKIP,
and --no-skip makes that a FAIL. Past that, any unexpected condition is a loud FAIL.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parent.parent.parent
MAKEFILE = PROJECT_ROOT / "Makefile"
DIST_DIR = PROJECT_ROOT / "dist"

SUCCESS_MARKER = "NETWORK_STDLIB_WINDOWS_PROBE_OK"

# Paths relative to the package. (label, path): each is renamed aside and must break the probe.
MUTATION_TARGETS = [
    ("socket", "lib/Python/Lib/socket.py"),
    ("ssl", "lib/Python/Lib/ssl.py"),
    ("asyncio", "lib/Python/Lib/asyncio"),
    ("selectors", "lib/Python/Lib/selectors.py"),
    ("_socket", "lib/Python/DLLs/_socket.pyd"),
    ("_ssl", "lib/Python/DLLs/_ssl.pyd"),
    ("_hashlib", "lib/Python/DLLs/_hashlib.pyd"),
    ("_asyncio", "lib/Python/DLLs/_asyncio.pyd"),
    ("select", "lib/Python/DLLs/select.pyd"),
    ("libssl", "lib/Python/DLLs/libssl-3.dll"),
    ("libcrypto", "lib/Python/DLLs/libcrypto-3.dll"),
]

PROBE_TEMPLATE = '''
import os
import sys

if sys.platform != "win32":
    print("FAIL: probe is not running as a Windows process: %r" % sys.platform)
    sys.exit(1)

# The test runs the exe with the package as its working directory.
PKG_DIR = os.path.normcase(os.path.realpath(os.getcwd()))

def assert_inside_pkg(mod, name):
    f = getattr(mod, "__file__", None)
    if f is None:
        print("FAIL: module %s has no __file__ (builtin?): not shipped as a file" % name)
        sys.exit(1)
    real = os.path.normcase(os.path.realpath(f))
    if os.path.commonpath([real, PKG_DIR]) != PKG_DIR:
        print("FAIL: module %s __file__ %r is NOT inside package dir %r" % (name, real, PKG_DIR))
        sys.exit(1)

import socket
import ssl
import asyncio
import selectors
import _socket
import _ssl
import _hashlib
import _asyncio
import select

for mod, name in ((socket, "socket"), (ssl, "ssl"), (asyncio, "asyncio"), (selectors, "selectors"),
                  (_socket, "_socket"), (_ssl, "_ssl"), (_hashlib, "_hashlib"),
                  (_asyncio, "_asyncio"), (select, "select")):
    assert_inside_pkg(mod, name)

# Actually use them, not just import them.
srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv.bind(("127.0.0.1", 0))
srv.listen(1)
port = srv.getsockname()[1]

sel = selectors.DefaultSelector()
sel.register(srv, selectors.EVENT_READ)
sel.unregister(srv)
sel.close()

ctx = ssl.create_default_context()
if ctx is None:
    print("FAIL: ssl.create_default_context() returned None")
    sys.exit(1)
if not ssl.OPENSSL_VERSION.startswith("OpenSSL"):
    print("FAIL: unexpected ssl.OPENSSL_VERSION %r" % ssl.OPENSSL_VERSION)
    sys.exit(1)

async def roundtrip():
    async def handle(reader, writer):
        writer.write((await reader.readline()).upper())
        await writer.drain()
        writer.close()
    server = await asyncio.start_server(handle, "127.0.0.1", 0)
    p = server.sockets[0].getsockname()[1]
    reader, writer = await asyncio.open_connection("127.0.0.1", p)
    writer.write(b"ping\\n")
    await writer.drain()
    got = await reader.readline()
    writer.close()
    server.close()
    await server.wait_closed()
    return got

got = asyncio.run(roundtrip())
if got != b"PING\\n":
    print("FAIL: asyncio TCP round trip returned %r" % (got,))
    sys.exit(1)

srv.close()
print({marker!r})
sys.exit(0)
'''


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
    """This test shortcuts to `tools/package.sh windows`; the Makefile target must still do so."""
    if not MAKEFILE.is_file():
        fail("Makefile not found at %s" % MAKEFILE)
    m = re.search(r'^package-windows:.*\n((?:\t.*\n?)*)', MAKEFILE.read_text(), re.MULTILINE)
    if not m:
        fail("no 'package-windows:' target in the Makefile; update this guard")
    recipe = m.group(1)
    if "tools/package.sh" not in recipe or not re.search(r'\bwindows\b', recipe):
        fail("'package-windows:' no longer runs 'tools/package.sh windows' (recipe: %r); "
             "this test's shortcut is no longer equivalent -- update both" % recipe)


def run_packaging():
    result = run(["bash", "tools/package.sh", "windows"], cwd=str(PROJECT_ROOT), timeout=300)
    if result.returncode != 0:
        print("--- tools/package.sh stdout ---")
        print(result.stdout)
        print("--- tools/package.sh stderr ---")
        print(result.stderr)
        fail("tools/package.sh windows exited with code %d" % result.returncode)


def extract_zip(zip_path, dest_dir):
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(dest_dir)
    entries = os.listdir(dest_dir)
    if len(entries) != 1:
        fail("Expected the zip to extract a single top-level directory, got: %r" % entries)
    pkg_dir = os.path.join(dest_dir, entries[0])
    if not os.path.isdir(pkg_dir):
        fail("Extracted top-level entry %r is not a directory" % pkg_dir)
    return pkg_dir


def run_probe(pkg_dir, probe_path):
    if not os.path.isfile(os.path.join(pkg_dir, "mcrogueface.exe")):
        fail("Packaged executable missing: %s" % pkg_dir)
    env = os.environ.copy()
    for var in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP"):
        env.pop(var, None)
    env["WINEDEBUG"] = "-all"
    env["ALSOFT_DRIVERS"] = "null"
    return subprocess.run(["wine", "mcrogueface.exe", "--headless", "--exec", str(probe_path)],
                          cwd=pkg_dir, env=env, capture_output=True, text=True, timeout=120)


def expect_pass(result, what):
    if result.returncode != 0 or SUCCESS_MARKER not in result.stdout:
        print("--- probe stdout ---")
        print(result.stdout)
        print("--- probe stderr ---")
        print(result.stderr[-3000:])
        fail("%s (returncode=%d)" % (what, result.returncode))


def main():
    print("=== network_stdlib_packaged_windows_test: packaged Windows stdlib under Wine ===")

    check_makefile_guard()
    print("OK: Makefile package-windows delegates to tools/package.sh windows")

    if shutil.which("wine") is None:
        fail("wine not found; it runs the Windows package")
    if not (PROJECT_ROOT / "build-windows" / "mcrogueface.exe").is_file():
        fail("build-windows/mcrogueface.exe not found; run `make windows` from the project root")

    version = engine_version()
    expected_zip = DIST_DIR / ("McRogueFace-%s-Windows.zip" % version)
    pre_existed = expected_zip.exists()
    pre_mtime = expected_zip.stat().st_mtime if pre_existed else None
    if pre_existed:
        print("NOTE: %s already existed (mtime %s); will NOT delete it at cleanup." %
              (expected_zip, pre_mtime))

    build_start = time.time()
    run_packaging()
    print("OK: tools/package.sh windows completed in %.2fs" % (time.time() - build_start))

    if not expected_zip.exists():
        fail("Expected zip not found after packaging: %s" % expected_zip)
    new_mtime = expected_zip.stat().st_mtime
    if (pre_existed and new_mtime <= pre_mtime) or new_mtime < build_start - 1:
        fail("%s was not re-created by this run (mtime %s)" % (expected_zip, new_mtime))

    temp_dir = tempfile.mkdtemp(prefix="mcrf_pkgtest_win_")
    print("Extracting into tempdir (outside source tree): %s" % temp_dir)
    try:
        pkg_dir = extract_zip(str(expected_zip), temp_dir)
        probe_path = Path(temp_dir) / "probe.py"
        probe_path.write_text(PROBE_TEMPLATE.format(marker=SUCCESS_MARKER))

        # --- POSITIVE CASE ---
        expect_pass(run_probe(pkg_dir, probe_path),
                    "Positive-case probe failed against the freshly packaged Windows build")
        print("OK: positive case -- packaged exe imports+uses socket/ssl/asyncio/selectors")

        # --- MUTATION / NON-VACUITY CASE ---
        for label, rel_path in MUTATION_TARGETS:
            target = os.path.join(pkg_dir, rel_path)
            disabled = target + ".disabled"
            if not os.path.exists(target):
                fail("Expected shipped path missing before mutation: %s" % target)
            os.rename(target, disabled)
            try:
                mutated = run_probe(pkg_dir, probe_path)
            finally:
                os.rename(disabled, target)
            if mutated.returncode == 0:
                fail("Removing %s (%s) did NOT break the probe -- no teeth for it. stdout:\n%s\n"
                     "stderr:\n%s" % (rel_path, label, mutated.stdout, mutated.stderr[-2000:]))
            print("OK: removing %s breaks the probe (returncode=%d)" % (rel_path, mutated.returncode))

        # Everything restored: the probe must pass again.
        expect_pass(run_probe(pkg_dir, probe_path),
                    "After restoring every mutated file the probe still fails")
        print("OK: restoring every file brings the probe back to passing")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        if not pre_existed and expected_zip.exists():
            expected_zip.unlink()
            print("Cleaned up freshly-created zip: %s" % expected_zip)

    print("=" * 60)
    print("Proven: `tools/package.sh windows` (== `make package-windows`) produces a zip whose")
    print("OWN stdlib, .pyd modules and OpenSSL DLLs provide working socket, ssl, asyncio and")
    print("selectors under Wine, each independently load-bearing.")
    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
