"""sys.exit() inside a callback is how a game quits (a key handler on Escape, a timer).
Every callback dispatcher printed "<kind> callback raised an exception:" before handing
the SystemExit to PyErr_Print(), which then exits: a bogus error line on every quit.
Now sys.exit() exits quietly with its status, and a real exception keeps the header."""
import os
import subprocess
import sys

failures = []


def check(cond, msg):
    print(("ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


def run(body):
    script = "import mcrfpy, sys\nfrom mcrfpy import automation\n" + body
    env = dict(os.environ, ALSOFT_DRIVERS="null")
    out = subprocess.run([sys.executable, "--headless", "-c", script], capture_output=True,
                         text=True, timeout=30, env=env, cwd=os.path.dirname(sys.executable))
    return out.returncode, out.stderr


rc, err = run("""
mcrfpy.Timer("t", lambda t, r: sys.exit(3), 10)
for _ in range(5): mcrfpy.step(0.02)
""")
check(rc == 3, f"sys.exit(3) in a timer exits with 3 (rc={rc})")
check("raised an exception" not in err, "no error header for sys.exit() in a timer")

rc, err = run("""
s = mcrfpy.Scene("k"); mcrfpy.current_scene = s
s.on_key = lambda k, st: sys.exit(4)
automation.keyDown("escape"); mcrfpy.step(0.02)
""")
check(rc == 4, f"sys.exit(4) in a key handler exits with 4 (rc={rc})")
check("raised an exception" not in err, "no error header for sys.exit() in a key handler")

rc, err = run("""
def bad(t, r):
    t.stop()
    raise ValueError("boom")
mcrfpy.Timer("t", bad, 10)
for _ in range(3): mcrfpy.step(0.02)
sys.exit(0)
""")
check("Timer callback raised an exception:" in err and "ValueError: boom" in err,
      "a real exception still gets the header and traceback")

if failures:
    sys.exit(1)
print("PASS")
sys.exit(0)
