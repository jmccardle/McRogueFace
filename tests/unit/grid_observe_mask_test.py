#!/usr/bin/env python3
"""
GridData.observe() / mcrfpy.VisibilityMask -- masked observation snapshot
===========================================================================

`observe()` projects a grid's cell state and entity list through a field-of-view
mask and returns an inert snapshot dict:

    {"tick": int, "mask": VisibilityMask, "walkable": frozenset, "transparent": frozenset,
     "entities": tuple[dict]}

This test is built around one standing rule from the review brief: **every positive
assertion is paired with a demonstration that it fails when the thing under test is
removed.** A test that always passes is not a gate. Concretely:

  - Section 1 shows the mask restricts (bounded < unmasked), that removing the mask
    un-restricts it, that reopening a wall (with the mask kept) changes the result
    -- proving the mask reflects live grid state rather than being fabricated from
    the call arguments -- and that a radius bound restricts further still.
  - Section 2 shows a mutation to the *live* entity changes a *new* snapshot but not
    an *old* one already taken -- proving the snapshot is inert data, not a view.
  - Section 3 shows the tick is an exact, countable measurement (K steps -> tick +K),
    and that a stored mask's tick/cells do not change even after further steps and a
    grid mutation -- proving it is a record of a past instant, not a live query.
  - Section 4 exercises the mask's read/iteration protocol and every documented
    argument-validation error path.
  - Section 5 cross-checks the mask against the engine's PRE-EXISTING FOV API
    (compute_fov/is_in_fov) cell by cell, so the mask cannot be an independent
    invention that merely looks plausible -- and measures that the occluder is
    doing real work (visible cell count is far below the grid area).
  - Section 6 measures resident-set growth across 5000 projections. observe()
    allocates a few hundred Python objects per call; a missing decref anywhere in
    the projection would show up here as tens of MB, so the number is a gate rather
    than a formality.

Every number this test relies on was measured against the live binary first (see the
Section 1 item 5 comment below) rather than asserted into existence.

This file is also the target of a C++ mutation A/B recorded in the task report: with
`observe()` altered to ignore the mask, to leak entities past the mask, to emit
`labels` as a plain set, or to re-read the tick on access, this file FAILS. It is a
gate, not a description.
"""

import gc
import sys

import mcrfpy


def rss_kb():
    """Resident set size in KB, read from /proc. No fallback: if this cannot be read the
    leak check is not running, and a leak check that silently does nothing is worse than
    no leak check at all."""
    with open("/proc/self/statm") as fh:
        pages = int(fh.read().split()[1])
    return pages * 4  # 4 KB pages

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


def make_grid(w, h):
    """A fresh scene + grid, every cell walkable and transparent."""
    scene_counter[0] += 1
    scene = mcrfpy.Scene(f"observe_test_{scene_counter[0]}")
    mcrfpy.current_scene = scene
    grid = mcrfpy.Grid(grid_size=(w, h))
    scene.children.append(grid)
    for y in range(h):
        for x in range(w):
            pt = grid.at(x, y)
            pt.walkable = True
            pt.transparent = True
    return grid


