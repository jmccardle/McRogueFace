"""#479: Caption.advance is the pen advance (advances + kerning), not ink width."""
import mcrfpy, sys

def adv(t, **kw):
    return mcrfpy.Caption(text=t, font_size=16, **kw).advance

a, b, ab = adv("a"), adv("b"), adv("ab")
assert a > 0 and b > 0
# kerning is small; "ab" ~ a + b
assert abs(ab - (a + b)) <= 2.0, (ab, a, b)
assert adv("") == 0
# trailing spaces count, ink width does not
assert adv("a ") > adv("a")
assert adv("a   ") > adv("a ")
c = mcrfpy.Caption(text="links", font_size=16)
assert c.advance != c.w and c.advance > 0
# widest line wins
assert abs(adv("ab\na") - ab) < 1e-3
assert adv("a\nabab") > adv("ab")
# outline does not change it
assert adv("ab", outline=3) == ab
# size scales it
assert mcrfpy.Caption(text="ab", font_size=32).advance > ab
# non-ASCII (UTF-8 code points, #477)
assert adv("éé") > adv("é") > 0
# read-only
try:
    c.advance = 1.0
except AttributeError:
    pass
else:
    raise AssertionError("advance must be read-only")
print("PASS"); sys.exit(0)
