"""Sprint perf baseline — isolated stress scenarios for #342/#343/#344/#348.

Wall-clock timed, step()-only / pure-loop (NO screenshots — avoids the PNG-encode
trap that buries engine work; see docs/profiling.md). Run BEFORE and AFTER the fixes
and compare the stable-format lines. Also usable under `make callgrind SCRIPT=...`
to capture function-level instruction counts for the four target hot paths in one run.

Usage:
  ./build/mcrogueface --headless --exec tests/benchmarks/sprint_perf_baseline.py
"""
import mcrfpy
from mcrfpy import automation
import sys
import time

# Scale knobs (kept modest so a Callgrind run finishes in a couple minutes).
ANIM_TARGETS = 500      # frames, each animating 2 properties => 1000 active animations
ANIM_STEPS = 200        # step() calls (animations have long duration -> stay active)
UPDATE_STEPS = 5000     # bare-scene step() calls (isolates PyScene::update overhead)
KEY_EVENTS = 3000       # keyDown/keyUp pairs (isolates on_key enum construction)
GRID_DIM = 120          # NxN grid
GRID_PASSES = 5         # full-grid at()/set() sweeps


def _report(name, ops, seconds):
    us = (seconds / ops) * 1e6 if ops else 0.0
    print(f"BASELINE | {name:22s} | {ops:8d} ops | {seconds*1000:9.2f} ms | "
          f"{us:8.3f} us/op")


def bench_anim_dispatch():
    """#342 — Animation::applyValue -> setProperty(std::string,...) strcmp cascade,
    per active animation per frame."""
    scene = mcrfpy.Scene("anim")
    ui = scene.children
    frames = []
    for i in range(ANIM_TARGETS):
        f = mcrfpy.Frame(pos=(i % 400, (i * 3) % 400), size=(10, 10))
        ui.append(f)
        # long duration so the animation never completes during the run
        f.animate("x", 9999.0, 1000.0, mcrfpy.Easing.LINEAR)
        f.animate("opacity", 0.1, 1000.0, mcrfpy.Easing.LINEAR)
        frames.append(f)
    mcrfpy.current_scene = scene

    t0 = time.perf_counter()
    for _ in range(ANIM_STEPS):
        mcrfpy.step(0.016)
    dt = time.perf_counter() - t0
    # ops = animation-value applications = active_anims * steps
    _report("342_anim_dispatch", ANIM_TARGETS * 2 * ANIM_STEPS, dt)


def bench_scene_update():
    """#343 — PyScene::update GetAttrString('update') every frame on a plain scene."""
    scene = mcrfpy.Scene("bare")
    mcrfpy.current_scene = scene
    t0 = time.perf_counter()
    for _ in range(UPDATE_STEPS):
        mcrfpy.step(0.016)
    dt = time.perf_counter() - t0
    _report("343_scene_update", UPDATE_STEPS, dt)


def bench_key_dispatch():
    """#344 — on_key rebuilds Key/InputState IntEnum members per event."""
    scene = mcrfpy.Scene("keys")
    count = [0]

    def on_key(key, state):
        count[0] += 1
    scene.on_key = on_key
    mcrfpy.current_scene = scene

    t0 = time.perf_counter()
    for _ in range(KEY_EVENTS):
        automation.keyDown('a')
        automation.keyUp('a')
    dt = time.perf_counter() - t0
    _report("344_key_dispatch", KEY_EVENTS * 2, dt)
    if count[0] == 0:
        print("  WARN: on_key never fired — key injection did not reach the handler")


def bench_grid_churn():
    """#348 — get_grid re-allocates a Grid wrapper + weakref per cell access."""
    color_layer = mcrfpy.ColorLayer(z_index=-1, name="c")
    grid = mcrfpy.Grid(grid_size=(GRID_DIM, GRID_DIM), pos=(0, 0), size=(800, 800),
                       layers=[color_layer])
    col = mcrfpy.Color(20, 20, 20, 255)
    t0 = time.perf_counter()
    ops = 0
    for _ in range(GRID_PASSES):
        for x in range(GRID_DIM):
            for y in range(GRID_DIM):
                c = grid.at(x, y)
                c.walkable = True
                color_layer.set((x, y), col)
                ops += 1
    dt = time.perf_counter() - t0
    _report("348_grid_churn", ops, dt)


def main():
    print(f"=== sprint perf baseline (anim={ANIM_TARGETS}x2/{ANIM_STEPS}, "
          f"update={UPDATE_STEPS}, keys={KEY_EVENTS}, grid={GRID_DIM}^2x{GRID_PASSES}) ===")
    bench_anim_dispatch()
    bench_scene_update()
    bench_key_dispatch()
    bench_grid_churn()
    print("=== done ===")


if __name__ == "__main__":
    main()
    sys.exit(0)
