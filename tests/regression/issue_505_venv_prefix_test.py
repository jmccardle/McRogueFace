"""Regression test for #505 - the engine finds a PEP 405 venv from its UNRESOLVED launch path.

`mcrogueface -m venv ENV` makes ENV/bin/{mcrogueface,python} symlinks to the engine plus a
pyvenv.cfg. Launched through one of those links the engine must behave as CPython does:
getpath looks for pyvenv.cfg beside (or one directory above) the unresolved executable path
(argv[0] made absolute lexically, or found on PATH when it has no slash; never realpath'd):

  sys.executable       == ENV/bin/<name used to launch>
  sys.prefix           == ENV
  sys.base_prefix      == E/lib/Python          (E = the real engine directory)
  sys._base_executable == the real engine binary
  ENV/lib/python3.X/site-packages is on sys.path once, after the stdlib (site.py adds it)
  sysconfig purelib/scripts are under ENV; site.py prints nothing to stderr

A venv also isolates from the engine's sibling E/venv/ (the engine's equivalent of the base
interpreter's site-packages): with `include-system-site-packages = false` (the default) its
site-packages is not on sys.path; with `= true` it is, as when launched directly.

Without a pyvenv.cfg the same symlink leaves sys.prefix at E/lib/Python. The venv here is
hand-made (no pip, no network) inside a private engine directory; nothing touches build/.
"""
import json
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
# the engine's own venv layout dir name, e.g. python3.15 or python3.15t
STDLIB_DIRNAME = "python%d.%d%s" % (sys.version_info[0], sys.version_info[1], sys.abiflags)

PROBE = (
    "import json, sys, sysconfig\n"
    "try:\n"
    "    import fake505mod; marker = fake505mod.VALUE\n"
    "except ImportError:\n"
    "    marker = None\n"
    "print('INFO ' + json.dumps({\n"
    "    'executable': sys.executable, 'prefix': sys.prefix, 'base_prefix': sys.base_prefix,\n"
    "    'base_executable': sys._base_executable, 'path': sys.path,\n"
    "    'purelib': sysconfig.get_path('purelib'), 'scripts': sysconfig.get_path('scripts'),\n"
    "    'marker': marker}))\n"
    "sys.exit(0)\n"
)


def make_engine(root):
    """A private engine directory: copied binary + symlinks to the read-only runtime dirs."""
    os.makedirs(root)
    e = os.path.realpath(root)
    exe = os.path.join(e, ENGINE_NAME)
    shutil.copy2(real_engine, exe)
    for name in ("lib", "assets", "scripts"):
        os.symlink(os.path.join(real_dir, name), os.path.join(e, name))
    return e, exe


def make_venv(root, engine_dir, cfg=True):
    """What `-m venv` writes: pyvenv.cfg, bin/ symlinks, and a site-packages with a marker."""
    os.makedirs(root)
    env_dir = os.path.realpath(root)
    if cfg:
        with open(os.path.join(env_dir, "pyvenv.cfg"), "w") as f:
            f.write("home = %s\ninclude-system-site-packages = false\nversion = %d.%d.%d\n"
                    % (engine_dir, sys.version_info[0], sys.version_info[1], sys.version_info[2]))
    bin_dir = os.path.join(env_dir, "bin")
    os.makedirs(bin_dir)
    os.symlink(os.path.join(engine_dir, ENGINE_NAME), os.path.join(bin_dir, ENGINE_NAME))
    os.symlink(ENGINE_NAME, os.path.join(bin_dir, "python"))
    sp = os.path.join(env_dir, "lib", STDLIB_DIRNAME, "site-packages")
    os.makedirs(sp)
    with open(os.path.join(sp, "fake505mod.py"), "w") as f:
        f.write("VALUE = 505\n")
    return env_dir, sp


def run(argv, cwd, path=None, executable=None):
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    env["ALSOFT_DRIVERS"] = "null"
    if path is not None:
        env["PATH"] = path
    try:
        return subprocess.run(argv, executable=executable, capture_output=True, text=True,
                              timeout=30, env=env, cwd=cwd)
    except subprocess.TimeoutExpired as ex:
        print("TIMEOUT", argv)
        return None


def info(out):
    if out is None:
        return None
    for line in out.stdout.splitlines():
        if line.startswith("INFO "):
            return json.loads(line[len("INFO "):])
    print(out.stdout, out.stderr)
    return None


def under(path, root):
    return path is not None and os.path.commonpath([os.path.abspath(path), root]) == root


def check_venv_launch(label, i, env_dir, sp, e, launched):
    check(i is not None, "%s: probe ran and printed its info" % label)
    if i is None:
        return
    check(i["executable"] == launched, "%s: sys.executable is the unresolved launch path (%r)" % (label, i["executable"]))
    check(i["prefix"] == env_dir, "%s: sys.prefix == ENV (%r)" % (label, i["prefix"]))
    check(i["base_prefix"] == e + "/lib/Python", "%s: sys.base_prefix == E/lib/Python (%r)" % (label, i["base_prefix"]))
    check(i["base_executable"] == os.path.join(e, ENGINE_NAME),
          "%s: sys._base_executable is the real engine (%r)" % (label, i["base_executable"]))
    p = i["path"]
    check(p.count(sp) == 1, "%s: venv site-packages on sys.path exactly once (%r)" % (label, p.count(sp)))
    stdlib = e + "/lib/Python/Lib"
    check(stdlib in p and sp in p and p.index(sp) > p.index(stdlib),
          "%s: venv site-packages comes after the stdlib entry (%r)" % (label, p))
    check(i["marker"] == 505, "%s: marker module imports from the venv" % label)
    check(under(i["purelib"], env_dir), "%s: sysconfig purelib under ENV (%r)" % (label, i["purelib"]))
    check(under(i["scripts"], env_dir), "%s: sysconfig scripts under ENV (%r)" % (label, i["scripts"]))


