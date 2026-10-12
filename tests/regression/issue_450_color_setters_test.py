"""Regression gate for #450 - every Color write converts exactly like Color(value).

Color setters used three converters: Frame's matched Color(); Circle's wrapped 300 to 44;
PyColor::fromPy() clamped, read 1.5 as 255, read None as White and took a bare int as grey.
Decided rule: anything written to a Color -- attribute, constructor keyword, ColorLayer item,
GridPoint layer attribute, method argument -- accepts a Color or exactly what Color(value)
accepts (an (r, g, b[, a]) tuple of ints in 0-255) and raises exactly what Color(value)
raises otherwise. Nothing is clamped, wrapped or defaulted.

The gate discovers Color attributes by introspection: every exported class whose getset
descriptors mention Color must have a maker below, and every attribute of a made object
that reads back as a Color is checked. A new Color attribute is covered automatically; a
new type with one fails here until it gets a maker.
"""
import sys
import types

import mcrfpy

C = mcrfpy.Color
failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


scene = mcrfpy.Scene("t450")
scene.activate()

ACCEPTED = [C(10, 20, 30, 40), (1, 2, 3), (1, 2, 3, 4), (0, 0, 0, 0), (255, 255, 255, 255),
            "red", "xkcd:dust", "#10203040"]   # colour strings since #458
REJECTED = [(300, 0, 0), (1.5, 0, 0), None, 5, 1.5, [1, 2, 3], (1, 2), (1, 2, 3, 4, 5),
            (-1, 0, 0), (0, 0, 0, 256), "no such colour", "#ggg", object()]
BASELINE = C(7, 8, 9, 10)


def expected(value):
    """What Color(value) does: ('ok', Color) or ('raise', exception type)."""
    if isinstance(value, C):
        return ("ok", C(value.r, value.g, value.b, value.a))
    try:
        return ("ok", C(value))
    except Exception as exc:
        return ("raise", type(exc))


def outcome(fn):
    try:
        return ("ok", fn())
    except Exception as exc:
        return ("raise", type(exc))


# Sanity: the table is the issue's table, as Color() sees it.
check(expected((300, 0, 0))[0] == "raise" and expected((1.5, 0, 0))[0] == "raise"
      and expected(None)[0] == "raise" and expected(5)[0] == "raise",
      "Color() rejects (300,0,0), (1.5,0,0), None and 5")


MAKERS = {
    "Frame": lambda **kw: mcrfpy.Frame(pos=(0, 0), size=(10, 10), **kw),
    "Caption": lambda **kw: mcrfpy.Caption(text="x", pos=(0, 0), **kw),
    "Arc": lambda **kw: mcrfpy.Arc(center=(10, 10), radius=5, **kw),
    "Circle": lambda **kw: mcrfpy.Circle(center=(10, 10), radius=5, **kw),
    "Line": lambda **kw: mcrfpy.Line(start=(0, 0), end=(5, 5), **kw),
    "Grid": lambda **kw: mcrfpy.Grid(grid_size=(4, 4), texture=mcrfpy.default_texture, **kw),
    "GridView": lambda **kw: mcrfpy.GridView(grid=mcrfpy.GridData(grid_size=(4, 4)), **kw),
    "GridData": lambda **kw: mcrfpy.GridData(grid_size=(4, 4), **kw),
    "Viewport3D": lambda **kw: mcrfpy.Viewport3D(**kw),
    "Entity3D": lambda **kw: mcrfpy.Entity3D(**kw),
    "Sprite": lambda **kw: mcrfpy.Sprite(pos=(0, 0), **kw),
    "Entity": lambda **kw: mcrfpy.Entity(grid_pos=(0, 0), **kw),
    "ColorLayer": lambda **kw: mcrfpy.ColorLayer(name="c", **kw),
}
# Attributes that store RGB only: the converter is the same, alpha reads back as 255.
RGB_ONLY = {
    "Viewport3D.fog_color": "fog is opaque (stored as an RGB vec3); documented on the attribute",
}
# Classes whose descriptors mention Color but which have no writable Color attribute.
NO_COLOR_ATTRIBUTE = {
    "WangSet": "color_count / colors are read-only terrain metadata from a tileset file",
}


# --- 1. every class with a Color-ish descriptor has a maker ---
for cname in sorted(dir(mcrfpy)):
    cls = getattr(mcrfpy, cname)
    if not isinstance(cls, type):
        continue
    hits = [k for k in dir(cls)
            if isinstance(getattr(cls, k, None), types.GetSetDescriptorType)
            and ("color" in k.lower() or "Color" in (getattr(cls, k).__doc__ or ""))]
    if hits and cname not in MAKERS and cname not in NO_COLOR_ATTRIBUTE:
        check(False, "%s has Color-ish attributes %s but no maker in this gate" % (cname, hits))


def color_attributes(obj):
    names = []
    for name in sorted(dir(obj)):
        if name.startswith("_"):
            continue
        try:
            v = getattr(obj, name)
        except Exception:
            continue
        if isinstance(v, C):
            names.append(name)
    return names


