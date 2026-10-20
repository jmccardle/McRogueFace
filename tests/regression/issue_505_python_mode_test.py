"""Regression test for #505 - a `python*` basename means "plain interpreter".

pip console-script shebangs (`#!ENV/bin/python`) cannot carry flags, so when argv[0]'s
basename starts with `python` the engine behaves as CPython does: `python script.py arg`
runs the script headless and EXITS (before, it fell through to the game loop and hung).

  python script.py arg            runs, exits 0, sys.argv == [script, arg]
  python raising.py               nonzero exit, traceback on stderr
  python --run-forever script.py  overrides the exit: stays up until killed
  mcrogueface --headless script.py   (non-python name) is still game mode: it does NOT
                                  exit by itself (a script that returns hands over to
                                  the frame loop), so the runner has to kill it

Both a venv's ENV/bin/python and a bare symlink named `python` beside an engine are covered.
Every layout is private to the test (copied binary + symlinks), never build/.
"""
import os
import shutil
import subprocess
import sys
import tempfile

failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


real_engine = os.path.realpath(sys.executable)
real_dir = os.path.dirname(real_engine)
ENGINE_NAME = os.path.basename(real_engine)
STDLIB_DIRNAME = "python%d.%d%s" % (sys.version_info[0], sys.version_info[1], sys.abiflags)

# Long enough for a cold interpreter start under load, short enough to keep the suite fast.
EXIT_TIMEOUT = 5      # a script that should exit
STAY_UP_TIMEOUT = 3   # a script that should NOT exit

OK_SCRIPT = ("import sys\n"
             "print('MARK505 argv=%r file=%s' % (sys.argv, __file__))\n")
RAISE_SCRIPT = "raise ValueError('boom505')\n"


def make_engine(root):
    os.makedirs(root)
    e = os.path.realpath(root)
    exe = os.path.join(e, ENGINE_NAME)
    shutil.copy2(real_engine, exe)
    for name in ("lib", "assets", "scripts"):
        os.symlink(os.path.join(real_dir, name), os.path.join(e, name))
    return e


def run(argv, cwd, timeout):
    """(returncode or None if it was still running at the timeout, stdout, stderr)"""
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    env["ALSOFT_DRIVERS"] = "null"
    p = subprocess.Popen(argv, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         text=True)
    try:
        out, err = p.communicate(timeout=timeout)
        return p.returncode, out, err
    except subprocess.TimeoutExpired:
        p.kill()
        out, err = p.communicate()
        return None, out, err


def python_mode_checks(label, python, cwd):
    script = os.path.join(cwd, "ok505.py")
    rc, out, err = run([python, script, "arg1"], cwd, EXIT_TIMEOUT)
    check(rc == 0, "%s: `python script.py arg` exits 0 by itself (rc=%r)" % (label, rc))
    check("MARK505" in out, "%s: script ran and printed its marker (%r)" % (label, out[:120]))
    check(("argv=%r" % [script, "arg1"]) in out, "%s: sys.argv == [script, 'arg1'] (%r)" % (label, out[:200]))
    check(("file=" + script) in out, "%s: __file__ is the script path" % label)

    rc, out, err = run([python, os.path.join(cwd, "raise505.py")], cwd, EXIT_TIMEOUT)
    check(rc is not None and rc != 0, "%s: a raising script exits nonzero (rc=%r)" % (label, rc))
    check("ValueError: boom505" in err and "Traceback" in err,
          "%s: the traceback is on stderr" % label)
    # (the runner scores any output containing a traceback as a failure, so it is not echoed on success)
    if not ("ValueError: boom505" in err and "Traceback" in err):
        print("FAIL: stderr was: %r" % err[-200:])

    rc, out, err = run([python, "--run-forever", script], cwd, STAY_UP_TIMEOUT)
    check(rc is None and "MARK505" in out,
          "%s: --run-forever overrides the exit (rc=%r, ran=%r)" % (label, rc, "MARK505" in out))


with tempfile.TemporaryDirectory() as tmp:
    tmp = os.path.realpath(tmp)
    for name, body in (("ok505.py", OK_SCRIPT), ("raise505.py", RAISE_SCRIPT)):
        with open(os.path.join(tmp, name), "w") as f:
            f.write(body)

    # --- a bare symlink named python next to the engine, no venv ------------------------------
    e = make_engine(os.path.join(tmp, "bare"))
    os.symlink(ENGINE_NAME, os.path.join(e, "python"))
    python_mode_checks("bare python symlink", os.path.join(e, "python"), tmp)

    # --- ENV/bin/python in a hand-made venv ---------------------------------------------------
    e = make_engine(os.path.join(tmp, "engine"))
    env_dir = os.path.join(tmp, "ENV")
    os.makedirs(os.path.join(env_dir, "bin"))
    os.makedirs(os.path.join(env_dir, "lib", STDLIB_DIRNAME, "site-packages"))
    with open(os.path.join(env_dir, "pyvenv.cfg"), "w") as f:
        f.write("home = %s\ninclude-system-site-packages = false\nversion = %d.%d.%d\n"
                % (e, sys.version_info[0], sys.version_info[1], sys.version_info[2]))
    os.symlink(os.path.join(e, ENGINE_NAME), os.path.join(env_dir, "bin", ENGINE_NAME))
    os.symlink(ENGINE_NAME, os.path.join(env_dir, "bin", "python"))
    python_mode_checks("venv ENV/bin/python", os.path.join(env_dir, "bin", "python"), tmp)

    # --- non-python basename: a script is still game mode -------------------------------------
    script = os.path.join(tmp, "ok505.py")
    rc, out, err = run([os.path.join(e, ENGINE_NAME), "--headless", script], tmp, STAY_UP_TIMEOUT)
    check("MARK505" in out, "game mode: the script ran (%r)" % out[:120])
    check(rc is None, "game mode: `mcrogueface script.py` does not exit by itself (rc=%r)" % rc)

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
