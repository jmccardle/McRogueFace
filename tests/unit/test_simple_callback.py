#!/usr/bin/env python3
"""Very simple callback test - refactored to use mcrfpy.step()"""
import mcrfpy
import sys

callback_fired = False

def cb(a, t):
    global callback_fired
    callback_fired = True
    print("CB")

# Setup scene
test = mcrfpy.Scene("test")
test.activate()
mcrfpy.step(0.01)  # Initialize

# Create entity and animation
e = mcrfpy.Entity((0, 0), texture=None, sprite_index=0)
a = mcrfpy.Animation("x", 1.0, 0.1, "linear", callback=cb)
a.start(e)

# Advance past animation duration (0.1s)
mcrfpy.step(0.15)

# Verify callback fired
if callback_fired:
    print("PASS: Callback fired")
    sys.exit(0)
else:
    print("FAIL: Callback did not fire")
    sys.exit(1)
