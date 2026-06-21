"""
Regression test for issue #316 -- Sparse (windowed) perspective writeback in
UIEntity::updateVisibility().

The optimization clips both the demote and promote passes to an AABB sized to
fov_radius around the entity, instead of walking the whole W*H buffer. This test
proves the windowed result is byte-for-byte identical to a full-grid reference,
and that the previous-window demote cache prevents "ghost vision" when an entity
moves.

ASCII-only source (scripts run via --exec use the ASCII codec).
Prints clear PASS/FAIL and sys.exit(0/1).
"""

import mcrfpy
import sys

# --- Test grid configuration -------------------------------------------------
W, H = 60, 60

scene = mcrfpy.Scene("issue316")
mcrfpy.current_scene = scene
grid = mcrfpy.Grid(grid_size=(W, H))
scene.children.append(grid)

# Make the whole grid walkable + transparent, then carve some interior walls so
# that FOV is actually occluded and light_walls lights boundary walls -- this is
# the strongest check that the +1 AABB margin is wide enough.
for gx in range(W):
    for gy in range(H):
        gp = grid.at(gx, gy)
        gp.walkable = True
        gp.transparent = True

# A few interior wall segments (opaque, blocking).
wall_cells = []
for gy in range(10, 50):
    wall_cells.append((25, gy))      # vertical wall
for gx in range(5, 55):
    wall_cells.append((gx, 30))      # horizontal wall
# isolated blocks scattered around
for (bx, by) in [(12, 12), (40, 18), (48, 48), (8, 45), (33, 8), (52, 33)]:
    wall_cells.append((bx, by))

for (wx, wy) in wall_cells:
    gp = grid.at(wx, wy)
    gp.transparent = False
    # keep walkable True so we can also stand near walls; transparency is what
    # matters for FOV.

