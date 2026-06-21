"""
Regression test for issue #317 -- automation.scroll() ignored the x-coordinate
of its position argument.

Root cause: scroll() resolved (x, y) from pos but called
    injectMouseEvent(MouseWheelScrolled, clicks, y)
passing `clicks` as the x argument, so the resolved x was dropped AND the event's
mouseWheelScroll.x was set to the scroll amount. The fix gives the scroll delta
its own injectMouseEvent parameter and forwards the real x/y.

LIMITATION: no Python-observable handler currently consumes a scroll event's
position (GameEngine maps only the wheel *delta* to a wheel_up/wheel_down action),
so this test cannot assert the forwarded x end-to-end. It is therefore a smoke /
API-contract regression guard: scroll(clicks, pos=(x, y)) must accept any x, all
documented pos forms, and not raise after the injectMouseEvent refactor (which is
the part that changed how the scroll delta is passed). The x-forwarding itself is
verified by code inspection (McRFPy_Automation.cpp scroll/injectMouseEvent).

ASCII-only. Prints PASS/FAIL + exit.
"""

import mcrfpy
from mcrfpy import automation
import sys

failures = []


def check(label, fn):
    try:
        fn()
        ok = True
    except Exception as e:
        ok = False
        label = "%s (raised %s: %s)" % (label, type(e).__name__, e)
    if not ok:
        failures.append(label)
    print(("  ok  " if ok else " FAIL ") + label)


# A scene must be current for event injection to have a target.
scene = mcrfpy.Scene("issue317")
mcrfpy.current_scene = scene

# Vary x across the position argument; previously x was silently dropped.
check("scroll(3) no position", lambda: automation.scroll(3))
check("scroll(3, pos=None)", lambda: automation.scroll(3, pos=None))
check("scroll(3, (100, 50)) tuple x!=0", lambda: automation.scroll(3, (100, 50)))
check("scroll(-2, (0, 50)) x==0", lambda: automation.scroll(-2, (0, 50)))
check("scroll(1, [250, 75]) list", lambda: automation.scroll(1, [250, 75]))
check("scroll(5, pos=(640, 480)) keyword", lambda: automation.scroll(5, pos=(640, 480)))
check("scroll(-5, mcrfpy.Vector(12, 34)) Vector",
      lambda: automation.scroll(-5, mcrfpy.Vector(12, 34)))

# Same y, different x must both be accepted (the regression dropped x entirely).
check("scroll(2, (10, 200))", lambda: automation.scroll(2, (10, 200)))
check("scroll(2, (900, 200))", lambda: automation.scroll(2, (900, 200)))


print("")
if failures:
    print("FAIL -- %d check(s) failed:" % len(failures))
    for f in failures:
        print("  - " + f)
    sys.exit(1)
print("PASS -- automation.scroll accepts a full (x, y) position across all forms "
      "(x-forwarding verified by code inspection; no observable consumer yet).")
sys.exit(0)
