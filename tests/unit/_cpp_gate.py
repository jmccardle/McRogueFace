"""Helper for tests that gate a standalone C++ test (not a test itself: leading underscore).

Compiles SOURCE (relative to tests/unit/) with the system C++ compiler into a temp dir, runs
the binary and returns its exit status. A missing compiler, a compile error, or a failing
binary is a failure with the output shown -- never a skip."""
import os
import shutil
import subprocess
import sys
import tempfile

UNIT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(os.path.dirname(os.path.dirname(UNIT_DIR)), "src")


def run(source, defines=(), compile_timeout=120, run_timeout=30):
    cxx = os.environ.get("CXX") or shutil.which("c++") or shutil.which("g++") or shutil.which("clang++")
    if not cxx:
        print("FAIL: no C++ compiler found (tried $CXX, c++, g++, clang++); "
              "this gate compiles %s" % source)
        return 1
    with tempfile.TemporaryDirectory() as tmp:
        exe = os.path.join(tmp, "gate")
        cmd = [cxx, "-std=c++17", "-I", SRC_DIR] + ["-D" + d for d in defines] + \
              [os.path.join(UNIT_DIR, source), "-o", exe]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=compile_timeout)
        if r.returncode != 0:
            print("FAIL: compiling %s:\n%s%s" % (source, r.stdout, r.stderr))
            return 1
        r = subprocess.run([exe], capture_output=True, text=True, timeout=run_timeout)
        sys.stdout.write(r.stdout)
        sys.stderr.write(r.stderr)
        if r.returncode != 0:
            print("FAIL: %s exited with status %d" % (source, r.returncode))
            return 1
    print("PASS")
    return 0
