#!/usr/bin/env python3
"""
McRogueFace Test Runner
Runs all headless tests and reports results.

Usage:
    python3 tests/run_tests.py           # Run all tests
    python3 tests/run_tests.py unit      # Run only unit tests
    python3 tests/run_tests.py -v        # Verbose output (show failure details)
    python3 tests/run_tests.py --checksums  # Show screenshot checksums
    python3 tests/run_tests.py --timeout=30  # Custom timeout
    python3 tests/run_tests.py --sanitizer=asan   # Detect ASan/UBSan errors in output (or =tsan)
    python3 tests/run_tests.py --valgrind   # Run tests under Valgrind memcheck
    python3 tests/run_tests.py --exclude=packaging  # Run everything but one directory
    python3 tests/run_tests.py --no-skip    # Missing EXTERNAL_INPUTS fail instead of SKIP
    python3 tests/run_tests.py -j 8         # 8 parallel workers, each on a private Xvfb (see below)
    python3 tests/run_tests.py --shard 2/4  # Every 4th test starting at the 2nd (for splitting CI)

Parallel runs (-j N, N > 1): the runner starts N private Xvfb servers and kills them on exit;
the inherited DISPLAY is never used (a desktop session would render the suite on the desktop).
Each worker runs its tests in its own scratch directory, <project root>/.test-worker-<k>/, that
looks like the build directory (assets, scripts, lib and the executables are symlinked in;
everything a test writes lands in the worker's own directory) with a private TMPDIR.
tests/packaging/ stays serial, after the parallel phase (SERIAL_DIRS): every test there runs
tools/package.sh, which packages build/ itself and writes the shared dist/ directory.
With -j 1 (the default) nothing changes: tests run one at a time in BUILD_DIR on whatever
DISPLAY the caller provides (e.g. an outer xvfb-run).

Environment variables:
    MCRF_BUILD_DIR          Build directory (default: ../build)
    MCRF_LIB_DIR            Library directory for LD_LIBRARY_PATH (default: ../__lib)
    MCRF_TIMEOUT_MULTIPLIER Multiply per-test timeout (default: 1, use 50 for valgrind)
"""
import os
import subprocess
import sys
import time
import hashlib
import re
import argparse
import shutil
import signal
import threading
import queue
from pathlib import Path

# Configuration — respect environment overrides for debug/sanitizer builds
TESTS_DIR = Path(__file__).parent
BUILD_DIR = Path(os.environ.get('MCRF_BUILD_DIR', str(TESTS_DIR.parent / "build")))
LIB_DIR = Path(os.environ.get('MCRF_LIB_DIR', str(TESTS_DIR.parent / "__lib")))
MCROGUEFACE = BUILD_DIR / "mcrogueface"
DEFAULT_TIMEOUT = 10  # seconds per test

# Sanitizer error patterns to scan for in stderr
SANITIZER_PATTERNS = [
    re.compile(r'ERROR: AddressSanitizer'),
    re.compile(r'ERROR: LeakSanitizer'),
    re.compile(r'runtime error:'),  # UBSan
    re.compile(r'ERROR: ThreadSanitizer'),
]

# Test directories to run (in order)
TEST_DIRS = ['unit', 'integration', 'regression', 'demo', 'snippets', 'packaging']

# tests/snippets/ holds the code samples published on mcrogueface.github.io. They live
# here, in the engine repo, so that breaking the API breaks the build -- the docs site
# pulls them from here rather than keeping its own copy to rot in parallel. Before this,
# 130 snippets were executed by nothing at all and carried a hand-typed "status=ok"
# header that no run had ever verified.
#
# They are display scripts with no sys.exit(), because they must stay copy-pasteable, so
# _harness.py is chained as a second --exec to supply the ending (see its docstring).
SNIPPET_HARNESS = 'tests/snippets/_harness.py'

# #372: tests/demo/ was never run by anything, so the demo screens -- which CLAUDE.md
# points at as the canonical API-usage examples -- silently bitrotted until they could
# not even import. Smoke-gate the entry point that exercises screens/base.py and every
# wired DemoScreen, so "read the demos for correct usage" stays true.
#
# An allowlist, not a glob, for the top level of tests/demo/ (it also holds ad-hoc
# showcase and screenshot scripts). #374: tests/demo/standalone/ is the opposite: every
# *.py there is a gated demo, run with tests/demo/_harness.py chained as a second
# --exec (they wait for ESC, which never comes headless). Adding a file adds a test.
# Demos render, so they need a longer timeout than a unit test.
DEMO_SMOKE_TESTS = ['demo_main.py']
DEMO_STANDALONE_DIR = 'standalone'
DEMO_HARNESS = 'tests/demo/_harness.py'
DEMO_TIMEOUT = 60  # seconds

