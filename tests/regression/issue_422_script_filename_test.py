"""Regression test for #422 - script tracebacks reported File "<string>".

Both script entry points read the file into memory and ran it with PyRun_SimpleString,
so the code object's co_filename was "<string>": tracebacks lost the path, linecache
couldn't show source lines, and the perf trampoline named frames ":<string>".

Checked for both entry points, as a subprocess so each gets a fresh __main__:
  mcrogueface --headless --exec script.py
  mcrogueface --headless script.py
"""
import os
import subprocess
import sys
import tempfile

# This file's own code object is the --exec path under test.
here = sys._getframe().f_code.co_filename
failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


check(here == __file__ and here.endswith("issue_422_script_filename_test.py"),
      "--exec: co_filename is the script path (%r)" % here)

engine = sys.executable
with tempfile.TemporaryDirectory() as tmp:
    script = os.path.join(tmp, "raises_422.py")
    with open(script, "w") as f:
        # The script mode keeps running the engine after an uncaught error, so the
        # script formats its own traceback and exits.
        f.write("import sys, traceback\n"
                "print('co_filename=' + sys._getframe().f_code.co_filename)\n"
                "def f():\n"
                "    raise ValueError('boom 422')\n"
                "try:\n"
                "    f()\n"
                "except ValueError:\n"
                "    traceback.print_exc(file=sys.stdout)\n"
                "sys.exit(0)\n")
    env = dict(os.environ, ALSOFT_DRIVERS="null")
    for args in (["--headless", "--exec", script], ["--headless", script]):
        try:
            out = subprocess.run([engine] + args, capture_output=True, text=True,
                                 timeout=30, env=env, cwd=os.path.dirname(engine))
        except subprocess.TimeoutExpired:
            check(False, "%s finished" % " ".join(args[:-1]))
            continue
        text = out.stdout + out.stderr
        mode = " ".join(args[:-1])
        check(out.returncode == 0, "%s: exits 0 (%d)" % (mode, out.returncode))
        check("co_filename=" + script in text, "%s: co_filename is the path" % mode)
        check('File "%s", line 4, in f' % script in text,
              "%s: traceback names the file and line" % mode)
        check("raise ValueError('boom 422')" in text,
              "%s: traceback shows the source line" % mode)
        check('File "<string>"' not in text, "%s: no <string> frames" % mode)

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
