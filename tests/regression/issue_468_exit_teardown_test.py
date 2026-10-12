"""#468: every Python reference the engine holds is released before the interpreter goes.

The engine held Python objects past Py_Finalize -- the scene registry, retained timers,
animation/key/click/step callbacks, identity pins -- and its destructors guarded their
DECREFs with Py_IsInitialized(), which CPython clears BEFORE its final GC and module
clearing. So nothing the engine owned was ever released at exit: every ASan run reported
the leaks, and a __del__ reachable only through the engine never ran.

Each probe below is reachable ONLY through one engine-held reference. Its __del__ writes
a marker to stderr, so a marker means that reference was released while Python was still
alive. Run on every exit path. Under an ASan build (make asan-test) the child also inherits
LSan, and any leak report in its stderr fails the test.
"""
import os
import subprocess
import sys
import tempfile

failures = []


def check(cond, msg):
    print(("ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


WORLD = r'''
import mcrfpy, os, sys

class Probe:
    def __init__(self, tag): self.tag = tag
    # os.write bound at definition: finalization may already have cleared module globals.
    def __del__(self, _w=os.write):
        _w(2, ("FREED:" + self.tag + "\n").encode())

class PFrame(mcrfpy.Frame):
    def __del__(self, _w=os.write):
        _w(2, ("FREED:" + self.name + "\n").encode())

class PEntity(mcrfpy.Entity):
    def __del__(self, _w=os.write):
        _w(2, ("FREED:" + self.name + "\n").encode())

# Finalization code that tries to run a frame after the engine released its scenes
# gets an error, not a frame over freed state.
class StepProbe:
    def __del__(self, _w=os.write, _step=mcrfpy.step):
        try:
            _step(0.01)
            _w(2, b"STEP:ran\n")
        except RuntimeError:
            _w(2, b"STEP:refused\n")

def build():
    scene = mcrfpy.Scene("i468")
    mcrfpy.current_scene = scene

    p = Probe("key_callback")
    scene.on_key = lambda k, s, p=p: None

    scene.children.append(PFrame(pos=(0, 0), size=(10, 10), name="scene_child_pin"))

    # A re-run __init__ used to reset weakreflist, orphaning the wrapper cache's weak
    # reference; releasing the scene at exit then read the freed wrapper (ASan: SEGV).
    again = PFrame(pos=(0, 0), size=(1, 1), name="reinit_child_pin")
    again.__init__(pos=(0, 0), size=(2, 2), name="reinit_child_pin")
    scene.children.append(again)
    cap = mcrfpy.Caption(text="x", pos=(0, 0))
    cap.__init__(text="y", pos=(1, 1))
    scene.children.append(cap)
    del again, cap
    # ...and dropped the old children without detaching them: each pinned child and
    # its wrapper then kept each other alive forever.
    old_parent = mcrfpy.Frame(pos=(0, 0), size=(3, 3))
    old_parent.children.append(PFrame(pos=(0, 0), size=(1, 1), name="reinit_dropped_child"))
    old_parent.__init__(pos=(0, 0), size=(3, 3))

    f = mcrfpy.Frame(pos=(20, 0), size=(10, 10))
    p = Probe("click_callback")
    f.on_click = lambda pos, b, a, p=p: None
    p = Probe("animation_callback")
    f.animate("x", 500.0, 1000.0, callback=lambda t, n, v, p=p: None)
    scene.children.append(f)

    grid = mcrfpy.Grid(grid_size=(5, 5), pos=(0, 50), size=(80, 80))
    scene.children.append(grid)
    e = PEntity((1, 1), name="grid_entity_pin")
    grid.entities.append(e)
    plain = mcrfpy.Entity((2, 2))
    p = Probe("entity_step_callback")
    plain.step = lambda trig, data, p=p: None
    grid.entities.append(plain)

    p = Probe("timer_callback")
    mcrfpy.Timer("i468_timer", lambda t, r, p=p: None, 100000)
    sp = StepProbe()
    mcrfpy.Timer("i468_step_probe", lambda t, r, sp=sp: None, 100000)
    del sp

    # Owned by a Frame in no scene, held only by a module with no cycles through it:
    # freed by refcount when finalization clears sys.modules, i.e. after
    # Py_IsInitialized() is already 0, so only a python_alive() guard releases its pin.
    import types
    mod = types.ModuleType("i468_holder")
    mod.holder = mcrfpy.Frame(pos=(0, 0), size=(5, 5))
    mod.holder.children.append(PFrame(pos=(0, 0), size=(1, 1), name="finalize_time_pin"))
    sys.modules["i468_holder"] = mod

build()

# A timer whose wrapper is a global its own callback reaches (via __globals__): once
# teardown stops it, only the GC can free the cycle, so Timer must report its callback.
def _cycle_timer():
    p = Probe("timer_wrapper_cycle")
    return mcrfpy.Timer("i468_cycle", lambda t, r, p=p: None, 100000)
cycle_timer = _cycle_timer()

# A children view in a global shares the scene's vector, so nobody could report the
# children to the GC: the cycle globals -> scene -> child -> callback -> globals stayed.
def _view_cycle():
    s = mcrfpy.Scene("i468_view")
    f = mcrfpy.Frame(pos=(0, 0), size=(1, 1))
    p = Probe("children_view_cycle")
    f.on_click = lambda pos, b, a, p=p: None
    s.children.append(f)
    return s, s.children
view_scene, view_children = _view_cycle()

mcrfpy.step(0.01)
'''

TAGS = ["key_callback", "scene_child_pin", "reinit_child_pin", "reinit_dropped_child", "click_callback", "animation_callback",
        "grid_entity_pin", "entity_step_callback", "timer_callback", "timer_wrapper_cycle", "children_view_cycle",
        "finalize_time_pin"]


def run(args, expect_rc, label):
    env = dict(os.environ, ALSOFT_DRIVERS="null")
    out = subprocess.run([sys.executable, "--headless"] + args, capture_output=True,
                         text=True, timeout=600, env=env, cwd=os.path.dirname(sys.executable))
    err = out.stderr
    check(out.returncode == expect_rc, f"{label}: exit status {out.returncode} == {expect_rc}")
    for tag in TAGS:
        check(f"FREED:{tag}\n" in err, f"{label}: engine released {tag}")
    check("STEP:refused\n" in err, f"{label}: step() during teardown raises RuntimeError")
    check("LeakSanitizer" not in err, f"{label}: no LeakSanitizer report")
    if "LeakSanitizer" in err or out.returncode != expect_rc:
        print(err[-6000:])


# -c, falling off the end: main.cpp's api_shutdown() path.
run(["-c", WORLD], 0, "-c, end of script")
# sys.exit() at top level: finalization runs inside PyErr_Print(), `delete engine` never does.
run(["-c", WORLD + "sys.exit(0)\n"], 0, "-c, sys.exit")
# sys.exit() inside an engine callback, with C++ frames (step -> timer) still on the stack.
run(["-c", WORLD + "mcrfpy.Timer('quit', lambda t, r: sys.exit(5), 10)\n"
     "for _ in range(5): mcrfpy.step(0.02)\n"], 5, "-c, sys.exit in a timer")

# --exec script with sys.exit (the test suite's own path).
with tempfile.TemporaryDirectory() as tmp:
    script = os.path.join(tmp, "world.py")
    with open(script, "w") as fh:
        fh.write(WORLD + "sys.exit(0)\n")
    run(["--exec", script], 0, "--exec, sys.exit")

if failures:
    print(f"{len(failures)} failure(s)")
    sys.exit(1)
print("PASS")
sys.exit(0)
