"""THE CRUCIBLE -- McRogueFace headless wall-clock microbenchmark.

The Gauntlet answers "how much load until the frame budget breaks?" by ramping
until failure -- it needs a display, varies run-to-run with desktop noise, and
(pre-2026-07-11) could ramp a viewport-bounded grid straight into OOM. The
Crucible answers a different, complementary question:

    "How many milliseconds of CPU does the engine spend on a FIXED, comically
     extreme but tractable amount of work?"

Every benchmark runs a fixed configuration to completion and times it with
time.perf_counter. No ramp, no display, no rendering -- so it is:

  * SAFE      -- every config is sized to fit in well under 512 MB and finish
                 in a couple of seconds; it cannot OOM the machine.
  * HEADLESS  -- pure engine CPU paths (allocation, cell writes, TCOD sync,
                 turn manager, pathfinding, FOV, layer writes). No frame_time.
  * DETERMINISTIC -- fixed seeds; the same build produces the same work every
                 run, so A/B deltas between builds are real signal, not noise.

This is the right tool for comparing two builds (e.g. current vs the 0.2.8
release artifact) on the CPU-bound paths the #329/#332/#348 perf work touched.

Run (this build):
    ./mcrogueface --headless --exec ../tests/benchmarks/crucible.py

Write JSON + compare against another build's JSON:
    MCRF_CRUCIBLE_OUT=/tmp/cur.json  ./mcrogueface --headless --exec .../crucible.py
    MCRF_CRUCIBLE_BASELINE=/tmp/cur.json ./other/mcrogueface --headless --exec .../crucible.py

Env vars:
    MCRF_CRUCIBLE_OUT       path to write this run's JSON (optional)
    MCRF_CRUCIBLE_BASELINE  path to a prior run's JSON to diff against (optional)
    MCRF_CRUCIBLE_REPS      override repetition count multiplier (default 1)
    MCRF_CRUCIBLE_ONLY      comma-separated benchmark names to run (default all)
"""
import os
import sys
import gc
import json
import time
import random

import mcrfpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "gauntlet"))
try:
    import safety
    _rss = safety.rss_mb
    _cap = safety.install_address_space_cap
except Exception:  # pragma: no cover - safety is in-tree, but stay robust
    def _rss():
        try:
            with open("/proc/self/statm") as f:
                return int(f.read().split()[1]) * 4096 / (1024.0 * 1024.0)
        except Exception:
            return 0.0

    def _cap(cap_mb=2500):
        return None


# --------------------------------------------------------------------------
# Timing harness
# --------------------------------------------------------------------------
class Bench:
    """A named fixed-configuration benchmark. `run` does one full unit of work
    and returns an integer 'work count' (for a work/ms figure). It is called
    `reps` times; we report the FASTEST rep (least contended) in ms plus the
    resident-memory high-water mark observed across reps."""

    def __init__(self, name, desc, reps, fn):
        self.name = name
        self.desc = desc
        self.reps = reps
        self.fn = fn

    def measure(self, seed):
        best_ms = None
        total_work = 0
        rss_peak = _rss()
        for i in range(self.reps):
            gc.collect()
            rng = random.Random(seed + i)
            try:
                t0 = time.perf_counter()
                work = self.fn(rng)
                dt_ms = (time.perf_counter() - t0) * 1000.0
            except (AttributeError, TypeError) as ex:
                # A missing API on an older/newer build -- report honestly as
                # unsupported rather than crashing the whole comparison run.
                return {
                    "name": self.name, "desc": self.desc, "reps": self.reps,
                    "best_ms": 0.0, "work": 0, "us_per_work": 0.0,
                    "rss_peak_mb": round(_rss(), 1),
                    "status": "unsupported", "error": "%s: %s" % (type(ex).__name__, ex),
                }
            total_work = work
            if best_ms is None or dt_ms < best_ms:
                best_ms = dt_ms
            r = _rss()
            if r > rss_peak:
                rss_peak = r
            gc.collect()
        return {
            "name": self.name,
            "desc": self.desc,
            "reps": self.reps,
            "best_ms": round(best_ms, 3),
            "work": total_work,
            "us_per_work": round(best_ms * 1000.0 / total_work, 4) if total_work else 0.0,
            "rss_peak_mb": round(rss_peak, 1),
            "status": "ok",
        }


# --------------------------------------------------------------------------
# Fixed workloads -- "comically extreme, but tractable"
# --------------------------------------------------------------------------
def _open_grid(side, layers=False):
    g = mcrfpy.Grid(grid_size=(side, side), texture=mcrfpy.default_texture)
    if layers:
        base = mcrfpy.TileLayer(z_index=-2, name="base", texture=mcrfpy.default_texture)
        g.add_layer(base)
        base.fill(0)
        color = mcrfpy.ColorLayer(z_index=-1, name="overlay")
        g.add_layer(color)
        color.fill(mcrfpy.Color(20, 26, 38, 120))
    return g


