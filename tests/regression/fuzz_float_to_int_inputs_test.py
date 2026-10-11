"""Float -> integer conversions found by the 0.3.0 fuzz campaign's second round.
Casting NaN, inf or a value outside the target type's range is undefined behaviour:

- SoundBuffer.echo(delay_ms=-1.6e10) cast the delay to size_t (audio_dsp); slice()
  did the same with an infinite end, concat() with an infinite overlap, and tone()
  with a NaN duration (which passed its `<= 0` check); every effect accepted NaN/inf.
- entity.cell_pos = (-inf, 0) cast to int (property_types); so did tile_size, and
  turn_order / sight_radius / default_behavior / cell_x past int's range.

Non-finite values now raise ValueError, out-of-range ones OverflowError (as Vector.int
does since #325). A finite echo delay longer than the sound leaves it unchanged (the
echo never lands) instead of allocating a delay line for it."""
import sys

import mcrfpy

failures = []


def check(cond, msg):
    print(("ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


def raises(exc, fn):
    try:
        fn()
    except exc:
        return True
    except Exception as e:  # noqa: BLE001 - report the wrong type
        print(f"   (raised {type(e).__name__}: {e})")
        return False
    return False


NAN, INF = float("nan"), float("inf")
buf = mcrfpy.SoundBuffer.from_samples(b"\x10\x00\x20\x00" * 2205, 1, 44100)  # 0.1 s

for label, fn in (("echo delay -1.6e10", lambda: buf.echo(-1.6e10, 0.5, 0.5)),
                  ("echo delay nan", lambda: buf.echo(NAN, 0.5, 0.5)),
                  ("echo feedback inf", lambda: buf.echo(10, INF, 0.5)),
                  ("slice end inf", lambda: buf.slice(0, INF)),
                  ("slice start nan", lambda: buf.slice(NAN, 0.05)),
                  ("reverb wet nan", lambda: buf.reverb(0.5, 0.5, NAN)),
                  ("low_pass cutoff inf", lambda: buf.low_pass(INF)),
                  ("high_pass cutoff nan", lambda: buf.high_pass(NAN)),
                  ("gain nan", lambda: buf.gain(NAN)),
                  ("distortion drive inf", lambda: buf.distortion(INF))):
    check(raises(ValueError, fn), f"{label} raises ValueError")

for label, fn in (("tone duration nan", lambda: mcrfpy.SoundBuffer.tone(440, NAN)),
                  ("tone frequency inf", lambda: mcrfpy.SoundBuffer.tone(INF, 0.1)),
                  ("tone duration 1e9 s", lambda: mcrfpy.SoundBuffer.tone(440, 1e9)),
                  ("tone sample_rate 0", lambda: mcrfpy.SoundBuffer.tone(440, 0.1, sample_rate=0)),
                  ("concat overlap inf", lambda: mcrfpy.SoundBuffer.concat([buf, buf], overlap=INF)),
                  ("concat overlap -1", lambda: mcrfpy.SoundBuffer.concat([buf, buf], overlap=-1))):
    check(raises(ValueError, fn), f"{label} raises ValueError")
joined = mcrfpy.SoundBuffer.concat([buf, buf], overlap=1e6)
check(joined.duration <= 2 * buf.duration + 1e-9, "a huge finite overlap is bounded by the output")

long_echo = buf.echo(1e9, 0.5, 0.5)
check(abs(long_echo.duration - buf.duration) < 1e-9, "an echo delay past the end leaves the sound unchanged")
check(abs(buf.slice(0, 1e300).duration - buf.duration) < 1e-9, "slice to a huge end clamps to the sound's end")

grid = mcrfpy.GridData(grid_size=(10, 10))
e = mcrfpy.Entity((1, 1), grid=grid)
check(raises(ValueError, lambda: setattr(e, "cell_pos", (-INF, 0))), "cell_pos = (-inf, 0) raises ValueError")
check(raises(ValueError, lambda: setattr(e, "cell_pos", (NAN, 0))), "cell_pos = (nan, 0) raises ValueError")
check(raises(OverflowError, lambda: setattr(e, "cell_pos", (1e12, 0))), "cell_pos = (1e12, 0) raises OverflowError")
check(raises(ValueError, lambda: setattr(e, "tile_size", (NAN, 16))), "tile_size = (nan, 16) raises ValueError")
for name in ("turn_order", "sight_radius", "cell_x"):
    check(raises(OverflowError, lambda: setattr(e, name, 2**40)), f"{name} = 2**40 raises OverflowError")

e.cell_pos = (3, 4)
check(tuple(e.cell_pos) == (3, 4), "an in-range cell_pos still works")

if failures:
    sys.exit(1)
print("PASS")
sys.exit(0)
