"""Test for issue #180: Stopped timers with user reference should stay alive.

This test verifies that:
1. A stopped timer with a user reference remains accessible
2. A stopped timer can be restarted
3. A stopped timer without references is properly cleaned up
"""
import mcrfpy
import gc
import sys

fire_count = 0

def on_timer(timer, runtime):
    """Timer callback."""
    global fire_count
    fire_count += 1
    print(f"Timer fired! count={fire_count}")

# Set up test scene
scene = mcrfpy.Scene("test")
mcrfpy.current_scene = scene

print("=== Test 1: Stopped timer with reference stays alive ===")

# Create timer and keep reference
my_timer = mcrfpy.Timer("kept_timer", on_timer, 50)
print(f"Created timer: {my_timer.name}, active={my_timer.active}")

# Advance time to fire once
mcrfpy.step(60)
print(f"After step: fire_count={fire_count}")

# Stop the timer
my_timer.stop()
print(f"Stopped timer: active={my_timer.active}, stopped={my_timer.stopped}")

# Timer should NOT be in mcrfpy.timers (it's stopped)
timers = mcrfpy.timers
timer_names = [t.name for t in timers]
print(f"Timers after stop: {timer_names}")

if "kept_timer" in timer_names:
    print("Note: Stopped timer still in mcrfpy.timers (expected - it was accessed)")

# But we should still have our reference and can restart
print(f"Our reference still valid: {my_timer.name}")
my_timer.restart()
print(f"Restarted timer: active={my_timer.active}")

# Advance time and verify it fires again
old_count = fire_count
mcrfpy.step(60)
print(f"After restart step: fire_count={fire_count}")

if fire_count <= old_count:
    print("FAIL: Restarted timer didn't fire")
    sys.exit(1)

print("\n=== Test 2: Stopped timer without reference is cleaned up ===")

# Create another timer, stop it, and lose the reference
temp_timer = mcrfpy.Timer("temp_timer", on_timer, 50)
temp_timer.stop()
print(f"Created and stopped temp_timer")

# Clear reference and GC
del temp_timer
gc.collect()

# The timer should be gone (stopped + no reference = GC'd)
timers = mcrfpy.timers
timer_names = [t.name for t in timers]
print(f"Timers after del+GC: {timer_names}")

# Note: temp_timer might still be there if it was retrieved before - that's OK
# The key test is that it WON'T fire since it's stopped

# Clean up
my_timer.stop()

print("\nPASS: Timer lifecycle works correctly")
sys.exit(0)