with tempfile.TemporaryDirectory() as tmp:
    tmp = os.path.realpath(tmp)
    e, exe = make_engine(os.path.join(tmp, "engine"))
    env_dir, sp = make_venv(os.path.join(tmp, "ENV"), e)
    cmd = ["-c", PROBE]

    # --- launched by absolute path through each symlink name -------------------------------
    for name in ("python", ENGINE_NAME):
        launched = os.path.join(env_dir, "bin", name)
        out = run([launched] + cmd, tmp)
        check_venv_launch("abs ENV/bin/" + name, info(out), env_dir, sp, e, launched)
        check(out is not None and out.stderr == "", "abs ENV/bin/%s: nothing on stderr (%r)" % (name, out and out.stderr))

    # --- launched relative to the cwd (argv[0] has a slash, not absolute) -------------------
    launched = os.path.join(env_dir, "bin", "python")
    out = run(["./bin/python"] + cmd, env_dir)
    check_venv_launch("relative ./bin/python", info(out), env_dir, sp, e, launched)

    # --- launched by PATH lookup: argv[0] is the bare name "python" --------------------------
    out = run(["python"] + cmd, tmp, path=os.path.join(env_dir, "bin"))
    check_venv_launch("PATH lookup 'python'", info(out), env_dir, sp, e, launched)
    check(out is not None and out.stderr == "", "PATH lookup 'python': nothing on stderr (%r)" % (out and out.stderr))

    # --- negative: the same symlink without pyvenv.cfg is not a venv -----------------------
    e2, exe2 = make_engine(os.path.join(tmp, "engine2"))
    env2, sp2 = make_venv(os.path.join(tmp, "NOCFG"), e2, cfg=False)
    out = run([os.path.join(env2, "bin", "python"), "-c",
               "import sys; print('INFO ' + __import__('json').dumps({'prefix': sys.prefix, 'path': sys.path}))"], tmp)
    i = info(out)
    check(i is not None and i["prefix"] == e2 + "/lib/Python",
          "no pyvenv.cfg: sys.prefix stays E/lib/Python (%r)" % (i and i["prefix"]))
    check(i is not None and sp2 not in i["path"], "no pyvenv.cfg: ENV site-packages is not on sys.path")

    # --- an argv[0] that names no file (exec with a made-up name) is the real binary --------
    out = run(["python-not-on-path-505"] + cmd, tmp, path="/nonexistent",
              executable=os.path.join(env_dir, "bin", "python"))
    i = info(out)
    check(out is not None and out.returncode == 0, "argv[0] not on PATH: still starts (%r)" % (out and out.stderr))
    check(i is not None and i["executable"] == os.path.join(e, ENGINE_NAME),
          "argv[0] not on PATH: sys.executable is the real engine (%r)" % (i and i["executable"]))

# --- the sibling E/venv/ is the engine's "system site-packages" ----------------------------
SIB_PROBE = ("import sys\n"
             "try:\n"
             "    import sibling505mod; found = True\n"
             "except ImportError:\n"
             "    found = False\n"
             "print('SIB %s %s' % (found, sys.prefix != sys.base_prefix))\n"
             "sys.exit(0)\n")


def sibling_result(out):
    for line in (out.stdout if out else "").splitlines():
        if line.startswith("SIB "):
            return line[4:]
    print(out and out.stdout, out and out.stderr)
    return None


with tempfile.TemporaryDirectory() as tmp:
    tmp = os.path.realpath(tmp)
    e, exe = make_engine(os.path.join(tmp, "engine"))
    sib = os.path.join(e, "venv", "lib", STDLIB_DIRNAME, "site-packages")
    os.makedirs(sib)
    with open(os.path.join(sib, "sibling505mod.py"), "w") as f:
        f.write("VALUE = 1\n")
    env_dir, sp = make_venv(os.path.join(tmp, "ENV"), e)
    cfg = os.path.join(env_dir, "pyvenv.cfg")

    out = run([exe, "-c", SIB_PROBE], tmp)
    check(sibling_result(out) == "True False", "launched directly: E/venv/ imports (%r)" % sibling_result(out))
    for mode in ("--exec",):
        script = os.path.join(tmp, "sib.py")
        with open(script, "w") as f:
            f.write(SIB_PROBE)
        out = run([exe, "--headless", "--exec", script], tmp)
        check(sibling_result(out) == "True False", "launched directly, --exec: E/venv/ imports")

    venv_python = os.path.join(env_dir, "bin", "python")
    out = run([venv_python, "-c", SIB_PROBE], tmp)
    check(sibling_result(out) == "False True",
          "through a venv (include-system-site-packages = false): E/venv/ is not visible (%r)" % sibling_result(out))
    check(out is not None and out.stderr == "", "through a venv: nothing on stderr")
    out = run([venv_python, "--headless", "--exec", script], tmp)
    check(sibling_result(out) == "False True", "through a venv, --exec: E/venv/ is not visible")

    with open(cfg) as f:
        text = f.read()
    with open(cfg, "w") as f:
        f.write(text.replace("include-system-site-packages = false", "include-system-site-packages = true"))
    out = run([venv_python, "-c", SIB_PROBE], tmp)
    check(sibling_result(out) == "True True",
          "through a venv with include-system-site-packages = true: E/venv/ is visible (%r)" % sibling_result(out))
    out = run([venv_python, "--headless", "--exec", script], tmp)
    check(sibling_result(out) == "True True", "include-system-site-packages = true, --exec: visible")

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
