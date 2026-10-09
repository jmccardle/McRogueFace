"""Engine <-> Python call-stack workload for frame-pointer profiling (#421, PEP 831).

The interesting shape is the "sandwich": the C++ main loop calls a Python timer
callback, which calls back into mcrfpy bindings implemented in C++:

    main -> GameEngine (run/doFrame | runSimFrame) -> Timer::test
         -> PyObject_Call -> [Python] on_tick -> update_world
         -> UIDrawable::set_float_member / entity.cell_pos setter  (C++)

With frame pointers in BOTH libpython and the engine, `perf --call-graph fp`
walks that whole chain; with the perf trampoline active each Python function
also gets its own symbol (py::update_world:...), instead of an anonymous
_PyEval_EvalFrameDefault.

Modes:
  headless:  ./mcrogueface --headless --exec tests/benchmarks/fp_loop_workload.py
             (the script drives mcrfpy.step(); the frame is runSimFrame)
  windowed:  MCRF_FP_WINDOWED=1 ./mcrogueface --exec tests/benchmarks/fp_loop_workload.py
             (the real GameEngine::run loop; needs a display, e.g. xvfb-run)

Environment:
  MCRF_PERF_TRAMPOLINE=1   activate sys.activate_stack_trampoline("perf")
                           (writes /tmp/perf-<pid>.map so perf names Python frames)
  MCRF_FP_TICKS=N          timer ticks to run (default 600)
  MCRF_FP_WINDOWED=1       let the engine's own loop fire the timer (no step())

Prints "ticks=N elapsed=S per_tick_us=U" so it doubles as a wall-clock benchmark.
See docs/profiling.md for the perf recipe.
"""
import mcrfpy
import os
import sys
import time

TICKS = int(os.environ.get("MCRF_FP_TICKS", "600"))
GRID_W, GRID_H = 40, 30
ENTITY_COUNT = 120
UI_FRAMES = 40

if os.environ.get("MCRF_PERF_TRAMPOLINE") == "1":
    sys.activate_stack_trampoline("perf")


def build():
    scene = mcrfpy.Scene("fp_workload")
    ui = scene.children
    grid = mcrfpy.Grid(grid_size=(GRID_W, GRID_H), pos=(0, 0), size=(640, 480))
    for x in range(GRID_W):
        for y in range(GRID_H):
            grid.at(x, y).walkable = True
    ui.append(grid)

    entities = [mcrfpy.Entity((i % GRID_W, (i * 7) % GRID_H), grid=grid)
                for i in range(ENTITY_COUNT)]
    frames = []
    for i in range(UI_FRAMES):
        f = mcrfpy.Frame(pos=(10 + i * 3, 10 + i * 2), size=(80, 40))
        f.children.append(mcrfpy.Caption(text=f"f{i}", pos=(4, 4)))
        ui.append(f)
        frames.append(f)
    return scene, grid, entities, frames


scene, grid, entities, frames = build()
mcrfpy.current_scene = scene
state = {"ticks": 0, "t0": None}


def update_world(n):
    # Python game logic that leans on mcrfpy bindings (C++ setters/getters)
    for i, e in enumerate(entities):
        p = e.cell_pos
        e.cell_pos = ((p.x + 1 + (i & 1)) % GRID_W, (p.y + (i % 3 == 0)) % GRID_H)
    for i, f in enumerate(frames):
        f.x = 10 + ((n + i * 7) % 200)
        f.y = 10 + ((n * 2 + i) % 150)


def finish():
    elapsed = time.perf_counter() - state["t0"]
    n = state["ticks"]
    print(f"ticks={n} elapsed={elapsed:.4f} per_tick_us={elapsed / n * 1e6:.2f}")
    sys.exit(0)


def on_tick(timer, runtime):
    if state["t0"] is None:
        state["t0"] = time.perf_counter()
    update_world(state["ticks"])
    state["ticks"] += 1
    if state["ticks"] >= TICKS and not HEADLESS:
        finish()


HEADLESS = os.environ.get("MCRF_FP_WINDOWED") != "1"
tick_timer = mcrfpy.Timer("fp_tick", on_tick, 1)

if __name__ == "__main__" and HEADLESS:
    while state["ticks"] < TICKS:
        mcrfpy.step(0.001)
    finish()
