#!/usr/bin/env python3
"""
Test the new mcrfpy.Timer object with pause/resume/cancel functionality
"""
import mcrfpy
import sys

# Test counters
call_count = 0
pause_test_count = 0
cancel_test_count = 0

def timer_callback(timer, runtime):
    global call_count
    call_count += 1
    print(f"Timer fired! Count: {call_count}, Runtime: {runtime}ms")

def pause_test_callback(timer, runtime):
    global pause_test_count
    pause_test_count += 1
    print(f"Pause test timer: {pause_test_count}")

def cancel_test_callback(timer, runtime):
    global cancel_test_count
    cancel_test_count += 1
    print(f"Cancel test timer: {cancel_test_count} - This should only print once!")

def run_tests(runtime):
    """Main test function that runs after game loop starts"""
    # Delete the timer that called us to prevent re-running
    mcrfpy.delTimer("run_tests")
    
    print("\n=== Testing mcrfpy.Timer object ===\n")
    
    # Test 1: Create a basic timer
    print("Test 1: Creating Timer object")
    timer1 = mcrfpy.Timer("test_timer", timer_callback, 500)
    print(f"✓ Created timer: {timer1}")
    print(f"  Interval: {timer1.interval}ms")
    print(f"  Active: {timer1.active}")
    print(f"  Paused: {timer1.paused}")
    
    # Test 2: Test pause/resume
    print("\nTest 2: Testing pause/resume functionality")
    timer2 = mcrfpy.Timer("pause_test", pause_test_callback, 200)
    
    # Schedule pause after 250ms
    def pause_timer2(runtime):
        print("  Pausing timer2...")
        timer2.pause()
        print(f"  Timer2 paused: {timer2.paused}")
        print(f"  Timer2 active: {timer2.active}")

        # Schedule resume after another 400ms
        def resume_timer2(runtime):
            print("  Resuming timer2...")
            timer2.resume()
            print(f"  Timer2 paused: {timer2.paused}")
            print(f"  Timer2 active: {timer2.active}")

        mcrfpy.setTimer("resume_timer2", resume_timer2, 400)
    
    mcrfpy.setTimer("pause_timer2", pause_timer2, 250)
    
    # Test 3: Test cancel
    print("\nTest 3: Testing cancel functionality")
    timer3 = mcrfpy.Timer("cancel_test", cancel_test_callback, 300)
    
    # Cancel after 350ms (should fire once)
    def cancel_timer3(runtime):
        print("  Canceling timer3...")
        timer3.cancel()
        print("  Timer3 canceled")
    
    mcrfpy.setTimer("cancel_timer3", cancel_timer3, 350)
    
    # Test 4: Test interval modification
    print("\nTest 4: Testing interval modification")
    def interval_test(timer, runtime):
        print(f"  Interval test fired at {runtime}ms")
    
    timer4 = mcrfpy.Timer("interval_test", interval_test, 1000)
    print(f"  Original interval: {timer4.interval}ms")
    timer4.interval = 500
    print(f"  Modified interval: {timer4.interval}ms")
    
    # Test 5: Test remaining time
    print("\nTest 5: Testing remaining time")
    def check_remaining(runtime):
        if timer1.active:
            print(f"  Timer1 remaining: {timer1.remaining}ms")
        if timer2.active or timer2.paused:
            print(f"  Timer2 remaining: {timer2.remaining}ms (paused: {timer2.paused})")
    
    mcrfpy.setTimer("check_remaining", check_remaining, 150)
    
    # Test 6: Test restart
    print("\nTest 6: Testing restart functionality")
    restart_count = [0]
    
    def restart_test(timer, runtime):
        restart_count[0] += 1
        print(f"  Restart test: {restart_count[0]}")
        if restart_count[0] == 2:
            print("  Restarting timer...")
            timer.restart()
    
    timer5 = mcrfpy.Timer("restart_test", restart_test, 400)
    
    # Final verification after 2 seconds
    def final_check(runtime):
        print("\n=== Final Results ===")
        print(f"Timer1 call count: {call_count} (expected: ~4)")
        print(f"Pause test count: {pause_test_count} (expected: ~6-7, with pause gap)")
        print(f"Cancel test count: {cancel_test_count} (expected: 1)")
        print(f"Restart test count: {restart_count[0]} (expected: ~5 with restart)")
        
        # Verify timer states
        try:
            print(f"\nTimer1 active: {timer1.active}")
            print(f"Timer2 active: {timer2.active}")
            print(f"Timer3 active: {timer3.active} (should be False after cancel)")
            print(f"Timer4 active: {timer4.active}")
            print(f"Timer5 active: {timer5.active}")
        except:
            print("Some timers may have been garbage collected")
        
        print("\n✓ All Timer object tests completed!")
        sys.exit(0)
    
    mcrfpy.setTimer("final_check", final_check, 2000)

# Create a minimal scene
mcrfpy.createScene("timer_test")
mcrfpy.setScene("timer_test")

# Start tests after game loop begins
mcrfpy.setTimer("run_tests", run_tests, 100)

print("Timer object tests starting...")