def section1_mask_restricts():
    print("Section 1: the mask restricts, and removing it un-restricts")
    grid = make_grid(12, 12)
    gd = grid.grid_data

    # Opaque column at x=5 separates near (x=3) from far (x=8), as seen from (2, 6).
    for y in range(12):
        grid.at(5, y).transparent = False

    near = mcrfpy.Entity((3, 6), grid=grid)
    near.name = "near"
    far = mcrfpy.Entity((8, 6), grid=grid)
    far.name = "far"

    # 1. Bounded observe: occlusion applies, far is behind the wall.
    bounded = gd.observe(origin=(2, 6))
    bounded_names = {e["name"] for e in bounded["entities"]}
    check("bounded entity names", bounded_names, {"near"})
    check_true("(8,6) not in bounded mask", (8, 6) not in bounded["mask"])

    # 2. Mutation check A: remove the mask entirely (unbounded observe()).
    unmasked = gd.observe()
    unmasked_names = {e["name"] for e in unmasked["entities"]}
    check("unmasked entity names", unmasked_names, {"near", "far"})
    check_true("(8,6) in unmasked mask", (8, 6) in unmasked["mask"])
    print(f"  len(bounded mask)={len(bounded['mask'])}  len(unmasked mask)={len(unmasked['mask'])}")
    check_true("bounded mask is strictly smaller than unmasked mask",
               len(bounded["mask"]) < len(unmasked["mask"]))

    # 3. Mutation check B: reopen the wall, keep the mask, rerun the IDENTICAL call.
    #    If observe() fabricated its result from the arguments alone rather than
    #    reading live grid state, this would report the same thing as step 1.
    for y in range(12):
        grid.at(5, y).transparent = True
    reopened = gd.observe(origin=(2, 6))
    reopened_names = {e["name"] for e in reopened["entities"]}
    check_true("far is observed once the wall is reopened", "far" in reopened_names)
    check_true("(8,6) in mask once the wall is reopened", (8, 6) in reopened["mask"])

    # 4. Radius bound, on the now-open grid.
    r2 = gd.observe(origin=(2, 6), fov_radius=2)
    r2_names = {e["name"] for e in r2["entities"]}
    print(f"  len(r2 mask)={len(r2['mask'])}  len(unmasked mask)={len(unmasked['mask'])}")
    check_true("near present within radius 2", "near" in r2_names)
    check_true("far absent beyond radius 2", "far" not in r2_names)
    check_true("radius-bounded mask strictly smaller than unmasked mask",
               len(r2["mask"]) < len(unmasked["mask"]))

    # 5. ALL is the limit case of the bounded case, not a special branch.
    #    MEASURED FIRST (see report): on this fully-open 12x12 grid,
    #    gd.observe()["mask"].cells == gd.observe(origin=(2,6), fov_radius=None)["mask"].cells
    #    exactly -- both are 144/144 cells, symmetric difference is empty. So the
    #    assertion below is equality, not a weakened approximation.
    all_cells = gd.observe()["mask"].cells
    origin_unbounded_cells = gd.observe(origin=(2, 6), fov_radius=None)["mask"].cells
    sym_diff = all_cells ^ origin_unbounded_cells
    print(f"  len(all_cells)={len(all_cells)}  len(origin_unbounded_cells)={len(origin_unbounded_cells)}  "
          f"symmetric_difference={len(sym_diff)}")
    check("unbounded observe() and origin+fov_radius=None agree exactly (limit case, not a special branch)",
          all_cells, origin_unbounded_cells)


def section2_entity_fields():
    print("Section 2: entity fields (req 4)")
    grid = make_grid(12, 12)
    gd = grid.grid_data

    probe = mcrfpy.Entity((4, 4), grid=grid)
    probe.name = "probe"
    probe.labels = {"hostile", "fast"}
    probe.turn_order = 3

    old_snap = gd.observe()
    check("exactly one entity in snapshot", len(old_snap["entities"]), 1)
    e = old_snap["entities"][0]

    check_true("labels type is exactly frozenset", type(e["labels"]) is frozenset)
    check_true("'hostile' in labels", "hostile" in e["labels"])
    check_true("'friendly' not in labels", "friendly" not in e["labels"])
    check("cell_pos value", e["cell_pos"], (4, 4))
    check_true("cell_pos type is exactly tuple", type(e["cell_pos"]) is tuple)
    check_true("cell_pos components are int",
               all(type(c) is int for c in e["cell_pos"]))
    check("turn_order", e["turn_order"], 3)

    # Mutation check: change the live entity, take a NEW snapshot, and confirm the
    # OLD snapshot (already captured above) is unaffected -- it must be inert data,
    # not a live view into the entity.
    probe.labels = {"friendly"}
    probe.turn_order = 9
    probe.cell_pos = (7, 7)

    new_snap = gd.observe()
    new_e = new_snap["entities"][0]
    check("new snapshot reports new labels", new_e["labels"], frozenset({"friendly"}))
    check("new snapshot reports new turn_order", new_e["turn_order"], 9)
    check("new snapshot reports new cell_pos", new_e["cell_pos"], (7, 7))

    old_e = old_snap["entities"][0]
    check("OLD snapshot still reports old labels", old_e["labels"], frozenset({"hostile", "fast"}))
    check("OLD snapshot still reports old turn_order", old_e["turn_order"], 3)
    check("OLD snapshot still reports old cell_pos", old_e["cell_pos"], (4, 4))


