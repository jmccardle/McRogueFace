"""Regression test for issue #307: Color.__eq__/__ne__ for value comparison.

Color had __hash__ but no __eq__/__ne__, meaning two Colors with identical RGBA
values compared by identity (id()) rather than by value. This violated the Python
convention that objects with __hash__ should also implement __eq__.
"""
import mcrfpy
import sys

errors = []

def check(condition, msg):
    if not condition:
        errors.append(msg)

# Basic equality
c1 = mcrfpy.Color(255, 0, 0)
c2 = mcrfpy.Color(255, 0, 0)
c3 = mcrfpy.Color(0, 255, 0)

check(c1 == c2, "Same RGBA should be equal")
check(not (c1 != c2), "Same RGBA should not be not-equal")
check(c1 != c3, "Different RGBA should be not-equal")
check(not (c1 == c3), "Different RGBA should not be equal")

# Alpha matters
c4 = mcrfpy.Color(255, 0, 0, 128)
check(c1 != c4, "Different alpha should be not-equal")

# Self-equality
check(c1 == c1, "Color should equal itself")

# Equality with tuples
check(c1 == (255, 0, 0), "Color should equal 3-tuple")
check(c1 == (255, 0, 0, 255), "Color should equal 4-tuple with matching alpha")
check(c1 != (255, 0, 0, 128), "Color should not equal tuple with different alpha")
check(c1 != (0, 0, 0), "Color should not equal different tuple")

# Equality with lists
check(c1 == [255, 0, 0], "Color should equal list")
check(c1 == [255, 0, 0, 255], "Color should equal list with alpha")

# Reflected comparisons (tuple on left)
check((255, 0, 0) == c1, "Reflected == should work")
check(not ((255, 0, 0) != c1), "Reflected != should work for equal")
check((0, 255, 0) != c1, "Reflected != should work for unequal")

# Non-comparable types return NotImplemented (Python converts to False/True)
check(not (c1 == "red"), "Color vs string should not be equal")
check(c1 != "red", "Color vs string should be not-equal")
check(not (c1 == 42), "Color vs int should not be equal")
check(not (c1 == None), "Color vs None should not be equal")

# Wrong-size tuples return NotImplemented
check(not (c1 == (255,)), "Color vs 1-tuple should not be equal")
check(not (c1 == (255, 0)), "Color vs 2-tuple should not be equal")
check(not (c1 == (255, 0, 0, 255, 0)), "Color vs 5-tuple should not be equal")

# Ordering operators should raise TypeError
try:
    c1 < c2
    errors.append("< should raise TypeError")
except TypeError:
    pass

try:
    c1 > c2
    errors.append("> should raise TypeError")
except TypeError:
    pass

# Hash consistency: equal objects must have equal hashes
check(hash(c1) == hash(c2), "Equal colors must have equal hashes")

# Explicit black
c_black = mcrfpy.Color(0, 0, 0)
check(c_black == (0, 0, 0, 255), "Color(0,0,0) should equal (0,0,0,255)")

if errors:
    for e in errors:
        print(f"FAIL: {e}")
    print(f"\n{len(errors)} error(s)")
    sys.exit(1)
else:
    print("PASS")
    sys.exit(0)
