#!/usr/bin/env python3
"""Regression #402: GridData.observe() must not disturb the shared FOV state.

THE DEFECT
----------
`compute_fov(pos, radius)` / `is_in_fov((x, y))` are a TWO-CALL API over ONE shared
per-grid TCOD FOV buffer: the compute writes the buffer's fov bits, the read consumes
them. Anything that computes in between silently re-answers the first caller's question
from a different vantage point.

`observe(origin=..., fov_radius=...)` used to call exactly that pair
(`GridData::computeFOV()` + `isInFOV()` per cell). So a background observer projecting
from an NPC's position clobbered whatever FOV the player or the renderer had just
computed. `observe()` with no origin never touched FOV state at all.

The fix is `GridData::computeFOVInto()` (src/GridData.cpp): the FOV is computed into a
scratch TCODMap that is a LOCAL of the call, so `observe()` is side-effect-free with or
without an origin, and does not participate in the #292 dedup memo either.

ASYMMETRIC FIXTURES, ON PURPOSE
-------------------------------
Every grid here is 21 wide by 13 tall, the occluder is a COLUMN at x=8 with its doorway
at row y=3, and the origins are (2, 9) / (9, 2) / (18, 11). A transposed grid_size or a
swapped (x, y) is therefore not merely wrong but out-of-bounds or visibly different --
on a square grid with centred origins such a bug is undetectable BY CONSTRUCTION.

Measured on this fixture (numbers, not guesses):
    grid area                  273 cells
    |FOV(P=(2,9),  r=12)|      119
    |FOV(N=(9,2),  r=7)|        81
    |FOV(O2=(18,11), r=5)|      43
    FOV(P) symmetric difference FOV(N)  = 152 cells

WHAT EACH SECTION IS
--------------------
Section 1 is the deterministic mechanism gate and fails on the pre-fix engine every
time, single-threaded, with no race required.

Sections 2 and 3 are concurrency arms, and it is worth being blunt about which half of
each is the actual gate:

  * Section 2's GATE is the MAIN thread's `compute_fov()` -> `is_in_fov()` pair. Those
    are two separate Python calls, so a GIL switch can land between them and let a
    background pre-fix `observe()` rewrite the buffer before the reads happen.
    Section 2's two background observers checking their OWN returned masks is a
    REGRESSION GUARD, not a gate: `observe()` never releases the GIL, so two observers'
    return values could not interleave and were already correct pre-fix. It guards
    against a "fix" that isolated via SHARED scratch state (one scratch buffer per grid
    rather than per call), which would break exactly there.

  * Section 3's GATE is again the main thread's compute/read pair, run alongside a real
    render. The entity-perspective arm is a REGRESSION GUARD: the renderer reads a
    materialised per-entity `perspective_map` (a DiscreteMap), NOT the TCOD FOV buffer,
    and `UIEntity::updateVisibility()` does its internal computeFOV+isInFOV inside a
    single C call holding the GIL, so it is atomic and could not be torn pre-fix either.

Section 4 covers the #292 dedup memo (`fov_last_x/y/radius/light_walls/algo` +
`fov_dirty` in src/GridData.h). Stated plainly: a faithful pre-fix control does NOT make
section 4 fail, and it cannot -- the pre-fix `observe()` left the memo and the buffer
CONSISTENT with each other, so a later `compute_fov()` with different parameters always
missed the memo and recomputed. Section 4 is a guard against a PARTIAL fix: one that
isolates the buffer but still stamps `fov_last_*`, which would make a later shared
`compute_fov()` a no-op that answers from the wrong buffer. That failure mode is not
reachable from Python, so section 4 carries its own in-file positive control (4c) to
prove its equality checks are measuring something rather than restating a constant.

NON-VACUITY
-----------
Every section's control run is documented in the task report: each `observe()` in this
file goes through the module-level `observe()` helper, and the control replaces its body
with a faithful simulation of the pre-fix engine --

    def observe(gd, **kwargs):
        if kwargs.get("origin") is not None:          # what pre-fix observe() did to
            gd.compute_fov(kwargs["origin"],          # the SHARED buffer, before
                           radius=kwargs.get("fov_radius") or 0)   # returning its (correct) mask
        return gd.observe(**kwargs)

Run: ./mcrogueface --headless --exec ../tests/regression/issue_402_observe_fov_isolation_test.py
"""

