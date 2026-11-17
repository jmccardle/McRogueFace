"""#540 items 5 and 6.

5. zoom <= 0 is rejected (ValueError) in the constructor, the setter and as an animation target:
   Grid(zoom=0) made center (inf, inf) and `g.center = g.center` then raised.
6. Out of float range is the same exception at every choke point: OverflowError for a finite value
   too large for a float, ValueError for nan/inf. The message names the property or argument."""
import sys
import mcrfpy

fails = []
tex = mcrfpy.default_texture
V = mcrfpy.Vector
nan, inf = float("nan"), float("inf")


def expect(label, fn, exc, needle=None):
    try:
        fn()
    except exc as e:
        if type(e) is not exc:  # exact: OverflowError is not ValueError here
            fails.append(f"{label}: raised {type(e).__name__}, want exactly {exc.__name__}")
        if needle is not None and needle not in str(e):
            fails.append(f"{label}: message {str(e)!r} lacks {needle!r}")
        return
    except BaseException as e:
        fails.append(f"{label}: raised {type(e).__name__}: {e}; want {exc.__name__}")
        return
    fails.append(f"{label}: accepted")


# ---- 5. zoom ----
for bad in (0, 0.0, -1, -0.5):
    expect(f"Grid(zoom={bad})", lambda: mcrfpy.Grid(grid_size=(4, 4), texture=tex, zoom=bad), ValueError, "zoom")
g = mcrfpy.Grid(grid_size=(4, 4), texture=tex, size=(40, 40))
for bad in (0, 0.0, -1, -0.5):
    expect(f"grid.zoom = {bad}", lambda: setattr(g, "zoom", bad), ValueError, "zoom")
    expect(f"grid.animate('zoom', {bad})", lambda: g.animate("zoom", bad, 1.0), ValueError, "zoom")
if g.zoom != 1.0:
    fails.append(f"zoom changed to {g.zoom} despite the rejected assignments")
g.zoom = 0.25
g.center = g.center   # round trip: no inf
if g.zoom != 0.25:
    fails.append("zoom = 0.25 not stored")
mcrfpy.Grid(grid_size=(4, 4), texture=tex, zoom=2.0)
g.animate("zoom", 2.0, 0.5)

# ---- 6. one exception for out-of-float-range, at every choke point ----
big = 1e39
for label, fn in (
    ("frame.x = 1e39", lambda: setattr(mcrfpy.Frame(), "x", big)),
    ("Frame(x=1e39)", lambda: mcrfpy.Frame(x=big)),
    ("Frame(w=1e39)", lambda: mcrfpy.Frame(w=big)),
    ("Frame(pos=(1, 1e39))", lambda: mcrfpy.Frame(pos=(1, big))),
    ("Frame(size=V)", lambda: mcrfpy.Frame(size=(big, 1))),
    ("frame.pos = (1e39, 0)", lambda: setattr(mcrfpy.Frame(), "pos", (big, 0))),
    ("frame.move(1, 1e39)", lambda: mcrfpy.Frame().move(1, big)),
    ("Caption(x=1e39)", lambda: mcrfpy.Caption(x=big)),
    ("Sprite(scale=1e39)", lambda: mcrfpy.Sprite(scale=big)),
    ("Circle(radius=1e39)", lambda: mcrfpy.Circle(radius=big)),
    ("frame.animate('x', 1e39)", lambda: mcrfpy.Frame().animate("x", big, 1.0)),
    ("frame.rotation = 10**400", lambda: setattr(mcrfpy.Frame(), "rotation", 10**400)),
):
    expect(label, fn, OverflowError)
for label, fn, name in (
    ("frame.x = nan", lambda: setattr(mcrfpy.Frame(), "x", nan), "x"),
    ("Frame(x=nan)", lambda: mcrfpy.Frame(x=nan), "x"),
    ("Frame(w=inf)", lambda: mcrfpy.Frame(w=inf), "w"),
    ("Frame(opacity=nan)", lambda: mcrfpy.Frame(opacity=nan), "opacity"),
    ("Frame(pos=(nan, 0))", lambda: mcrfpy.Frame(pos=(nan, 0)), "pos"),
    ("frame.pos = V(0, inf)", lambda: setattr(mcrfpy.Frame(), "pos", V(0, inf)), "pos"),
    ("frame.size = (inf, 0)", lambda: setattr(mcrfpy.Frame(), "size", (inf, 0)), "size"),
    ("frame.rotation = nan", lambda: setattr(mcrfpy.Frame(), "rotation", nan), "rotation"),
    ("frame.opacity = inf", lambda: setattr(mcrfpy.Frame(), "opacity", inf), "opacity"),
    ("frame.outline = nan", lambda: setattr(mcrfpy.Frame(), "outline", nan), "outline"),
    ("sprite.scale = inf", lambda: setattr(mcrfpy.Sprite(), "scale", inf), "scale"),
    ("circle.radius = nan", lambda: setattr(mcrfpy.Circle(), "radius", nan), "radius"),
    ("grid.zoom = nan", lambda: setattr(g, "zoom", nan), "zoom"),
    ("grid.center_x = inf", lambda: setattr(g, "center_x", inf), "center_x"),
    ("entity.sprite_offset_x = nan", lambda: setattr(mcrfpy.Entity(), "sprite_offset_x", nan), "sprite_offset_x"),
    ("entity.move_speed = inf", lambda: setattr(mcrfpy.Entity(), "move_speed", inf), "move_speed"),
):
    expect(label, fn, ValueError, name)
# the specific Caption glyph messages are kept (they are range messages, ValueError)
c = mcrfpy.Caption(text="x")
for attr in ("font_size", "outline"):
    for bad in (nan, inf, -1.0, 1e9):
        expect(f"caption.{attr} = {bad}", lambda: setattr(c, attr, bad), ValueError, "pixels")

# ---- arithmetic that leaves float range after entry: move() checks its result ----
f = mcrfpy.Frame(pos=(3e38, 0), size=(10, 10))
expect("Frame(pos=(3e38, 0)).move(3e38, 0)", lambda: f.move(3e38, 0), OverflowError)
if f.x != float(mcrfpy.Frame(pos=(3e38, 0)).x):
    fails.append(f"frame moved despite the OverflowError: x = {f.x}")

for fl in fails:
    print("FAIL:", fl)
print("FAIL" if fails else "PASS")
sys.exit(1 if fails else 0)
