"""Regression gate for #449 - Entity3D.animate() names are attributes, in their units.

Same rule as #423/#426: every name animate() accepts is a readable attribute, and
animating it ends where assigning it would. Entity3D's world position is exposed as
world_x/world_y/world_z floats (pos/grid_pos stay the integer cell, not animatable).
color, anim_time and anim_speed are writable but deliberately not animatable.
"""
import sys
import mcrfpy

failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


vp = mcrfpy.Viewport3D(pos=(0, 0), size=(100, 100))
vp.set_grid_size(16, 16)


def make():
    e = mcrfpy.Entity3D(pos=(2, 2), scale=1.0)
    vp.entities.append(e)
    return e


EXCLUDED = {"color", "anim_time", "anim_speed", "anim_frame", "anim_loop", "anim_paused", "auto_animate"}
probe = make()
names = []
for name in sorted(dir(probe)):
    if name.startswith("_"):
        continue
    try:
        v = getattr(probe, name)
    except Exception:
        continue
    if isinstance(v, (int, float)):   # bools count: visible
        names.append(name)

for name in names:
    if name in EXCLUDED:
        e = make()
        try:
            e.animate(name, getattr(e, name), 0.01)
            check(False, "%s is excluded but animatable" % name)
        except (ValueError, TypeError):
            check(True, "%s is not animatable" % name)
        continue
    o = make()
    start = getattr(o, name)
    try:
        setattr(o, name, start)
    except (AttributeError, TypeError):
        try:
            o.animate(name, start, 0.01)
            check(False, "%s is read-only but animatable" % name)
        except (ValueError, TypeError):
            check(True, "%s is read-only and not animatable" % name)
        continue
    if isinstance(start, bool):
        target = not start
    elif isinstance(start, int):
        target = start + 1
    else:
        target = start + 3.0
    setattr(o, name, target)
    expected = getattr(o, name)
    setattr(o, name, start)
    try:
        o.animate(name, int(target) if isinstance(target, bool) else target, 0.01)
    except Exception as exc:
        check(False, "%s rejected: %s: %s" % (name, type(exc).__name__, exc))
        continue
    mcrfpy.step(0.05)
    got = getattr(o, name)
    check(abs(float(got) - float(expected)) < 1e-3, "%s: animate -> %r, assign -> %r" % (name, got, expected))

# the attributes the issue named exist
for name in ("world_x", "world_y", "world_z", "rotation", "scale", "scale_x", "scale_y",
             "scale_z", "sprite_index", "visible"):
    check(name in names, "%s is a readable attribute" % name)

# world_x/y/z agree with world_pos
e = make()
e.world_y = 2.5
check(abs(e.world_pos[1] - 2.5) < 1e-6, "world_y assignment moves world_pos")
e.animate("world_z", 7.0, 0.01)
mcrfpy.step(0.05)
check(abs(e.world_pos[2] - 7.0) < 1e-3, "animate('world_z') moves world_pos")

# non-uniform scale
e.animate("scale_y", 4.0, 0.01)
mcrfpy.step(0.05)
check(e.scale_y == 4.0 and e.scale_x == 1.0, "scale_y animates alone")

# delta
e.world_x = 1.0
e.animate("world_x", 2.0, 0.01, delta=True)
mcrfpy.step(0.05)
check(abs(e.world_x - 3.0) < 1e-3, "delta is relative to the attribute")

# sprite_index / visible take ints
e.animate("sprite_index", 5, 0.01)
mcrfpy.step(0.05)
check(e.sprite_index == 5, "sprite_index animates to an int")
e.animate("visible", 0, 0.01)
mcrfpy.step(0.05)
check(e.visible is False, "visible animates")

# bad targets and removed names
try:
    e.animate("world_x", "far", 0.1)
    check(False, "string target must raise TypeError")
except TypeError as exc:
    check("world_x" in str(exc), "string target raises TypeError naming the property")
for name, hint in (("x", "world_x"), ("y", "world_y"), ("z", "world_z"), ("rot_y", "rotation"),
                   ("color", ""), ("pos", ""), ("no_such_thing", "")):
    try:
        e.animate(name, 1.0, 0.1)
        check(False, "animate(%r) must raise ValueError" % name)
    except ValueError as exc:
        check(hint in str(exc), "animate(%r) raises ValueError: %s" % (name, exc))

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