def bench_grid_alloc(rng):
    """Construct + destroy a big grid with two layers. Stresses #332 SoA plane
    allocation + layer allocation + TCOD map alloc/free."""
    side = 600
    n = 12
    for _ in range(n):
        g = _open_grid(side, layers=True)
        del g
        gc.collect()
    return n * side * side  # cells allocated


def bench_grid_fill(rng):
    """Set walkable/transparent across every cell of a large grid. Each write
    goes through the GridPoint wrapper -> setWalkable/Transparent + TCOD sync."""
    side = 400
    g = _open_grid(side)
    for y in range(side):
        for x in range(side):
            p = g.at(x, y)
            p.walkable = True
            p.transparent = True
    return side * side


def bench_layer_fill(rng):
    """Bulk ColorLayer/TileLayer writes: full fills + many fill_rect windows."""
    side = 500
    g = _open_grid(side, layers=True)
    color = g.layer("overlay")
    tile = g.layer("base")
    reps = 60
    for i in range(reps):
        c = mcrfpy.Color(i % 256, (i * 3) % 256, (i * 7) % 256, 180)
        ox = rng.randint(0, side - 64)
        oy = rng.randint(0, side - 64)
        color.fill_rect((ox, oy), (64, 64), c)
        tile.fill_rect((ox, oy), (64, 64), (i % 10))
    return reps * 64 * 64


def bench_layer_edit_buffer(rng):
    """#335 edit() zero-copy buffer path. With numpy: whole-plane vectorized
    writes. Without numpy (light build): a coarse memoryview stripe write so the
    benchmark still exercises the buffer + __exit__ invalidation."""
    side = 400
    g = _open_grid(side, layers=True)
    color = g.layer("overlay")
    reps = 40
    try:
        import numpy as np
        for i in range(reps):
            with color.edit() as view:
                a = np.asarray(view)
                a[:, :, 0] = (i * 5) % 256
                a[:, :, 3] = 200
        return reps * side * side
    except ImportError:
        for i in range(reps):
            with color.edit() as view:
                # touch one row per rep (cheap, still crosses the buffer boundary)
                row = i % side
                for x in range(side):
                    view[row, x, 0] = (x + i) % 256
        return reps * side


def bench_step_swarm(rng):
    """Turn manager: many entities random-walking (NOISE4) for several turns.
    Stresses executeBehavior + isCellWalkable + spatial hash + (post-fix) the
    single view invalidation per step()."""
    side = 60
    g = _open_grid(side)
    for y in range(side):
        for x in range(side):
            p = g.at(x, y)
            p.walkable = True
            p.transparent = True
    n_ent = 1000
    for _ in range(n_ent):
        e = mcrfpy.Entity(grid_pos=(rng.randint(0, side - 1), rng.randint(0, side - 1)),
                          texture=mcrfpy.default_texture, sprite_index=84)
        e.move_speed = 0
        g.entities.append(e)
        e.set_behavior(mcrfpy.Behavior.NOISE4)
    turns = 30
    g.step(n=turns)
    return n_ent * turns


