#!/usr/bin/env python3
"""
Test if AnimationManager crashes with no animations
"""

import mcrfpy

print("Creating empty scene...")
mcrfpy.createScene("test")
mcrfpy.setScene("test")

print("Scene created, no animations added")
print("Starting game loop in 100ms...")

def check_alive(runtime):
    print(f"Timer fired at {runtime}ms - AnimationManager survived!")
    mcrfpy.setTimer("exit", lambda t: mcrfpy.exit(), 100)

mcrfpy.setTimer("check", check_alive, 1000)
print("If this crashes immediately, AnimationManager has an issue with empty state")