import os
import shutil
import sys
import tempfile
import threading
import time

import mcrfpy
from mcrfpy import automation

W, H = 21, 13                 # wider than tall, deliberately
WALL_X = 8                    # occluding COLUMN
DOOR_Y = 3                    # doorway at an asymmetric row
P, R_P = (2, 9), 12           # "player" origin, west of the wall
N, R_N = (9, 2), 7            # "NPC" observer -- (2,9) transposed, east of the wall
O2, R_O2 = (18, 11), 5        # second observer, far corner

# Concurrency shaping. A small switch interval maximises the number of places a GIL
# switch can land between the main thread's compute_fov() and its is_in_fov() reads --
# that is the window the pre-fix defect lives in, so widening it makes the gate sharper
# rather than looser. Restored at the end of main().
SWITCH_INTERVAL = 1e-4
# Per participant. The >= 30 gate is checked separately and is the requirement; 200 is
# what this costs (~20 ms for the whole section), and more cycles means more places a
# clobber could land, so the number is chosen for sensitivity, not for the gate.
S2_TARGET_ITERS = 200
S2_DEADLINE = 3.0
S3_FRAMES = 25                # each frame forces a real render (~60 ms in headless)
S3_DEADLINE = 6.0

failures = []
scene_counter = [0]


def check(label, actual, expected):
    ok = actual == expected
    print(f"  {'ok  ' if ok else 'FAIL'} {label}: got {actual!r}, expected {expected!r}")
    if not ok:
        failures.append(f"{label}: got {actual!r}, expected {expected!r}")
    return ok


def check_true(label, cond):
    print(f"  {'ok  ' if cond else 'FAIL'} {label}")
    if not cond:
        failures.append(label)
    return cond


def check_set(label, actual, expected):
    """Set EQUALITY, reported by its difference rather than by dumping 119 tuples.

    The assertion is `actual == expected` -- never a cardinality comparison, because two
    different vantage points on this fixture can see the same number of cells. The
    printed symmetric difference is what makes a failure diagnosable.
    """
    ok = actual == expected
    diff = actual ^ expected
    detail = (f"|got| = {len(actual)}, |expected| = {len(expected)}, "
              f"symmetric difference = {len(diff)}")
    if diff:
        detail += f", e.g. {sorted(diff)[:8]}"
    print(f"  {'ok  ' if ok else 'FAIL'} {label}: {detail}")
    if not ok:
        failures.append(f"{label}: {detail}")
    return ok


def observe(gd, **kwargs):
    """Every observe() in this file goes through here.

    The indirection exists for one reason: the control run that proves this file is a
    gate patches THIS function to simulate the pre-fix engine (see the module docstring),
    so the control differs from the shipped test by exactly one edit in exactly one
    place. It adds nothing to the shipped behaviour.
    """
    return gd.observe(**kwargs)


def make_grid():
    """A 21x13 grid, all open, with an opaque+solid column at x=8 and a doorway at y=3."""
    scene_counter[0] += 1
    scene = mcrfpy.Scene(f"issue_402_{scene_counter[0]}")
    mcrfpy.current_scene = scene
    grid = mcrfpy.Grid(grid_size=(W, H), pos=(0, 0), size=(W * 16, H * 16))
    scene.children.append(grid)
    for y in range(H):
        for x in range(W):
            pt = grid.at(x, y)
            pt.walkable = True
            pt.transparent = True
    for y in range(H):
        grid.at(WALL_X, y).transparent = False
        grid.at(WALL_X, y).walkable = False
    grid.at(WALL_X, DOOR_Y).transparent = True
    grid.at(WALL_X, DOOR_Y).walkable = True
    return grid


