"""#498: an unpacked engine package must be able to `import pydoc` / `sysconfig`.

CPython's sysconfig imports `_sysconfigdata_*` (a .py file) from the extension-module
directory; the package filtered that directory to *.so and shipped without it. This
stages a package with `mcrf_project package-engine`, runs the PACKAGED binary from a
temp dir outside the source tree, and checks sysconfig answers from inside the package.
"""
import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "build" / "mcrogueface"

PROBE = """
import sys, sysconfig, pydoc
assert sysconfig.get_config_var('SOABI'), 'no SOABI'
print('PROBE_OK', sysconfig.get_path('stdlib'))
sys.exit(0)
"""


def fail(msg):
    print("FAIL: " + msg)
    sys.exit(1)


with tempfile.TemporaryDirectory() as tmp:
    out = Path(tmp) / "out"
    r = subprocess.run([str(ENGINE), "-m", "mcrf_project", "package-engine",
                        "--version", "0.0.0-test", "--out", str(out)],
                       capture_output=True, text=True, timeout=170)
    if r.returncode != 0:
        fail("package-engine failed:\n" + r.stdout + r.stderr)
    archive = out / "McRogueFace-0.0.0-test-Linux.tar.gz"
    with tarfile.open(archive) as tf:
        tf.extractall(out, filter="data")
    pkg = out / "McRogueFace-0.0.0-test-Linux"
    env = {k: v for k, v in os.environ.items()
           if k not in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP")}
    env["LD_LIBRARY_PATH"] = str(pkg / "lib")
    env["ALSOFT_DRIVERS"] = "null"
    r = subprocess.run(["./mcrogueface", "--headless", "-c", PROBE], cwd=pkg, env=env,
                       capture_output=True, text=True, timeout=60)
    text = r.stdout + r.stderr
    if r.returncode != 0 or "PROBE_OK" not in text:
        fail("packaged binary could not import pydoc/sysconfig:\n" + text[-1500:])
print("PASS")
sys.exit(0)