# Directories that never run concurrently with anything (-j N): after the parallel phase,
# one at a time, in BUILD_DIR itself. tests/packaging/ runs tools/package.sh, which packages
# build/ (so it needs build/ unchanged underneath it) and writes the shared dist/ directory;
# the same tests also build tarballs and probe them, which is the heaviest I/O in the suite.
SERIAL_DIRS = ('packaging',)

# Entries of BUILD_DIR that a worker's scratch directory links to. Everything else in
# BUILD_DIR is build-system state or output a test might write to (imgui.ini, save/,
# test_screenshots/, *.png ...), and each worker must have its own. Executables are linked
# too (a test may run ./mcrogueface from its cwd).
WORKER_LINKS = ('assets', 'scripts', 'lib')
# A worker's directory is a sibling of build/ (directly under the project root), not a
# child of it: tests reach the repository from their cwd as `../tests/...`, `../docs/...`.
WORKER_DIR_FMT = '.test-worker-{}'
XVFB_SCREEN = '1280x1024x24'  # xvfb-run's default

# tests/packaging/ drives the real `tools/package.sh linux full` pipeline (the same
# thing `make package-linux` calls) end to end: build the tarball, extract it
# OUTSIDE the source tree, and prove the packaged binary's own filtered stdlib can
# still import and USE the networking/async modules (socket/ssl/asyncio/selectors)
# that docs/CLAUDE.md promise ship in the "full" preset. Nothing previously verified
# that the shipped, filtered interpreter -- as opposed to the dev tree's __lib/ --
# actually works. Building the tarball + running the packaged binary several times
# is much slower than a unit test, so it gets its own generous timeout.
PACKAGING_TIMEOUT = 180  # seconds

# Tests whose inputs are NOT in git: licensed/large asset packs (assets/ is
# gitignored except two files) and docs generated by tools/generate_all_docs.sh.
# On a fresh clone these cannot pass, so the runner reports them as SKIP with
# the missing path -- counted separately, listed in the summary, never as a
# pass. This is deliberately a table here rather than self-skipping tests
# (those rotted unnoticed before, see #341/#350/#372), and only for inputs
# outside the repo: a test absent from this table still FAILs loudly.
# --no-skip turns every SKIP into a FAIL (for jobs that should have them all).
# Paths are relative to the project root.
_ASSET_PACK = "untracked asset pack (assets/ is gitignored)"
_GENERATED_DOCS = "generated docs: run tools/generate_all_docs.sh"
EXTERNAL_INPUTS = {
    "unit/animated_model_test.py": (["assets/models/RiggedSimple.glb", "assets/models/CesiumMan.glb"], _ASSET_PACK),
    "unit/audio_and_keyboard_test.py": (["assets/sfx/splat1.ogg"], _ASSET_PACK),
    "regression/issue_430_identity_tilesets_audio_test.py": (["assets/sfx/splat1.ogg"], _ASSET_PACK),
    "snippets/253_Music.py": (["assets/sfx/splat1.ogg"], _ASSET_PACK),
    "unit/generate_sprite_screenshot.py": (["assets/kenney_TD_MR_IP.png"], _ASSET_PACK),
    "unit/ui_Sprite_issue19_test.py": (["assets/kenney_TD_MR_IP.png"], _ASSET_PACK),
    "regression/issue_148_layer_dirty_flags.py": (["assets/kenney_TD_MR_IP.png"], _ASSET_PACK),
    "demo/skeletal_animation_demo.py": (["assets/models/RiggedSimple.glb", "assets/models/CesiumMan.glb"], _ASSET_PACK),
    "unit/test_api_docs.py": (["docs/API_REFERENCE_DYNAMIC.md"], _GENERATED_DOCS),
    "unit/test_stubs.py": (["stubs/mcrfpy.pyi"], _GENERATED_DOCS),
    "packaging/network_stdlib_packaged_windows_test.py": (["build-windows/mcrogueface.exe"], "needs a `make windows` build (and wine)"),
}


