"""Benchmark: 1/2/4 GridView instances viewing shared Grid data (Phase 5.2).

A `mcrfpy.step()` in headless mode does not actually render -- the render path
is stubbed. To force a real render we use `automation.screenshot()`, which
flushes the current scene to a PNG via the off-screen render target. Each
screenshot is one full render of all currently-mounted children.

We measure mean wall time per screenshot for view counts {1, 2, 4} on the same
underlying grid, with grid cells populated to mimic a real overworld scene.

Usage:
  ./mcrogueface --headless --exec ../tests/benchmarks/gridview_render_bench.py
"""
import mcrfpy
from mcrfpy import automation
import sys
import os
import time
import json
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
import _baseline


GRID_W, GRID_H = 80, 80
N_FRAMES = 60
WARMUP_FRAMES = 5
VIEW_COUNTS = [1, 2, 4]
VIEW_PIXEL_SIZE = (320, 320)


def populate_grid(g):
    for y in range(GRID_H):
        for x in range(GRID_W):
            c = g.at(x, y)
            c.walkable = True
            c.transparent = True


def make_scene(view_count, tmpdir):
    scene = mcrfpy.Scene(f"bench_views_{view_count}")
    grid = mcrfpy.Grid(grid_size=(GRID_W, GRID_H))
    populate_grid(grid)
    views = []
    for i in range(view_count):
        # Stack views in a row; tolerate going off-screen, the renderer clips.
        v = mcrfpy.GridView(
            grid=grid,
            pos=(i * 100, 0),
            size=VIEW_PIXEL_SIZE,
        )
        scene.children.append(v)
        views.append(v)
    return scene, grid, views


def bench(view_count, tmpdir):
    scene, grid, views = make_scene(view_count, tmpdir)
    mcrfpy.current_scene = scene

    # Warmup: a few screenshots so any first-time texture loads / shader
    # compilations are amortised away.
    for i in range(WARMUP_FRAMES):
        automation.screenshot(os.path.join(tmpdir, f"warm_{view_count}_{i}.png"))

    times = []
    for i in range(N_FRAMES):
        path = os.path.join(tmpdir, f"frame_{view_count}_{i}.png")
        t0 = time.perf_counter()
        automation.screenshot(path)
        times.append(time.perf_counter() - t0)

    times.sort()
    total = sum(times)
    mean = total / len(times)
    p95 = times[int(0.95 * len(times))]

    return {
        "views": view_count,
        "frames": N_FRAMES,
        "warmup_frames": WARMUP_FRAMES,
        "total_sec": total,
        "mean_frame_ms": mean * 1000.0,
        "p95_frame_ms": p95 * 1000.0,
        "implied_fps": (1.0 / mean) if mean > 0 else float("inf"),
        "per_view_frame_ms": mean * 1000.0 / view_count,
    }


def main():
    runs = []
    with tempfile.TemporaryDirectory(prefix="mcrf_bench_") as tmpdir:
        for n in VIEW_COUNTS:
            r = bench(n, tmpdir)
            runs.append(r)
            print(f"  views={r['views']}  frames={r['frames']}  "
                  f"mean={r['mean_frame_ms']:7.2f} ms  "
                  f"p95={r['p95_frame_ms']:7.2f} ms  "
                  f"fps~{r['implied_fps']:6.1f}  "
                  f"per-view={r['per_view_frame_ms']:6.2f} ms")

    base = runs[0]["mean_frame_ms"]
    print()
    for r in runs[1:]:
        ratio = r["mean_frame_ms"] / base if base > 0 else 0
        print(f"  views={r['views']}: total frame time vs 1-view = {ratio:.2f}x")

    out = {"runs": runs, "config": {
        "grid": f"{GRID_W}x{GRID_H}",
        "frames": N_FRAMES,
        "warmup_frames": WARMUP_FRAMES,
        "view_counts": VIEW_COUNTS,
        "view_pixel_size": VIEW_PIXEL_SIZE,
    }}
    print(json.dumps(out, indent=2))
    _baseline.write("gridview_render_bench.json", out)
    print("DONE")


if __name__ == "__main__":
    main()
    sys.exit(0)
