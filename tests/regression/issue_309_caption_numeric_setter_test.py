"""Regression test for issue #309.

Caption numeric setters (outline, font_size) previously cast raw floats to
unsigned int without clamping. Feeding a negative or out-of-range value
triggered UBSan under the fuzz harness (fuzz_property_types).

This test exercises the patched paths with values that would previously be UB:
- negative outline
- negative font_size
- extremely large font_size (beyond UINT_MAX)

Also exercises the constructor path which had the same bug.
"""

import mcrfpy
import sys


def main():
    # Setter path: create a Caption then poke the values
    c = mcrfpy.Caption(text="x", pos=(0, 0))

    # Negative outline: used to be UB via setOutlineThickness -> sane now
    c.outline = -5.0
    # Post-clamp: the value exposed is the raw float (getter returns float),
    # but the UB path is gone. Just assert no crash and no Python exception.
    _ = c.outline

    # Very large outline: float stays a float, not UB, but make sure it doesn't explode
    c.outline = 1e9
    _ = c.outline

    # Negative font_size: this was the UBSan trigger (-992.065 in the original crash)
    c.font_size = -992.065
    _ = c.font_size  # must not crash

    # Font size above UINT_MAX: would cast to huge unsigned, now clamped
    c.font_size = 1e20
    _ = c.font_size

    # Constructor path: kwargs with pathological values
    c2 = mcrfpy.Caption(text="y", pos=(10, 10), outline=-3.0, font_size=-17.5)
    # Accessing properties must not crash
    _ = c2.outline
    _ = c2.font_size

    c3 = mcrfpy.Caption(text="z", pos=(20, 20), font_size=1e15)
    _ = c3.font_size

    # Type errors should still be raised for non-numeric input
    try:
        c.font_size = "not a number"
    except TypeError:
        pass
    else:
        print("FAIL: font_size should reject strings")
        sys.exit(1)

    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