# Tests that legitimately run 6-13 s (subprocess `deps` installs, many screenshots) and so
# sit on the 10 s default's edge: they pass alone and time out under suite load (#513).
# Timeouts here are a per-test budget, not a flake mask: each is still bounded.
SLOW_TESTS = {
    "regression/issue_478_caption_baseline_test.py": 40,  # 2 s alone, 12 s at load 23 even after the PNG crop
    # 5-7 s alone (software-rendered screenshots; llvmpipe uses every core), 10-15 s with
    # several engines rendering at once under -j N.
    "regression/issue_536_visible_chunk_range_test.py": 40,
    "regression/issue_427_layer_edit_under_cache_test.py": 40,
    "regression/issue_446_entity_collection_dirty_test.py": 40,
    "regression/issue_539_chunk_vertex_array_test.py": 40,
    "regression/issue_529_first_frame_screenshot_test.py": 120,  # 20 child engines, half windowed: 19 s idle, ~55 s with all 8 cores busy
    "integration/mcrf_project_test.py": 40,
    # Near the 10 s limit with the machine to themselves (procgen_interactive 11 s,
    # uicaption_visual 8.5 s on arecibo), so any contention timed them out (CI 1997/1998).
    "unit/procgen_interactive_test.py": 40,
    "unit/test_uicaption_visual.py": 40,
    "regression/issue_402_observe_fov_isolation_test.py": 40,  # its loop deadlines scale too
    "integration/issue_509_deps_keeps_foreign_venv_test.py": 40,
    "integration/issue_517_console_scripts_test.py": 40,
    "integration/venv_pip_end_to_end_test.py": 90,
    "regression/issue_505_python_mode_test.py": 40,
    # FrameLock tests (#535): each runs in well under a second, but its hang detector
    # (30 s, or 20 s per child process) must be able to fire, and say "deadlock/hang",
    # before the runner's own timeout does. The tests scale their detectors by the same
    # MCRF_TIMEOUT_MULTIPLIER this table is multiplied by.
    "regression/issue_410_framelock_readmission_test.py": 120,
    "integration/frame_lock_hold_ordering_test.py": 120,
    "integration/frame_lock_stress_test.py": 120,
    "integration/frame_lock_soak_test.py": 120,
    "packaging/venv_packaged_test.py": 240,
    "packaging/issue_525_linux_closure_packaged_test.py": 240,  # builds the package (170s cap)
}

# Tests that do not fit one sanitizer variant (`--sanitizer=asan` for make asan-test,
# `--sanitizer=tsan` for make tsan-test): the test, not the engine, is what the instrumented
# build breaks. One table per variant, one reason per test, reported as SKIP in the summary.
# A key that names no test file is an error at runner start (a renamed test must not
# silently drop out of the table).
#
# asan: measured on `make asan-test` 2026-11-17 (#513): 737/745 with zero ASan/UBSan
# reports, these being the eight failures. tsan: nothing is skipped here; the FrameLock tests
# are exactly the thread tests TSan exists for. (Any engine whose Python has ABI flags,
# TSan's included, also skips ABI_FLAG_SKIPS below.)
_SAN_STDERR = ("asserts nothing on stderr, but LSan prints its \"Suppressions used\" table there; "
               "child engines also run the debug Python (3.15d)")
_SAN_DEPS = ("`mcrf_project deps` needs a packaging-capable engine, but the sanitizer engine "
             "is a Python 3.15d build; plus the stderr noise (see issue_505)")
SANITIZER_VARIANTS = ("asan", "tsan")
SANITIZER_SKIPS = {
    "asan": {
        "regression/issue_505_venv_prefix_test.py": _SAN_STDERR,
        "regression/issue_505_virtual_env_ignored_test.py": _SAN_STDERR,
        "integration/issue_517_console_scripts_test.py": _SAN_DEPS,
        "integration/issue_509_deps_keeps_foreign_venv_test.py": _SAN_DEPS,
        "unit/grid_observe_mask_test.py": "RSS-growth budget (4 MB over 5000 projections); ASan's quarantine grows RSS by ~200 MB",
        "regression/issue_421_frame_pointer_test.py": "times out (50 s) under ASan; it measures Release frame pointers, not memory safety",
    },
    "tsan": {},
}


# Tests that cannot hold on an engine whose Python is not a plain Release build (sys.abiflags
# non-empty: 'd' for `make debug`/asan, 't'/'td' for free-threaded/TSan). Found by asking the
# engine, so debug-test and valgrind-test (which have no --sanitizer) get them too. Reported
# as SKIP with the reason; same rules as SANITIZER_SKIPS (a key naming no test is an error).
_DEPS_RELEASE_ONLY = ("`mcrf_project deps` refuses an engine whose Python has ABI flags "
                      "(src/pylib/mcrf_project/deps.py): dependencies are installed for Release engines")
ABI_FLAG_SKIPS = {
    "integration/issue_509_deps_keeps_foreign_venv_test.py": _DEPS_RELEASE_ONLY,
    "integration/issue_517_console_scripts_test.py": _DEPS_RELEASE_ONLY,
}


def check_sanitizer_skip_tables():
    """Every SANITIZER_SKIPS / ABI_FLAG_SKIPS key must be an existing test file; returns the bad keys."""
    keys = [k for table in SANITIZER_SKIPS.values() for k in table] + list(ABI_FLAG_SKIPS)
    return sorted(k for k in keys if not (TESTS_DIR / k).is_file())


