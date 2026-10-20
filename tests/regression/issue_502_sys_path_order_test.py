"""Regression test for #502 - the engine's sys.path order is documented and asserted.

The order (docs/sys-path-order.md), for an engine directory E:

  --exec        [E/venv site-packages]  E/scripts  <extension dir>  E/lib/Python  E/lib/Python/Lib
  game / script [script dir]            [E/venv site-packages]  <extension dir>  E/lib/Python  E/lib/Python/Lib

The sibling `E/venv/lib/python3.X/site-packages` is honoured only if that directory exists
(a bare E/venv is ignored). In game/script mode the main script's directory replaces
E/scripts (#452). Every layout here is private to the test: it never depends on what
happens to sit next to the binary under test.
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
env = dict(os.environ, ALSOFT_DRIVERS="null")
# the engine's venv layout dir name, e.g. python3.15 or python3.15t
STDLIB_DIRNAME = "python%d.%d%s" % (sys.version_info[0], sys.version_info[1],
                                    "t" if sysconfig.get_config_var("Py_GIL_DISABLED") else "")

PROBE = "import json, sys\nprint('SYSPATH ' + json.dumps(sys.path))\nsys.exit(0)\n"


def make_engine(root, venv_site_packages=False, bare_venv=False):
    """A private engine directory: copied binary + symlinks to the read-only runtime dirs."""
    os.makedirs(root)
    e = os.path.realpath(root)
    exe = os.path.join(e, os.path.basename(real_engine))
    shutil.copy2(real_engine, exe)
    for name in ("lib", "assets", "scripts"):
        os.symlink(os.path.join(real_dir, name), os.path.join(e, name))
    sp = os.path.join(e, "venv", "lib", STDLIB_DIRNAME, "site-packages")
    if venv_site_packages:
        os.makedirs(sp)
    elif bare_venv:
        os.makedirs(os.path.join(e, "venv"))
    return e, exe, sp


def sys_path(exe, args, cwd):
    out = subprocess.run([exe, "--headless"] + args, capture_output=True, text=True,
                         timeout=30, env=env, cwd=cwd)
    for line in out.stdout.splitlines():
        if line.startswith("SYSPATH "):
            return json.loads(line[len("SYSPATH "):])
    print(out.stdout, out.stderr)
    return None


def index_of(path, entry):
    return path.index(entry) if entry in path else -1


with tempfile.TemporaryDirectory() as tmp:
    probe = os.path.join(tmp, "scripts_dir", "probe.py")
    os.makedirs(os.path.dirname(probe))
    with open(probe, "w") as f:
        f.write(PROBE)
    script_dir = os.path.dirname(probe)

    # --- no venv at all -------------------------------------------------------------
    e, exe, sp = make_engine(os.path.join(tmp, "plain"))
    p = sys_path(exe, ["--exec", probe], tmp)
    check(p is not None, "plain: --exec prints sys.path")
    if p:
        order = [index_of(p, e + "/scripts"), index_of(p, e + "/lib/Python"), index_of(p, e + "/lib/Python/Lib")]
        check(p[0] == e + "/scripts", "plain --exec: E/scripts first (%r)" % p[:2])
        check(all(i >= 0 for i in order) and order == sorted(order),
              "plain --exec: E/scripts < E/lib/Python < E/lib/Python/Lib (%r)" % order)
        check(not any(x.startswith(e + "/venv") for x in p), "plain --exec: no venv entry")
    p = sys_path(exe, [probe], tmp)
    check(p is not None and p[0] == script_dir, "plain script mode: script dir first (%r)" % (p and p[:2]))
    check(p is not None and (e + "/scripts") not in p, "plain script mode: E/scripts is replaced, not kept")
    check(p is not None and (e + "/lib/Python/Lib") in p, "plain script mode: stdlib still present")

    # --- sibling venv with site-packages -----------------------------------------------
    e, exe, sp = make_engine(os.path.join(tmp, "withvenv"), venv_site_packages=True)
    p = sys_path(exe, ["--exec", probe], tmp)
    check(p is not None and p[:2] == [sp, e + "/scripts"],
          "venv --exec: sibling site-packages, then E/scripts (%r)" % (p and p[:2]))
    p = sys_path(exe, [probe], tmp)
    check(p is not None and p[:2] == [script_dir, sp],
          "venv script mode: script dir, then sibling site-packages (%r)" % (p and p[:2]))

    # --- a bare venv/ (no site-packages) is ignored --------------------------------------
    e, exe, sp = make_engine(os.path.join(tmp, "barevenv"), bare_venv=True)
    p = sys_path(exe, ["--exec", probe], tmp)
    check(p is not None and p[0] == e + "/scripts" and not any(x.startswith(e + "/venv") for x in p),
          "bare venv/ without site-packages is ignored (%r)" % (p and p[:2]))

    # --- engine inside a venv (pyvenv.cfg one level above the binary) ---------------------
    # #505: getpath finds the venv from the launch path and site.py (not the engine) adds its
    # site-packages, after the stdlib; a sibling E/venv site-packages is still first. (Before
    # #505 the engine prepended it ahead of E/scripts; the order is now CPython's.)
    root = os.path.join(tmp, "invenv")
    os.makedirs(root)
    with open(os.path.join(root, "pyvenv.cfg"), "w") as f:
        f.write("home = /usr/bin\n")
    e, exe, sp = make_engine(os.path.join(root, "bin"), venv_site_packages=True)
    parent_sp = os.path.join(os.path.realpath(root), "lib", STDLIB_DIRNAME, "site-packages")
    os.makedirs(parent_sp)
    p = sys_path(exe, ["--exec", probe], tmp)
    check(p is not None and p[:2] == [sp, e + "/scripts"],
          "pyvenv.cfg above binary: sibling sp, E/scripts first (%r)" % (p and p[:2]))
    check(p is not None and p.count(parent_sp) == 1 and
          index_of(p, parent_sp) > index_of(p, e + "/lib/Python/Lib"),
          "pyvenv.cfg above binary: venv sp once, after the stdlib (%r)" % (p and p[-3:]))

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
