"""#520: DiscreteMap.add/subtract with a negative scalar do the arithmetic (saturating)."""
import sys
import mcrfpy


def fail(msg):
    print("FAIL", msg)
    sys.exit(1)


def val(d):
    return d.get(0, 0)


d = mcrfpy.DiscreteMap((2, 1)); d.fill(100)
d.add(-10)
if val(d) != 90: fail("add(-10) gave %r" % val(d))
d.subtract(-10)
if val(d) != 100: fail("subtract(-10) gave %r" % val(d))
d.add(-1000)
if val(d) != 0: fail("add(-1000) should saturate at 0, got %r" % val(d))
d.add(10 ** 12)
if val(d) != 255: fail("add(10**12) should saturate at 255, got %r" % val(d))
d.subtract(10 ** 12)
if val(d) != 0: fail("subtract(10**12) should saturate at 0, got %r" % val(d))
d.fill(7); d.subtract(-(10 ** 12))
if val(d) != 255: fail("subtract(-10**12) should saturate at 255, got %r" % val(d))

for op in ("add", "subtract"):
    try:
        getattr(d, op)(1.5)
    except TypeError as e:
        if "int" not in str(e) or "float" not in str(e):
            fail("%s(1.5) error does not name the accepted types and the bad one: %s" % (op, e))
    else:
        fail("%s(1.5) did not raise" % op)
print("PASS")
sys.exit(0)
