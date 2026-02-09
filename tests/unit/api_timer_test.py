#!/usr/bin/env python3
"""Test for mcrfpy.Timer class - replaces old setTimer/delTimer tests (#173)"""
import mcrfpy
import sys

def test_timers():
    """Test Timer class API"""
    print("Testing mcrfpy.Timer class...")

    # Test 1: Create a simple timer
    try:
        call_count = [0]
        def simple_callback(timer, runtime):
            call_count[0] += 1
            print(f"Timer callback called, count={call_count[0]}, runtime={runtime}")

        timer = mcrfpy.Timer("test_timer", simple_callback, 100)
        print("✓ Timer() created successfully")
        print(f"  Timer repr: {timer}")
    except Exception as e:
        print(f"✗ Timer() failed: {e}")
        print("FAIL")
        return

    # Test 2: Stop the timer
    try:
        timer.stop()
        print("✓ timer.stop() called successfully")
        assert timer.stopped == True, "Timer should be stopped"
        print(f"  Timer after stop: {timer}")
    except Exception as e:
        print(f"✗ timer.stop() failed: {e}")
        print("FAIL")
        return

    # Test 3: Restart the timer
    try:
        timer.start()
        print("✓ timer.start() called successfully")
        assert timer.stopped == False, "Timer should not be stopped"
        assert timer.active == True, "Timer should be active"
        timer.stop()  # Clean up
    except Exception as e:
        print(f"✗ timer.start() failed: {e}")
        print("FAIL")
        return

    # Test 4: Create timer with start=False
    try:
        def callback2(timer, runtime): pass
        timer2 = mcrfpy.Timer("timer2", callback2, 500, start=False)
        assert timer2.stopped == True, "Timer with start=False should be stopped"
        print("✓ Timer with start=False created in stopped state")
        timer2.start()
        assert timer2.active == True, "Timer should be active after start()"
        timer2.stop()
    except Exception as e:
        print(f"✗ Timer with start=False failed: {e}")
        print("FAIL")
        return

    # Test 5: Create multiple timers
    try:
        def callback3(t, rt): pass

        t1 = mcrfpy.Timer("multi1", callback3, 500)
        t2 = mcrfpy.Timer("multi2", callback3, 750)
        t3 = mcrfpy.Timer("multi3", callback3, 250)
        print("✓ Multiple timers created successfully")

        # Clean up
        t1.stop()
        t2.stop()
        t3.stop()
        print("✓ Multiple timers stopped successfully")
    except Exception as e:
        print(f"✗ Multiple timer test failed: {e}")
        print("FAIL")
        return

    # Test 6: mcrfpy.timers collection
    try:
        # Create a timer that's running
        running_timer = mcrfpy.Timer("running_test", callback3, 1000)

        timers = mcrfpy.timers
        assert isinstance(timers, tuple), "mcrfpy.timers should be a tuple"
        print(f"✓ mcrfpy.timers returns tuple with {len(timers)} timer(s)")

        # Clean up
        running_timer.stop()
    except Exception as e:
        print(f"✗ mcrfpy.timers test failed: {e}")
        print("FAIL")
        return

    # Test 7: active property is read-write
    try:
        active_timer = mcrfpy.Timer("active_test", callback3, 1000)
        assert active_timer.active == True, "New timer should be active"

        active_timer.active = False  # Should pause
        assert active_timer.paused == True, "Timer should be paused after active=False"

        active_timer.active = True  # Should resume
        assert active_timer.active == True, "Timer should be active after active=True"

        active_timer.stop()
        active_timer.active = True  # Should restart from stopped
        assert active_timer.active == True, "Timer should restart from stopped via active=True"

        active_timer.stop()
        print("✓ active property is read-write")
    except Exception as e:
        print(f"✗ active property test failed: {e}")
        print("FAIL")
        return

    # Test 8: remaining property
    try:
        rem_timer = mcrfpy.Timer("remaining_test", callback3, 1000)
        remaining = rem_timer.remaining
        assert isinstance(remaining, (int, float)), f"remaining should be numeric, got {type(remaining)}"
        assert remaining > 0, f"remaining should be > 0 on fresh timer, got {remaining}"
        assert remaining <= 1000, f"remaining should be <= interval, got {remaining}"
        rem_timer.stop()
        print(f"  Timer.remaining = {remaining}")
        print("OK: remaining property works")
    except Exception as e:
        print(f"FAIL: remaining property: {e}")
        print("FAIL")
        return

    # Test 9: callback property (read and write)
    try:
        cb_counts = [0, 0]
        def cb_a(timer, runtime):
            cb_counts[0] += 1
        def cb_b(timer, runtime):
            cb_counts[1] += 1

        cb_timer = mcrfpy.Timer("callback_test", cb_a, 200)

        # Read callback
        assert cb_timer.callback is cb_a, "callback should return original function"

        # Replace callback
        cb_timer.callback = cb_b
        assert cb_timer.callback is cb_b, "callback should return new function"

        # Fire the timer to confirm new callback is used
        for _ in range(3):
            mcrfpy.step(0.21)
        cb_timer.stop()
        assert cb_counts[0] == 0, f"old callback should not fire, got {cb_counts[0]}"
        assert cb_counts[1] >= 1, f"new callback should fire, got {cb_counts[1]}"
        print("OK: callback property read/write works")
    except Exception as e:
        print(f"FAIL: callback property: {e}")
        print("FAIL")
        return

    print("\nAll Timer API tests passed")
    print("PASS")

# Run the test
test_timers()

# Exit cleanly
sys.exit(0)
