"""#532 (#530 residual): the default camera (cell (0,0) at the widget's top-left)
follows a resize of the widget, however the resize is made. An explicit camera
(center= / center_camera()) is the user's and must not move."""
import sys
import mcrfpy

fails = []

def make(zoom, sized=True, **kw):
    args = dict(grid_size=(20, 15), texture=mcrfpy.default_texture, pos=(0, 0), zoom=zoom)
    if sized:
        args["size"] = (320, 240)
    args.update(kw)
    return mcrfpy.Grid(**args)

def check(label, g, expect):
    got = (g.center.x, g.center.y)
    if abs(got[0] - expect[0]) > 1e-3 or abs(got[1] - expect[1]) > 1e-3:
        fails.append(f"{label}: center {got}, expected {expect}")

def settle(g):
    for _ in range(30):
        mcrfpy.step(0.01)

for zoom in (1.0, 2.0):
    exp = (640 / (2 * zoom), 480 / (2 * zoom))

    g = make(zoom); g.size = (640, 480)
    check(f"size= zoom={zoom}", g, exp)

    g = make(zoom); g.w = 640; g.h = 480
    check(f"w/h zoom={zoom}", g, exp)

    g = make(zoom)
    g.animate("w", 640.0, 0.1, mcrfpy.Easing.LINEAR)
    g.animate("h", 480.0, 0.1, mcrfpy.Easing.LINEAR)
    settle(g)
    check(f"animate zoom={zoom}", g, exp)

    g = make(zoom)
    g.animate("size", (640.0, 480.0), 0.1, mcrfpy.Easing.LINEAR)
    settle(g)
    check(f"animate size zoom={zoom}", g, exp)

    g = make(zoom); g.resize(640, 480)
    check(f"resize() zoom={zoom}", g, exp)

    # explicit cameras survive a resize
    g = make(zoom, center_x=100, center_y=80)
    g.size = (640, 480)
    check(f"explicit center zoom={zoom}", g, (100, 80))

    g = make(zoom)
    g.center_camera((5, 5))
    before = (g.center.x, g.center.y)
    g.size = (640, 480)
    check(f"center_camera zoom={zoom}", g, before)

g = make(2.0, sized=False)
g.size = (640, 480)
check("no size kwarg zoom=2", g, (160, 120))

if fails:
    for f in fails:
        print("FAIL", f)
    sys.exit(1)
print("PASS")
sys.exit(0)
