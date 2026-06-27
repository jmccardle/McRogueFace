"""
Regression test for issue #325 -- Vector.int float->long undefined behavior.

Vector.int floored each component and cast to C long with (long)std::floor(...).
For a non-finite component (inf/-inf/NaN) or a finite value outside the long
range, that cast is undefined behavior (UBSan: "inf is outside the range of
representable values of type 'long'", PyVector.cpp:610-611). The fix range-checks
both components and raises OverflowError instead of casting.

ASCII-only source. Prints PASS/FAIL and sys.exit(0/1).
"""

import mcrfpy
import sys
import math

failures = []


def check(label, cond):
    if not cond:
        failures.append(label)
    print(("  ok  " if cond else " FAIL ") + label)


# --- finite components still floor + convert correctly ----------------------
check("finite .int floors toward -inf", mcrfpy.Vector(3.7, -2.2).int == (3, -3))
check("finite negative .int", mcrfpy.Vector(-0.1, 9.9).int == (-1, 9))

# --- non-finite components must raise, not invoke UB ------------------------
bad = [
    ("inf, 1", math.inf, 1.0),
    ("1, inf", 1.0, math.inf),
    ("-inf, 0", -math.inf, 0.0),
    ("nan, 0", math.nan, 0.0),
    ("0, nan", 0.0, math.nan),
    ("1e300, 0 (finite but > LONG_MAX)", 1e300, 0.0),
    ("0, -1e300 (finite but < LONG_MIN)", 0.0, -1e300),
]
for label, x, y in bad:
    v = mcrfpy.Vector(x, y)
    try:
        result = v.int
        check("Vector(%s).int raises (got %r)" % (label, result), False)
    except OverflowError:
        check("Vector(%s).int raises OverflowError" % label, True)
    except Exception as e:
        check("Vector(%s).int raises OverflowError (got %s)" % (label, type(e).__name__), False)


print("")
if failures:
    print("FAIL -- %d check(s) failed:" % len(failures))
    for f in failures:
        print("  - " + f)
    sys.exit(1)
print("PASS -- Vector.int rejects non-finite / out-of-range components.")
sys.exit(0)
