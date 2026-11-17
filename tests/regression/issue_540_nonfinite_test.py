"""#540 item 12 (decided: ALL RAISE): constructors, property setters and animation targets that
take a position, size or float reject nan / inf with ValueError, just as move() / resize() do.
A rejected assignment leaves the object unchanged; a rejected constructor creates nothing.

Deliberately NOT covered (documented in the commit): Vector() itself (a math type that may hold
inf; it is rejected where it is stored), Grid(center_x=nan, center_y=nan) which is the
"center the camera by default" sentinel (#169; inf is rejected), duration / delay arguments."""
import sys
import mcrfpy

fails = []
V = mcrfpy.Vector
nan, inf = float("nan"), float("inf")
BAD = (("inf", inf), ("-inf", -inf), ("nan", nan))


def must_raise(label, fn):
    try:
        fn()
    except ValueError:
        return
    except BaseException as e:
        fails.append(f"{label}: raised {type(e).__name__}: {e}; want ValueError")
        return
    fails.append(f"{label}: accepted")


def ok(label, fn):
    try:
        return fn()
    except BaseException as e:
        fails.append(f"{label}: raised {type(e).__name__}: {e}; want success")


tex = mcrfpy.default_texture

# ---- constructors: every position / size / float keyword ----
ctor_kwargs = {
    "Frame": (mcrfpy.Frame, ["x", "y", "w", "h", "outline", "opacity", "margin", "horiz_margin", "vert_margin"],
              ["pos", "size"]),
    "Caption": (mcrfpy.Caption, ["x", "y", "opacity", "margin", "horiz_margin", "vert_margin"], ["pos"]),
    "Sprite": (mcrfpy.Sprite, ["x", "y", "scale", "scale_x", "scale_y", "opacity", "margin", "horiz_margin", "vert_margin"],
               ["pos"]),
    "Grid": (lambda **kw: mcrfpy.Grid(grid_size=(4, 4), texture=tex, **kw),
             ["x", "y", "w", "h", "zoom", "opacity", "margin", "horiz_margin", "vert_margin"], ["pos", "size"]),
    "Entity": (mcrfpy.Entity, ["x", "y", "opacity"], ["grid_pos"]),
    "Arc": (mcrfpy.Arc, ["radius", "start_angle", "end_angle", "thickness", "opacity", "margin"], ["center"]),
    "Line": (mcrfpy.Line, ["thickness", "opacity", "margin"], ["start", "end"]),
    "Circle": (mcrfpy.Circle, ["radius", "outline", "opacity", "margin"], ["center"]),
}
for cname, (ctor, scalars, vectors) in ctor_kwargs.items():
    for kw in scalars:
        for bl, bad in BAD:
            must_raise(f"{cname}({kw}={bl})", lambda: ctor(**{kw: bad}))
    for kw in vectors:
        for bl, bad in BAD:
            for shape, val in (("tuple", (bad, 1.0)), ("tuple-y", (1.0, bad)), ("list", [bad, 1.0]), ("Vector", V(bad, 1.0))):
                must_raise(f"{cname}({kw}={shape} with {bl})", lambda: ctor(**{kw: val}))
    must_raise(f"{cname}(1e39) overflows to inf", lambda: ctor(**{(vectors[0]): (1e39, 0.0)}))
# the first positional argument too
must_raise("Frame((inf, 0))", lambda: mcrfpy.Frame((inf, 0)))
must_raise("Caption((nan, 0))", lambda: mcrfpy.Caption((nan, 0)))
must_raise("Sprite((inf, 0))", lambda: mcrfpy.Sprite((inf, 0)))
# Grid.center_x / center_y: nan is the "default camera" sentinel, infinity is an error
must_raise("Grid(center_x=inf)", lambda: mcrfpy.Grid(grid_size=(4, 4), texture=tex, center_x=inf))
must_raise("Grid(center_y=-inf)", lambda: mcrfpy.Grid(grid_size=(4, 4), texture=tex, center_y=-inf))
ok("Grid(center_x=nan) is the default-camera sentinel", lambda: mcrfpy.Grid(grid_size=(4, 4), texture=tex, center_x=nan))

# valid values still construct
ok("Frame valid", lambda: mcrfpy.Frame(pos=(1.5, 2), size=(3, 4), outline=1.0, opacity=0.5, margin=0.0))
ok("Caption valid", lambda: mcrfpy.Caption(pos=V(1, 2), text="x"))
ok("Sprite valid", lambda: mcrfpy.Sprite(pos=[1, 2], scale=2.0))
ok("Grid valid", lambda: mcrfpy.Grid(grid_size=(4, 4), texture=tex, pos=(1, 2), size=(30, 40), zoom=2.0))
ok("Entity valid", lambda: mcrfpy.Entity(grid_pos=(1, 2)))
ok("Arc valid", lambda: mcrfpy.Arc(center=(1, 2), radius=3.0, start_angle=0, end_angle=90, thickness=1.0))
ok("Line valid", lambda: mcrfpy.Line(start=(0, 0), end=(1, 1), thickness=2.0))
ok("Circle valid", lambda: mcrfpy.Circle(center=(1, 2), radius=3.0))

# ---- setters: rejected, and the object is unchanged ----
def check_setter(label, make, attr, getter=None):
    for bl, bad in BAD:
        obj = make()
        before = getattr(obj, attr)
        before = tuple(before) if hasattr(before, "__len__") and not isinstance(before, str) else before
        try:
            setattr(obj, attr, bad)
        except ValueError:
            pass
        except BaseException as e:
            fails.append(f"{label}.{attr} = {bl}: raised {type(e).__name__}: {e}; want ValueError")
            continue
        else:
            fails.append(f"{label}.{attr} = {bl}: accepted")
            continue
        after = getattr(obj, attr)
        after = tuple(after) if hasattr(after, "__len__") and not isinstance(after, str) else after
        if after != before:
            fails.append(f"{label}.{attr} = {bl}: changed {before} -> {after} despite raising")


