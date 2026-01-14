#!/usr/bin/env python3
"""
Test if AnimationManager crashes with no animations
Refactored to use mcrfpy.step() for synchronous execution.
"""

import mcrfpy
import sys

print("Creating empty scene...")
test = mcrfpy.Scene("test")
test.activate()

print("Scene created, no animations added")
print("Advancing simulation with step()...")

# Step multiple times to simulate game loop running
# If AnimationManager crashes with empty state, this will fail
try:
    for i in range(10):
        mcrfpy.step(0.1)  # 10 steps of 0.1s = 1 second simulated

    print("AnimationManager survived 10 steps with no animations!")
    print("PASS")
    sys.exit(0)
except Exception as e:
    print(f"FAIL: AnimationManager crashed: {e}")
    sys.exit(1)