ALL_CELLS = tuple((x, y) for y in range(H) for x in range(W))


def read_fov(gd):
    """The shared FOV buffer, read cell by cell -- the SECOND half of the two-call API.

    This is deliberately a Python loop of separate is_in_fov() calls: that is exactly how
    a game reads FOV, and it is exactly where a GIL switch can let another thread's
    compute land in the middle.
    """
    return frozenset(c for c in ALL_CELLS if gd.is_in_fov(c[0], c[1]))


def compute_and_read(gd, origin, radius):
    gd.compute_fov(origin, radius=radius)
    return read_fov(gd)


# =========================================================================
# Section 1 -- the deterministic mechanism gate (single-threaded)
# =========================================================================

def section1_mechanism():
    print("Section 1: observe() does not disturb a compute_fov() already in flight "
          "(single-threaded, deterministic)")
    grid = make_grid()
    gd = grid.grid_data

    # The player computes. This is the question the shared buffer now holds the answer to.
    golden_P = compute_and_read(gd, P, R_P)

    # A background observer projects from somewhere else entirely. Pre-fix this WAS a
    # compute_fov(N) against the same buffer.
    snap = observe(gd, origin=N, fov_radius=R_N)

    # ...and the player finishes reading. Set equality, not cardinality: two different
    # vantage points can easily see the same NUMBER of cells.
    after = read_fov(gd)
    check_set("the FOV buffer still answers the player's question after observe(origin=NPC)",
              after, golden_P)

    # ---- Non-vacuity, asserted with numbers rather than assumed. ----
    golden_N = compute_and_read(gd, N, R_N)
    sym = golden_P ^ golden_N
    print(f"  grid area = {W * H}   |FOV(P={P}, r={R_P})| = {len(golden_P)}   "
          f"|FOV(N={N}, r={R_N})| = {len(golden_N)}   symmetric difference = {len(sym)}")
    check_true(f"FOV(P) and FOV(N) differ by a wide margin ({len(sym)} cells > 20), so the "
               "equality above cannot hold by the two answers coincidentally agreeing",
               len(sym) > 20)
    check_true(f"|FOV(P)| = {len(golden_P)} is neither 0 nor the whole grid ({W * H}), so the "
               "occluder and the radius are both doing real work",
               0 < len(golden_P) < W * H)

    # ---- observe()'s OWN answer must still be right. ----
    # Without this, a "fix" that isolated the shared buffer by returning garbage -- an
    # empty mask, the whole grid, the previous call's mask -- would pass everything above.
    check_set("observe(origin=N)'s mask is exactly the compute_fov(N)+is_in_fov() set",
              snap["mask"].cells, golden_N)

    # ---- Regression guard: the UNBOUNDED case never touched FOV state, even pre-fix. ----
    # Labelled as a guard, not a gate: this arm passes on the pre-fix engine.
    golden_P2 = compute_and_read(gd, P, R_P)
    observe(gd, origin=None)
    check_set("regression guard -- unbounded observe() leaves the FOV state untouched "
              "(this arm passed pre-fix too)", read_fov(gd), golden_P2)


# =========================================================================
# Section 2 -- two concurrent observers on one grid
# =========================================================================

