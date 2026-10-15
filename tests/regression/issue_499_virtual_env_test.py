"""Regression test for #499 - the engine honours an activated virtualenv (VIRTUAL_ENV).

Rule (docs/sys-path-order.md): if VIRTUAL_ENV is set, `$VIRTUAL_ENV/lib/python3.X/site-packages`
goes on sys.path after the main script directory and before the sibling E/venv entry. It must
have a pyvenv.cfg and that directory must exist, or the engine exits with an error naming the
path (no fallback). Unset: nothing changes. The engine never guesses `.venv`/`venv` names.

Every layout is a private engine directory (copied binary + symlinks), never build/.
"""
import json
import os
import shutil
import subprocess
import sys
import sysconfig
import tempfile

failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


real_engine = os.path.realpath(sys.executable)
real_dir = os.path.dirname(real_engine)
STDLIB_DIRNAME = "python%d.%d%s" % (sys.version_info[0], sys.version_info[1],
                                    "t" if sysconfig.get_config_var("Py_GIL_DISABLED") else "")
SP_REL = os.path.join("lib", STDLIB_DIRNAME, "site-packages")
PROBE = ("import json, sys\n"
         "import fake499mod\n"
         "print('SYSPATH ' + json.dumps(sys.path))\n"
         "print('MODFILE ' + fake499mod.__file__)\n"
         "sys.exit(0)\n")
PROBE_NOIMPORT = "import json, sys\nprint('SYSPATH ' + json.dumps(sys.path))\nsys.exit(0)\n"


def make_engine(root, sibling_venv=False):
    os.makedirs(root)
    e = os.path.realpath(root)
    exe = os.path.join(e, os.path.basename(real_engine))
    shutil.copy2(real_engine, exe)
    for name in ("lib", "assets", "scripts"):
        os.symlink(os.path.join(real_dir, name), os.path.join(e, name))
    sp = os.path.join(e, "venv", SP_REL)
    if sibling_venv:
        os.makedirs(sp)
    return e, exe, sp


def make_venv(root, cfg=True, site_packages=True):
    os.makedirs(root)
    root = os.path.realpath(root)
    if cfg:
        with open(os.path.join(root, "pyvenv.cfg"), "w") as f:
            f.write("home = /usr/bin\n")
    sp = os.path.join(root, SP_REL)
    if site_packages:
        os.makedirs(sp)
        with open(os.path.join(sp, "fake499mod.py"), "w") as f:
            f.write("VALUE = 499\n")
    return root, sp


def run(exe, args, cwd, virtual_env):
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    env["ALSOFT_DRIVERS"] = "null"
    if virtual_env is not None:
        env["VIRTUAL_ENV"] = virtual_env
    return subprocess.run([exe, "--headless"] + args, capture_output=True, text=True,
                          timeout=30, env=env, cwd=cwd)


def sys_path(out):
    for line in out.stdout.splitlines():
        if line.startswith("SYSPATH "):
            return json.loads(line[len("SYSPATH "):])
    print(out.stdout, out.stderr)
    return None


with tempfile.TemporaryDirectory() as tmp:
    probe = os.path.join(tmp, "game", "probe.py")
    os.makedirs(os.path.dirname(probe))
    with open(probe, "w") as f:
        f.write(PROBE)
    script_dir = os.path.dirname(probe)
    probe2 = os.path.join(tmp, "game", "noimport.py")
    with open(probe2, "w") as f:
        f.write(PROBE_NOIMPORT)

    # --- VIRTUAL_ENV set: importable, ordered ---------------------------------------
    venv, vsp = make_venv(os.path.join(tmp, "venv_a"))
    e, exe, sibling_sp = make_engine(os.path.join(tmp, "eng1"), sibling_venv=True)
    out = run(exe, [probe], tmp, venv)
    p = sys_path(out)
    check(out.returncode == 0 and p is not None, "script mode with VIRTUAL_ENV runs")
    check("MODFILE " + os.path.join(vsp, "fake499mod.py") in out.stdout, "module in VIRTUAL_ENV is importable")
    if p:
        check(p[:3] == [script_dir, vsp, sibling_sp],
              "order: script dir, VIRTUAL_ENV, sibling venv (%r)" % p[:3])
        check(p.count(vsp) == 1, "VIRTUAL_ENV entry appears once")
    out = run(exe, ["--exec", probe], tmp, venv)
    p = sys_path(out)
    check(p is not None and p[:3] == [vsp, sibling_sp, e + "/scripts"],
          "--exec order: VIRTUAL_ENV, sibling venv, E/scripts (%r)" % (p and p[:3]))

    # --- unset: unchanged --------------------------------------------------------------
    e, exe, _ = make_engine(os.path.join(tmp, "eng2"))
    out = run(exe, [probe2], tmp, None)
    p = sys_path(out)
    check(p is not None and not any("site-packages" in x for x in p),
          "unset: no site-packages entry (%r)" % (p and p[:3]))
    check(p is not None and p[0] == script_dir, "unset: script dir first")

    # --- missing pyvenv.cfg: fail early ------------------------------------------------
    nocfg, _ = make_venv(os.path.join(tmp, "venv_nocfg"), cfg=False)
    out = run(exe, [probe2], tmp, nocfg)
    check(out.returncode != 0, "no pyvenv.cfg: nonzero exit (got %d)" % out.returncode)
    check("SYSPATH" not in out.stdout, "no pyvenv.cfg: the script did not run")
    check(nocfg in out.stderr and "pyvenv.cfg" in out.stderr and "VIRTUAL_ENV" in out.stderr,
          "no pyvenv.cfg: error names VIRTUAL_ENV, path and pyvenv.cfg (%r)" % out.stderr[:300])

    # --- missing site-packages: fail early ---------------------------------------------
    nosp, nosp_sp = make_venv(os.path.join(tmp, "venv_nosp"), site_packages=False)
    out = run(exe, [probe2], tmp, nosp)
    check(out.returncode != 0, "no site-packages: nonzero exit (got %d)" % out.returncode)
    check("SYSPATH" not in out.stdout, "no site-packages: the script did not run")
    check(nosp_sp in out.stderr, "no site-packages: error names the directory (%r)" % out.stderr[:300])
    out = run(exe, ["--exec", probe2], tmp, nosp)
    check(out.returncode != 0 and nosp_sp in out.stderr, "no site-packages (--exec): also fails early")

    # --- nonexistent VIRTUAL_ENV directory ----------------------------------------------
    missing = os.path.join(tmp, "does_not_exist")
    out = run(exe, [probe2], tmp, missing)
    check(out.returncode != 0 and missing in out.stderr, "nonexistent VIRTUAL_ENV: fails naming it")

    # --- the engine never guesses .venv / venv ------------------------------------------
    guess, _ = make_venv(os.path.join(tmp, "game", ".venv"))
    out = run(exe, [probe2], os.path.join(tmp, "game"), None)
    p = sys_path(out)
    check(p is not None and not any(x.startswith(guess) for x in p), "an unannounced ./.venv is not looked at")

    # --- same directory as the pyvenv.cfg-above-binary rule: added once -----------------
    root = os.path.join(tmp, "invenv")
    vroot, vsp2 = make_venv(root)
    e, exe, _ = make_engine(os.path.join(root, "bin"))
    out = run(exe, ["--exec", probe], tmp, vroot)
    p = sys_path(out)
    check(p is not None and p.count(vsp2) == 1,
          "engine in venv + VIRTUAL_ENV same venv: listed once (%r)" % (p and p[:3]))

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
