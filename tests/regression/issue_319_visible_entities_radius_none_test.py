"""
Regression test for issue #319 -- Entity.visible_entities(radius=None) raised
TypeError instead of applying the grid default.

Root cause: radius was parsed with the PyArg 'i' format code ("|Oi"), which
rejects Python None. The fix parses radius as an object ("|OO") and treats
None / omitted / -1 as "use the grid's default fov_radius".

ASCII-only source. Prints PASS/FAIL and sys.exit(0/1).
"""

import mcrfpy
import sys

failures = []


def check(label, cond):
    if not cond:
        failures.append(label)
    print(("  ok  " if cond else " FAIL ") + label)


# --- grid + entities -------------------------------------------------------
grid = mcrfpy.Grid(grid_size=(20, 20))
grid.fov_radius = 7
for gx in range(20):
    for gy in range(20):
        gp = grid.at(gx, gy)
        gp.walkable = True
        gp.transparent = True

seeker = mcrfpy.Entity(grid_pos=(10, 10))
grid.entities.append(seeker)
neighbor = mcrfpy.Entity(grid_pos=(11, 10))
grid.entities.append(neighbor)

# --- the bug: radius=None must NOT raise (it used to TypeError) -------------
try:
    res_none = seeker.visible_entities(radius=None)
    check("visible_entities(radius=None) does not raise", True)
    check("returns a list", isinstance(res_none, list))
except TypeError as e:
    check("visible_entities(radius=None) does not raise (got TypeError: %s)" % e, False)
    res_none = []

# Adjacent transparent neighbor should be visible.
def positions(lst):
    return {(int(e.cell_pos.x), int(e.cell_pos.y)) for e in lst}

check("neighbor (11,10) visible with radius=None", (11, 10) in positions(res_none))
check("self excluded from results", (10, 10) not in positions(res_none))

# --- equivalence: None, omitted, and -1 all mean 'use grid default' --------
res_omitted = seeker.visible_entities()
res_default = seeker.visible_entities(radius=-1)
check("radius=None matches omitted", positions(res_none) == positions(res_omitted))
check("radius=None matches radius=-1", positions(res_none) == positions(res_default))

# --- explicit int radius still works ---------------------------------------
try:
    res_int = seeker.visible_entities(radius=3)
    check("radius=3 (int) works", isinstance(res_int, list) and (11, 10) in positions(res_int))
except Exception as e:
    check("radius=3 (int) works (raised %s)" % e, False)

# A tiny radius can still see the immediately-adjacent neighbor.
res_one = seeker.visible_entities(radius=1)
check("radius=1 sees adjacent neighbor", (11, 10) in positions(res_one))

# --- fov + radius=None combined (None must be fine alongside fov) -----------
try:
    res_combo = seeker.visible_entities(fov=mcrfpy.FOV.SHADOW, radius=None)
    check("visible_entities(fov=SHADOW, radius=None) works", isinstance(res_combo, list))
except Exception as e:
    check("visible_entities(fov=SHADOW, radius=None) works (raised %s)" % e, False)

# --- invalid radius type must raise a clear TypeError ----------------------
try:
    seeker.visible_entities(radius="not an int")
    check("radius='str' raises TypeError", False)
except TypeError:
    check("radius='str' raises TypeError", True)
except Exception as e:
    check("radius='str' raises TypeError (got %s)" % type(e).__name__, False)


print("")
if failures:
    print("FAIL -- %d check(s) failed:" % len(failures))
    for f in failures:
        print("  - " + f)
    sys.exit(1)
print("PASS -- visible_entities accepts radius=None (and -1/omitted) as the grid default.")
sys.exit(0)
