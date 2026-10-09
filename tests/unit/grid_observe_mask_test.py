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
    argument-validation error path, and gates #404 (an unbounded mask reports
    light_walls/algorithm as None) in BOTH directions on one grid: None when
    unbounded, and the real, DIFFERING values on bounded masks taken with
    light_walls True vs False and with two different algorithms.
  - Section 5 cross-checks the mask against the engine's PRE-EXISTING FOV API
    (compute_fov/is_in_fov) cell by cell, so the mask cannot be an independent
    invention that merely looks plausible -- and measures that the occluder is
    doing real work (visible cell count is far below the grid area). It also gates
    mask.origin/fov_radius/tick/grid_size on a BOUNDED mask, which is where those
    fields carry information; section 4 sees them only as the constant None.
  - Section 6 measures resident-set growth across 5000 projections. observe()
    allocates a few hundred Python objects per call; a missing decref anywhere in
    the projection would show up here as tens of MB, so the number is a gate rather
    than a formality.

Every number this test relies on was measured against the live binary first (see the
Section 1 item 5 comment below) rather than asserted into existence.

The grids in sections 4 and 5 are deliberately NON-SQUARE (7x5 and 15x11). On a square
grid a transposed grid_size -- or a transposed origin -- is undetectable by construction,
so a square fixture cannot gate either field no matter what it asserts.

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

    # IDENTITY first, then the delta. The contract is not that the tick advances in
    # step with current_frame -- it is that the tick IS current_frame. A delta cannot
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
    # 7 wide x 5 tall, deliberately NOT square. Every grid in this file used to be
    # square, which made a transposed grid_size (or any other w/h mix-up) invisible:
    # (6, 6) is its own transpose, so `mask.grid_size == (6, 6)` gated nothing.
    W, H = 7, 5
    grid = make_grid(W, H)
    gd = grid.grid_data
    snap = gd.observe()
    mask = snap["mask"]

    check("len(mask)", len(mask), W * H)
    check_true("(3,3) in mask", (3, 3) in mask)
    ordered = list(mask)
    row_major = sorted(ordered, key=lambda p: (p[1], p[0]))
    check("list(mask) is already in row-major order", ordered, row_major)
    check_true("repr(mask) is non-empty", len(repr(mask)) > 0)
    print(f"  repr(mask) = {mask!r}")

    check("mask.origin (unbounded)", mask.origin, None)
    check("mask.fov_radius (unbounded)", mask.fov_radius, None)
    check("mask.grid_size is (w, h) of a NON-SQUARE grid, so a transpose cannot hide",
          mask.grid_size, (W, H))
    # #404: an unbounded mask ran no FOV computation at all -- the visibility plane is
    # filled with 1s -- so light_walls and algorithm did not participate in this result
    # and are reported as None rather than as the values that were parsed and ignored.
    # A mask never reports a setting that had no effect on it; a record that cannot
    # distinguish "shaped the result" from "present and inert" reads as more specified
    # than it is. The both-directions gate is at the end of this section.
    check("mask.light_walls (unbounded: no FOV ran, so None -- #404)", mask.light_walls, None)
    check("mask.algorithm (unbounded: no FOV ran, so None -- #404)", mask.algorithm, None)

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

    # ---- #404, gated in BOTH directions on this one grid. ----
    #
    # `unbounded.light_walls is None` on its own is not a gate: it passes just as well
    # for an implementation that answers None for EVERY mask. Nor is
    # `bounded.light_walls is True`: that passes for one that answers True for every
    # mask. What follows leaves no constant that satisfies all of it -- None unbounded,
    # True for light_walls=True, False for light_walls=False, and each of two bounded
    # masks reporting its OWN, different algorithm.
    #
    # Occluders first. On a fully open grid every algorithm returns every cell and
    # light_walls has no wall to light, so "the two algorithms produce different cell
    # sets" -- the measurement that stops the algorithm field from being pinned without
    # anything noticing -- would be vacuously false. MEASURED on this fixture (7x5,
    # three pillars, origin (0, 2), unlimited radius): BASIC sees 21 cells, SHADOW 27,
    # symmetric difference 6; light_walls=False drops BASIC to 18.
    for px, py in ((2, 1), (3, 2), (4, 3)):
        grid.at(px, py).transparent = False

    bounded_origin = (0, 2)
    unbounded = gd.observe()["mask"]
    check_true("#404 unbounded: origin is None", unbounded.origin is None)
    check_true("#404 unbounded: fov_radius is None", unbounded.fov_radius is None)
    check_true("#404 unbounded: light_walls is None (no FOV ran)", unbounded.light_walls is None)
    check_true("#404 unbounded: algorithm is None (no algorithm ran)", unbounded.algorithm is None)

    lw_on = gd.observe(origin=bounded_origin, light_walls=True)["mask"]
    lw_off = gd.observe(origin=bounded_origin, light_walls=False)["mask"]
    print(f"  bounded from {bounded_origin}: light_walls=True -> {len(lw_on)} cells, "
          f"light_walls=False -> {len(lw_off)} cells")
    check_true("#404 bounded, light_walls=True: reports exactly True",
               lw_on.light_walls is True)
    # The assertion that rules out both "always None" and "always True".
    check_true("#404 bounded, light_walls=False: reports exactly False",
               lw_off.light_walls is False)
    check_true("bounded light_walls is a bool, not an int or a truthy stand-in",
               type(lw_on.light_walls) is bool and type(lw_off.light_walls) is bool)
    # Non-vacuity for the pair above: light_walls actually changed what was seen, so the
    # field is reporting a setting that did something.
    check_true(f"light_walls=False sees strictly fewer cells than light_walls=True "
               f"({len(lw_off)} < {len(lw_on)}), so the recorded flag had an effect",
               len(lw_off) < len(lw_on))

    basic = gd.observe(origin=bounded_origin, algorithm=mcrfpy.FOV.BASIC)["mask"]
    shadow = gd.observe(origin=bounded_origin, algorithm=mcrfpy.FOV.SHADOW)["mask"]
    check("#404 bounded: BASIC mask reports BASIC", basic.algorithm, int(mcrfpy.FOV.BASIC))
    check("#404 bounded: SHADOW mask reports SHADOW", shadow.algorithm, int(mcrfpy.FOV.SHADOW))
    check_true("the two masks report DIFFERENT algorithms, so the field is not pinned",
               basic.algorithm != shadow.algorithm)
    check_true("bounded algorithm is an int",
               type(basic.algorithm) is int and type(shadow.algorithm) is int)
    # ...and the algorithms genuinely disagree on this fixture. Without this, `algorithm`
    # could be a value carried through from the call while the FOV was always computed
    # one way, and nothing above would notice.
    sym = basic.cells ^ shadow.cells
    print(f"  BASIC = {len(basic)} cells, SHADOW = {len(shadow)} cells, "
          f"symmetric_difference = {len(sym)}")
    check_true(f"BASIC and SHADOW produce DIFFERENT cell sets on this fixture "
               f"({len(sym)} cells differ), so the algorithm is not decorative",
               len(sym) > 0)


