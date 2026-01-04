#!/usr/bin/env python3
"""
Test if AnimationManager crashes with no animations
"""

import mcrfpy

print("Creating empty scene...")
test = mcrfpy.Scene("test")
test.activate()

print("Scene created, no animations added")
print("Starting game loop in 100ms...")

def check_alive(timer, runtime):
    print(f"Timer fired at {runtime}ms - AnimationManager survived!")
    mcrfpy.Timer("exit", lambda t, r: mcrfpy.exit(), 100, once=True)

mcrfpy.Timer("check", check_alive, 1000, once=True)
print("If this crashes immediately, AnimationManager has an issue with empty state")
