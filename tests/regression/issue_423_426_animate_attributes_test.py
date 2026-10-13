"""Regression gate for #423 and #426 - animate() names and units drifted from the attributes.

#423: Entity.x/.y are pixels, but animate("x") wrote draw_x in tiles (64 -> 1024 px).
#426: GridView lost x/y/w/h/pos/opacity in the type split; Entity.opacity and every
      Color/Vector target (Color(...), Vector(...)) were rejected; Arc/Circle/Line had no pos.

Decided rule: every name animate() accepts is a readable attribute, animated in that
attribute's units and type, so `obj.animate(name, v, d)` ends where `obj.name = v` puts it.
The exceptions are explicit (EXCLUDED below): logical/layout state that is writable but not
a render value. Names animate() used to accept that are not attributes now raise ValueError
pointing at the replacement.

The gate walks every readable number/Vector/Color attribute of every animatable type, so a
new attribute (or a new type that forgets the shared ones) fails here until it is either
animatable or listed.
"""
import sys

import mcrfpy

failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


scene = mcrfpy.Scene("t423")
scene.activate()
grid = mcrfpy.Grid(grid_size=(20, 20), texture=mcrfpy.default_texture, pos=(0, 0), size=(320, 320))   # 16 px cells
scene.children.append(grid)


def entity():
    e = mcrfpy.Entity(grid_pos=(2, 2))
    grid.entities.append(e)
    return e


MAKERS = {
    "Frame": lambda: mcrfpy.Frame(pos=(1, 2), size=(30, 40)),
    "Caption": lambda: mcrfpy.Caption(text="hi", pos=(1, 2)),
    "Sprite": lambda: mcrfpy.Sprite(pos=(1, 2)),
    "Arc": lambda: mcrfpy.Arc(center=(10, 10), radius=5),
    "Circle": lambda: mcrfpy.Circle(center=(10, 10), radius=5),
    "Line": lambda: mcrfpy.Line(start=(0, 0), end=(6, 8)),
    "Grid": lambda: mcrfpy.Grid(grid_size=(10, 10), texture=mcrfpy.default_texture, pos=(0, 0), size=(160, 160)),
    "Viewport3D": lambda: mcrfpy.Viewport3D(),
    "Entity": entity,
}

LAYOUT = {"margin", "horiz_margin", "vert_margin"}
# Writable attributes that are deliberately not animatable.
EXCLUDED = {
    # Caption.baseline (#478) is a discrete anchor (TextBaseline), not a quantity.
    "Frame": LAYOUT, "Caption": LAYOUT | {"baseline"}, "Sprite": LAYOUT, "Arc": LAYOUT, "Circle": LAYOUT,
    "Line": LAYOUT, "Grid": LAYOUT, "Viewport3D": {"cell_size"},
    # Logical state: the integer cell, turn order and behaviour configuration.
    "Entity": {"grid_pos", "grid_x", "grid_y", "cell_pos", "cell_x", "cell_y",
               "tile_size", "tile_width", "tile_height", "turn_order", "sight_radius",
               "default_behavior", "move_speed"},
}


def is_value(v):
    return (not isinstance(v, bool)) and isinstance(v, (int, float, mcrfpy.Vector, mcrfpy.Color))


def nudged(name, v):
    if isinstance(v, mcrfpy.Color):
        return mcrfpy.Color(10, 20, 30, 200)
    if isinstance(v, mcrfpy.Vector):
        return mcrfpy.Vector(v.x + 3, v.y + 4)
    if isinstance(v, int):
        return v + 1
    return 0.25 if name == "opacity" else v + 3.0


def same(a, b):
    if isinstance(a, float) or isinstance(b, float):
        return abs(a - b) < 1e-3
    if isinstance(a, mcrfpy.Vector):
        return abs(a.x - b.x) < 1e-3 and abs(a.y - b.y) < 1e-3
    return a == b


def writable(o, name, v):
    try:
        setattr(o, name, v)
        return True
    except AttributeError:
        return False


# --- 1. every attribute: animate == assign, or explicitly excluded, or read-only ---
for tname, make in MAKERS.items():
    probe = make()
    names = []
    for name in sorted(dir(probe)):
        if name.startswith("_"):
            continue
        try:
            v = getattr(probe, name)
        except Exception:
            continue
        if is_value(v):
            names.append(name)

    wrong = []
    for name in names:
        # Expected: what assignment does, on a fresh object
        o = make()
        if tname not in ("Grid", "Viewport3D", "Entity"):
            scene.children.append(o)
        start = getattr(o, name)
        if not writable(o, name, start):
            try:
                o.animate(name, start, 0.01)
                wrong.append("%s is read-only but animatable" % name)
            except ValueError:
                pass
            continue
        target = nudged(name, start)
        setattr(o, name, target)
        expected = getattr(o, name)
        setattr(o, name, start)

        try:
            o.animate(name, target, 0.01)
            mcrfpy.step(0.05)
            got = getattr(o, name)
            if name in EXCLUDED[tname]:
                wrong.append("%s is excluded but animatable" % name)
            elif not same(got, expected):
                wrong.append("%s: animate -> %r, assign -> %r" % (name, got, expected))
        except ValueError as exc:
            if name not in EXCLUDED[tname]:
                wrong.append("%s rejected: %s" % (name, exc))
        except Exception as exc:
            wrong.append("%s raised %s: %s" % (name, type(exc).__name__, exc))
    check(not wrong, "%s: animate() matches assignment for %d attributes %s"
          % (tname, len(names), wrong or ""))

