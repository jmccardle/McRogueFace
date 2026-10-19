"""#523: Grid.apply_threshold / apply_ranges check min>max and accept list ranges."""
import sys
import mcrfpy


def fail(msg):
    print("FAIL", msg)
    sys.exit(1)


grid = mcrfpy.Grid(grid_size=(3, 1), texture=mcrfpy.default_texture)
hm = mcrfpy.HeightMap((3, 1))
for x, v in enumerate((0.0, 0.5, 1.0)):
    hm[x, 0] = v

try:
    grid.apply_threshold(hm, (0.8, 0.2), walkable=True)
except ValueError as e:
    if "min" not in str(e): fail("message: %s" % e)
else:
    fail("min>max did not raise")
try:
    grid.apply_ranges(hm, [((0.8, 0.2), {"walkable": True})])
except ValueError:
    pass
else:
    fail("apply_ranges min>max did not raise")

for rng in ((0.4, 0.6), [0.4, 0.6]):
    g = mcrfpy.Grid(grid_size=(3, 1), texture=mcrfpy.default_texture)
    g.apply_threshold(hm, rng, walkable=True)
    flags = [g.at(x, 0).walkable for x in range(3)]
    if flags != [False, True, False]: fail("range %r gave %r" % (rng, flags))
g = mcrfpy.Grid(grid_size=(3, 1), texture=mcrfpy.default_texture)
g.apply_ranges(hm, [([0.9, 1.0], {"walkable": True})])
if [g.at(x, 0).walkable for x in range(3)] != [False, False, True]: fail("list range in apply_ranges")
print("PASS")
sys.exit(0)
