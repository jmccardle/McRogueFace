"""#507: animate() takes a colour string wherever it takes a Color (#458).

Color("red") and frame.fill_color = "red" both work; animate("fill_color", "red", ...)
raised TypeError because its Color target only admitted Color objects and tuples.
"""
import sys
import mcrfpy


def check(cond, msg):
    if not cond:
        print("FAIL:", msg)
        sys.exit(1)


def rgba(c):
    return (c.r, c.g, c.b, c.a)


# A name reaches its colour, interpolating on the way
f = mcrfpy.Frame(pos=(0, 0), size=(10, 10), fill_color=(0, 0, 0, 255))
f.animate("fill_color", "red", 1.0)
mcrfpy.step(0.5)
mid = rgba(f.fill_color)
check(0 < mid[0] < 255 and mid[1:] == (0, 0, 255), "midpoint of black -> 'red' is %r" % (mid,))
mcrfpy.step(0.6)
check(rgba(f.fill_color) == (255, 0, 0, 255), "'red' ends at %r" % (rgba(f.fill_color),))

# Hex, with alpha, and the same normalisation as Color()
f.animate("fill_color", "#00ff0080", 0.1)
mcrfpy.step(0.2)
check(rgba(f.fill_color) == (0, 255, 0, 128), "'#00ff0080' ends at %r" % (rgba(f.fill_color),))
f.animate("fill_color", "Dark Green", 0.1)
mcrfpy.step(0.2)
check(rgba(f.fill_color) == rgba(mcrfpy.Color("darkgreen")), "'Dark Green' ends at %r" % (rgba(f.fill_color),))

# Another type's colour property
cap = mcrfpy.Caption(text="x", pos=(0, 0))
cap.animate("outline_color", "navy", 0.1)
mcrfpy.step(0.2)
check(rgba(cap.outline_color) == (0, 0, 128, 255), "Caption outline_color -> %r" % (rgba(cap.outline_color),))

# An unknown name is the same ValueError as Color('redd'), raised before anything runs
before = rgba(f.fill_color)
try:
    f.animate("fill_color", "redd", 1.0)
except ValueError as e:
    check("redd" in str(e), "ValueError names the bad string: %s" % e)
else:
    check(False, "animate('fill_color', 'redd') should raise ValueError")
mcrfpy.step(1.1)
check(rgba(f.fill_color) == before, "a rejected target must not animate")

# A string is still not a number
try:
    f.animate("x", "red", 1.0)
except TypeError:
    pass
else:
    check(False, "animate('x', 'red') should raise TypeError")

print("PASS")
sys.exit(0)