# --- 1b. the reverse: every shared name animate() accepts is an attribute of that type ---
SHARED = ("x", "y", "pos", "w", "h", "size", "rotation", "origin", "opacity", "z_index",
          "draw_pos", "sprite_offset")
for tname, make in MAKERS.items():
    o = make()
    stray = []
    for name in SHARED:
        try:
            o.animate(name, getattr(o, name) if hasattr(o, name) else 1.0, 0.01)
            accepted = True
        except (ValueError, TypeError):
            accepted = False
        if accepted and not hasattr(o, name):
            stray.append(name)
    check(not stray, "%s: animate() accepts only attribute names %s" % (tname, stray or ""))

# --- 2. targets in every form the setter takes ---
f = mcrfpy.Frame(pos=(0, 0), size=(10, 10))
scene.children.append(f)
for target in (mcrfpy.Color(255, 0, 0), (255, 0, 0), (255, 0, 0, 255)):
    f.fill_color = (0, 0, 0, 255)
    f.animate("fill_color", target, 0.01)
    mcrfpy.step(0.05)
    check(f.fill_color == mcrfpy.Color(255, 0, 0, 255),
          "fill_color animates to a %s target" % type(target).__name__)
for target in (mcrfpy.Vector(40, 50), (40, 50), [40, 50]):
    f.pos = (0, 0)
    f.animate("pos", target, 0.01)
    mcrfpy.step(0.05)
    check(f.pos == mcrfpy.Vector(40, 50), "pos animates to a %s target" % type(target).__name__)

for name, bad in (("fill_color", 5.0), ("x", "far"), ("pos", "far"), ("z_index", 2.5)):
    try:
        f.animate(name, bad, 0.1)
        check(False, "animate(%r, %r) must raise TypeError" % (name, bad))
    except TypeError as exc:
        check(name in str(exc), "a %s target for %r raises TypeError naming it" % (type(bad).__name__, name))

# Color targets are as strict as Color(): no silent clamping or 255-for-a-float
for bad in ((1.5, 0, 0), (300, 0, 0), (1, 2)):
    try:
        f.animate("fill_color", bad, 0.1)
        check(False, "fill_color target %r must raise" % (bad,))
    except (ValueError, TypeError) as exc:
        check(True, "fill_color target %r raises %s" % (bad, type(exc).__name__))

f.fill_color = (0, 0, 0, 255)
f.animate("fill_color.r", 200.0, 0.01)
mcrfpy.step(0.05)
check(f.fill_color.r == 200, "one Color channel still animates ('fill_color.r')")

# --- 3. #423: Entity x/y/pos are pixels, draw_pos is tiles ---
e = entity()
e.animate("x", 64.0, 0.01)
mcrfpy.step(0.05)
check(e.x == 64.0 and e.draw_pos.x == 4.0,
      "animate('x', 64) ends at x=64 px, draw_pos.x=4 tiles (was x=1024) [%r, %r]" % (e.x, e.draw_pos.x))
e.animate("pos", (32, 48), 0.01)
mcrfpy.step(0.05)
check(e.pos == mcrfpy.Vector(32, 48) and e.draw_pos == mcrfpy.Vector(2, 3), "animate('pos') is pixels")
e.animate("draw_pos", (6, 4), 1.0)
mcrfpy.step(0.5)
check(e.draw_pos == mcrfpy.Vector(4, 3.5), "animate('draw_pos') moves in tiles (%r)" % e.draw_pos)
mcrfpy.step(0.6)
check(e.draw_pos == mcrfpy.Vector(6, 4) and e.x == 96.0, "draw_pos lands on its target")

loose = mcrfpy.Entity(grid_pos=(1, 1))
for name, target in (("x", 10.0), ("pos", (10, 10))):
    try:
        loose.animate(name, target, 0.1)
        check(False, "animating %r on an entity with no grid must raise" % name)
    except RuntimeError as exc:
        check("not attached to a Grid" in str(exc), "%r on a grid-less entity raises RuntimeError" % name)
loose.animate("draw_pos", (3, 3), 0.01)
mcrfpy.step(0.05)
check(loose.draw_pos == mcrfpy.Vector(3, 3), "draw_pos animates without a grid")

# --- 4. names that are not attributes are gone, and say what replaced them ---
cap = mcrfpy.Caption(text="x", pos=(0, 0))
line = mcrfpy.Line(start=(0, 0), end=(4, 4))
for obj, name, hint in ((entity(), "draw_x", "draw_pos"), (entity(), "draw_y", "draw_pos"),
                        (entity(), "sprite_scale", "zoom"), (f, "position", "'pos'"),
                        (f, "origin_x", "'origin'"), (cap, "size", "font_size"),
                        (line, "start_x", "'start'"), (f, "no_such_thing", "")):
    try:
        obj.animate(name, 1.0, 0.1)
        check(False, "animate(%r) must raise ValueError" % name)
    except ValueError as exc:
        check(hint in str(exc), "animate(%r) raises ValueError -> %s" % (name, exc))

# --- 5. a Line's pos is its midpoint, and moving it moves the line ---
line = mcrfpy.Line(start=(0, 0), end=(10, 20))
scene.children.append(line)
line.animate("pos", (105, 210), 0.01)
mcrfpy.step(0.05)
check(line.start == mcrfpy.Vector(100, 200) and line.end == mcrfpy.Vector(110, 220),
      "animating Line.pos translates both endpoints (%r, %r)" % (line.start, line.end))
line.end = (130, 220)
check(line.pos == mcrfpy.Vector(115, 210), "moving an endpoint moves the midpoint")

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