# --- 2. attribute assignment == Color(value), for every Color attribute ---
covered = []
for tname, make in MAKERS.items():
    probe = make()
    for name in color_attributes(probe):
        try:
            setattr(probe, name, BASELINE)
        except AttributeError:
            continue   # read-only Color attribute: nothing to convert
        key = "%s.%s" % (tname, name)
        covered.append(key)
        stored = (lambda c: C(c.r, c.g, c.b, 255)) if key in RGB_ONLY else (lambda c: c)
        wrong = []
        for value in ACCEPTED + REJECTED:
            o = make()
            setattr(o, name, BASELINE)
            want = expected(value)
            if want[0] == "ok":
                want = ("ok", stored(want[1]))
            got = outcome(lambda: setattr(o, name, value))
            after = getattr(o, name)
            if want[0] == "ok":
                if got[0] != "ok" or after != want[1]:
                    wrong.append("%r -> %r / %r, want %r" % (value, got, after, want[1]))
            else:
                if got != want or after != stored(BASELINE):
                    wrong.append("%r -> %r (value %r), want %s and unchanged"
                                 % (value, got, after, want[1].__name__))
        check(not wrong, "%s.%s = v matches Color(v) %s" % (tname, name, wrong or ""))

        # Same rule for the constructor keyword, where there is one (None = default there).
        try:
            make(**{name: BASELINE})
        except TypeError:
            continue
        wrong = []
        for value in ACCEPTED + [v for v in REJECTED if v is not None]:
            want = expected(value)
            if want[0] == "ok":
                want = ("ok", stored(want[1]))
            got = outcome(lambda: getattr(make(**{name: value}), name))
            if want[0] == "ok" and not (got[0] == "ok" and got[1] == want[1]):
                wrong.append("%r -> %r, want %r" % (value, got, want[1]))
            if want[0] == "raise" and got != want:
                wrong.append("%r -> %r, want %s" % (value, got, want[1].__name__))
        check(not wrong, "%s(%s=v) matches Color(v) %s" % (tname, name, wrong or ""))

for must in ("Frame.fill_color", "Frame.outline_color", "Caption.fill_color",
             "Caption.outline_color", "Circle.fill_color", "Circle.outline_color",
             "Arc.color", "Line.color", "Grid.fill_color", "GridView.fill_color",
             "Viewport3D.bg_color", "Viewport3D.fog_color", "Entity3D.color"):
    check(must in covered, "%s discovered and checked" % must)


# --- 3. Color writes that are not attributes: layer cells and method arguments ---
def same_as_color(label, write, read):
    wrong = []
    for value in ACCEPTED + REJECTED:
        write(BASELINE)
        want = expected(value)
        got = outcome(lambda: write(value))
        after = read()
        if want[0] == "ok" and not (got[0] == "ok" and after == want[1]):
            wrong.append("%r -> %r / %r" % (value, got, after))
        if want[0] == "raise" and (got != want or after != BASELINE):
            wrong.append("%r -> %r (value %r), want %s" % (value, got, after, want[1].__name__))
    check(not wrong, "%s matches Color(v) %s" % (label, wrong or ""))


grid = mcrfpy.Grid(grid_size=(4, 4), texture=mcrfpy.default_texture)
layer = mcrfpy.ColorLayer(name="tint", z_index=1)
grid.add_layer(layer)


def cell():
    v = layer.at(1, 1)
    return C(*v) if isinstance(v, tuple) else v


def item_write(v):
    layer[1, 1] = v


def point_write(v):
    grid.at(1, 1).tint = v


def fill_rect_write(v):
    layer.fill_rect((1, 1), (1, 1), v)


same_as_color("ColorLayer[x, y] = v", item_write, cell)
same_as_color("GridPoint.<color layer> = v", point_write, cell)
same_as_color("ColorLayer.set(pos, v)", lambda v: layer.set((1, 1), v), cell)
same_as_color("ColorLayer.fill(v)", lambda v: layer.fill(v), cell)
same_as_color("ColorLayer.fill_rect(pos, size, v)", fill_rect_write, cell)

# An optional color argument (None = its default) converts the same way otherwise.
wrong = []
for value in ACCEPTED + [v for v in REJECTED if v is not None]:
    want = expected(value)

    def fov():
        layer.draw_fov((1, 1), radius=3, visible=value)
        return cell()
    got = outcome(fov)
    if got != want:
        wrong.append("%r -> %r, want %r" % (value, got, want))
check(not wrong, "ColorLayer.draw_fov(visible=v) matches Color(v) %s" % (wrong or ""))

vg = mcrfpy.VoxelGrid(size=(2, 2, 2))
wrong = []
for value in ACCEPTED + [v for v in REJECTED if v is not None]:
    want = expected(value)
    got = outcome(lambda: vg.get_material(vg.add_material("m", color=value))["color"])
    if want[0] == "ok" and got != want:
        wrong.append("%r -> %r" % (value, got))
    if want[0] == "raise" and got != want:
        wrong.append("%r -> %r, want %s" % (value, got, want[1].__name__))
check(not wrong, "VoxelGrid.add_material(color=v) matches Color(v) %s" % (wrong or ""))

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
