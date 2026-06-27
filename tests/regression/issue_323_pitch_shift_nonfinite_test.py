"""
Regression test for issue #323 -- SoundBuffer.pitch_shift float->size_t UB.

pitch_shift only rejected factor <= 0.0. A NaN factor passes that test (every
NaN comparison is false), so it reached AudioEffects::pitchShift where
static_cast<size_t>(frames / factor) / static_cast<size_t>(srcPos) on a NaN is
undefined behavior (UBSan: "nan is outside the range of representable values of
type 'unsigned long'", AudioEffects.cpp:20/27). The fix rejects non-finite
factors at the binding (ValueError) and hardens the DSP helper guard.

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


# 100 int16 samples (non-empty so pitchShift does not early-return on empty).
sb = mcrfpy.SoundBuffer.from_samples(data=bytes(200), channels=1, sample_rate=44100)
check("from_samples built a non-empty SoundBuffer", sb.sample_count == 100)

# --- valid factor still resamples -------------------------------------------
out = sb.pitch_shift(2.0)
check("valid pitch_shift returns a SoundBuffer", isinstance(out, mcrfpy.SoundBuffer))

# --- invalid factors must raise ValueError, not invoke UB -------------------
bad = [("nan", math.nan), ("inf", math.inf), ("-inf", -math.inf), ("zero", 0.0), ("negative", -1.5)]
for label, f in bad:
    try:
        sb.pitch_shift(f)
        check("pitch_shift(%s) raises" % label, False)
    except ValueError:
        check("pitch_shift(%s) raises ValueError" % label, True)
    except Exception as e:
        check("pitch_shift(%s) raises ValueError (got %s)" % (label, type(e).__name__), False)


print("")
if failures:
    print("FAIL -- %d check(s) failed:" % len(failures))
    for f in failures:
        print("  - " + f)
    sys.exit(1)
print("PASS -- SoundBuffer.pitch_shift rejects non-finite / non-positive factors.")
sys.exit(0)