def engine_abiflags():
    """sys.abiflags of the engine's Python ('' for a Release build), asked of the engine itself."""
    env = os.environ.copy()
    existing_ld = env.get('LD_LIBRARY_PATH', '')
    env['LD_LIBRARY_PATH'] = f"{LIB_DIR}:{existing_ld}" if existing_ld else str(LIB_DIR)
    r = subprocess.run([str(MCROGUEFACE), '--headless', '-c', 'import sys; print("ABIFLAGS=" + sys.abiflags)'],
                       capture_output=True, text=True, timeout=60, cwd=str(BUILD_DIR), env=env)
    for line in r.stdout.splitlines():
        if line.startswith('ABIFLAGS='):
            return line[len('ABIFLAGS='):]
    raise RuntimeError(f"could not read sys.abiflags from {MCROGUEFACE} (rc={r.returncode}):\n"
                       f"{r.stdout}{r.stderr}")


def missing_external_inputs(test_dir, test_name):
    """(missing paths, reason) for a test in EXTERNAL_INPUTS, else ([], None)."""
    paths, reason = EXTERNAL_INPUTS.get(f"{test_dir}/{test_name}", ([], None))
    missing = [p for p in paths if not (TESTS_DIR.parent / p).exists()]
    return missing, (reason if missing else None)

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'

def get_screenshot_checksum(cwd):
    """Get checksums of test-generated PNG files in the test's working directory."""
    checksums = {}
    for png in Path(cwd).glob("test_*.png"):
        with open(png, 'rb') as f:
            checksums[png.name] = hashlib.md5(f.read()).hexdigest()[:8]
    return checksums

def check_sanitizer_output(output):
    """Check output for sanitizer error messages. Returns list of matches."""
    errors = []
    for pattern in SANITIZER_PATTERNS:
        matches = pattern.findall(output)
        if matches:
            errors.extend(matches)
    return errors

def run_test(test_path, verbose=False, timeout=DEFAULT_TIMEOUT,
             sanitizer_mode=False, valgrind_mode=False, cwd=None, extra_env=None):
    """Run a single test and return (passed, duration, output, sanitizer_errors).

    cwd: the engine's working directory (default BUILD_DIR; a parallel worker passes its own).
    extra_env: environment overrides on top of this process's (a parallel worker's DISPLAY).
    """
    start = time.time()
    cwd = Path(cwd) if cwd is not None else BUILD_DIR

    # Clean any existing screenshots
    for png in cwd.glob("test_*.png"):
        png.unlink()

    # Set up environment with library path
    env = os.environ.copy()
    for k, v in (extra_env or {}).items():
        if v is None:
            env.pop(k, None)
        else:
            env[k] = v
    # The engine reads no VIRTUAL_ENV (#505), but the tests' own child pythons might; keep
    # the shell's activated virtualenv out of them. The ones about VIRTUAL_ENV set it themselves.
    env.pop('VIRTUAL_ENV', None)
    existing_ld = env.get('LD_LIBRARY_PATH', '')
    env['LD_LIBRARY_PATH'] = f"{LIB_DIR}:{existing_ld}" if existing_ld else str(LIB_DIR)
    # Keep the committed demo gallery (tests/demo/screenshots/) out of suite runs
    env.setdefault('MCRF_DEMO_SCREENSHOT_DIR', str(BUILD_DIR / "demo-screenshots"))

    # Build the command
    cmd = []
    valgrind_log = None

    if valgrind_mode:
        valgrind_log = BUILD_DIR / f"valgrind-{test_path.stem}.log"
        supp_file = TESTS_DIR.parent / "sanitizers" / "valgrind-mcrf.supp"
        cmd.extend([
            'valgrind',
            '--tool=memcheck',
            '--leak-check=full',
            '--error-exitcode=42',
            f'--log-file={valgrind_log}',
        ])
        if supp_file.exists():
            cmd.append(f'--suppressions={supp_file}')

    cmd.extend([str(MCROGUEFACE), '--headless', '--exec', str(test_path)])

    # A snippet has no ending of its own; chain the harness to supply one.
    if test_path.parent.name == 'snippets':
        cmd.extend(['--exec', str(TESTS_DIR / 'snippets' / '_harness.py')])
    elif test_path.parent.name == DEMO_STANDALONE_DIR:
        cmd.extend(['--exec', str(TESTS_DIR.parent / DEMO_HARNESS)])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(cwd),
            env=env
        )
        duration = time.time() - start
        passed = result.returncode == 0
        output = result.stdout + result.stderr

        # An uncaught exception is never a pass. Exit code alone was not enough:
        # a script that raised during setup registered no timers, was auto-exited 0
        # by the engine, and was scored PASS -- 59 tests sat rotted this way, their
        # assertions never once executing. (#341/#350/#372)
        if 'Traceback (most recent call last)' in output:
            passed = False

        # Check for PASS/FAIL in output
        if 'FAIL' in output and 'PASS' not in output.split('FAIL')[-1]:
            passed = False

        # Check for sanitizer errors in output
        sanitizer_errors = []
        if sanitizer_mode:
            sanitizer_errors = check_sanitizer_output(output)
            if sanitizer_errors:
                passed = False

        # Check valgrind results
        if valgrind_mode:
            if result.returncode == 42:
                passed = False
                if valgrind_log and valgrind_log.exists():
                    vg_output = valgrind_log.read_text()
                    # Extract error summary
                    error_lines = [l for l in vg_output.split('\n')
                                   if 'ERROR SUMMARY' in l or 'definitely lost' in l
                                   or 'Invalid' in l]
                    sanitizer_errors.extend(error_lines[:5])
                    output += f"\n--- Valgrind log: {valgrind_log} ---\n"
                    output += '\n'.join(error_lines)

        return passed, duration, output, sanitizer_errors

    except subprocess.TimeoutExpired:
        return False, timeout, "TIMEOUT", []
    except Exception as e:
        return False, 0, str(e), []

