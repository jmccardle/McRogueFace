"""Regression test for issue #309.

Caption numeric setters (outline, font_size) previously cast raw floats to
unsigned int without any check. Feeding a negative or out-of-range value
triggered UBSan under the fuzz harness (fuzz_property_types).

#309 first clamped these values; #463 replaced the clamp with a ValueError
(0 to 2048 px). The values that were UB must now raise, through both the
setter and the constructor, and never reach the cast.
"""

import mcrfpy
import sys

BAD = (-5.0, -992.065, 1e9, 1e20, float("nan"), float("inf"))


def expect_value_error(fn, label):
    try:
        fn()
    except ValueError:
        return
    print(f"FAIL: {label} was accepted")
    sys.exit(1)


def main():
    c = mcrfpy.Caption(text="x", pos=(0, 0))
    for v in BAD:
        expect_value_error(lambda: setattr(c, "outline", v), f"outline = {v}")
        expect_value_error(lambda: setattr(c, "font_size", v), f"font_size = {v}")
        expect_value_error(lambda: mcrfpy.Caption(text="y", outline=v), f"Caption(outline={v})")
        expect_value_error(lambda: mcrfpy.Caption(text="y", font_size=v), f"Caption(font_size={v})")

    # Type errors are still raised for non-numeric input
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