def section3_tick():
    print("Section 3: the tick (req 3)")
    grid = make_grid(6, 6)
    gd = grid.grid_data

    # IDENTITY first, then the delta. Freeze v1 §4 and §13.3 do not say the tick advances
    # in step with current_frame -- they say the tick IS current_frame. A delta cannot
    # establish that: any affine offset of the counter (including an off-by-one at the
    # barrier, the realistic mistake) produces the same delta forever. get_metrics()'s
    # current_frame is the engine's own reading of the same counter.
    for probe_step in range(4):
        snap = gd.observe()
        frame = mcrfpy.get_metrics()["current_frame"]
        check(f"snap['tick'] IS current_frame (probe {probe_step})", snap["tick"], frame)
        check(f"snap['mask'].tick IS current_frame (probe {probe_step})",
              snap["mask"].tick, frame)
        mcrfpy.step(1.0)

    K = 7
    t0 = gd.observe()["tick"]
    for _ in range(K):
        mcrfpy.step(1.0)
    t1 = gd.observe()["tick"]
    print(f"  t0={t0}  t1={t1}  delta={t1 - t0}  (K={K})")
    check("tick advances by EXACTLY K after K step() calls", t1 - t0, K)
    check("and the tick is still current_frame after those steps",
          t1, mcrfpy.get_metrics()["current_frame"])

    snap = gd.observe()
    check("snap['tick'] == snap['mask'].tick", snap["tick"], snap["mask"].tick)

    # Storability: a held mask is a record of a past tick, not a live query.
    held = snap["mask"]
    tick_before = held.tick
    cells_before = len(held.cells)
    for _ in range(3):
        mcrfpy.step(1.0)
    grid.at(0, 0).transparent = False  # mutate the grid after taking the mask
    check("held mask.tick unchanged after further steps", held.tick, tick_before)
    check("held mask cell count unchanged after grid mutation", len(held.cells), cells_before)


def section4_protocol_and_validation():
    print("Section 4: mask protocol and argument validation")
    grid = make_grid(6, 6)
    gd = grid.grid_data
    snap = gd.observe()
    mask = snap["mask"]

    check("len(mask)", len(mask), 36)
    check_true("(3,3) in mask", (3, 3) in mask)
    ordered = list(mask)
    row_major = sorted(ordered, key=lambda p: (p[1], p[0]))
    check("list(mask) is already in row-major order", ordered, row_major)
    check_true("repr(mask) is non-empty", len(repr(mask)) > 0)
    print(f"  repr(mask) = {mask!r}")

    check("mask.origin (unbounded)", mask.origin, None)
    check("mask.fov_radius (unbounded)", mask.fov_radius, None)
    check("mask.grid_size", mask.grid_size, (6, 6))
    check("mask.light_walls default", mask.light_walls, True)
    check("mask.algorithm default", mask.algorithm, int(mcrfpy.FOV.BASIC))

    check_true("mask.cells type is frozenset", type(mask.cells) is frozenset)
    check("set(iter(mask)) == mask.cells", set(iter(mask)), mask.cells)

    try:
        mask.tick = 5
        failures.append("mask.tick = 5 did not raise AttributeError")
        print("  FAIL mask.tick = 5 did not raise AttributeError")
    except AttributeError as ex:
        print(f"  ok   mask.tick = 5 raised AttributeError: {ex}")

    try:
        mcrfpy.VisibilityMask()
        failures.append("mcrfpy.VisibilityMask() did not raise TypeError")
        print("  FAIL mcrfpy.VisibilityMask() did not raise TypeError")
    except TypeError as ex:
        print(f"  ok   mcrfpy.VisibilityMask() raised TypeError: {ex}")

    try:
        gd.observe(fov_radius=3)
        failures.append("observe(fov_radius=3) without origin did not raise ValueError")
        print("  FAIL observe(fov_radius=3) without origin did not raise ValueError")
    except ValueError as ex:
        print(f"  ok   observe(fov_radius=3) without origin raised ValueError: {ex}")

    try:
        gd.observe(origin=(99, 99))
        failures.append("observe(origin=(99,99)) did not raise ValueError")
        print("  FAIL observe(origin=(99,99)) did not raise ValueError")
    except ValueError as ex:
        print(f"  ok   observe(origin=(99,99)) raised ValueError: {ex}")

    for bad_radius in (0, -1):
        try:
            gd.observe(origin=(2, 2), fov_radius=bad_radius)
            failures.append(f"observe(fov_radius={bad_radius}) did not raise ValueError")
            print(f"  FAIL observe(fov_radius={bad_radius}) did not raise ValueError")
        except ValueError as ex:
            print(f"  ok   observe(fov_radius={bad_radius}) raised ValueError: {ex}")

    try:
        result = (1, 2, 3) in mask
        failures.append(f"(1,2,3) in mask did not raise TypeError (got {result!r})")
        print(f"  FAIL (1,2,3) in mask did not raise TypeError, got {result!r}")
    except TypeError as ex:
        print(f"  ok   (1,2,3) in mask raised TypeError: {ex}")

    # walkable/transparent are subsets of mask.cells; a non-walkable cell inside the
    # mask is in mask.cells but not in walkable.
    grid.at(2, 2).walkable = False
    snap2 = gd.observe()
    m2, walkable, transparent = snap2["mask"], snap2["walkable"], snap2["transparent"]
    print(f"  len(mask)={len(m2)}  len(walkable)={len(walkable)}  len(transparent)={len(transparent)}")
    check_true("walkable is a subset of mask.cells", walkable <= m2.cells)
    check_true("transparent is a subset of mask.cells", transparent <= m2.cells)
    check_true("(2,2) in mask.cells", (2, 2) in m2)
    check_true("(2,2) not in walkable (it was made non-walkable)", (2, 2) not in walkable)