def find_tests(directory):
    """Find all test files in a directory."""
    test_dir = TESTS_DIR / directory
    if not test_dir.exists():
        return []
    if directory == 'demo':
        # #372: allowlisted entry points only -- see DEMO_SMOKE_TESTS.
        found = [test_dir / name for name in DEMO_SMOKE_TESTS if (test_dir / name).exists()]
        return found + sorted((test_dir / DEMO_STANDALONE_DIR).glob("*.py"))
    # Leading underscore = support file, not a test (tests/snippets/_harness.py).
    return sorted(p for p in test_dir.glob("*.py") if not p.name.startswith('_'))

class Entry:
    """One test: what to run, its budget, and (once known) how it went."""
    __slots__ = ('dir', 'path', 'name', 'timeout', 'skip', 'skip_is_fail', 'result', 'cwd')

    def __init__(self, test_dir, path, timeout):
        self.dir, self.path, self.name, self.timeout = test_dir, path, path.name, timeout
        self.skip = None           # note, if this test is not run
        self.skip_is_fail = False  # --no-skip: the skip is a failure
        self.result = None         # (passed, duration, output, san_errors, checksum_str)
        self.cwd = None

    @property
    def key(self):
        return f"{self.dir}/{self.name}"


def plan_tests(dirs_to_test, effective_timeout, timeout_multiplier, no_skip,
               sanitizer_mode, sanitizer_variant, abiflags=''):
    """Every selected test, in (directory order, name order), with budgets and skips decided."""
    entries = []
    for test_dir in dirs_to_test:
        for test_path in find_tests(test_dir):
            test_name = test_path.name
            # Demos render several scenes; they need more headroom than a unit test.
            if test_dir == 'demo':
                test_timeout = DEMO_TIMEOUT * timeout_multiplier
            elif test_dir == 'packaging':
                test_timeout = PACKAGING_TIMEOUT * timeout_multiplier
            else:
                test_timeout = effective_timeout
                if f"{test_dir}/{test_name}" in SLOW_TESTS:
                    test_timeout = max(test_timeout, SLOW_TESTS[f"{test_dir}/{test_name}"] * timeout_multiplier)
            e = Entry(test_dir, test_path, test_timeout)
            missing, reason = missing_external_inputs(test_dir, test_name)
            if missing:
                e.skip = f"{reason}; missing {', '.join(missing)}"
                e.skip_is_fail = no_skip
            elif sanitizer_mode and e.key in SANITIZER_SKIPS[sanitizer_variant]:
                e.skip = (f"does not fit --sanitizer={sanitizer_variant}: "
                          f"{SANITIZER_SKIPS[sanitizer_variant][e.key]}")
            elif abiflags and e.key in ABI_FLAG_SKIPS:
                e.skip = f"engine Python is a '{abiflags}' build: {ABI_FLAG_SKIPS[e.key]}"
            entries.append(e)
    return entries


def parse_shard(text):
    m = re.fullmatch(r'(\d+)/(\d+)', text)
    if not m or not 1 <= int(m.group(1)) <= int(m.group(2)):
        raise argparse.ArgumentTypeError(f"expected i/n with 1 <= i <= n, got {text!r}")
    return int(m.group(1)), int(m.group(2))


def format_line(e, verbose):
    """The lines printed for one finished (or skipped) test."""
    if e.skip:
        if e.skip_is_fail:
            return [f"  {RED}FAIL{RESET} {e.name} (--no-skip: {e.skip})"]
        return [f"  {YELLOW}SKIP{RESET} {e.name} ({e.skip})"]
    passed, duration, output, san_errors, checksum_str = e.result
    status = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
    san_str = f" {RED}[SANITIZER]{RESET}" if san_errors else ""
    lines = [f"  {status} {e.name} ({duration:.2f}s){checksum_str}{san_str}"]
    if verbose and not passed:
        lines.append(f"    Output: {output[:200]}...")
        for err in san_errors[:3]:
            lines.append(f"    {RED}>> {err}{RESET}")
    return lines


# ---------------------------------------------------------------------------------------
# Parallel workers: private Xvfb servers and scratch working directories
# ---------------------------------------------------------------------------------------

