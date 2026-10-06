"""The mcrogueface binary must locate its bundled libraries relative to itself.

CMake's default build RPATH bakes the absolute link directories of the build
machine (__lib/, plus any -DCMAKE_LIBRARY_PATH prefix) into DT_RUNPATH, and the
intended INSTALL_RPATH ($ORIGIN/./lib) only applies to `make install`, which the
packaging flow never runs. A shipped binary then found libpython/SFML/libtcod
only via run.sh's LD_LIBRARY_PATH, and on the build machine silently loaded
__lib/ instead of the package's own lib/.

Invariant: every DT_RUNPATH/DT_RPATH entry is $ORIGIN-relative.
"""
import shutil
import subprocess
import sys

exe = sys.executable
readelf = shutil.which("readelf")
if readelf is None:
    print("FAIL: readelf (binutils) not found; cannot inspect", exe)
    sys.exit(1)

out = subprocess.run([readelf, "-d", exe], capture_output=True, text=True)
if out.returncode != 0:
    print("FAIL: readelf -d failed:", out.stderr.strip())
    sys.exit(1)

entries = []
for line in out.stdout.splitlines():
    if "(RUNPATH)" in line or "(RPATH)" in line:
        # 0x...1d (RUNPATH)  Library runpath: [a:b]
        entries += line.split("[", 1)[1].rstrip("]").split(":")

entries = [e for e in entries if e]
if not entries:
    print("FAIL: %s has no RUNPATH; it cannot find its bundled lib/ directory" % exe)
    sys.exit(1)

bad = [e for e in entries if not e.startswith("$ORIGIN")]
if bad:
    print("FAIL: non-relocatable RUNPATH entries in %s: %r" % (exe, bad))
    sys.exit(1)

print("RUNPATH:", entries)
print("PASS")
sys.exit(0)