def check_vec_setter(label, make, attr):
    for bl, bad in BAD:
        for shape, val in (("tuple", (bad, 1.0)), ("tuple-y", (1.0, bad)), ("Vector", V(bad, 1.0)), ("list", [bad, 1.0])):
            obj = make()
            before = tuple(getattr(obj, attr))
            try:
                setattr(obj, attr, val)
            except ValueError:
                pass
            except BaseException as e:
                fails.append(f"{label}.{attr} = {shape} with {bl}: raised {type(e).__name__}: {e}; want ValueError")
                continue
            else:
                fails.append(f"{label}.{attr} = {shape} with {bl}: accepted")
                continue
            if tuple(getattr(obj, attr)) != before:
                fails.append(f"{label}.{attr} = {shape} with {bl}: changed despite raising")


mk_frame = lambda: mcrfpy.Frame(pos=(1, 2), size=(30, 40))
mk_caption = lambda: mcrfpy.Caption(pos=(1, 2), text="hi")
mk_sprite = lambda: mcrfpy.Sprite(pos=(1, 2))
mk_grid = lambda: mcrfpy.Grid(grid_size=(4, 4), texture=tex, pos=(1, 2), size=(30, 40))
mk_arc = lambda: mcrfpy.Arc(center=(5, 5), radius=3.0, start_angle=0, end_angle=90)
mk_circle = lambda: mcrfpy.Circle(center=(5, 5), radius=3.0)
mk_line = lambda: mcrfpy.Line(start=(0, 0), end=(5, 5), thickness=2.0)


_keep = []


def mk_entity():
    g = mcrfpy.Grid(grid_size=(8, 8), texture=tex)
    _keep.append(g)
    e = mcrfpy.Entity(grid_pos=(2, 3))
    g.entities.append(e)
    return e


scalar_setters = [
    ("Frame", mk_frame, ["x", "y", "w", "h", "rotation", "opacity", "margin", "horiz_margin", "vert_margin", "outline"]),
    ("Caption", mk_caption, ["x", "y", "rotation", "opacity", "margin", "horiz_margin", "vert_margin"]),
    ("Sprite", mk_sprite, ["x", "y", "scale", "rotation", "opacity", "margin"]),
    ("Grid", mk_grid, ["x", "y", "w", "h", "zoom", "center_x", "center_y", "rotation", "opacity", "margin"]),
    ("Arc", mk_arc, ["radius", "start_angle", "end_angle", "thickness", "rotation", "opacity"]),
    ("Circle", mk_circle, ["radius", "outline", "rotation", "opacity"]),
    ("Line", mk_line, ["thickness", "rotation", "opacity"]),
    ("Entity", mk_entity, ["opacity", "move_speed"]),
]
for label, make, attrs in scalar_setters:
    for attr in attrs:
        try:
            make()
        except BaseException as e:
            fails.append(f"{label}: could not construct: {e}")
            break
        if not hasattr(make(), attr):
            continue  # not every class has every shared property
        check_setter(label, make, attr)

vector_setters = [
    ("Frame", mk_frame, ["pos", "size", "origin"]),
    ("Caption", mk_caption, ["pos", "origin"]),
    ("Sprite", mk_sprite, ["pos", "origin"]),
    ("Grid", mk_grid, ["pos", "size", "center", "origin"]),
    ("Arc", mk_arc, ["center", "pos", "origin"]),
    ("Circle", mk_circle, ["center", "pos", "origin"]),
    ("Line", mk_line, ["start", "end", "pos", "origin"]),
    ("Entity", mk_entity, ["pos", "draw_pos", "sprite_offset"]),
]
for label, make, attrs in vector_setters:
    for attr in attrs:
        if not hasattr(make(), attr):
            continue
        check_vec_setter(label, make, attr)

# ---- center_camera ----
g = mk_grid()
for bl, bad in BAD:
    must_raise(f"Grid.center_camera(({bl}, 1))", lambda: g.center_camera((bad, 1.0)))
    must_raise(f"Grid.center_camera(Vector({bl}, 1))", lambda: g.center_camera(V(bad, 1.0)))

# ---- animation targets ----
f = mk_frame()
for bl, bad in BAD:
    must_raise(f"frame.animate('x', {bl})", lambda: f.animate("x", bad, 1.0))
    must_raise(f"frame.animate('opacity', {bl})", lambda: f.animate("opacity", bad, 1.0))
    must_raise(f"frame.animate('pos', ({bl}, 0))", lambda: f.animate("pos", (bad, 0.0), 1.0))
ok("frame.animate valid", lambda: f.animate("x", 50.0, 1.0))

# ---- values that stay valid ----
fr = mk_frame()
fr.x = 5
fr.x = 6.5
fr.pos = (7, 8)
fr.size = V(9, 10)
fr.opacity = 2.0  # still clamped, not an error
if (fr.x, fr.y, fr.w, fr.h) != (7.0, 8.0, 9.0, 10.0):
    fails.append(f"valid assignments changed meaning: {(fr.x, fr.y, fr.w, fr.h)}")

for f_ in fails:
    print("FAIL:", f_)
print("FAIL" if fails else "PASS")
sys.exit(1 if fails else 0)