def start_xvfb():
    """Start an Xvfb on a free display number (Xvfb picks it: -displayfd). Returns (proc, ':N')."""
    exe = shutil.which('Xvfb')
    if not exe:
        raise RuntimeError("-j needs Xvfb on PATH (apt install xvfb)")
    import ctypes
    import select
    libc = ctypes.CDLL(None)

    def die_with_parent():
        # An Xvfb must not outlive a runner that was SIGKILLed (the finally below cannot run).
        libc.prctl(1, signal.SIGTERM)  # PR_SET_PDEATHSIG

    r, w = os.pipe()
    try:
        proc = subprocess.Popen(
            [exe, '-displayfd', str(w), '-screen', '0', XVFB_SCREEN, '-noreset', '-nolisten', 'tcp'],
            pass_fds=(w,), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE, preexec_fn=die_with_parent, start_new_session=True)
    finally:
        os.close(w)
    try:
        deadline = time.time() + 30
        buf = b''
        while not buf.endswith(b'\n'):
            left = deadline - time.time()
            if left <= 0 or not select.select([r], [], [], left)[0]:
                proc.kill()
                proc.wait()
                raise RuntimeError("Xvfb did not report a display number within 30 s")
            chunk = os.read(r, 64)
            if not chunk:  # closed without a number: it exited
                err = proc.communicate()[1].decode(errors='replace').strip()
                raise RuntimeError(f"Xvfb exited (status {proc.returncode}) before it was ready: {err}")
            buf += chunk
    finally:
        os.close(r)
    return proc, ':' + buf.decode().strip()


def stop_xvfb(procs):
    for proc in procs:
        if proc.poll() is None:
            proc.terminate()
    for proc in procs:
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        if proc.stderr:
            proc.stderr.close()


def make_worker_dir(k):
    """A scratch directory that looks like BUILD_DIR to a test, and is private to worker k."""
    d = TESTS_DIR.parent / WORKER_DIR_FMT.format(k)
    if d.exists():
        shutil.rmtree(d)
    (d / 'tmp').mkdir(parents=True)
    for entry in sorted(BUILD_DIR.iterdir()):
        if entry.name in WORKER_LINKS or (entry.is_file() and os.access(entry, os.X_OK)):
            (d / entry.name).symlink_to(entry.resolve())
    return d


# Other ways a test could find the caller's desktop; None removes the variable.
NO_INHERITED_DISPLAY = {'XAUTHORITY': None, 'WAYLAND_DISPLAY': None}


def worker_env(display, workdir):
    """The environment overrides of one parallel worker."""
    env = {'DISPLAY': display, 'TMPDIR': str(workdir / 'tmp'), **NO_INHERITED_DISPLAY}
    return env