def section2_concurrent_observers():
    """GATE: the main thread's compute_fov() -> is_in_fov() pair, which a GIL switch can
    split. GUARD: each observer's own returned mask -- observe() holds the GIL for its
    whole duration, so those could not interleave pre-fix; they guard against a fix that
    isolated using shared scratch state instead of a per-call local."""
    print("Section 2: two background observers + a reading main thread, one grid")
    grid = make_grid()
    gd = grid.grid_data

    golden_1 = compute_and_read(gd, N, R_N)
    golden_2 = compute_and_read(gd, O2, R_O2)
    golden_P = compute_and_read(gd, P, R_P)
    print(f"  goldens: |FOV(P)| = {len(golden_P)}  |FOV(O1={N}, r={R_N})| = {len(golden_1)}  "
          f"|FOV(O2={O2}, r={R_O2})| = {len(golden_2)}")
    check_true("the three observers' fields of view are pairwise different, so a mixed-up "
               "answer is detectable",
               golden_P != golden_1 and golden_P != golden_2 and golden_1 != golden_2)

    stop = threading.Event()
    # [iterations, mismatches], published live so the main thread can wait for each
    # observer to reach its own iteration gate instead of guessing at a sleep.
    stats = {"obs1": [0, 0], "obs2": [0, 0]}
    errors = []

    def observer(name, origin, radius, golden):
        counters = stats[name]
        try:
            while not stop.is_set():
                mask = observe(gd, origin=origin, fov_radius=radius)["mask"]
                counters[0] += 1
                if mask.cells != golden:
                    counters[1] += 1
        except BaseException as exc:  # noqa: BLE001 -- re-reported on the main thread
            errors.append(f"{name}: {exc!r}")

    threads = [
        threading.Thread(target=observer, args=("obs1", N, R_N, golden_1),
                         name="obs1", daemon=True),
        threading.Thread(target=observer, args=("obs2", O2, R_O2, golden_2),
                         name="obs2", daemon=True),
    ]
    for t in threads:
        t.start()

    main_iters = 0
    main_mismatches = 0
    deadline = time.monotonic() + S2_DEADLINE
    while main_iters < S2_TARGET_ITERS and time.monotonic() < deadline:
        gd.compute_fov(P, radius=R_P)
        got = read_fov(gd)          # <-- the split-able pair; the gate lives here
        main_iters += 1
        if got != golden_P:
            main_mismatches += 1
        mcrfpy.step(0.016)

    # Let the observers reach their own iteration gate before stopping them.
    while (time.monotonic() < deadline
           and min(stats["obs1"][0], stats["obs2"][0]) < S2_TARGET_ITERS
           and all(t.is_alive() for t in threads)):
        time.sleep(0.005)

    stop.set()
    for t in threads:
        t.join(timeout=2.0)

    for name, t in zip(("obs1", "obs2"), threads):
        if t.is_alive():
            errors.append(f"{name} thread still alive after join(timeout=2.0)")

    o1_iters, o1_bad = stats["obs1"]
    o2_iters, o2_bad = stats["obs2"]
    print(f"  iterations: main = {main_iters}   obs1 = {o1_iters}   obs2 = {o2_iters}")
    print(f"  mismatches: main = {main_mismatches}   obs1 = {o1_bad}   obs2 = {o2_bad}")

    for err in errors:
        failures.append(f"section 2 worker error -- {err}")
        print(f"  FAIL section 2 worker error -- {err}")

    # Iteration gates FIRST: a thread that never ran proves nothing, and zero mismatches
    # out of zero iterations is the classic vacuous pass.
    check_true(f"main thread completed >= 30 compute/read cycles (got {main_iters})",
               main_iters >= 30)
    check_true(f"obs1 completed >= 30 observe() calls (got {o1_iters})", o1_iters >= 30)
    check_true(f"obs2 completed >= 30 observe() calls (got {o2_iters})", o2_iters >= 30)

    check("GATE -- main thread's is_in_fov() reads matched FOV(P) on every cycle "
          "(mismatch count)", main_mismatches, 0)
    check("guard -- obs1's own mask was correct on every call (mismatch count)", o1_bad, 0)
    check("guard -- obs2's own mask was correct on every call (mismatch count)", o2_bad, 0)


# =========================================================================
# Section 3 -- an observer against an active renderer
# =========================================================================