def section5_fov_crosscheck():
    """The mask must be the SAME set the engine's pre-existing FOV API reports.

    Without this, `observe()` could compute visibility by some private rule of its own
    that happens to look reasonable, and every other assertion in this file would still
    pass. Comparing against compute_fov()/is_in_fov() -- the API §6.1 [IV] names as the
    engine's native partial-observation mode -- is what ties the new surface to the old.
    """
    print("Section 5: the mask agrees with compute_fov()/is_in_fov(), cell for cell")
    # 15 wide x 11 tall -- NON-SQUARE on purpose, see the module docstring.
    W, H = 15, 11
    grid = make_grid(W, H)
    gd = grid.grid_data

    # A full-height wall at x=9 with a single doorway at (9, 7), plus a solid horizontal
    # wall at y=5 across the left side. That splits the left half into a top room and a
    # bottom room, which is what makes the asymmetric origin (3, 7) and its transpose
    # (7, 3) land in DIFFERENT rooms -- see the origin gate below. Both walls are solid
    # underfoot as well as opaque: walkability and transparency are independent
    # properties, and making them differ is what stops the walkable/mask comparison
    # below from being trivially true.
    for y in range(H):
        grid.at(9, y).transparent = False
        grid.at(9, y).walkable = False
    grid.at(9, 7).transparent = True
    grid.at(9, 7).walkable = True
    for x in range(9):
        grid.at(x, 5).transparent = False
        grid.at(x, 5).walkable = False

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
    check_true("the doorway cell (9,7) is visible through the wall", (9, 7) in mask_cells)

    # Beyond the wall, only a cone through the doorway is visible. MEASURED FIRST rather
    # than asserted: an earlier version of this check guessed that the wall cell directly
    # in line with the observer would be invisible and was wrong -- light_walls=True
    # lights it, because the visible floor next to it lights it. The engine was right and
    # the guess was wrong, which is the reason this section compares against a
    # measurement instead of an intuition. Measured here: exactly 3 far-side cells,
    # [(10,7), (11,7), (12,7)], of the 55 beyond the wall.
    far_side_total = (W - 10) * H
    far_side = {(x, y) for (x, y) in mask_cells if x > 9}
    print(f"  cells visible beyond the wall (x > 9) = {len(far_side)} of {far_side_total}: "
          f"{sorted(far_side)}")
    check_true(f"only a narrow cone reaches past the doorway "
               f"({len(far_side)} of {far_side_total} far-side cells)",
               len(far_side) < far_side_total // 4)
    check_true("(10,0), directly behind the wall and far from the doorway, is not visible",
               (10, 0) not in mask_cells)
    check_true("(12,0), deep behind the wall, is not visible", (12, 0) not in mask_cells)
    check_true("(0,0), in the OTHER room on this side of the wall, is not visible",
               (0, 0) not in mask_cells)

    # ---- mask.origin / fov_radius / tick / grid_size, gated on a BOUNDED mask. ----
    #
    # A known hole, and a measured one: two earlier reviewer mutations -- origin recorded
    # transposed as (oy, ox), and fov_radius recorded as radius + 1 -- BOTH survived this
    # file, because origin and fov_radius were only ever asserted in section 4, on an
    # unbounded mask where both are the constant None. On a bounded mask they are the
    # record of what was seen from where, and a wrong value there is a silently wrong
    # belief state.
    #
    # The origin (3, 7) is ASYMMETRIC on purpose and its transpose (7, 3) is a different,
    # in-bounds cell in the OTHER room. That is verified below by measurement, not
    # assumed: if the two origins happened to see the same thing, a transposition would
    # be undetectable no matter what this asserts.
    transposed = (origin[1], origin[0])
    t_cells = gd.observe(origin=transposed, fov_radius=radius)["mask"].cells
    sym = mask_cells ^ t_cells
    print(f"  FOV from {origin} = {len(mask_cells)} cells; from its transpose {transposed} = "
          f"{len(t_cells)} cells; symmetric_difference = {len(sym)} of {W * H}")
    check_true(f"the transposed origin sees a SUBSTANTIALLY different set "
               f"({len(sym)} of {W * H} cells differ), so the origin check below is not vacuous",
               len(sym) > len(mask_cells) // 2)

    mask = snap["mask"]
    check("mask.origin is the origin passed in, not its transpose", mask.origin, origin)
    check_true("mask.origin type is exactly tuple", type(mask.origin) is tuple)
    check_true("mask.origin components are int",
               all(type(c) is int for c in mask.origin))
    # Independent of the equality: the stated vantage point must be a cell the mask can
    # actually see, and the transpose is not one -- these two rooms do not see each other.
    check_true("the origin is inside its own mask", mask.origin in mask_cells)
    check_true("the transposed origin is NOT in this mask (it is in the other room)",
               transposed not in mask_cells)

    check("mask.fov_radius is the radius passed in", mask.fov_radius, radius)
    check("mask.tick is the snapshot's tick", mask.tick, snap["tick"])
    check("mask.grid_size is the source grid's (w, h), non-square", mask.grid_size, (W, H))

    # A SECOND observe from the same origin at a different radius: it must record its own
    # radius and see strictly fewer cells, so fov_radius is read from the call rather than
    # pinned to a constant (or to whatever the first call used). Measured: radius 9 sees
    # 63 cells, radius 3 sees 30.
    tighter_radius = 3
    tighter = gd.observe(origin=origin, fov_radius=tighter_radius)["mask"]
    check("a second observe records its OWN, different fov_radius",
          tighter.fov_radius, tighter_radius)
    check("...from the same origin", tighter.origin, origin)
    check_true(f"...and sees strictly fewer cells ({len(tighter)} < {len(mask_cells)})",
               len(tighter) < len(mask_cells))

    # ---- BOUNDED but UNLIMITED: origin given, fov_radius omitted. ----
    #
    # This is the case that separates #404's ACTUAL rule -- "did an FOV computation run"
    # -- from the plausible wrong rule someone might implement instead, "is fov_radius
    # None". An FOV computation DID run here (occlusion applies; the far room is not
    # visible), so light_walls and algorithm must report their real values, NOT None,
    # even though fov_radius is None. Gate the two apart or an implementation keyed on
    # the wrong field passes every other check in this file. Same defect class as the
    # origin/fov_radius hole above: a field asserted only where it is a constant.
    unlimited = gd.observe(origin=origin)["mask"]
    print(f"  bounded+unlimited from {origin}: {len(unlimited)} cells "
          f"(radius {radius} saw {len(mask_cells)}; grid area {W * H})")
    check("bounded+unlimited: origin is the real origin, not None", unlimited.origin, origin)
    check_true("bounded+unlimited: origin is a tuple, so this mask is bounded",
               type(unlimited.origin) is tuple)
    check("bounded+unlimited: fov_radius is None (no radius cap)", unlimited.fov_radius, None)
    # The point of the whole block:
    check_true("bounded+unlimited: light_walls is True, NOT None -- an FOV computation "
               "ran, so the setting participated (#404 keys on origin, not on fov_radius)",
               unlimited.light_walls is True)
    check("bounded+unlimited: algorithm is the real algorithm, NOT None",
          unlimited.algorithm, int(mcrfpy.FOV.BASIC))

    # ...and "unlimited" is neither vacuously everything nor accidentally identical to a
    # finite radius. MEASURED: 65 cells, exactly the radius-9 set plus (13,7) and (14,7)
    # -- the two cells further down the doorway cone than radius 9 reached -- out of 165.
    check_true(f"bounded+unlimited is a STRICT superset of the radius-{radius} mask "
               f"({len(unlimited)} > {len(mask_cells)}), so the cap really was lifted",
               unlimited.cells > mask_cells)
    check_true(f"bounded+unlimited still occludes ({len(unlimited)} of {W * H} cells), so "
               "'unlimited' is not 'everything'",
               len(unlimited) < W * H)

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