def main():
    ap = argparse.ArgumentParser(
        prog='run_tests.py', description="McRogueFace test runner: runs the headless test suite.",
        epilog="Environment: MCRF_BUILD_DIR (build directory), MCRF_LIB_DIR (libraries), "
               "MCRF_TIMEOUT_MULTIPLIER (scale every timeout).")
    ap.add_argument('dirs', nargs='*', metavar='DIR',
                    help=f"test directories to run (default: all of {', '.join(TEST_DIRS)})")
    ap.add_argument('-v', '--verbose', action='store_true', help="show failure details")
    ap.add_argument('--checksums', action='store_true', help="show screenshot checksums")
    ap.add_argument('--timeout', type=int, default=DEFAULT_TIMEOUT, metavar='N',
                    help=f"per-test timeout in seconds (default {DEFAULT_TIMEOUT})")
    ap.add_argument('--sanitizer', nargs='?', const='', default=None, metavar='asan|tsan',
                    help="detect sanitizer errors in output")
    ap.add_argument('--valgrind', action='store_true', help="run tests under Valgrind memcheck")
    ap.add_argument('--exclude', action='append', default=[], metavar='DIRS',
                    help="comma-separated directories to leave out")
    ap.add_argument('--no-skip', action='store_true',
                    help="tests with missing external inputs fail instead of SKIP")
    ap.add_argument('-j', '--jobs', type=int, default=1, metavar='N',
                    help="run N tests at once, each worker on its own Xvfb and scratch directory "
                         "(default 1: one at a time on the caller's DISPLAY)")
    ap.add_argument('--shard', type=parse_shard, default=None, metavar='I/N',
                    help="run only shard I of N (1-based): every N-th test of the sorted list")
    args = ap.parse_args()

    verbose = args.verbose
    show_checksums = args.checksums
    # The variant picks the skip table; a bare --sanitizer or an unknown value is an error
    # rather than a guess.
    sanitizer_variant = None
    if args.sanitizer is not None:
        if args.sanitizer not in SANITIZER_VARIANTS:
            print(f"{RED}--sanitizer needs a variant: --sanitizer={'|'.join(SANITIZER_VARIANTS)}{RESET}")
            sys.exit(2)
        sanitizer_variant = args.sanitizer
    sanitizer_mode = sanitizer_variant is not None
    stale = check_sanitizer_skip_tables()
    if stale:
        print(f"{RED}SANITIZER_SKIPS names tests that do not exist (renamed?): {', '.join(stale)}{RESET}")
        sys.exit(2)
    valgrind_mode = args.valgrind
    if args.jobs < 1:
        ap.error("-j needs at least 1")
    jobs = args.jobs

    # Apply timeout multiplier from environment
    timeout_multiplier = float(os.environ.get('MCRF_TIMEOUT_MULTIPLIER', '1'))
    effective_timeout = args.timeout * timeout_multiplier

    # --exclude=a,b -- drop whole directories from this run.
    #
    # Exists for the alternate-build targets (debug-test/asan-test/tsan-test/
    # valgrind-test). Those point MCRF_BUILD_DIR at build-debug/build-asan/build-tsan,
    # but tests/packaging/ drives tools/package.sh, which packages the RELEASE build/
    # no matter what the suite is driving -- so it is orthogonal to sanitizer coverage
    # and would fail outright in a job that never built build/. Excluding a directory
    # is deliberate and visible at the invocation site; it is not a test quietly
    # skipping itself, and the default run (and CI's release job) still includes
    # everything.
    excluded = [d.strip() for arg in args.exclude for d in arg.split(',') if d.strip()]
    unknown = [d for d in excluded if d not in TEST_DIRS]
    if unknown:
        print(f"{RED}Unknown directory in --exclude: {', '.join(unknown)}{RESET}")
        print(f"Known directories: {', '.join(TEST_DIRS)}")
        sys.exit(2)

    # Determine which directories to test (in TEST_DIRS order, however they were named)
    bad = [d for d in args.dirs if d not in TEST_DIRS]
    if bad:
        print(f"{RED}Unknown test directory: {', '.join(bad)}{RESET}")
        print(f"Known directories: {', '.join(TEST_DIRS)}")
        sys.exit(2)
    dirs_to_test = [d for d in TEST_DIRS if d in args.dirs] if args.dirs else list(TEST_DIRS)
    dirs_to_test = [d for d in dirs_to_test if d not in excluded]

    if not MCROGUEFACE.is_file():
        print(f"{RED}No engine at {MCROGUEFACE}: build one (make) or set MCRF_BUILD_DIR{RESET}")
        sys.exit(2)

    entries = plan_tests(dirs_to_test, effective_timeout, timeout_multiplier, args.no_skip,
                         sanitizer_mode, sanitizer_variant, engine_abiflags())
    if args.shard:
        idx, n = args.shard
        chosen = {e.key for pos, e in enumerate(sorted(entries, key=lambda e: e.key)) if pos % n == idx - 1}
        entries = [e for e in entries if e.key in chosen]

    # Header
    mode_str = ""
    if sanitizer_mode:
        mode_str = f" {YELLOW}[{'ASan/UBSan' if sanitizer_variant == 'asan' else 'TSan'}]{RESET}"
    elif valgrind_mode:
        mode_str = f" {YELLOW}[Valgrind]{RESET}"

    print(f"{BOLD}McRogueFace Test Runner{RESET}{mode_str}")
    print(f"Build: {BUILD_DIR}")
    print(f"Testing: {', '.join(dirs_to_test)} (timeout: {effective_timeout:.0f}s)")
    if jobs > 1:
        print(f"Jobs: {jobs} (private Xvfb each; serial afterwards: {', '.join(SERIAL_DIRS)})")
    if args.shard:
        print(f"Shard: {args.shard[0]}/{args.shard[1]} ({len(entries)} tests)")
    print("=" * 60)
    sys.stdout.flush()

    by_dir = {d: [e for e in entries if e.dir == d] for d in dirs_to_test}
    wall_start = time.time()

    def run_entry(e, cwd, extra_env):
        e.cwd = cwd
        passed, duration, output, san_errors = run_test(
            e.path, verbose, e.timeout, sanitizer_mode=sanitizer_mode,
            valgrind_mode=valgrind_mode, cwd=cwd, extra_env=extra_env)
        checksum_str = ""
        if show_checksums:
            checksums = get_screenshot_checksum(cwd)
            if checksums:
                checksum_str = f" [{', '.join(f'{k}:{v}' for k,v in checksums.items())}]"
        e.result = (passed, duration, output, san_errors, checksum_str)

    def emit_group(test_dir):
        print(f"\n{BOLD}{test_dir}/{RESET} ({len(by_dir[test_dir])} tests)")
        for e in by_dir[test_dir]:
            for line in format_line(e, verbose):
                print(line)
        sys.stdout.flush()

    def is_done(e):
        return e.skip is not None or e.result is not None

    if jobs == 1:
        # The original behaviour: one test at a time in BUILD_DIR, output as it happens.
        for test_dir in dirs_to_test:
            if not by_dir[test_dir]:
                continue
            print(f"\n{BOLD}{test_dir}/{RESET} ({len(by_dir[test_dir])} tests)")
            for e in by_dir[test_dir]:
                if e.skip is None:
                    run_entry(e, BUILD_DIR, None)
                for line in format_line(e, verbose):
                    print(line)
                sys.stdout.flush()
    else:
        xvfbs, displays, workdirs = [], [], []
        old_term = signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
        stop = threading.Event()
        try:
            for k in range(jobs):
                proc, display = start_xvfb()
                xvfbs.append(proc)
                displays.append(display)
                workdirs.append(make_worker_dir(k))

            parallel = [e for e in entries if e.skip is None and e.dir not in SERIAL_DIRS]
            # Longest budgets first, so a 120 s test does not start last and set the wall time.
            work = queue.Queue()
            for e in sorted(parallel, key=lambda e: -e.timeout):
                work.put(e)
            finished = queue.Queue()

            def worker(k):
                env = worker_env(displays[k], workdirs[k])
                while not stop.is_set():
                    try:
                        e = work.get_nowait()
                    except queue.Empty:
                        return
                    try:
                        run_entry(e, workdirs[k], env)
                    except BaseException as exc:  # a runner bug: report it, never hang the collector
                        e.result = (False, 0, f"runner error: {exc!r}", [], "")
                    finished.put(e)

            threads = [threading.Thread(target=worker, args=(k,), daemon=True) for k in range(jobs)]
            for t in threads:
                t.start()

            order = [d for d in dirs_to_test if by_dir[d]]
            printed = 0

            def flush_ready():
                nonlocal printed
                while printed < len(order) and all(is_done(e) for e in by_dir[order[printed]]):
                    emit_group(order[printed])
                    printed += 1

            flush_ready()
            for _ in range(len(parallel)):
                finished.get()
                flush_ready()

            # Serial phase: in BUILD_DIR itself, one test at a time, on worker 0's display.
            serial_env = {'DISPLAY': displays[0], **NO_INHERITED_DISPLAY}
            for e in entries:
                if e.skip is None and e.dir in SERIAL_DIRS:
                    run_entry(e, BUILD_DIR, serial_env)
            flush_ready()
        finally:
            stop.set()
            signal.signal(signal.SIGTERM, old_term)
            stop_xvfb(xvfbs)
            for d in workdirs:
                shutil.rmtree(d, ignore_errors=True)
    wall = time.time() - wall_start

    # Summary, from the entries in plan order (so it is the same however the run interleaved)
    results = {'pass': 0, 'fail': 0, 'skip': 0, 'total_time': 0}
    failures = []
    skipped = []
    for e in entries:
        if e.skip:
            if e.skip_is_fail:
                results['fail'] += 1
                failures.append((e.dir, e.name, f"--no-skip: {e.skip}", []))
            else:
                results['skip'] += 1
                skipped.append((e.dir, e.name, e.skip))
            continue
        passed, duration, output, san_errors, _ = e.result
        results['total_time'] += duration
        if passed:
            results['pass'] += 1
        else:
            results['fail'] += 1
            failures.append((e.dir, e.name, output, san_errors))

    print("\n" + "=" * 60)
    total = results['pass'] + results['fail']
    pass_rate = (results['pass'] / total * 100) if total > 0 else 0

    skip_str = f", {results['skip']} skipped" if results['skip'] else ""
    print(f"{BOLD}Results:{RESET} {results['pass']}/{total} passed ({pass_rate:.1f}%){skip_str}")
    print(f"{BOLD}Time:{RESET} {results['total_time']:.2f}s")
    if jobs > 1:
        print(f"{BOLD}Wall:{RESET} {wall:.2f}s ({jobs} jobs)")

    if valgrind_mode:
        print(f"{BOLD}Valgrind logs:{RESET} {BUILD_DIR}/valgrind-*.log")

    if skipped:
        print(f"\n{YELLOW}{BOLD}Skipped (missing inputs: --no-skip fails them; sanitizer skips: SANITIZER_SKIPS):{RESET}")
        for test_dir, test_name, note in skipped:
            print(f"  {test_dir}/{test_name}: {note}")

    if failures:
        print(f"\n{RED}{BOLD}Failures:{RESET}")
        for test_dir, test_name, output, san_errors in failures:
            print(f"  {test_dir}/{test_name}")
            if san_errors:
                for err in san_errors[:3]:
                    print(f"    {RED}>> {err}{RESET}")
            # The complete output of every failing test, whatever -v says: a CI log is all
            # there is to diagnose a failure from, and its last five lines rarely name the
            # check that failed.
            for line in output.rstrip().split('\n'):
                print(f"    {line}")

    sys.exit(0 if results['fail'] == 0 else 1)

if __name__ == '__main__':
    main()
