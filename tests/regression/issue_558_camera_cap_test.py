"""#558: the paths that cannot raise cap a camera value instead of refusing it.

(a) an animation tick that would leave the camera invariant (an overshooting easing, or a setter call
    that changed the limits mid-animation) displays the nearest valid value for that tick; the
    animation still completes, ends exactly at its target and fires its callback;
(b) the default texture assigned on the first draw of a texture-less grid changes the cell size; the
    camera is capped to the nearest valid one.
Python setters still raise (tests/regression/issue_558_zoom_invariant_test.py). Time is mcrfpy.step(dt)."""
import os
import sys
import tempfile
import warnings
import mcrfpy

fails = []
L = (2**31 - 1) // 4
tex = mcrfpy.default_texture


def grid(size=(40, 40), **kw):
    return mcrfpy.Grid(grid_size=(4, 4), texture=tex, size=size, **kw)


def min_zoom(g):
    return (abs(g.size.x) + abs(g.size.y)) / L


def valid(g, label):
    mz = min_zoom(g)
    if not (g.zoom > 0 and g.zoom >= mz * (1 - 1e-6)):
        fails.append(f"{label}: zoom {g.zoom} below minimum {mz}")
    c = g.center
    if not (abs(c.x) <= L and abs(c.y) <= L):
        fails.append(f"{label}: centre {c} outside +/-{L}")


def run_easing(easing, label):
    g = grid()
    target = 2e-7                      # valid: minimum for 40 x 40 is 80 / L ~ 1.49e-7
    g.zoom = 1e-6                      # start near the target: the animation interpolates in float
    done = []
    g.animate("zoom", target, 1.0, easing, callback=lambda *a: done.append(a))
    seen_low = False
    for i in range(40):
        mcrfpy.step(0.05)
        valid(g, f"{label} step {i}")
        if g.zoom <= min_zoom(g) * (1 + 1e-6):
            seen_low = True
    mcrfpy.step(0.5)
    if abs(g.zoom - target) > 1e-12:
        fails.append(f"{label}: ended at {g.zoom}, want {target}")
    if len(done) != 1:
        fails.append(f"{label}: callback fired {len(done)} times")
    elif abs(done[0][2] - target) > 1e-12:
        fails.append(f"{label}: callback value {done[0][2]}")
    return seen_low


if not run_easing(mcrfpy.Easing.EASE_OUT_BACK, "out_back"):
    fails.append("out_back never reached the cap (test does not exercise it)")
run_easing(mcrfpy.Easing.EASE_OUT_ELASTIC, "out_elastic")
run_easing(mcrfpy.Easing.EASE_IN_OUT_ELASTIC, "in_out_elastic")

# Centre: an overshoot past +/-L is capped, not raised; the end value stays exact.
g = grid()
g.center = (5.0e8, 0)
done = []
g.animate("center_x", 5.36e8, 1.0, mcrfpy.Easing.EASE_OUT_BACK, callback=lambda *a: done.append(a))
for i in range(25):
    mcrfpy.step(0.05)
    valid(g, f"center_x step {i}")
mcrfpy.step(0.5)
if len(done) != 1:
    fails.append("center_x callback did not fire once")

# Mid-animation setter: w heads for 1e6; a valid setter then makes later ticks invalid.
g = grid()
done = []
g.animate("w", 1e6, 0.01, callback=lambda *a: done.append(a))
g.zoom = 0.0015                         # valid for the 40 x 40 view being animated
for i in range(5):
    mcrfpy.step(0.01)
    valid(g, f"w mid-animation step {i}")
mcrfpy.step(0.5)
valid(g, "w mid-animation end")
if len(done) != 1:
    fails.append(f"w mid-animation callback fired {len(done)} times")
# 'size' likewise
g = grid()
g.animate("size", (1e6, 1e6), 0.01)
g.zoom = 0.0015
for i in range(5):
    mcrfpy.step(0.01)
    valid(g, f"size mid-animation step {i}")

# The setters still raise.
g = grid()
try:
    g.zoom = 1e-8
    fails.append("zoom setter no longer raises")
except ValueError:
    pass

# (b) first draw with no texture and a far-off centre: the cell size goes from 1x1 to the default
# texture's; centre / cell scaling would leave +/-L. The assignment proceeds and the camera is capped.
g = mcrfpy.Grid(grid_size=(4, 4), size=(40, 40))
g.center = (5.0e8, 5.0e8)
g.zoom = 1.0
scene = mcrfpy.Scene("cap")
scene.children.append(g)
mcrfpy.current_scene = scene
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    mcrfpy.step(0.01)
    from mcrfpy import automation
    automation.screenshot(os.path.join(tempfile.mkdtemp(prefix="mcrf558_"), "shot.png"))
if g.texture is None:
    fails.append("first draw did not assign the default texture")
else:
    cs = g.cell_size
    c = g.center
    if not (abs(c.x) <= L and abs(c.y) <= L):
        fails.append(f"first draw (cell {cs}): centre {c} outside +/-{L}")
    valid(g, "first draw")

if fails:
    print("FAIL")
    for f in fails:
        print(" ", f)
    sys.exit(1)
print("PASS")
sys.exit(0)
