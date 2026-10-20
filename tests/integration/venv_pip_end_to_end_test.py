"""#505: a real venv made by the engine, and pip working in it, end to end.

    <engine> -m venv ENV                  -> ENV/bin/python (a PEP 405 venv, with pip)
    ENV/bin/python -m pip install wheel   -> lands in ENV, never in the engine's own tree
    ENV/bin/<console script>              -> runs under ENV/bin/python and EXITS

The wheel is built here with zipfile (no network: --no-index --no-deps). It holds a pure
module and a [console_scripts] entry point, so pip writes the script itself: a shebang
`#!ENV/bin/python` (or pip's /bin/sh re-exec form when that path is long). That script only
works if `python <script>` is a plain interpreter (it exits instead of starting the game
loop) and the venv's `python` finds ENV (sys.prefix, site-packages) the way CPython does.

The engine layout is private to the test (copied binary + symlinks to the read-only runtime
dirs), and a snapshot of that tree -- following the symlinks into the real lib/ and scripts/
dirs, which is exactly what must not change -- is compared before and after.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


final_check = []


def finish():
    for fn in final_check:
        fn()
    if failures:
        print("FAIL: %d check(s) failed" % len(failures))
        sys.exit(1)
    print("PASS")
    sys.exit(0)


def need(cond, msg, detail=""):
    """A step the rest depends on: report and stop at the first failure."""
    check(cond, msg)
    if not cond:
        if detail:
            print(detail)
        finish()


real_engine = os.path.realpath(sys.executable)
real_dir = os.path.dirname(real_engine)
env = {k: v for k, v in os.environ.items()
       if k not in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV", "DISPLAY", "WAYLAND_DISPLAY")}
env["ALSOFT_DRIVERS"] = "null"
env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
env["PIP_NO_INPUT"] = "1"

NAME = "demo505"
MARKER = "DEMO505-MARKER-7f3a"


def make_engine(root):
    """A private engine directory: copied binary + symlinks to the read-only runtime dirs."""
    os.makedirs(root)
    e = os.path.realpath(root)
    exe = os.path.join(e, os.path.basename(real_engine))
    shutil.copy2(real_engine, exe)
    for name in ("lib", "assets", "scripts"):
        os.symlink(os.path.join(real_dir, name), os.path.join(e, name))
    return e, exe


def snapshot(e):
    """{relative path: (mtime_ns, size)} of E, following the symlinks into the real dirs.
    __pycache__ is left out: the interpreter may legitimately cache bytecode of its own
    stdlib; what must not appear is anything pip or venv installed."""
    snap = {}
    for top in ("lib", "scripts"):
        for dirpath, dirnames, filenames in os.walk(os.path.join(e, top), followlinks=True):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for n in dirnames + filenames:
                p = os.path.join(dirpath, n)
                st = os.stat(p)
                snap[os.path.relpath(p, e)] = (st.st_mtime_ns, st.st_size)
    return snap


def run(argv, timeout, cwd):
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout, env=env, cwd=cwd)


def out_of(r):
    return "rc=%d\n--- stdout ---\n%s--- stderr ---\n%s" % (r.returncode, r.stdout, r.stderr)


def make_wheel(path):
    info = "%s-1.0.dist-info" % NAME
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("%s.py" % NAME, "VALUE = 505\n")
        zf.writestr("%s_cli.py" % NAME,
                    "import sys\n"
                    "def main():\n"
                    "    print('EXE ' + sys.executable)\n"
                    "    print('PREFIX ' + sys.prefix)\n"
                    "    print('%s')\n"
                    "    return 0\n" % MARKER)
        zf.writestr("%s/METADATA" % info, "Metadata-Version: 2.1\nName: %s\nVersion: 1.0\n" % NAME)
        zf.writestr("%s/WHEEL" % info, "Wheel-Version: 1.0\nGenerator: test\nRoot-Is-Purelib: true\n"
                                       "Tag: py3-none-any\n")
        zf.writestr("%s/entry_points.txt" % info,
                    "[console_scripts]\n%s = %s_cli:main\n" % (NAME, NAME))
        zf.writestr("%s/RECORD" % info, "")


with tempfile.TemporaryDirectory() as tmp:
    tmp = os.path.realpath(tmp)
    e, exe = make_engine(os.path.join(tmp, "engine"))
    venv = os.path.join(tmp, "ENV")
    vpy = os.path.join(venv, "bin", "python")
    wheel = os.path.join(tmp, "%s-1.0-py3-none-any.whl" % NAME)
    make_wheel(wheel)
    before = snapshot(e)
    check(len(before) > 100, "engine tree snapshot is not empty (%d entries)" % len(before))

    # --- nothing was written into the engine's tree (checked on every exit path, so registered up front)
    def engine_tree_unchanged():
        after = snapshot(e)
        added = sorted(set(after) - set(before))
        removed = sorted(set(before) - set(after))
        changed = sorted(k for k in set(before) & set(after) if before[k] != after[k])
        check(not (added or removed or changed),
              "engine tree unchanged (added %d, removed %d, modified %d)"
              % (len(added), len(removed), len(changed)))
        for label, items in (("added", added), ("removed", removed), ("modified", changed)):
            for k in items[:10]:
                print("  %s: %s" % (label, k))
        # The engine's lib/ is a symlink into the real build tree: a failing run must not
        # leave pip or the wheel behind there for the next test to trip over.
        for k in sorted(added, reverse=True):
            p = os.path.join(e, k)
            if os.path.islink(p) or os.path.isfile(p):
                os.unlink(p)
            elif os.path.isdir(p):
                shutil.rmtree(p, ignore_errors=True)

    final_check.append(engine_tree_unchanged)

    # --- create the venv, with pip (ensurepip from the bundled wheel) -----------------------
    r = run([exe, "-m", "venv", venv], 120, tmp)
    need(r.returncode == 0, "-m venv ENV exits 0", out_of(r))
    need(os.path.exists(vpy), "ENV/bin/python exists", out_of(r))
    check(os.path.isfile(os.path.join(venv, "pyvenv.cfg")), "ENV/pyvenv.cfg exists")

    # --- install the wheel with the venv's own pip -------------------------------------------
    r = run([vpy, "-m", "pip", "install", "--no-index", "--no-deps", wheel], 120, tmp)
    need(r.returncode == 0, "ENV/bin/python -m pip install --no-index --no-deps <wheel> exits 0",
         out_of(r))

    # --- the module is importable from the venv, and from there only -------------------------
    r = run([vpy, "-c", "import %s, sys; print(%s.VALUE); print(%s.__file__)" % (NAME, NAME, NAME)],
            30, tmp)
    check(r.returncode == 0 and r.stdout.split("\n")[0] == "505",
          "ENV/bin/python -c imports the installed module", )
    if r.returncode != 0:
        print(out_of(r))
    mod_file = r.stdout.split("\n")[1] if r.returncode == 0 and "\n" in r.stdout else ""
    check(os.path.realpath(mod_file).startswith(os.path.realpath(venv) + os.sep),
          "the module lives under ENV (%s)" % mod_file)

    # --- the console script pip wrote ---------------------------------------------------------
    script = os.path.join(venv, "bin", NAME)
    need(os.path.isfile(script), "ENV/bin/%s exists" % NAME)
    with open(script, "rb") as f:
        lines = f.read().decode().splitlines()
    shebang = lines[0]
    want = "#!" + vpy
    # pip falls back to a /bin/sh re-exec when the shebang would be too long
    sh_form = shebang == "#!/bin/sh" and any(vpy in l for l in lines[1:4])
    check(shebang == want or sh_form,
          "console script shebang is %r (or pip's sh re-exec of it); got %r" % (want, shebang))
    check(os.access(script, os.X_OK), "console script is executable")

    # --- running it: under ENV, exits on its own ----------------------------------------------
    try:
        r = run([script], 20, tmp)
        timed_out = False
    except subprocess.TimeoutExpired as ex:
        timed_out = True
        r = None
        print("--- partial stdout ---\n%s" % (ex.stdout or b""))
    check(not timed_out, "ENV/bin/%s exits by itself (did not start the game loop)" % NAME)
    if r is not None:
        if r.returncode != 0:
            print(out_of(r))
        check(r.returncode == 0, "ENV/bin/%s exits 0" % NAME)
        lines_out = dict(l.split(" ", 1) for l in r.stdout.splitlines() if " " in l)
        exe_out = lines_out.get("EXE", "")
        prefix_out = lines_out.get("PREFIX", "")
        check(MARKER in r.stdout, "the entry point ran (marker printed)")
        check(exe_out.startswith(venv + os.sep), "sys.executable is inside ENV (%s)" % exe_out)
        check(os.path.realpath(prefix_out) == os.path.realpath(venv),
              "sys.prefix is ENV (%s)" % prefix_out)

    # --- pip sees it, and can remove it -------------------------------------------------------
    r = run([vpy, "-m", "pip", "list"], 60, tmp)
    check(r.returncode == 0 and NAME in r.stdout, "pip list shows %s" % NAME)
    if r.returncode != 0 or NAME not in r.stdout:
        print(out_of(r))
    r = run([vpy, "-m", "pip", "uninstall", "-y", NAME], 60, tmp)
    check(r.returncode == 0, "pip uninstall -y %s exits 0" % NAME)
    if r.returncode != 0:
        print(out_of(r))
    check(not os.path.exists(script), "uninstall removed ENV/bin/%s" % NAME)
    r = run([vpy, "-c", "import %s" % NAME], 30, tmp)
    check(r.returncode != 0, "the module no longer imports after uninstall")


    finish()