def section3_renderer():
    """GATE: the main thread's compute_fov()/is_in_fov() pair, run inside a real frame
    loop. GUARD: the entity's perspective_map -- the renderer reads that materialised
    DiscreteMap, not the TCOD FOV buffer, and update_visibility() is one atomic C call
    under the GIL, so it could not be torn pre-fix."""
    print("Section 3: a background observer while the main thread renders a perspective view")
    grid = make_grid()
    gd = grid.grid_data

    player = mcrfpy.Entity(P, grid=grid)
    player.name = "player"
    grid.perspective = player

    # The perspective map is built from the GRID's own fov_radius, not from R_P.
    golden_persp = compute_and_read(gd, P, gd.fov_radius)
    golden_P = compute_and_read(gd, P, R_P)
    print(f"  grid.grid_data.fov_radius = {gd.fov_radius}   |perspective FOV| = "
          f"{len(golden_persp)}   |FOV(P, r={R_P})| = {len(golden_P)}")
    check_true("the perspective FOV and the read FOV are different sets, so the two arms "
               "below are not the same measurement twice",
               golden_persp != golden_P)

    stop = threading.Event()
    stats = {}
    errors = []

    def hammer():
        iters = 0
        mismatches = 0
        try:
            while not stop.is_set():
                mask = observe(gd, origin=N, fov_radius=R_N)["mask"]
                iters += 1
                if len(mask.cells) == 0:
                    mismatches += 1
        except BaseException as exc:  # noqa: BLE001
            errors.append(repr(exc))
        finally:
            stats["obs"] = (iters, mismatches)

    thread = threading.Thread(target=hammer, name="obs-render", daemon=True)
    thread.start()

    tmpdir = tempfile.mkdtemp(prefix="issue402_")
    shot = os.path.join(tmpdir, "frame.png")
    frames = 0
    fov_bad = 0
    persp_bad = 0
    render_failed = 0
    frame0 = mcrfpy.get_metrics()["current_frame"]
    deadline = time.monotonic() + S3_DEADLINE
    try:
        while frames < S3_FRAMES and time.monotonic() < deadline:
            # 1. The engine's own FOV consumer: builds/refreshes the entity's
            #    perspective_map (internally compute_fov + is_in_fov, one atomic C call).
            player.update_visibility()

            # 2. A REAL render of the perspective view. automation.screenshot() is the
            #    only screenshot-taking path that forces GameEngine::renderScene() in
            #    headless; there is no bare render() binding, so this is the render.
            if not automation.screenshot(shot):
                render_failed += 1

            # 3. The renderer's input, checked: the materialised perspective map.
            pmap = player.perspective_map
            visible = frozenset(c for c in ALL_CELLS
                                if pmap[c[0], c[1]] == mcrfpy.Perspective.VISIBLE)
            if visible != golden_persp:
                persp_bad += 1

            # 4. Game-style FOV question and answer -- the split-able pair, the gate.
            gd.compute_fov(P, radius=R_P)
            if read_fov(gd) != golden_P:
                fov_bad += 1

            mcrfpy.step(0.016)
            frames += 1
    finally:
        stop.set()
        thread.join(timeout=2.0)
        shutil.rmtree(tmpdir, ignore_errors=True)

    obs_iters, obs_empty = stats.get("obs", (0, 0))
    frame_delta = mcrfpy.get_metrics()["current_frame"] - frame0
    print(f"  frames = {frames}   engine current_frame delta = {frame_delta}   "
          f"observer iterations = {obs_iters}")
    print(f"  fov mismatches = {fov_bad}   perspective mismatches = {persp_bad}   "
          f"failed renders = {render_failed}")

    for err in errors:
        failures.append(f"section 3 observer error -- {err}")
        print(f"  FAIL section 3 observer error -- {err}")
    if thread.is_alive():
        failures.append("section 3 observer thread still alive after join(timeout=2.0)")

    check_true(f"the frame loop actually ran {S3_FRAMES} frames (got {frames})",
               frames >= S3_FRAMES)
    check_true(f"the engine's frame counter actually advanced (delta {frame_delta} >= {S3_FRAMES})",
               frame_delta >= S3_FRAMES)
    check_true(f"the background observer actually ran (>= 30 iterations, got {obs_iters})",
               obs_iters >= 30)
    check("every render succeeded (failure count)", render_failed, 0)
    check("the observer's own masks were never empty (a hammering thread that returned "
          "nothing would make the arms above vacuous)", obs_empty, 0)

    check("GATE -- the main thread's FOV reads were correct on every frame (mismatch count)",
          fov_bad, 0)
    check("guard -- the entity's perspective visible-set was correct on every frame "
          "(mismatch count)", persp_bad, 0)


