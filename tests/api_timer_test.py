#!/usr/bin/env python3
"""Test for mcrfpy.setTimer() and delTimer() methods"""
import mcrfpy
import sys

def test_timers():
    """Test timer API methods"""
    print("Testing mcrfpy timer methods...")
    
    # Test 1: Create a simple timer
    try:
        call_count = [0]
        def simple_callback(runtime):
            call_count[0] += 1
            print(f"Timer callback called, count={call_count[0]}, runtime={runtime}")
        
        mcrfpy.setTimer("test_timer", simple_callback, 100)
        print("✓ setTimer() called successfully")
    except Exception as e:
        print(f"✗ setTimer() failed: {e}")
        print("FAIL")
        return
    
    # Test 2: Delete the timer
    try:
        mcrfpy.delTimer("test_timer")
        print("✓ delTimer() called successfully")
    except Exception as e:
        print(f"✗ delTimer() failed: {e}")
        print("FAIL")
        return
    
    # Test 3: Delete non-existent timer (should not crash)
    try:
        mcrfpy.delTimer("nonexistent_timer")
        print("✓ delTimer() accepts non-existent timer names")
    except Exception as e:
        print(f"✗ delTimer() failed on non-existent timer: {e}")
        print("FAIL")
        return
    
    # Test 4: Create multiple timers
    try:
        def callback1(rt): pass
        def callback2(rt): pass
        def callback3(rt): pass
        
        mcrfpy.setTimer("timer1", callback1, 500)
        mcrfpy.setTimer("timer2", callback2, 750)
        mcrfpy.setTimer("timer3", callback3, 250)
        print("✓ Multiple timers created successfully")
        
        # Clean up
        mcrfpy.delTimer("timer1")
        mcrfpy.delTimer("timer2")
        mcrfpy.delTimer("timer3")
        print("✓ Multiple timers deleted successfully")
    except Exception as e:
        print(f"✗ Multiple timer test failed: {e}")
        print("FAIL")
        return
    
    print("\nAll timer API tests passed")
    print("PASS")

# Run the test
test_timers()

# Exit cleanly
sys.exit(0)