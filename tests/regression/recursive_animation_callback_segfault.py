# Regression test: Recursive animation callbacks
# Issue: Animation callbacks that started new animations caused segfault in AnimationManager::update
# Fixed by: Deferring animation removal during update loop iteration
#
# This test verifies that:
# 1. Animation callbacks can start new animations on the same property (REPLACE mode)
# 2. No segfault occurs from iterator invalidation
# 3. The animation chain completes properly

import mcrfpy
import sys

scene = mcrfpy.Scene("test")
mcrfpy.current_scene = scene

frame = mcrfpy.Frame(pos=(100, 100), size=(50, 50), fill_color=mcrfpy.Color(255, 0, 0))
scene.children.append(frame)

callback_count = 0
MAX_CALLBACKS = 10

def recursive_callback(target, prop, value):
    """Animation callback that starts another animation on the same property"""
    global callback_count
    callback_count += 1

    if callback_count >= MAX_CALLBACKS:
        return

    # Chain another animation - this used to cause segfault due to iterator invalidation
    target.animate("x", 100 + (callback_count * 20), 0.1, mcrfpy.Easing.LINEAR, callback=recursive_callback)

# Start the chain
frame.animate("x", 200, 0.1, mcrfpy.Easing.LINEAR, callback=recursive_callback)

# In headless mode mcrfpy.step() is the only clock: drive the animation chain forward.
# Each link is 0.1s; MAX_CALLBACKS links need >= 1.0s of simulated time. Step generously
# and bail out as soon as the chain is complete.
MAX_STEPS = 400
steps = 0
while callback_count < MAX_CALLBACKS and steps < MAX_STEPS:
    mcrfpy.step(0.02)
    steps += 1

if callback_count < MAX_CALLBACKS:
    print(f"FAIL - only {callback_count}/{MAX_CALLBACKS} callbacks executed after {steps} steps")
    sys.exit(1)

# The chain completed without segfault (iterator invalidation in AnimationManager::update).
# The final animation of the chain targets x = 100 + (MAX_CALLBACKS-1)*20; run a few more
# steps so it settles, proving the manager is still healthy after the recursive churn.
for _ in range(20):
    mcrfpy.step(0.02)

expected_x = 100 + (MAX_CALLBACKS - 1) * 20
if abs(frame.x - expected_x) > 0.5:
    print(f"FAIL - final animation did not complete: frame.x={frame.x}, expected {expected_x}")
    sys.exit(1)

print(f"PASS - {callback_count} recursive animation callbacks completed without segfault; frame.x={frame.x}")
sys.exit(0)
