"""#463: Caption.font_size was unbounded: about 30000 made SFML allocate a 3.8 GB glyph
bitmap, and outline grew the bitmap the same way. Both are now limited to 0..2048 px
(taller than a 4K screen), on assignment, in the constructor and as animate() targets,
including delta animations. An easing that overshoots stays in range while it runs."""
import sys

import mcrfpy

failures = []


def check(cond, msg):
    print(("ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


def raises(fn):
    try:
        fn()
    except ValueError:
        return True
    return False


c = mcrfpy.Caption(text="A", pos=(0, 0))
for name in ("font_size", "outline"):
    setattr(c, name, 0)
    check(getattr(c, name) == 0, f"{name} = 0 accepted")
    setattr(c, name, 2048)
    check(getattr(c, name) == 2048, f"{name} = 2048 accepted")
    check(raises(lambda: setattr(c, name, 2049)), f"{name} = 2049 raises ValueError")
    check(raises(lambda: setattr(c, name, 30000)), f"{name} = 30000 raises ValueError")

check(raises(lambda: mcrfpy.Caption(text="A", font_size=4096)), "Caption(font_size=4096) raises")
check(raises(lambda: mcrfpy.Caption(text="A", outline=4096)), "Caption(outline=4096) raises")

c.font_size = 16
c.outline = 0
check(raises(lambda: c.animate("font_size", 3000, 0.1)), "animate font_size to 3000 raises")
check(raises(lambda: c.animate("font_size", -1, 0.1)), "animate font_size to -1 raises")
c.font_size = 2000
check(raises(lambda: c.animate("font_size", 100, 0.1, delta=True)),
      "delta animate past 2048 raises")
c.font_size = 16
check(raises(lambda: c.animate("outline", 5000, 0.1)), "animate outline to 5000 raises")

# Overshooting easing from 0 dips below 0 (and past the end): clamped while it runs.
c.font_size = 2040
c.animate("font_size", 2048, 0.2, mcrfpy.Easing.EASE_OUT_BACK)
c2 = mcrfpy.Caption(text="A", pos=(0, 0), font_size=1)
c2.animate("font_size", 0, 0.2, mcrfpy.Easing.EASE_IN_BACK)
seen = []
for _ in range(30):
    mcrfpy.step(0.01)
    seen += [c.font_size, c2.font_size]
check(all(0 <= v <= 2048 for v in seen), f"overshooting easings stay in 0..2048 (min {min(seen)}, max {max(seen)})")
check(c.font_size == 2048 and c2.font_size == 0, "animations end on their targets")

if failures:
    sys.exit(1)
print("PASS")
sys.exit(0)
