#!/usr/bin/env python3
"""libghostty-vt is linked into the engine (#550, build plumbing only).

`mcrogueface --version` reports the version of the statically linked libghostty-vt, read
through ghostty_version(). The pin is modules/ghostty (vt-1.0.1 plus Emscripten commits), so
a version that is not 1.0.1 means the wrong checkout was built.
"""
import subprocess
import sys

proc = subprocess.run([sys.executable, "--version"], capture_output=True, text=True, timeout=20)
if proc.returncode != 0:
    print("FAIL: --version exited %d: %s" % (proc.returncode, proc.stderr))
    sys.exit(1)
lines = [l for l in proc.stdout.splitlines() if l.startswith("libghostty-vt ")]
if len(lines) != 1:
    print("FAIL: expected one 'libghostty-vt <version>' line in --version output, got:\n%s" % proc.stdout)
    sys.exit(1)
version = lines[0].split(" ", 1)[1]
# "1.0.1" or a dev build of it ("1.0.1-dev+abc"): the pinned release line.
if not version.startswith("1.0.1"):
    print("FAIL: libghostty-vt reports %r, expected 1.0.1" % version)
    sys.exit(1)
print("PASS: libghostty-vt %s" % version)
sys.exit(0)