def section5_fov_crosscheck():
    """The mask must be the SAME set the engine's pre-existing FOV API reports.

    Without this, `observe()` could compute visibility by some private rule of its own
    that happens to look reasonable, and every other assertion in this file would still
    pass. Comparing against compute_fov()/is_in_fov() -- the API §6.1 [IV] names as the
    engine's native partial-observation mode -- is what ties the new surface to the old.
    """
    print("Section 5: the mask agrees with compute_fov()/is_in_fov(), cell for cell")
    W = H = 15
    grid = make_grid(W, H)
    gd = grid.grid_data

    # A full-height wall at x=7 with a single doorway at (7, 7). The wall is also solid
    # underfoot except at the doorway -- walkability and transparency are independent
    # properties, and making them differ is what stops the walkable/mask comparison below
    # from being trivially true.
    for y in range(H):
        grid.at(7, y).transparent = False
        grid.at(7, y).walkable = False
    grid.at(7, 7).transparent = True
    grid.at(7, 7).walkable = True

    origin, radius = (3, 7), 9
    snap = gd.observe(origin=origin, fov_radius=radius)

    # Same parameters through the OLD API, then read the plane back cell by cell.
    gd.compute_fov(origin, radius=radius, light_walls=True, algorithm=mcrfpy.FOV.BASIC)
    api_cells = frozenset((x, y) for y in range(H) for x in range(W) if gd.is_in_fov(x, y))

    mask_cells = snap["mask"].cells
    print(f"  observe() mask cells = {len(mask_cells)}   is_in_fov() cells = {len(api_cells)}   "
          f"grid area = {W * H}   symmetric_difference = {len(mask_cells ^ api_cells)}")
    check("observe()'s mask is exactly the is_in_fov() set", mask_cells, api_cells)

    # Non-vacuity: if the occluder did nothing, both sets would be the whole grid and the
    # equality above would be trivially true.
    check_true(f"the occluder actually occludes ({len(mask_cells)} of {W * H} cells visible)",
               len(mask_cells) < W * H)
    check_true("the doorway cell (7,7) is visible through the wall", (7, 7) in mask_cells)

    # Beyond the wall, only a cone through the doorway is visible. MEASURED FIRST rather
    # than asserted: the first version of this check guessed that the wall cell (7, 0)
    # would be invisible and was wrong -- light_walls=True lights it, because (6, 0) next
    # to it is visible floor. The engine was right and the guess was wrong, which is the
    # reason this section compares against a measurement instead of an intuition.
    far_side = {(x, y) for (x, y) in mask_cells if x > 7}
    print(f"  cells visible beyond the wall (x > 7) = {len(far_side)} of {7 * H}: "
          f"{sorted(far_side)}")
    check_true("only a narrow cone reaches past the doorway (< 15 of 105 far-side cells)",
               len(far_side) < 15)
    check_true("(8,0), directly behind the wall and far from the doorway, is not visible",
               (8, 0) not in mask_cells)
    check_true("(12,0), deep behind the wall, is not visible", (12, 0) not in mask_cells)

    # ---- The terrain projection, gated under a BOUNDED mask. ----
    #
    # Section 4 checks `walkable <= mask.cells` on an *unbounded* observe, where the mask
    # is the whole grid and the subset relation is true of any set at all -- including the
    # empty set and including an unmasked ground-truth dump. Under a bounded mask it is a
    # real constraint, and these three checks are what the requirement "a projection of
    # GridData, never a flat dump" actually rests on: `mask.cells` is only half of the
    # GridData being projected; `walkable`/`transparent` are the other half.
    walkable, transparent = snap["walkable"], snap["transparent"]
    print(f"  walkable = {len(walkable)}   transparent = {len(transparent)}   "
          f"mask.cells = {len(mask_cells)}   grid area = {W * H}")

    check_true("walkable is a subset of the BOUNDED mask (not of the grid)",
               walkable <= mask_cells)
    check_true("transparent is a subset of the BOUNDED mask (not of the grid)",
               transparent <= mask_cells)

    # Named cell, not a cardinality: (12, 0) is genuinely walkable ground truth and is
    # outside the mask, so it must not appear in the projection.
    check_true("(12,0) is walkable in ground truth", grid.at(12, 0).walkable)
    check_true("(12,0) is outside the mask, so it is absent from walkable",
               (12, 0) not in walkable)
    check_true("(12,0) is transparent in ground truth", grid.at(12, 0).transparent)
    check_true("(12,0) is outside the mask, so it is absent from transparent",
               (12, 0) not in transparent)

    # Cell for cell against the pre-existing per-cell API, the same way the mask itself is
    # checked against is_in_fov(). This is what forbids `walkable` being anything other
    # than exactly "the walkable cells of the mask" -- an empty set and a whole-grid dump
    # both fail here.
    expected_walkable = frozenset((x, y) for (x, y) in mask_cells if grid.at(x, y).walkable)
    expected_transparent = frozenset((x, y) for (x, y) in mask_cells if grid.at(x, y).transparent)
    check("walkable == the walkable cells of the mask, per grid.at()",
          set(walkable), set(expected_walkable))
    check("transparent == the transparent cells of the mask, per grid.at()",
          set(transparent), set(expected_transparent))

    # Non-vacuity for the two equalities above: if every masked cell were walkable and
    # transparent, both would degenerate to `== mask.cells` and would no longer
    # distinguish a real projection from a copy of the mask.
    check_true(f"walkable is strictly smaller than the mask ({len(walkable)} < {len(mask_cells)}), "
               "so the equality above is not a restatement of the mask",
               len(walkable) < len(mask_cells))
    check_true(f"transparent is strictly smaller than the mask "
               f"({len(transparent)} < {len(mask_cells)})",
               len(transparent) < len(mask_cells))


