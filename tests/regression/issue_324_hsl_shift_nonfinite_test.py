"""
Regression test for issue #324 -- Texture.hsl_shift float->Uint8 UB.

A NaN/inf hue/sat/lit shift propagated through hsl_to_rgb to NaN r/g/b, and the
final (sf::Uint8)(r * 255.0f) casts are undefined behavior on NaN (UBSan:
"nan is outside the range of representable values of type 'unsigned char'",
PyTexture.cpp:458-460). The fix rejects non-finite shift arguments with a
ValueError before any pixel math runs.

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


tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)

# --- finite shifts still produce a new Texture ------------------------------
shifted = tex.hsl_shift(30.0, 0.1, -0.1)
check("finite hsl_shift returns a Texture", isinstance(shifted, mcrfpy.Texture))

# --- non-finite shifts must raise ValueError, not invoke UB -----------------
bad = [
    ("nan hue", (math.nan,)),
    ("inf hue", (math.inf,)),
    ("nan sat", (10.0, math.nan)),
    ("-inf sat", (10.0, -math.inf)),
    ("nan lit", (10.0, 0.0, math.nan)),
    ("inf lit", (10.0, 0.0, math.inf)),
]
for label, args in bad:
    try:
        tex.hsl_shift(*args)
        check("hsl_shift(%s) raises" % label, False)
    except ValueError:
        check("hsl_shift(%s) raises ValueError" % label, True)
    except Exception as e:
        check("hsl_shift(%s) raises ValueError (got %s)" % (label, type(e).__name__), False)


print("")
if failures:
    print("FAIL -- %d check(s) failed:" % len(failures))
    for f in failures:
        print("  - " + f)
    sys.exit(1)
print("PASS -- Texture.hsl_shift rejects non-finite shift arguments.")
sys.exit(0)