def bench_fov_storm(rng):
    """Field of view recomputed from many origins on a large open grid."""
    side = 200
    g = _open_grid(side)
    for y in range(side):
        for x in range(side):
            p = g.at(x, y)
            p.walkable = True
            p.transparent = True
    # scatter some blocking walls so FOV actually casts
    for _ in range(side * side // 20):
        x = rng.randint(0, side - 1)
        y = rng.randint(0, side - 1)
        g.at(x, y).transparent = False
    n = 1500
    for _ in range(n):
        g.compute_fov((rng.randint(0, side - 1), rng.randint(0, side - 1)), radius=20)
    return n


def bench_path_queries(rng):
    """A* pathfinding between many random walkable pairs on an open grid."""
    side = 120
    g = _open_grid(side)
    for y in range(side):
        for x in range(side):
            p = g.at(x, y)
            p.walkable = True
            p.transparent = True
    n = 600
    found = 0
    for _ in range(n):
        a = (rng.randint(0, side - 1), rng.randint(0, side - 1))
        b = (rng.randint(0, side - 1), rng.randint(0, side - 1))
        path = g.find_path(a, b)
        if path is not None:
            found += 1
    return n


def bench_entity_churn(rng):
    """Add then remove many entities repeatedly -- spatial hash + cache churn."""
    side = 80
    g = _open_grid(side)
    for y in range(side):
        for x in range(side):
            g.at(x, y).walkable = True
    reps = 8
    n_ent = 800
    for _ in range(reps):
        ents = []
        for _ in range(n_ent):
            e = mcrfpy.Entity(grid_pos=(rng.randint(0, side - 1), rng.randint(0, side - 1)),
                              texture=mcrfpy.default_texture, sprite_index=84)
            g.entities.append(e)
            ents.append(e)
        col = g.entities
        while len(col):
            col.remove(col[len(col) - 1])
    return reps * n_ent * 2


BENCHES = [
    Bench("grid_alloc",        "construct+destroy 600x600 grid w/2 layers x12",  3, bench_grid_alloc),
    Bench("grid_fill",         "set walkable+transparent on 400x400 cells",       3, bench_grid_fill),
    Bench("layer_fill",        "500x500 layers: fills + 60 fill_rect windows",    3, bench_layer_fill),
    Bench("layer_edit_buffer", "#335 edit() buffer writes on 400x400 ColorLayer", 3, bench_layer_edit_buffer),
    Bench("step_swarm",        "1000 NOISE4 entities x 30 turns on 60x60",        3, bench_step_swarm),
    Bench("fov_storm",         "1500 compute_fov(r=20) on 200x200",               3, bench_fov_storm),
    Bench("path_queries",      "600 A* queries on open 120x120",                  3, bench_path_queries),
    Bench("entity_churn",      "add+remove 800 entities x8 on 80x80",             3, bench_entity_churn),
]


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------
def _git_short():
    # The engine forbids subprocess spawns; read HEAD directly.
    try:
        gitdir = os.path.normpath(os.path.join(HERE, "..", "..", ".git"))
        head = open(os.path.join(gitdir, "HEAD")).read().strip()
        if head.startswith("ref:"):
            ref = head.split(" ", 1)[1]
            return open(os.path.join(gitdir, ref)).read().strip()[:10]
        return head[:10]
    except Exception:
        return "unknown"


def _print_table(results):
    print("=" * 78)
    print("THE CRUCIBLE -- wall-clock (fastest of %d reps), headless" % results[0]["reps"])
    print("-" * 78)
    print("%-18s %10s %14s %10s  %s" % ("bench", "best_ms", "us/work", "rss_mb", "desc"))
    print("-" * 78)
    for r in results:
        if r.get("status") == "unsupported":
            print("%-18s %10s %14s %10.1f  %s"
                  % (r["name"], "UNSUPP", "-", r["rss_peak_mb"], r["desc"]))
        else:
            print("%-18s %10.2f %14.4f %10.1f  %s"
                  % (r["name"], r["best_ms"], r["us_per_work"], r["rss_peak_mb"], r["desc"]))
    print("=" * 78)


def _print_compare(results, baseline):
    base_by = {b["name"]: b for b in baseline.get("benches", [])}
    print("A/B vs baseline  (%s @ %s)  -- lower ms is better; -N%% = faster now"
          % (baseline.get("version", "?"), baseline.get("commit", "?")))
    print("-" * 78)
    print("%-18s %12s %12s %10s" % ("bench", "base_ms", "now_ms", "delta"))
    print("-" * 78)
    ratios = []
    for r in results:
        b = base_by.get(r["name"])
        if r.get("status") == "unsupported" or (b and b.get("status") == "unsupported"):
            print("%-18s %12s %12s %10s" % (r["name"], "--", "--", "unsupp"))
            continue
        if not b:
            print("%-18s %12s %12.2f %10s" % (r["name"], "--", r["best_ms"], "new"))
            continue
        base_ms = b["best_ms"]
        now_ms = r["best_ms"]
        if base_ms > 0:
            pct = (now_ms - base_ms) / base_ms * 100.0
            ratios.append(now_ms / base_ms)
            tag = "%+.1f%%" % pct
        else:
            tag = "n/a"
        print("%-18s %12.2f %12.2f %10s" % (r["name"], base_ms, now_ms, tag))
    print("-" * 78)
    if ratios:
        geo = 1.0
        for x in ratios:
            geo *= x
        geo = geo ** (1.0 / len(ratios))
        print("geomean now/base: %.3f  (%.1f%% %s overall)"
              % (geo, abs(geo - 1.0) * 100.0, "faster" if geo < 1.0 else "slower"))
    print("=" * 78)


def main():
    cap = _cap()
    if cap is not None:
        print("[safety] address-space cap: %.0f MB" % cap)

    only = os.environ.get("MCRF_CRUCIBLE_ONLY", "").strip()
    only_set = set(s.strip() for s in only.split(",") if s.strip()) if only else None

    results = []
    for b in BENCHES:
        if only_set and b.name not in only_set:
            continue
        sys.stdout.write("  running %-18s ... " % b.name)
        sys.stdout.flush()
        res = b.measure(seed=1337)
        results.append(res)
        sys.stdout.write("%.2f ms  (rss %.0f MB)\n" % (res["best_ms"], res["rss_peak_mb"]))
        sys.stdout.flush()

    print("")
    _print_table(results)

    record = {
        "schema": 1,
        "kind": "crucible",
        "version": getattr(mcrfpy, "__version__", "?"),
        "commit": _git_short(),
        "benches": results,
    }

    out = os.environ.get("MCRF_CRUCIBLE_OUT", "").strip()
    if out:
        with open(out, "w") as f:
            json.dump(record, f, indent=2)
        print("wrote %s" % out)

    base_path = os.environ.get("MCRF_CRUCIBLE_BASELINE", "").strip()
    if base_path and os.path.exists(base_path):
        with open(base_path) as f:
            baseline = json.load(f)
        print("")
        _print_compare(results, baseline)

    sys.exit(0)


if __name__ == "__main__":
    main()
