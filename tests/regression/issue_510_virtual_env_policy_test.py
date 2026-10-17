"""Regression test for #510 - an activated virtualenv must not stop the engine starting.

#499 made the engine honour VIRTUAL_ENV and exit when it was unusable, so any venv left
active in the shell -- one for another Python, say -- stopped the test suite and shipped
games alike. The rule now (docs/sys-path-order.md):

  * a venv for another Python (pyvenv.cfg `version`/`version_info`, or its lib/pythonX.Y
    directory) can't be meant for this engine: ignored, one line on stderr, recorded in
    mcrfpy.config.virtual_env_ignored;
  * a venv for this Python that is unusable (no site-packages) is meant for it: still the
    #499 hard error;
  * a packaged game (mcrf-game.json beside the binary, written by `mcrf_project dist`)
    ignores VIRTUAL_ENV entirely and silently, so its bundled venv/ wins, unless run with
    --use-virtual-env.

Every layout is a private engine directory (copied binary + symlinks), never build/. Both
init paths are covered: script/--exec mode and game mode (scripts/game.py), which is how a
packaged game starts.
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
PY = "%d.%d" % sys.version_info[:2]
FT = bool(sysconfig.get_config_var("Py_GIL_DISABLED"))
OURS = "python" + PY + ("t" if FT else "")
OTHER_ABI = "python" + PY + ("" if FT else "t")      # same version, the other build
PROBE = ("import json, sys, mcrfpy\n"
         "try:\n"
         "    import fake510mod; where = fake510mod.WHERE\n"
         "except ImportError:\n"
         "    where = None\n"
         "c = mcrfpy.config\n"
         "print('RESULT ' + json.dumps({'where': where, 've': c.virtual_env,\n"
         "      'ignored': c.virtual_env_ignored, 'flag': c.use_virtual_env}))\n"
         "sys.exit(0)\n")


def make_engine(root, packaged=False, bundled=False, game_py=False):
    """A private engine dir. packaged: has the dist marker. bundled: a sibling venv/ with
    fake510mod. game_py: its own scripts/game.py (the probe) for game mode."""
    os.makedirs(root)
    e = os.path.realpath(root)
    exe = os.path.join(e, os.path.basename(real_engine))
    shutil.copy2(real_engine, exe)
    for name in ("lib", "assets") + (() if game_py else ("scripts",)):
        os.symlink(os.path.join(real_dir, name), os.path.join(e, name))
    if game_py:
        os.makedirs(os.path.join(e, "scripts"))
        with open(os.path.join(e, "scripts", "game.py"), "w") as f:
            f.write(PROBE)
    if packaged:
        with open(os.path.join(e, "mcrf-game.json"), "w") as f:
            f.write('{"game": "t", "version": "0"}\n')
    if bundled:
        sp = os.path.join(e, "venv", "lib", OURS, "site-packages")
        os.makedirs(sp)
        with open(os.path.join(sp, "fake510mod.py"), "w") as f:
            f.write("WHERE = 'bundled'\n")
    return e, exe


def make_venv(root, cfg_lines=(), libdir=OURS, module=True):
    os.makedirs(root)
    root = os.path.realpath(root)
    with open(os.path.join(root, "pyvenv.cfg"), "w") as f:
        f.write("home = /usr/bin\n" + "".join(l + "\n" for l in cfg_lines))
    if libdir:
        sp = os.path.join(root, "lib", libdir, "site-packages")
        os.makedirs(sp)
        if module:
            with open(os.path.join(sp, "fake510mod.py"), "w") as f:
                f.write("WHERE = 'shell'\n")
    return root


def run(exe, args, cwd, virtual_env):
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    env["ALSOFT_DRIVERS"] = "null"
    if virtual_env is not None:
        env["VIRTUAL_ENV"] = virtual_env
    return subprocess.run([exe, "--headless"] + args, capture_output=True, text=True,
                          timeout=30, env=env, cwd=cwd)


def result(out):
    for line in out.stdout.splitlines():
        if line.startswith("RESULT "):
            return json.loads(line[len("RESULT "):])
    print(out.stdout[-800:], out.stderr[-800:])
    return None


def notes(out):
    return [l for l in out.stderr.splitlines() if "VIRTUAL_ENV" in l]


with tempfile.TemporaryDirectory() as tmp:
    probe = os.path.join(tmp, "probe.py")
    with open(probe, "w") as f:
        f.write(PROBE)
    e, exe = make_engine(os.path.join(tmp, "dev"))

    # --- another Python: ignored, said once, recorded ------------------------------------
    for i, (label, cfg, libdir) in enumerate((
            ("venv's `version`", ["version = 3.11.4"], "python3.11"),
            ("virtualenv/uv `version_info`", ["version_info = 3.11.4.final.0"], "python3.11"),
            ("no version line: its lib/python3.11", [], "python3.11"),
            ("same version, the other build (%s)" % OTHER_ABI, ["version = %s.0" % PY], OTHER_ABI))):
        venv = make_venv(os.path.join(tmp, "mismatch%d" % i), cfg, libdir)
        for mode in (["--exec", probe], [probe]):
            out = run(exe, mode, tmp, venv)
            r = result(out)
            check(out.returncode == 0 and r is not None and r["where"] is None,
                  "%s, %s: runs without it (rc=%d)" % (label, mode[0], out.returncode))
            check(r is not None and r["ve"] is None and r["ignored"] and r["ignored"][0] == venv,
                  "%s: config.virtual_env None, virtual_env_ignored names it (%r)" % (label, r))
            check(len(notes(out)) == 1 and venv in notes(out)[0] and "ignoring" in notes(out)[0],
                  "%s: exactly one stderr line naming it (%r)" % (label, notes(out)))

    # --- this Python but unusable: still the #499 hard error ------------------------------
    broken = make_venv(os.path.join(tmp, "broken"), ["version = %s.0" % PY], libdir=None)
    out = run(exe, ["--exec", probe], tmp, broken)
    check(out.returncode == 1 and "RESULT" not in out.stdout and broken in out.stderr,
          "a %s venv without site-packages is fatal, naming it (rc=%d)" % (PY, out.returncode))

    # --- this Python and usable: honoured -----------------------------------------------
    good = make_venv(os.path.join(tmp, "good"), ["version = %s.0" % PY])
    out = run(exe, ["--exec", probe], tmp, good)
    r = result(out)
    check(r is not None and r["where"] == "shell" and r["ve"] == good and r["ignored"] is None,
          "a matching venv is honoured and reported as config.virtual_env (%r)" % r)
    check(notes(out) == [], "a honoured venv prints nothing")

    # --- packaged game: VIRTUAL_ENV ignored, silently; bundled venv/ wins -----------------
    pe, pexe = make_engine(os.path.join(tmp, "pkg"), packaged=True, bundled=True, game_py=True)
    for label, args in (("game mode", []), ("--exec", ["--exec", probe])):
        out = run(pexe, args, pe, good)
        r = result(out)
        check(out.returncode == 0 and r is not None and r["where"] == "bundled",
              "packaged, %s: the bundled venv/ beats a valid VIRTUAL_ENV (%r)" % (label, r))
        check(r is not None and r["ve"] is None and r["ignored"] and "packaged" in r["ignored"][1],
              "packaged, %s: recorded as ignored because packaged (%r)" % (label, r))
        check(notes(out) == [], "packaged, %s: nothing on stderr for the player" % label)
    out = run(pexe, [], pe, os.path.join(tmp, "does-not-exist"))
    check(out.returncode == 0 and (result(out) or {}).get("where") == "bundled",
          "packaged: even a VIRTUAL_ENV that isn't a venv can't stop it (rc=%d)" % out.returncode)

    # --- packaged game, --use-virtual-env: the modder's escape hatch ----------------------
    out = run(pexe, ["--use-virtual-env"], pe, good)
    r = result(out)
    check(r is not None and r["where"] == "shell" and r["ve"] == good and r["flag"] is True,
          "packaged + --use-virtual-env: VIRTUAL_ENV is honoured again (%r)" % r)
    out = run(pexe, ["--use-virtual-env"], pe, broken)
    check(out.returncode == 1 and broken in out.stderr,
          "packaged + --use-virtual-env: a broken %s venv is the hard error again" % PY)

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