# Entity to test with.
entity = mcrfpy.Entity(grid_pos=(W // 2, H // 2))
grid.entities.append(entity)

# Algorithms to exercise (names verified against PyFOV.cpp).
ALGOS = [
    ("BASIC", mcrfpy.FOV.BASIC),
    ("DIAMOND", mcrfpy.FOV.DIAMOND),
    ("SHADOW", mcrfpy.FOV.SHADOW),
    ("SYMMETRIC_SHADOWCAST", mcrfpy.FOV.SYMMETRIC_SHADOWCAST),
]

VISIBLE = 2
DISCOVERED = 1
UNKNOWN = 0

failures = []


def move_entity(ex, ey):
    """Move the entity's logical cell position."""
    entity.grid_pos = (ex, ey)


def reference_fov_set(ex, ey, radius, algo):
    """Compute the authoritative in-FOV cell set using the SAME parameters
    updateVisibility() uses internally (radius, light_walls=True, same algo)."""
    grid.compute_fov((ex, ey), radius=radius, light_walls=True, algorithm=algo)
    s = set()
    for gx in range(W):
        for gy in range(H):
            if grid.is_in_fov((gx, gy)):
                s.add((gx, gy))
    return s


def assert_full_equivalence(label, ex, ey, radius, algo):
    """Set up grid FOV params, run windowed update_visibility(), and compare the
    ENTIRE perspective map against a full-grid reference scan."""
    grid.fov_radius = radius
    grid.fov = algo
    move_entity(ex, ey)
    pm = entity.perspective_map
    pm.fill(0)  # wipe DISCOVERED history so out-of-FOV must be exactly UNKNOWN
    entity.update_visibility()

    expected_fov = reference_fov_set(ex, ey, radius, algo)

    mism = 0
    first_bad = None
    for gx in range(W):
        for gy in range(H):
            got = int(pm[gx, gy])
            exp = VISIBLE if (gx, gy) in expected_fov else UNKNOWN
            if got != exp:
                mism += 1
                if first_bad is None:
                    first_bad = (gx, gy, got, exp)
    if mism:
        failures.append(
            "EQUIV FAIL [%s] pos=(%d,%d) r=%d algo=%s: %d mismatched cells; "
            "first=%s" % (label, ex, ey, radius, label_algo(algo), mism, first_bad)
        )
        return False
    return True


def label_algo(algo):
    for name, a in ALGOS:
        if a == algo:
            return name
    return str(algo)


# ----------------------------------------------------------------------------
# 1. EQUIVALENCE MATRIX: positions x radii x algorithms
# ----------------------------------------------------------------------------
positions = [
    ("corner_TL", 0, 0),
    ("corner_BR", W - 1, H - 1),
    ("edge_left_mid", 0, H // 2),
    ("edge_top_mid", W // 2, 0),
    ("center", W // 2, H // 2),
    ("near_wall", 24, 30),  # right next to interior wall cross
]
radii = [8, 16, 32]

equiv_total = 0
equiv_pass = 0
for (pname, px, py) in positions:
    for radius in radii:
        for (aname, algo) in ALGOS:
            equiv_total += 1
            if assert_full_equivalence(aname, px, py, radius, algo):
                equiv_pass += 1

print("Equivalence matrix: %d/%d cases passed" % (equiv_pass, equiv_total))


# ----------------------------------------------------------------------------
# 2. radius 0 == unlimited == full grid window
# ----------------------------------------------------------------------------
r0_total = 0
r0_pass = 0
for (pname, px, py) in [("center", W // 2, H // 2), ("corner_TL", 0, 0)]:
    for (aname, algo) in ALGOS:
        r0_total += 1
        if assert_full_equivalence(aname, px, py, 0, algo):
            r0_pass += 1
print("Radius-0 (unlimited) cases: %d/%d passed" % (r0_pass, r0_total))


# ----------------------------------------------------------------------------
# 3. MOVING TEST (disjoint windows): no ghost vision after a long jump.
# ----------------------------------------------------------------------------
def current_fov_set(ex, ey, radius, algo):
    return reference_fov_set(ex, ey, radius, algo)


radius = 8
algo = mcrfpy.FOV.SHADOW
grid.fov_radius = radius
grid.fov = algo

pm = entity.perspective_map
pm.fill(0)

# Place at A, update, record the VISIBLE set.
Ax, Ay = 12, 12
move_entity(Ax, Ay)
entity.update_visibility()
S1 = set()
for gx in range(W):
    for gy in range(H):
        if int(pm[gx, gy]) == VISIBLE:
            S1.add((gx, gy))

# Move to B with chebyshev distance > 2*radius so the windows are disjoint.
Bx, By = 45, 45
assert max(abs(Bx - Ax), abs(By - Ay)) > 2 * radius, "B not far enough for disjoint test"
move_entity(Bx, By)
entity.update_visibility()

fov_B = current_fov_set(Bx, By, radius, algo)

ghost = 0
ghost_first = None
for (gx, gy) in S1:
    if (gx, gy) not in fov_B:
        # Cell visible at A but not currently in FOV must be DISCOVERED, NEVER VISIBLE.
        if int(pm[gx, gy]) == VISIBLE:
            ghost += 1
            if ghost_first is None:
                ghost_first = (gx, gy)
if ghost:
    failures.append(
        "MOVING(disjoint) FAIL: %d cells from A still VISIBLE after moving to B "
        "(ghost vision); first=%s" % (ghost, ghost_first)
    )

# Every currently-in-FOV cell at B must be VISIBLE.
missing_B = 0
missing_first = None
for (gx, gy) in fov_B:
    if int(pm[gx, gy]) != VISIBLE:
        missing_B += 1
        if missing_first is None:
            missing_first = (gx, gy, int(pm[gx, gy]))
if missing_B:
    failures.append(
        "MOVING(disjoint) FAIL: %d cells in B's FOV not VISIBLE; first=%s"
        % (missing_B, missing_first)
    )

print("Moving test (disjoint A->B): ghost=%d, missing_at_B=%d" % (ghost, missing_B))


# ----------------------------------------------------------------------------
# 4. TRAILING-EDGE TEST (overlapping windows): cells that leave FOV after a
#    1-cell move are demoted to DISCOVERED, not stuck at VISIBLE.
# ----------------------------------------------------------------------------
pm.fill(0)
Cx, Cy = 30, 45  # open area away from walls
move_entity(Cx, Cy)
entity.update_visibility()
fov_C = current_fov_set(Cx, Cy, radius, algo)

move_entity(Cx + 1, Cy)  # small overlapping move
entity.update_visibility()
fov_D = current_fov_set(Cx + 1, Cy, radius, algo)

trailing_bad = 0
trailing_first = None
for (gx, gy) in fov_C:
    if (gx, gy) not in fov_D:
        # left FOV between C and D: must be demoted to DISCOVERED(1), not VISIBLE(2)
        if int(pm[gx, gy]) == VISIBLE:
            trailing_bad += 1
            if trailing_first is None:
                trailing_first = (gx, gy)
if trailing_bad:
    failures.append(
        "TRAILING-EDGE FAIL: %d cells that left FOV remain VISIBLE; first=%s"
        % (trailing_bad, trailing_first)
    )

# And new cells now in FOV at D must be VISIBLE.
trailing_missing = 0
for (gx, gy) in fov_D:
    if int(pm[gx, gy]) != VISIBLE:
        trailing_missing += 1
if trailing_missing:
    failures.append(
        "TRAILING-EDGE FAIL: %d cells in D's FOV not VISIBLE" % trailing_missing
    )

print("Trailing-edge test (1-cell move): stuck_visible=%d, missing=%d"
      % (trailing_bad, trailing_missing))


# ----------------------------------------------------------------------------
# 5. GRID RESIZE: moving entity to a differently-sized grid reallocates the
#    perspective map (size() != expected), takes the fresh path (no stale demote,
#    no OOB), and yields a correct map of the new size.
# ----------------------------------------------------------------------------
small_W, small_H = 20, 20
small_grid = mcrfpy.Grid(grid_size=(small_W, small_H))
scene.children.append(small_grid)
for gx in range(small_W):
    for gy in range(small_H):
        gp = small_grid.at(gx, gy)
        gp.walkable = True
        gp.transparent = True
small_grid.fov_radius = 6
small_grid.fov = mcrfpy.FOV.BASIC

resize_ok = True

# Put a fresh entity on the small grid first.
e2 = mcrfpy.Entity(grid_pos=(5, 5))
small_grid.entities.append(e2)
e2.update_visibility()
pm_small = e2.perspective_map
if pm_small.size != (small_W, small_H):
    failures.append("RESIZE FAIL: small pm.size=%s expected=%s"
                    % (pm_small.size, (small_W, small_H)))
    resize_ok = False

# Now move the SAME entity object to the big grid (different dimensions). This
# triggers the size mismatch realloc path. Use grid setter via entity.grid.
e2.grid = grid  # reassign to the 60x60 grid
grid.fov_radius = 8
grid.fov = mcrfpy.FOV.BASIC
e2.grid_pos = (30, 30)
e2.update_visibility()
pm_big = e2.perspective_map
if pm_big.size != (W, H):
    failures.append("RESIZE FAIL: after move pm.size=%s expected=%s"
                    % (pm_big.size, (W, H)))
    resize_ok = False

# Verify equivalence on the resized (large) map: no stale VISIBLE, correct FOV.
ref_fov = reference_fov_set(30, 30, 8, mcrfpy.FOV.BASIC)
resize_mism = 0
for gx in range(W):
    for gy in range(H):
        got = int(pm_big[gx, gy])
        exp = VISIBLE if (gx, gy) in ref_fov else got  # only require: no stale 2 outside FOV
        if (gx, gy) not in ref_fov and got == VISIBLE:
            resize_mism += 1
        if (gx, gy) in ref_fov and got != VISIBLE:
            resize_mism += 1
if resize_mism:
    failures.append("RESIZE FAIL: %d cells wrong after realloc" % resize_mism)
    resize_ok = False

print("Grid resize test: %s" % ("OK" if resize_ok else "FAIL"))


# ----------------------------------------------------------------------------
# 6. EXTERNAL ASSIGNMENT (load / resume): assigning a whole DiscreteMap that
#    carries VISIBLE cells anywhere must NOT leave ghost-visible cells. The
#    windowed demote tracks only cells the engine itself promoted (prev_fov), so
#    an externally-supplied map needs a one-shot full demote on the next
#    update_visibility(): loaded VISIBLE -> DISCOVERED before the FOV recompute,
#    matching the pre-#316 full-demote semantics. This is the documented
#    from_bytes/assign/update_visibility workflow; the naive windowed demote
#    regressed it (caught by the #316 adversarial verify, not the moving test).
# ----------------------------------------------------------------------------
assign_entity = mcrfpy.Entity(grid_pos=(W // 2, H // 2))
grid.entities.append(assign_entity)
grid.fov_radius = 8
grid.fov = mcrfpy.FOV.SHADOW

# A "saved" perspective with VISIBLE cells FAR from where the entity now stands
# (simulating a map saved while the entity was elsewhere), plus a far DISCOVERED
# cell that must be preserved (demote only touches 2 -> 1, never 1 -> 0).
saved = mcrfpy.DiscreteMap(size=(W, H), fill=0)
far_visible = [(2, 2), (3, 2), (2, 3), (55, 5), (5, 55), (57, 57)]
for (gx, gy) in far_visible:
    saved[gx, gy] = VISIBLE
saved[10, 2] = DISCOVERED

Ex, Ey = W // 2, H // 2
assign_entity.grid_pos = (Ex, Ey)
assign_entity.perspective_map = saved      # set_perspective_map -> full_demote_pending
assign_entity.update_visibility()

pm_a = assign_entity.perspective_map
fov_assign = reference_fov_set(Ex, Ey, 8, mcrfpy.FOV.SHADOW)

assign_ghost = 0
assign_first = None
for (gx, gy) in far_visible:
    if (gx, gy) not in fov_assign:
        v = int(pm_a[gx, gy])
        if v == VISIBLE:
            assign_ghost += 1
            if assign_first is None:
                assign_first = (gx, gy, v)
        elif v != DISCOVERED:
            failures.append("ASSIGN(load/resume) FAIL: loaded VISIBLE cell %s "
                            "should be DISCOVERED, got %d" % ((gx, gy), v))
if assign_ghost:
    failures.append(
        "ASSIGN(load/resume) FAIL: %d loaded VISIBLE cells outside FOV stayed "
        "VISIBLE (ghost vision); first=%s" % (assign_ghost, assign_first))

# Pre-existing far DISCOVERED cell must remain DISCOVERED.
if int(pm_a[10, 2]) != DISCOVERED:
    failures.append("ASSIGN(load/resume) FAIL: pre-existing DISCOVERED cell lost "
                    "(got %d)" % int(pm_a[10, 2]))

# Current FOV must be VISIBLE.
assign_missing = sum(1 for (gx, gy) in fov_assign if int(pm_a[gx, gy]) != VISIBLE)
if assign_missing:
    failures.append("ASSIGN(load/resume) FAIL: %d cells in FOV not VISIBLE"
                    % assign_missing)

# A SECOND update with no further assignment must keep working windowed (the
# pending flag was consumed) and still leave no ghosts.
assign_entity.update_visibility()
second_ghost = sum(1 for (gx, gy) in far_visible
                   if (gx, gy) not in fov_assign and int(pm_a[gx, gy]) == VISIBLE)
if second_ghost:
    failures.append("ASSIGN(load/resume) FAIL: %d ghosts after second update "
                    "(pending flag not consumed correctly)" % second_ghost)

print("Assignment (load/resume) test: ghost=%d, missing=%d, second_update_ghost=%d"
      % (assign_ghost, assign_missing, second_ghost))


# ----------------------------------------------------------------------------
# 7. AABB MARGIN LOCK: a wall ring at chebyshev distance r+1 around an open-area
#    entity. With light_walls those boundary walls are lit; the windowed map must
#    match a full-grid reference there, locking the +/-(r+1) window margin. Sound
#    oracle (full-grid compare), so it can only fail if the window drops boundary
#    cells -- and it reports how many in-FOV cells lie beyond radius r, proving
#    the margin is actually exercised.
# ----------------------------------------------------------------------------
AW, AH = 40, 40
arena = mcrfpy.Grid(grid_size=(AW, AH))
scene.children.append(arena)
for gx in range(AW):
    for gy in range(AH):
        gp = arena.at(gx, gy)
        gp.walkable = True
        gp.transparent = True

acx, acy, ar = 20, 20, 6
for gx in range(AW):
    for gy in range(AH):
        if max(abs(gx - acx), abs(gy - acy)) == ar + 1:
            arena.at(gx, gy).transparent = False  # opaque ring at distance r+1

arena_entity = mcrfpy.Entity(grid_pos=(acx, acy))
arena.entities.append(arena_entity)

margin_total = 0
margin_pass = 0
margin_exercised = 0
for (aname, algo) in ALGOS:
    arena.fov_radius = ar
    arena.fov = algo
    arena_entity.grid_pos = (acx, acy)
    apm = arena_entity.perspective_map
    apm.fill(0)
    arena_entity.update_visibility()

    arena.compute_fov((acx, acy), radius=ar, light_walls=True, algorithm=algo)
    ref = set()
    for gx in range(AW):
        for gy in range(AH):
            if arena.is_in_fov((gx, gy)):
                ref.add((gx, gy))

    margin_total += 1
    mism = 0
    for gx in range(AW):
        for gy in range(AH):
            exp = VISIBLE if (gx, gy) in ref else UNKNOWN
            if int(apm[gx, gy]) != exp:
                mism += 1
    if mism == 0:
        margin_pass += 1
    else:
        failures.append("AABB MARGIN FAIL [%s]: %d cells differ from full-grid "
                        "reference in r+1 wall-ring arena" % (aname, mism))
    for (gx, gy) in ref:
        if max(abs(gx - acx), abs(gy - acy)) > ar:
            margin_exercised += 1

print("AABB margin lock (r+1 wall ring): %d/%d algos equivalent; %d in-FOV cells "
      "beyond radius r exercised the margin" % (margin_pass, margin_total, margin_exercised))


# ----------------------------------------------------------------------------
# Summary
# ----------------------------------------------------------------------------
print("")
if failures:
    print("FAIL -- %d failure(s):" % len(failures))
    for f in failures:
        print("  - " + f)
    sys.exit(1)
else:
    print("PASS -- windowed perspective writeback matches full-grid reference "
          "across all equivalence, moving, trailing-edge, and resize cases.")
    sys.exit(0)
