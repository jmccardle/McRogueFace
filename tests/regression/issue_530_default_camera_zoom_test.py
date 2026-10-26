"""#530: the default camera (cell (0,0) at the widget's top-left, #169) follows zoom.

Assigning zoom after construction must give the same camera as passing it."""
import sys
import mcrfpy

def make(**kw):
    return mcrfpy.Grid(grid_size=(20, 15), texture=mcrfpy.default_texture,
                       pos=(0, 0), size=(640, 480), **kw)

def center(g):
    return (g.center.x, g.center.y)

ref = make(zoom=2.0)
assert center(ref) == (160.0, 120.0), center(ref)

g = make()
assert center(g) == (320.0, 240.0), center(g)
g.zoom = 2.0
assert center(g) == center(ref), ("assigned zoom left a stale default", center(g))
g.zoom = 0.5
assert center(g) == (640.0, 480.0), center(g)

# animated zoom goes through setProperty
a = make()
a.animate("zoom", 4.0, 0.1, mcrfpy.Easing.LINEAR)
for _ in range(20):
    mcrfpy.step(0.01)
assert abs(a.zoom - 4.0) < 1e-6, a.zoom
assert center(a) == (80.0, 60.0), center(a)

# an explicit camera is the user's: zoom doesn't move it
e = make()
e.center = (100.0, 100.0)
e.zoom = 2.0
assert center(e) == (100.0, 100.0), center(e)
c = make()
c.center_camera()
c.zoom = 2.0
assert center(c) == (160.0, 120.0), center(c)

print("PASS")
sys.exit(0)
