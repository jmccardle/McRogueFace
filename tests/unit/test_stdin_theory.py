#!/usr/bin/env python3
"""Test that a --exec script never falls through into an interactive REPL

Original intent: "is stdin the reason the >>> prompt appears after my script runs?"
The script tried closing / redirecting stdin and then eyeballed the terminal for a
">>>" prompt. It asserted nothing and never stated an exit status.

Current contract: --exec scripts are run non-interactively. The engine never hands
stdin to the Python REPL, whether or not stdin is open, and whether or not the
script exits cleanly. That is verified here in child processes that are *given* a
readable stdin containing Python source: if the interpreter ever went interactive,
it would echo ">>>" and execute the fed-in line.
"""
import mcrfpy
import os
import subprocess
import sys

failures = []
scratch = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       "..", "..", "build"))

print("=== Testing stdin theory ===")
print("stdin.isatty(): %s" % sys.stdin.isatty())
print("stdin fileno: %s" % sys.stdin.fileno())

# A --exec script is not interactive even though stdin is a real, readable fd.
if sys.stdin.isatty():
    failures.append("--exec script should not have a tty on stdin")

# Set up a basic scene (the original script did this to have the engine "live")
stdin_test = mcrfpy.Scene("stdin_test")
stdin_test.activate()
if mcrfpy.current_scene is not stdin_test:
    failures.append("scene.activate() did not set mcrfpy.current_scene")

# --- 1. stdin fed Python source is NOT evaluated as a REPL ---------------------
# sys.executable is the mcrogueface binary itself.
FED = "print('REPL_LEAKED')\n"

child_exit = os.path.join(scratch, "_stdin_theory_child_exit.py")
child_fallthrough = os.path.join(scratch, "_stdin_theory_child_fallthrough.py")
with open(child_exit, "w") as f:
    f.write("import mcrfpy\nimport sys\nprint('CHILD_RAN')\nsys.exit(0)\n")
with open(child_fallthrough, "w") as f:
    # Deliberately falls off the end: the historical case where >>> showed up.
    f.write("import mcrfpy\nprint('CHILD_RAN')\n")

for name, path, expect_zero in (("clean-exit", child_exit, True),
                                ("fall-through", child_fallthrough, False)):
    try:
        proc = subprocess.run(
            [sys.executable, "--headless", "--exec", path],
            cwd=scratch, input=FED, capture_output=True, text=True, timeout=20)
    except subprocess.TimeoutExpired:
        failures.append("%s child hung: it is waiting on stdin (interactive mode)" % name)
        continue

    out = proc.stdout + proc.stderr
    if "CHILD_RAN" not in out:
        failures.append("%s child never ran the script" % name)
    if ">>>" in out:
        failures.append("%s child printed a >>> prompt: --exec went interactive" % name)
    if "REPL_LEAKED" in out:
        failures.append("%s child executed source fed on stdin: --exec went interactive"
                        % name)
    if expect_zero and proc.returncode != 0:
        failures.append("%s child should exit 0, got %d" % (name, proc.returncode))
    if not expect_zero and proc.returncode == 0:
        failures.append("fall-through child should exit nonzero (#350 exit contract)")

for path in (child_exit, child_fallthrough):
    if os.path.exists(path):
        os.remove(path)

# --- 2. The stdin manipulations the original script tried still work ----------
# (They are unnecessary -- part 1 proves stdin was never the cause -- but the engine
#  must not be destabilized by a script that closes or redirects fd 0.)
print("\nAttempting the original stdin manipulations...")
sys.stdin.close()
print("Closed sys.stdin")

devnull = open(os.devnull, 'r')
os.dup2(devnull.fileno(), 0)
print("Redirected stdin to /dev/null")

# Engine is still alive and steppable after fd 0 was yanked out from under it.
mcrfpy.step(0.016)
if mcrfpy.current_scene is not stdin_test:
    failures.append("engine lost its scene after stdin was closed/redirected")

if failures:
    for f in failures:
        print("FAIL: %s" % f)
    sys.exit(1)

print("PASS")
sys.exit(0)
