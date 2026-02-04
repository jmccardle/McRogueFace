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
        print(f"PASS - {callback_count} recursive animation callbacks completed without segfault")
        sys.exit(0)

    # Chain another animation - this used to cause segfault due to iterator invalidation
    target.animate("x", 100 + (callback_count * 20), 0.1, mcrfpy.Easing.LINEAR, callback=recursive_callback)

# Start the chain
frame.animate("x", 200, 0.1, mcrfpy.Easing.LINEAR, callback=recursive_callback)

def timeout_check(timer, runtime):
    """Safety timeout"""
    if callback_count >= MAX_CALLBACKS:
        print(f"PASS - {callback_count} callbacks completed")
        sys.exit(0)
    else:
        print(f"FAIL - only {callback_count}/{MAX_CALLBACKS} callbacks executed")
        sys.exit(1)

safety_timer = mcrfpy.Timer("safety", timeout_check, 5000, once=True)
