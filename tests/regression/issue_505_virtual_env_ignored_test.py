"""Regression test for #505 - the engine does not read VIRTUAL_ENV at all.

CPython doesn't read VIRTUAL_ENV; a venv is found from the launch path (pyvenv.cfg beside, or
one directory above, the unresolved executable path). #499/#510 had the engine honour
VIRTUAL_ENV, ignore it for packaged games, and complain about it; #505 removes all of that.
This replaces issue_499_virtual_env_test.py and issue_510_virtual_env_policy_test.py, whose
contract (honour / ignore-with-a-note / hard error) no longer exists.

  * VIRTUAL_ENV naming a valid venv, an invalid directory, a missing path, or a venv for
    another Python changes nothing: same sys.path, same sys.prefix, exit status 0, nothing on
    stderr -- in script/--exec mode and in game mode (scripts/game.py), plain and packaged.
  * --use-virtual-env is an unknown option.
  * mcrfpy.config.virtual_env is None outside a venv and the venv's directory inside one;
    use_virtual_env and virtual_env_ignored no longer exist.

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
ENGINE_NAME = os.path.basename(real_engine)
PY = "%d.%d" % sys.version_info[:2]
OURS = "python" + PY + ("t" if sysconfig.get_config_var("Py_GIL_DISABLED") else "")
PROBE = ("import json, sys, mcrfpy\n"
         "try:\n"
         "    import fake505env; where = fake505env.WHERE\n"
         "except ImportError:\n"
         "    where = None\n"
         "c = mcrfpy.config\n"
         "print('RESULT ' + json.dumps({'where': where, 'path': sys.path, 'prefix': sys.prefix,\n"
         "      've': c.virtual_env, 'use': hasattr(c, 'use_virtual_env'),\n"
         "      'ignored': hasattr(c, 'virtual_env_ignored')}))\n"
         "sys.exit(0)\n")


def make_engine(root, packaged=False):
    """A private engine dir whose scripts/game.py is the probe (game mode)."""
    os.makedirs(root)
    e = os.path.realpath(root)
    exe = os.path.join(e, ENGINE_NAME)
    shutil.copy2(real_engine, exe)
    for name in ("lib", "assets"):
        os.symlink(os.path.join(real_dir, name), os.path.join(e, name))
    os.makedirs(os.path.join(e, "scripts"))
    with open(os.path.join(e, "scripts", "game.py"), "w") as f:
        f.write(PROBE)
    if packaged:
        with open(os.path.join(e, "mcrf-game.json"), "w") as f:
            f.write('{"game": "t", "version": "0"}\n')
    return e, exe


def make_venv(root, cfg_lines, libdir=OURS):
    """A venv-shaped directory with fake505env in its site-packages. No bin/: it is only ever
    named by VIRTUAL_ENV, never launched through."""
    os.makedirs(root)
    root = os.path.realpath(root)
    with open(os.path.join(root, "pyvenv.cfg"), "w") as f:
        f.write("home = /usr/bin\n" + "".join(l + "\n" for l in cfg_lines))
    sp = os.path.join(root, "lib", libdir, "site-packages")
    os.makedirs(sp)
    with open(os.path.join(sp, "fake505env.py"), "w") as f:
        f.write("WHERE = 'VIRTUAL_ENV'\n")
    return root


def run(argv, cwd, virtual_env=None):
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    env["ALSOFT_DRIVERS"] = "null"
    if virtual_env is not None:
        env["VIRTUAL_ENV"] = virtual_env
    return subprocess.run(argv, capture_output=True, text=True, timeout=30, env=env, cwd=cwd)


def result(out):
    for line in out.stdout.splitlines():
        if line.startswith("RESULT "):
            return json.loads(line[len("RESULT "):])
    print(out.stdout[-800:], out.stderr[-800:])
    return None


with tempfile.TemporaryDirectory() as tmp:
    tmp = os.path.realpath(tmp)
    probe = os.path.join(tmp, "probe.py")
    with open(probe, "w") as f:
        f.write(PROBE)

    valid = make_venv(os.path.join(tmp, "valid"), ["version = %s.0" % PY])
    foreign = make_venv(os.path.join(tmp, "foreign"), ["version = 3.11.4"], "python3.11")
    plain_dir = os.path.join(tmp, "plain")
    os.makedirs(plain_dir)
    venvs = (("a valid venv", valid), ("a venv for another Python", foreign),
             ("a directory that is no venv", plain_dir),
             ("a path that does not exist", os.path.join(tmp, "missing")))

    for pkg_label, packaged in (("plain", False), ("packaged", True)):
        e, exe = make_engine(os.path.join(tmp, "engine-" + pkg_label), packaged)
        for mode_label, args in (("game mode", [exe, "--headless"]),
                                 ("--exec", [exe, "--headless", "--exec", probe])):
            base_out = run(args, e)
            base = result(base_out)
            label = "%s %s" % (pkg_label, mode_label)
            check(base is not None and base_out.returncode == 0, "%s: baseline runs" % label)
            if base is None:
                continue
            check(base["ve"] is None, "%s: config.virtual_env is None outside a venv" % label)
            check(not base["use"] and not base["ignored"],
                  "%s: config.use_virtual_env / virtual_env_ignored are gone" % label)
            for what, ve in venvs:
                out = run(args, e, virtual_env=ve)
                r = result(out)
                check(out.returncode == 0, "%s, VIRTUAL_ENV=%s: exit status 0 (rc=%d)"
                      % (label, what, out.returncode))
                check(out.stderr == "", "%s, VIRTUAL_ENV=%s: nothing on stderr (%r)"
                      % (label, what, out.stderr))
                check(r is not None and r["where"] is None and r["path"] == base["path"]
                      and r["prefix"] == base["prefix"] and r["ve"] is None,
                      "%s, VIRTUAL_ENV=%s: sys.path / sys.prefix unchanged, module not found"
                      % (label, what))

    # --- --use-virtual-env is an unknown option ------------------------------------------
    e, exe = make_engine(os.path.join(tmp, "engine-flag"))
    out = run([exe, "--headless", "--use-virtual-env", "--exec", probe], e)
    check(out.returncode != 0 and "RESULT" not in out.stdout,
          "--use-virtual-env is rejected (rc=%d)" % out.returncode)
    check("--use-virtual-env" in out.stderr, "--use-virtual-env: the error names it (%r)" % out.stderr[-200:])

    # --- inside a venv config.virtual_env is the venv --------------------------------------
    e, exe = make_engine(os.path.join(tmp, "engine-venv"))
    env_dir = os.path.realpath(os.path.join(tmp, "ENV"))
    os.makedirs(os.path.join(env_dir, "bin"))
    with open(os.path.join(env_dir, "pyvenv.cfg"), "w") as f:
        f.write("home = %s\ninclude-system-site-packages = false\nversion = %s.0\n" % (e, PY))
    os.symlink(exe, os.path.join(env_dir, "bin", ENGINE_NAME))
    os.symlink(ENGINE_NAME, os.path.join(env_dir, "bin", "python"))
    out = run([os.path.join(env_dir, "bin", "python"), "--headless", "--exec", probe], e)
    r = result(out)
    check(r is not None and r["ve"] == env_dir and r["prefix"] == env_dir,
          "inside a venv: config.virtual_env == ENV == sys.prefix (%r)" % (r and r["ve"]))
    check(r is not None and isinstance(r["ve"], str), "config.virtual_env is a str inside a venv")

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
