#!/usr/bin/env python3
"""Test that mcrfpy.exit() shuts the engine down instead of leaving it running

Original intent: "does calling mcrfpy.exit() prevent the >>> prompt?" -- i.e. does
exit() actually terminate the application rather than falling through into an
interactive/never-ending loop?

Current contract (#350): mcrfpy.exit() calls GameEngine::quit(); it stops the run
loop. It is NOT a SystemExit -- the Python script keeps executing after it, and a
headless --exec script still states its own outcome with sys.exit().  So the real
"did exit() work?" question is answered in a child process that DOES enter the run
loop (--run-forever): with exit() it must terminate; without it, it must not.
"""
import mcrfpy
import os
import subprocess
import sys

failures = []
scratch = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "build")
scratch = os.path.abspath(scratch)

# --- 1. exit() is a no-arg call returning None; it does not abort the interpreter ---
print("Calling mcrfpy.exit() immediately...")
result = mcrfpy.exit()
print("This still prints: exit() quits the engine, it does not raise SystemExit")

if result is not None:
    failures.append("mcrfpy.exit() should return None, got %r" % (result,))

try:
    mcrfpy.exit(1)
except TypeError:
    pass
else:
    failures.append("mcrfpy.exit() takes no arguments; exit(1) should raise TypeError")

# --- 2. exit() really stops the run loop (the ">>> prompt"/hang the test was about) ---
child_exit = os.path.join(scratch, "_exit_immediately_child_exit.py")
child_stay = os.path.join(scratch, "_exit_immediately_child_stay.py")
with open(child_exit, "w") as f:
    f.write("import mcrfpy\nmcrfpy.exit()\n")
with open(child_stay, "w") as f:
    f.write("import mcrfpy\n")

try:
    # sys.executable is the mcrogueface binary itself.
    proc = subprocess.run(
        [sys.executable, "--headless", "--run-forever", "--exec", child_exit],
        cwd=scratch, capture_output=True, text=True, timeout=20)
    if proc.returncode != 0:
        failures.append("exit() child should terminate cleanly, got returncode %d"
                        % proc.returncode)
except subprocess.TimeoutExpired:
    failures.append("exit() did not stop the run loop: --run-forever child hung")

# Control: without exit(), --run-forever must keep the process alive. This proves the
# check above is actually observing exit(), not just a run loop that always ends.
try:
    subprocess.run(
        [sys.executable, "--headless", "--run-forever", "--exec", child_stay],
        cwd=scratch, capture_output=True, text=True, timeout=5)
    failures.append("control child (no exit()) terminated on its own; "
                    "the exit() check above proves nothing")
except subprocess.TimeoutExpired:
    pass  # expected: still running

for path in (child_exit, child_stay):
    if os.path.exists(path):
        os.remove(path)

if failures:
    for f in failures:
        print("FAIL: %s" % f)
    sys.exit(1)

print("PASS")
sys.exit(0)
