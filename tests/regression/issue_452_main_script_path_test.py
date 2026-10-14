"""Regression test for #452 - sys.path[0] was always the engine's build/scripts.

A game whose scripts/ isn't the engine's (any project outside the engine tree) couldn't
import its own modules, and a module named like one of the engine's demo scripts imported
the engine's copy. Like `python dir/script.py`, the main script's directory is now
sys.path[0]:
  - game mode (scripts/game.py from the working directory);
  - `mcrogueface dir/script.py`.
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


# #502: this test must not depend on what else sits next to the binary it runs under (a
# build/venv with site-packages is prepended to sys.path, and is legitimate). So it runs a
# private engine layout: a copy of the binary (the engine resolves its directory through
# symlinks, so the binary itself must be a real file) with symlinks to the read-only
# lib/, assets/ and scripts/ of the engine under test. Nothing else is in that directory.
real_engine = os.path.realpath(sys.executable)
real_dir = os.path.dirname(real_engine)
env = dict(os.environ, ALSOFT_DRIVERS="null")
_engine_tmp = tempfile.TemporaryDirectory()
engine_dir = os.path.realpath(_engine_tmp.name)
engine = os.path.join(engine_dir, os.path.basename(real_engine))
shutil.copy2(real_engine, engine)
for name in ("lib", "assets", "scripts"):
    os.symlink(os.path.join(real_dir, name), os.path.join(engine_dir, name))
engine_scripts = os.path.join(engine_dir, "scripts")

PROBE = """import sys
import helper
print("HELPER", helper.VALUE)
print("PATH0", sys.path[0])
try:
    import cos_level
    print("SHADOWED", cos_level.__file__)
except ImportError:
    print("NOT SHADOWED")
sys.exit(0)
"""

with tempfile.TemporaryDirectory() as tmp:
    project = os.path.join(tmp, "proj")
    scripts = os.path.join(project, "scripts")
    os.makedirs(scripts)
    os.symlink(os.path.join(engine_dir, "assets"), os.path.join(project, "assets"))
    with open(os.path.join(scripts, "helper.py"), "w") as f:
        f.write("VALUE = 'project helper'\n")
    with open(os.path.join(scripts, "game.py"), "w") as f:
        f.write(PROBE)

    for label, args, cwd in (("game mode", ["--headless"], project),
                             ("script mode", ["--headless", os.path.join(scripts, "game.py")], tmp)):
        try:
            out = subprocess.run([engine] + args, capture_output=True, text=True, timeout=30,
                                 env=env, cwd=cwd)
            text = out.stdout + out.stderr
        except subprocess.TimeoutExpired:
            text = ""
        check("HELPER project helper" in text, "%s: the game imports its own module" % label)
        check("PATH0 " + scripts in text, "%s: sys.path[0] is the game's scripts dir" % label)
        check("NOT SHADOWED" in text,
              "%s: an engine demo module name doesn't import the engine's copy" % label)

# --exec isn't the main script: sys.path is unchanged.
with tempfile.TemporaryDirectory() as tmp2:
    probe = os.path.join(tmp2, "probe_exec.py")
    with open(probe, "w") as f:
        f.write("import sys\nprint('PATH0', sys.path[0])\nsys.exit(0)\n")
    out = subprocess.run([engine, "--headless", "--exec", probe], capture_output=True, text=True,
                         timeout=30, env=env, cwd=tmp2)
    check("PATH0 " + engine_scripts in out.stdout + out.stderr,
          "--exec: sys.path[0] is still the engine's scripts (%r)" % (out.stdout + out.stderr))
_engine_tmp.cleanup()
if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
