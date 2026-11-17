"""Benchmark: cost of repainting a fully dirty grid layer (#539).

`layer.edit()` marks the whole layer dirty on exit, so the next render repaints every
chunk in view. This measures that repaint for a TileLayer and a ColorLayer at two sizes,
and, for comparison, a render with nothing dirty.

Per row, over N_FRAMES:
  grid_min / grid_med  get_metrics()["grid_render_time"]: the time inside UIGridView's
           render for the frame, layer repaints included. There is no glFinish(), so on
           a GPU driver this is mostly CPU submit time; on llvmpipe it is close to the
           total. The minimum is the number to compare on a shared machine; the median
           shows how noisy the run was.
  shot_med wall time of automation.screenshot(): render, read back, PNG encode. The PNG
           encode dominates and is the same in every row; read differences, not values.

A step() does not render in headless mode; a screenshot is what forces a real render.

Usage:
  cd build && xvfb-run -a -s "-noreset" ./mcrogueface --headless --exec ../tests/benchmarks/layer_chunk_repaint_bench.py
  LAYER_BENCH_JSON=path.json ...   also write the results as JSON
"""
import json
import os
import statistics
import sys
import tempfile
import time

import mcrfpy
from mcrfpy import automation

N_FRAMES = 40
WARMUP = 4
VIEW = (640, 360)          # 40x22 cells of 16 px; small, to keep the PNG encode small
CASES = [                  # (label, grid size, zoom)
    ("80x25, one view of it", (80, 25), 1.0),
    ("256x256, 40x22 cells in view", (256, 256), 1.0),
    ("256x256, whole layer in view", (256, 256), 360 / (256 * 16)),
]
SHOT = os.path.join(tempfile.mkdtemp(prefix="mcrf_layerbench_"), "f.png")


def build(kind, size, zoom):
    scene = mcrfpy.Scene(f"bench_{kind}_{size[0]}")
    grid = mcrfpy.Grid(grid_size=size, pos=(0, 0), size=VIEW, texture=mcrfpy.default_texture)
    count = mcrfpy.default_texture.sheet_width * mcrfpy.default_texture.sheet_height
    if kind == "tile":
        layer = mcrfpy.TileLayer(name="bench", z_index=-1, grid_size=size)
        for y in range(size[1]):
            for x in range(size[0]):
                layer.set((x, y), (x * 3 + y * 5) % count)
    else:
        layer = mcrfpy.ColorLayer(name="bench", z_index=-1, grid_size=size)
        for y in range(size[1]):
            for x in range(size[0]):
                layer.set((x, y), mcrfpy.Color((x * 9) % 256, (y * 11) % 256, 128, 255))
    grid.add_layer(layer)
    grid.zoom = zoom
    scene.children.append(grid)
    mcrfpy.current_scene = scene
    return grid, layer


def measure(grid, layer, dirty):
    grid_ms, shot_ms, chunks = [], [], None
    for i in range(WARMUP + N_FRAMES):
        if dirty:
            with layer.edit():
                pass
        else:
            # Something must change or the view re-blits its cached raster (no layer work
            # at all); a 1 px pan redraws from clean chunk textures.
            grid.center = (grid.center.x + (1 if i % 2 else -1), grid.center.y)
        t0 = time.perf_counter()
        automation.screenshot(SHOT)
        dt = (time.perf_counter() - t0) * 1000.0
        m = mcrfpy.get_metrics()
        if i >= WARMUP:
            grid_ms.append(m["grid_render_time"])
            shot_ms.append(dt)
            chunks = m.get("grid_chunks_repainted")
    return min(grid_ms), statistics.median(grid_ms), statistics.median(shot_ms), chunks


results = []
print(f"{'case':<34} {'layer':<6} {'state':<6} {'chunks':>6} {'grid_min':>9} {'grid_med':>9} {'shot_med':>9}")
for label, size, zoom in CASES:
    for kind in ("tile", "color"):
        grid, layer = build(kind, size, zoom)
        for state in ("dirty", "clean"):
            gmin, gmed, shot, chunks = measure(grid, layer, state == "dirty")
            results.append({"case": label, "layer": kind, "state": state,
                            "chunks_repainted": chunks, "grid_min_ms": round(gmin, 3),
                            "grid_median_ms": round(gmed, 3), "shot_median_ms": round(shot, 3)})
            print(f"{label:<34} {kind:<6} {state:<6} {str(chunks):>6} {gmin:>9.3f} {gmed:>9.3f} {shot:>9.3f}")

out = os.environ.get("LAYER_BENCH_JSON")
if out:
    with open(out, "w") as f:
        json.dump({"version": mcrfpy.__version__, "frames": N_FRAMES, "results": results}, f, indent=2)
    print("written:", out)
sys.exit(0)
