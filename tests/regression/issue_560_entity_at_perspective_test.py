"""#560 C: Entity.at() indexed perspective_map with the CURRENT grid's width, not the map's."""
import sys
import mcrfpy

fails = []
def check(c, m):
    if not c: fails.append(m)

tex = mcrfpy.default_texture
small = mcrfpy.Grid(grid_size=(2, 2), texture=tex)
big = mcrfpy.Grid(grid_size=(2000, 2000), texture=tex)
e = mcrfpy.Entity((0, 0), grid=small)
pm = e.perspective_map                     # allocates a 2x2 map
check(pm.size == (2, 2), "map sized to the small grid")
e.grid = big                               # the grid-change choke point
for pos in ((1999, 1999), (1000, 1500), (0, 1999)):
    check(e.at(pos) is None, f"at{pos} on the big grid before any FOV update")   # was an OOB read
check(e.perspective_map.size == (2000, 2000), "map follows the grid")
e.update_visibility()
check(e.at((0, 0)) is not None, "the entity's own cell is VISIBLE after an update on the new grid")
check(e.perspective_map[0, 0] == 2, "perspective_map marks its own cell visible")

# same-sized grids keep their memory
a = mcrfpy.Grid(grid_size=(5, 5), texture=tex)
b = mcrfpy.Grid(grid_size=(5, 5), texture=tex)
e2 = mcrfpy.Entity((1, 1), grid=a)
m2 = e2.perspective_map
m2[2, 2] = 1
e2.grid = b
check(e2.perspective_map[2, 2] == 1, "same-sized move keeps the map")

# back to small, and to no grid
e.grid = small
check(e.perspective_map.size == (2, 2), "map follows the grid back down")
e.at((1, 1))
e.grid = None
check(e.perspective_map is None, "no grid, no map")
print("FAIL: " + "; ".join(fails) if fails else "PASS")
sys.exit(1 if fails else 0)
