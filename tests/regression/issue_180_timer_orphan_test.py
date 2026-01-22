"""Test for issue #180: Timers without a user-stored reference should still fire.

This test verifies that timers continue running even when the Python object
goes out of scope, and that they can be accessed via mcrfpy.timers.
"""
import mcrfpy
import gc
import sys

# Track timer fires
fire_count = 0

def on_timer(timer, runtime):
    """Timer callback that increments fire count."""
    global fire_count
    fire_count += 1
    print(f"Timer fired! count={fire_count}, runtime={runtime}")

def create_orphan_timer():
    """Create a timer without storing a reference."""
    # This timer should keep running even though we don't store the reference
    mcrfpy.Timer("orphan_timer", on_timer, 50)  # 50ms interval
    print("Created orphan timer (no reference stored)")

# Set up test scene
scene = mcrfpy.Scene("test")
mcrfpy.current_scene = scene

# Create the orphan timer (no reference stored)
create_orphan_timer()

# Force garbage collection to ensure the Python wrapper is collected
gc.collect()
print("Forced garbage collection")

# Check timers immediately after GC
timers = mcrfpy.timers
print(f"Timers after GC: {len(timers)}")
for t in timers:
    print(f"  - {t.name}")

# In headless mode, use step() to advance time and process timers
print("\nAdvancing time with step()...")
for i in range(6):
    mcrfpy.step(50)  # Advance 50ms per step = 300ms total
    print(f"  Step {i+1}: fire_count={fire_count}")

# Now check results
print(f"\n=== Final Results ===")
print(f"Fire count: {fire_count}")

# Check that we can still find the timer in mcrfpy.timers
timers = mcrfpy.timers
print(f"Number of timers: {len(timers)}")

orphan_found = False
for t in timers:
    print(f"  - Timer: name={t.name}, interval={t.interval}")
    if t.name == "orphan_timer":
        orphan_found = True
        # Stop it now that we've verified it exists
        t.stop()
        print(f"  -> Stopped orphan timer")

# Verify the orphan timer was found and fired
if not orphan_found:
    print("FAIL: Orphan timer not found in mcrfpy.timers")
    sys.exit(1)

if fire_count == 0:
    print("FAIL: Orphan timer never fired")
    sys.exit(1)

print(f"\nPASS: Orphan timer fired {fire_count} times and was accessible via mcrfpy.timers")
sys.exit(0)