# =========================================================================
# Section 4 -- observe() leaves no FOV state at all, memo included
# =========================================================================

def section4_memo():
    """GridData::computeFOV() has a dedup memo (fov_last_x/y/radius/light_walls/algo +
    fov_dirty). computeFOVInto() must not participate in it: a scratch computation that
    stamped fov_last_* would make a LATER shared compute_fov() a no-op returning the
    wrong buffer.

    Stated plainly: this section does NOT fail under a faithful pre-fix control, and
    cannot -- pre-fix observe() left memo and buffer consistent, so a differing-parameter
    compute_fov() always missed the memo and recomputed correctly. It is a guard against
    a PARTIAL fix, a failure mode not reachable from Python. 4c is the in-file positive
    control that keeps 4a/4b/4d from being restatements of a constant."""
    print("Section 4: observe() leaves no FOV state at all, including the #292 dedup memo")
    grid = make_grid()
    gd = grid.grid_data

    golden_P = compute_and_read(gd, P, R_P)
    golden_N = compute_and_read(gd, N, R_N)

    # 4a. compute -> observe -> RECOMPUTE the same thing -> read.
    #     Under the fix the memo still reads (P, R_P) after the observe, so the second
    #     compute_fov(P) is a memo hit and a no-op -- which is only correct if the buffer
    #     was never disturbed in the first place.
    compute_and_read(gd, P, R_P)
    observe(gd, origin=N, fov_radius=R_N)
    gd.compute_fov(P, radius=R_P)
    check_set("4a: compute(P) -> observe(N) -> compute(P) -> read still answers P",
              read_fov(gd), golden_P)

    # 4b. The reverse ordering: observe first, then the player's compute.
    observe(gd, origin=N, fov_radius=R_N)
    check_set("4b: observe(N) -> compute(P) -> read answers P",
              compute_and_read(gd, P, R_P), golden_P)

    # 4c. POSITIVE CONTROL for 4a/4b/4d. A shared compute at N DOES change what the reads
    #     return -- so the three equalities above are measurements of a value that can
    #     move, not restatements of a constant. If this check ever passes-as-equal, the
    #     rest of this section is meaningless.
    gd.compute_fov(P, radius=R_P)
    gd.compute_fov(N, radius=R_N)
    moved = read_fov(gd)
    print(f"  4c positive control: after a shared compute at N the read set is "
          f"{len(moved)} cells (was {len(golden_P)}); differs from FOV(P) by "
          f"{len(moved ^ golden_P)} cells")
    check_true("4c: a SHARED compute at N really does move the read set away from FOV(P)",
               moved != golden_P)
    check_set("4c: ...and it moves it to exactly FOV(N)", moved, golden_N)

    # 4d. The memo must not have been poisoned in the other direction either: after an
    #     observe(N), a caller asking the shared API for N's FOV must get a real
    #     computation, not a memo hit against a buffer that still holds P.
    compute_and_read(gd, P, R_P)
    observe(gd, origin=N, fov_radius=R_N)
    check_set("4d: compute(P) -> observe(N) -> compute(N) -> read answers N "
              "(no memo hit answering from P's buffer)",
              compute_and_read(gd, N, R_N), golden_N)


def main():
    prev_switch = sys.getswitchinterval()
    sys.setswitchinterval(SWITCH_INTERVAL)
    t0 = time.monotonic()
    try:
        section1_mechanism()
        section2_concurrent_observers()
        section3_renderer()
        section4_memo()
    finally:
        sys.setswitchinterval(prev_switch)

    print()
    print(f"total runtime: {time.monotonic() - t0:.2f} s")
    if failures:
        for f in failures:
            print(f"FAILURE: {f}")
        sys.exit(1)
    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