def section6_projection_does_not_leak():
    """5000 projections, measured. Not a formality: each observe() on this grid allocates
    ~400 coordinate tuples, 3 frozensets, a mask, and 40 entity dicts. A single missing
    Py_DECREF in the projection loop leaks on the order of 100 MB over this run."""
    print("Section 6: 5000 projections do not leak")
    grid = make_grid(20, 20)
    gd = grid.grid_data
    for i in range(40):
        e = mcrfpy.Entity((i % 20, i // 20), grid=grid)
        e.name = f"e{i}"
        e.labels = {"alpha", "beta"}

    N = 5000
    # Warm up: let the allocator reach steady state so the measurement is of growth,
    # not of first-touch.
    for _ in range(500):
        gd.observe(origin=(10, 10), fov_radius=12)
    gc.collect()
    before = rss_kb()
    for _ in range(N):
        gd.observe(origin=(10, 10), fov_radius=12)
    gc.collect()
    after = rss_kb()

    probe = gd.observe(origin=(10, 10), fov_radius=12)
    per_call_objects = len(probe["mask"]) + len(probe["entities"]) + 4
    growth = after - before
    print(f"  rss before = {before} KB   after {N} projections = {after} KB   growth = {growth} KB")
    print(f"  (~{per_call_objects} Python objects per call; a full leak would be "
          f"~{N * per_call_objects * 60 // 1024} KB)")
    check_true(f"rss growth over {N} projections stays under 4096 KB (got {growth} KB)",
               growth < 4096)


def main():
    section1_mask_restricts()
    section2_entity_fields()
    section3_tick()
    section4_protocol_and_validation()
    section5_fov_crosscheck()
    section6_projection_does_not_leak()

    print()
    if failures:
        for f in failures:
            print(f"FAILURE: {f}")
        print("FAIL")
        sys.exit(1)
    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
