#!/usr/bin/env python3
"""Very simple animation callback test"""
import mcrfpy
import sys

callback_fired = False

def cb(target, prop, value):
    global callback_fired
    callback_fired = True

# Setup scene
test = mcrfpy.Scene("test")
mcrfpy.current_scene = test

# Create frame and animate it
f = mcrfpy.Frame(pos=(0, 0), size=(50, 50))
test.children.append(f)
f.animate("x", 100.0, 0.1, "linear", callback=cb)

# Advance past animation duration (0.1s)
for _ in range(3):
    mcrfpy.step(0.05)

# Verify callback fired
if callback_fired:
    print("PASS: Callback fired", file=sys.stderr)
    sys.exit(0)
else:
    print("FAIL: Callback did not fire", file=sys.stderr)
    sys.exit(1)
