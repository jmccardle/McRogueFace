"""mcrfpy.TextBaseline, Caption.baseline and mcrfpy.default_text_baseline (#478)."""
import sys

import mcrfpy

TB = mcrfpy.TextBaseline
failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


def raises(exc, fn):
    try:
        fn()
    except exc:
        return True
    except Exception as e:  # the wrong exception is a failure too
        print("    raised %r" % e)
        return False
    return False


print("1. The enum")
check([m.name for m in TB] == ["TOP", "BASELINE", "EM_TOP"], "members: %s" % [m.name for m in TB])
check(TB.TOP == "TOP" and TB.TOP != "EM_TOP" and not (TB.TOP != "TOP"), "compares to its name")
check(TB.EM_TOP == 2 and repr(TB.BASELINE) == "TextBaseline.BASELINE" and str(TB.TOP) == "TOP",
      "int value, repr, str")

print("2. The built-in default is TOP")
check(mcrfpy.default_text_baseline is TB.TOP, "default_text_baseline is TOP")
check(mcrfpy.Caption(text="a").baseline is TB.TOP, "a new Caption is TOP")

print("3. default_text_baseline applies to new captions only")
before = mcrfpy.Caption(text="before")
mcrfpy.default_text_baseline = TB.EM_TOP
check(mcrfpy.default_text_baseline is TB.EM_TOP, "the default reads back")
after = mcrfpy.Caption(text="after")
check(after.baseline is TB.EM_TOP, "a caption made after the change copies it")
check(before.baseline is TB.TOP, "a caption made before keeps its own")
explicit = mcrfpy.Caption(text="explicit", baseline=TB.BASELINE)
check(explicit.baseline is TB.BASELINE, "an explicit baseline= beats the default")
mcrfpy.default_text_baseline = 1  # the int value of a member is accepted, as for Transition
check(mcrfpy.default_text_baseline is TB.BASELINE, "default accepts the int value")
check(after.baseline is TB.EM_TOP, "existing captions still keep theirs")
mcrfpy.default_text_baseline = TB.TOP

print("4. Invalid values raise and change nothing")
for bad, exc in (("nonsense", TypeError), ("TOP", TypeError), (None, TypeError), (True, TypeError),
                 (1.0, TypeError), (mcrfpy.InputState.PRESSED, TypeError), (7, ValueError),
                 (-1, ValueError)):
    def set_default():
        mcrfpy.default_text_baseline = bad
    check(raises(exc, set_default), "default_text_baseline = %r raises %s" % (bad, exc.__name__))
    check(mcrfpy.default_text_baseline is TB.TOP, "  ...and the default is unchanged")
    c = mcrfpy.Caption(text="x", baseline=TB.EM_TOP)

    def set_prop():
        c.baseline = bad
    check(raises(exc, set_prop), "caption.baseline = %r raises %s" % (bad, exc.__name__))
    check(c.baseline is TB.EM_TOP, "  ...and the caption is unchanged")
    check(raises(exc, lambda: mcrfpy.Caption(text="x", baseline=bad)),
          "Caption(baseline=%r) raises %s" % (bad, exc.__name__))
check(raises(AttributeError, lambda: delattr(mcrfpy, "default_text_baseline")),
      "default_text_baseline can't be deleted")

print("5. A font file that can't be read raises instead of laying text out with no metrics")
check(raises(IOError, lambda: mcrfpy.Font("no_such_font_478.ttf")), "Font(missing) raises IOError")

print("=" * 50)
if failures:
    print("FAIL (%d)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
