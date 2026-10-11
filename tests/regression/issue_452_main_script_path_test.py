"""Regression test for #452 - sys.path[0] was always the engine's build/scripts.

A game whose scripts/ isn't the engine's (any project outside the engine tree) couldn't
import its own modules, and a module named like one of the engine's demo scripts imported
the engine's copy. Like `python dir/script.py`, the main script's directory is now
sys.path[0]:
  - game mode (scripts/game.py from the working directory);
  - `mcrogueface dir/script.py`.
"""
import os
import subprocess
import sys
import tempfile

failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


engine = sys.executable
engine_scripts = os.path.join(os.path.dirname(engine), "scripts")
env = dict(os.environ, ALSOFT_DRIVERS="null")

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
    os.symlink(os.path.join(os.path.dirname(engine), "assets"), os.path.join(project, "assets"))
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
check(sys.path[0] == engine_scripts, "--exec: sys.path[0] is still the engine's scripts (%r)" % sys.path[0])
if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
