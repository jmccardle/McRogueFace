# This script is intentionally (almost) empty.
#
# Intent: the engine must survive a script that sets nothing up -- no scene, no UI,
# no timers -- and must not crash when the headless clock is driven in that state.
#
# Under the #350 exit contract a bare `pass` is no longer a valid --exec script:
# falling off the end exits nonzero with a diagnostic. So the "do nothing" case is
# now spelled as "do nothing, then exit 0", plus the checks that make it a real test.
import sys

import mcrfpy

failures = []

# A script that never creates a scene must still find the engine in a sane state.
if not hasattr(mcrfpy, "step"):
    failures.append("mcrfpy.step is missing")
if not hasattr(mcrfpy, "current_scene"):
    failures.append("mcrfpy.current_scene is missing")

# Driving the clock with no scene / no timers / no animations must be a harmless no-op.
try:
    for _ in range(3):
        mcrfpy.step(0.05)
except Exception as e:
    failures.append("mcrfpy.step() raised with no scene set up: %r" % (e,))

if failures:
    for f in failures:
        print("FAIL:", f)
    sys.exit(1)

print("PASS")
sys.exit(0)
