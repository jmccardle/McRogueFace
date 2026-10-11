"""Regression test for #451 - interpreter modes aborted without an X display.

    $ DISPLAY= mcrogueface --headless -c "print(1)"
    Failed to open X11 display ... Aborted (core dumped)

The SFML build creates textures through a GL context, and SFML abort()s when it can't open
the display for one. The engine created a headless render texture and the default texture
at startup, so nothing ran. Now:
  - GL resources are created on first use, so pure-Python work never needs a display;
  - -c and -m imply --headless (they exit without running a frame);
  - creating one with no display raises RuntimeError instead of aborting.

The no-display cases run as subprocesses with DISPLAY removed. On a machine with no display
at all the parent's own checks still hold; with a display they also check the lazy default
texture still works.
"""
import os
import subprocess
import sys

import mcrfpy

failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


engine = sys.executable
cwd = os.path.dirname(engine)
env = {k: v for k, v in os.environ.items() if k not in ("DISPLAY", "WAYLAND_DISPLAY")}
env["ALSOFT_DRIVERS"] = "null"


def run(*args):
    try:
        return subprocess.run([engine] + list(args), capture_output=True, text=True,
                              timeout=30, env=env, cwd=cwd)
    except subprocess.TimeoutExpired:
        return None


# --- 1. interpreter modes start and exit cleanly with no display ---
for args in (["-c", "print('ran 451')"], ["--headless", "-c", "print('ran 451')"]):
    out = run(*args)
    check(out is not None and out.returncode == 0 and "ran 451" in out.stdout,
          "%s runs with no display (rc=%s)" % (" ".join(args[:-1]), out and out.returncode))
out = run("-m", "platform")
check(out is not None and out.returncode == 0 and out.stdout.strip(),
      "-m runs a module with no display (rc=%s)" % (out and out.returncode))

# --- 2. pure-Python engine work runs; creating a GL resource raises RuntimeError ---
probe = r'''
import mcrfpy
mcrfpy.Frame(pos=(0, 0), size=(10, 10))
mcrfpy.Caption(text="no display")
scene = mcrfpy.Scene("s451")
scene.activate()
mcrfpy.step(0.1)
print("PURE OK", mcrfpy.automation.size())
cases = {
    "Texture": lambda: mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16),
    "default_texture": lambda: mcrfpy.default_texture,
    "Sprite": lambda: mcrfpy.Sprite(),
    "Grid": lambda: mcrfpy.Grid(grid_size=(3, 3)),
    "screenshot": lambda: mcrfpy.automation.screenshot("never_451.png"),
    "transition": lambda: mcrfpy.Scene("t451").activate(transition=mcrfpy.Transition.FADE, duration=0.5),
}
for name, make in cases.items():
    try:
        make()
        print("NOERROR", name)
    except RuntimeError as exc:
        print("RAISED", name, "needs a display" in str(exc))
'''
out = run("-c", probe)
text = (out.stdout + out.stderr) if out else ""
check(out is not None and out.returncode == 0, "the probe exits cleanly (rc=%s)" % (out and out.returncode))
check("PURE OK <Vector (1024, 768)>" in text,
      "Frame, Caption, a scene, step() and automation.size() need no display")
for name in ("Texture", "default_texture", "Sprite", "Grid", "screenshot", "transition"):
    check("RAISED %s True" % name in text, "%s raises RuntimeError saying it needs a display" % name)
check("Aborted" not in text and "core dumped" not in text, "nothing aborts")

# --- 3. a headless frame loop has to render: it exits 1 saying why, not abort() ---
import tempfile
with tempfile.TemporaryDirectory() as tmp:
    loop = os.path.join(tmp, "loop_451.py")
    with open(loop, "w") as f:
        f.write("import mcrfpy, sys\n"
                "mcrfpy.Scene('x').activate()\n"
                "mcrfpy.Timer('t', lambda t, rt: sys.exit(0), 10)\n")
    for args in (["--headless", "--run-forever", "--exec", loop], ["--headless", loop]):
        out = run(*args)
        text = (out.stdout + out.stderr) if out else ""
        check(out is not None and out.returncode == 1 and "rendering needs a display" in text
              and "Aborted" not in text,
              "%s: a frame loop exits 1 naming the missing display (rc=%s)"
              % (" ".join(args[:-1]), out and out.returncode))

# --- 4. with a display, the default texture still loads on first use ---
if os.environ.get("DISPLAY"):
    tex = mcrfpy.default_texture
    check(isinstance(tex, mcrfpy.Texture) and mcrfpy.default_texture is tex,
          "mcrfpy.default_texture loads once and is the same object")
    check(mcrfpy.Sprite().texture is tex, "a Sprite with no texture uses it")
    other = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    mcrfpy.default_texture = other
    check(mcrfpy.Sprite().texture is other, "assigning default_texture changes what Sprite() uses")
    mcrfpy.default_texture = tex
    try:
        mcrfpy.default_texture = 5
        check(False, "default_texture = 5 must raise TypeError")
    except TypeError:
        check(True, "default_texture rejects a non-Texture")
    check("default_texture" in dir(mcrfpy), "default_texture is in dir(mcrfpy)")

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
