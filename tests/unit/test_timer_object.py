#!/usr/bin/env python3
"""
Test the new mcrfpy.Timer object with pause/resume/stop functionality
Updated for new Timer API (#173)
Uses mcrfpy.step() to advance time in headless mode.
"""
import mcrfpy
import sys

print("\n=== Testing mcrfpy.Timer object ===\n")

# Create a minimal scene
timer_test = mcrfpy.Scene("timer_test")
mcrfpy.current_scene = timer_test

all_pass = True

# Test 1: Create a basic timer and verify properties
print("Test 1: Creating Timer object")
call_count = 0

def timer_callback(timer, runtime):
    global call_count
    call_count += 1

timer1 = mcrfpy.Timer("test_timer", timer_callback, 500)
print(f"  Created timer: {timer1}")
print(f"  Interval: {timer1.interval}ms")
print(f"  Active: {timer1.active}")
print(f"  Paused: {timer1.paused}")

if not timer1.active:
    print("  FAIL: Timer should be active after creation")
    all_pass = False
else:
    print("  PASS: Timer is active")

# Stop timer1 before next test to avoid interference
timer1.stop()

# Test 2: Timer fires when stepped
print("\nTest 2: Timer fires with step()")
timer1b = mcrfpy.Timer("test_timer2", timer_callback, 500)
call_count = 0
for i in range(5):
    mcrfpy.step(0.51)  # 510ms > 500ms interval
timer1b.stop()

if call_count >= 3:
    print(f"  PASS: Timer fired {call_count} times (expected >=3)")
else:
    print(f"  FAIL: Timer fired {call_count} times (expected >=3)")
    all_pass = False

# Test 3: Test pause/resume
print("\nTest 3: Testing pause/resume functionality")
pause_count = 0

def pause_callback(timer, runtime):
    global pause_count
    pause_count += 1

timer2 = mcrfpy.Timer("pause_test", pause_callback, 200)

# Let it fire once
mcrfpy.step(0.21)
fires_before_pause = pause_count

# Pause it
timer2.pause()
print(f"  Timer2 paused: {timer2.paused}")
print(f"  Timer2 active: {timer2.active}")

if not timer2.paused:
    print("  FAIL: Timer should be paused")
    all_pass = False

# Step while paused - should not fire
mcrfpy.step(0.51)
fires_while_paused = pause_count

if fires_while_paused == fires_before_pause:
    print(f"  PASS: Timer did not fire while paused (count={fires_while_paused})")
else:
    print(f"  FAIL: Timer fired while paused ({fires_before_pause} -> {fires_while_paused})")
    all_pass = False

# Resume
timer2.resume()
print(f"  Timer2 paused after resume: {timer2.paused}")
mcrfpy.step(0.21)
fires_after_resume = pause_count

if fires_after_resume > fires_while_paused:
    print(f"  PASS: Timer fired after resume (count={fires_after_resume})")
else:
    print(f"  FAIL: Timer did not fire after resume (count={fires_after_resume})")
    all_pass = False

# Test 4: Test stop
print("\nTest 4: Testing stop functionality")
cancel_count = 0

def cancel_callback(timer, runtime):
    global cancel_count
    cancel_count += 1

timer3 = mcrfpy.Timer("cancel_test", cancel_callback, 300)

# Let it fire once
mcrfpy.step(0.31)
fires_before_stop = cancel_count

# Stop it
timer3.stop()
print(f"  Timer3 stopped, active: {timer3.active}")

# Step after stop - should not fire
mcrfpy.step(0.61)
fires_after_stop = cancel_count

if fires_after_stop == fires_before_stop:
    print(f"  PASS: Timer did not fire after stop (count={fires_after_stop})")
else:
    print(f"  FAIL: Timer fired after stop ({fires_before_stop} -> {fires_after_stop})")
    all_pass = False

# Test 5: Test interval modification
print("\nTest 5: Testing interval modification")

def interval_test(timer, runtime):
    pass

timer4 = mcrfpy.Timer("interval_test", interval_test, 1000)
print(f"  Original interval: {timer4.interval}ms")
timer4.interval = 500
print(f"  Modified interval: {timer4.interval}ms")

if timer4.interval == 500:
    print("  PASS: Interval modified successfully")
else:
    print("  FAIL: Interval modification failed")
    all_pass = False

# Test 6: Test restart
print("\nTest 6: Testing restart functionality")
restart_count = 0

def restart_test(timer, runtime):
    global restart_count
    restart_count += 1

timer5 = mcrfpy.Timer("restart_test", restart_test, 400)

# Let it fire twice
mcrfpy.step(0.41)
mcrfpy.step(0.41)

# Restart it
timer5.restart()
count_at_restart = restart_count

# Let it fire again
mcrfpy.step(0.41)

if restart_count > count_at_restart:
    print(f"  PASS: Timer fires after restart (count={restart_count})")
else:
    print(f"  FAIL: Timer did not fire after restart")
    all_pass = False

# Clean up timers
timer2.stop()
timer4.stop()
timer5.stop()

# Final results
print("\n=== Final Results ===")
if all_pass:
    print("All Timer object tests PASSED!")
    print("PASS")
    sys.exit(0)
else:
    print("Some Timer object tests FAILED!")
    print("FAIL")
    sys.exit(1)
