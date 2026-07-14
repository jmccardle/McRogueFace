#!/usr/bin/env python3
"""Tripwire test: the engine must never consult the REPL prompt while running.

Originally this was a debugging aid -- it monkey-patched sys.ps1 with an object
that printed a stack trace when accessed, then did "nothing else, let the game
run", so a human could see whether the engine dropped into an interactive REPL.
It never asserted anything and never declared an exit status.

The tripwire is still the right instrument; it just needs to be checked. sys.ps1
is only read by a read-eval-print loop, so any access to it during an --exec run
means the embedded interpreter fell into interactive mode (which, headless, hangs
the process on stdin). This installs the detector, drives a full headless run
past it (#350: mcrfpy.step() is the clock; screenshot() forces a render), and
fails if the tripwire was touched.

Sibling force_non_interactive.py asserts the *static* non-interactive properties
(flags, absent prompts, stdin); this one watches the *running* engine.
"""
import sys
import os
import traceback
import mcrfpy

failures = []
accesses = []


def check(label, condition, detail=""):
    if condition:
        print("  ok   : %s" % label)
    else:
        print("  FAIL : %s %s" % (label, detail))
        failures.append(label)


class PS1Detector:
    """Screams (and records) if anything asks for the interactive prompt."""

    def _trip(self, how):
        accesses.append(how)
        print("\n!!! sys.ps1 accessed via %s! Stack trace:" % how)
        traceback.print_stack()
        return ">>> "

    def __repr__(self):
        return self._trip("__repr__")

    def __str__(self):
        return self._trip("__str__")


# The engine must not have installed a prompt of its own before we get here.
check("sys.ps1 not preinstalled by engine", not hasattr(sys, "ps1"))

detector = PS1Detector()
sys.ps1 = detector
print("ps1 detector installed")

# Now let the engine actually run. In headless mode the engine advances only when
# we drive it, so "letting the game run" means stepping the clock ourselves and
# forcing a render -- both of which are the paths that historically could reenter
# the interpreter.
scene = mcrfpy.Scene("trace_interactive")
mcrfpy.current_scene = scene

ticks = []
mcrfpy.Timer("tick", lambda timer, runtime: ticks.append(runtime), 50)

frame = mcrfpy.Frame(pos=(10, 10), size=(100, 100))
scene.children.append(frame)
frame.animate("x", 200.0, 0.2, mcrfpy.Easing.EASE_IN_OUT)

for _ in range(10):
    mcrfpy.step(0.05)

shot = "trace_interactive_render.png"
mcrfpy.automation.screenshot(shot)
if os.path.exists(shot):
    os.remove(shot)

# The run must have been real, or the tripwire proves nothing.
check("headless clock advanced (timer fired)", len(ticks) >= 1,
      "timer fired %d time(s)" % len(ticks))
check("animation advanced during run", frame.x > 10.0,
      "frame.x = %r" % (frame.x,))

# The tripwire itself: nothing may have read sys.ps1 during any of that.
check("sys.ps1 never accessed during engine run", not accesses,
      "accessed %d time(s): %s" % (len(accesses), accesses))

# And the engine must not have reconfigured the interpreter behind our back --
# our detector should still be the installed prompt, and inspect mode still off.
check("sys.ps1 still our detector", sys.ps1 is detector)
check("sys.flags.inspect == 0", sys.flags.inspect == 0,
      "got %r" % (sys.flags.inspect,))
check("sys.flags.interactive == 0", sys.flags.interactive == 0,
      "got %r" % (sys.flags.interactive,))

# Leave the interpreter as we found it.
del sys.ps1

if failures:
    print("FAIL: %d check(s) failed: %s" % (len(failures), ", ".join(failures)))
    sys.exit(1)

print("PASS")
sys.exit(0)
