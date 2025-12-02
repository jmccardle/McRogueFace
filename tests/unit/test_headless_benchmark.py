#!/usr/bin/env python3
"""
Test benchmark API behavior in headless mode with step()
=========================================================

Verifies whether step() and screenshot() produce benchmark events.
"""

import mcrfpy
from mcrfpy import automation
import sys
import os
import json

def run_tests():
    """Run headless benchmark tests"""
    print("=== Headless Benchmark Tests ===\n")

    # Create a test scene
    mcrfpy.createScene("benchmark_test")
    mcrfpy.setScene("benchmark_test")
    ui = mcrfpy.sceneUI("benchmark_test")

    # Add some UI elements to have something to render
    frame = mcrfpy.Frame(pos=(100, 100), size=(200, 200))
    frame.fill_color = mcrfpy.Color(255, 0, 0)
    ui.append(frame)

    # Test 1: Start benchmark, call step() multiple times, check frame count
    print("Test 1: Benchmark with step() calls")
    mcrfpy.start_benchmark()

    # Make 10 step() calls
    for i in range(10):
        mcrfpy.step(0.016)  # ~60fps frame time

    filename = mcrfpy.end_benchmark()
    print(f"  Benchmark file: {filename}")

    # Check the benchmark file
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            data = json.load(f)

        frame_count = data['benchmark']['total_frames']
        print(f"  Total frames recorded: {frame_count}")

        if frame_count == 0:
            print("  NOTE: step() does NOT produce benchmark frames")
            print("  (Benchmark system is tied to main game loop)")
        else:
            print(f"  step() produced {frame_count} benchmark frames")

        # Clean up
        os.remove(filename)
    else:
        print("  ERROR: Benchmark file not created")
        return False
    print()

    # Test 2: Benchmark with screenshots
    print("Test 2: Benchmark with screenshot() calls")
    mcrfpy.start_benchmark()

    # Make 5 screenshot calls
    for i in range(5):
        automation.screenshot(f"/tmp/bench_test_{i}.png")

    filename = mcrfpy.end_benchmark()
    print(f"  Benchmark file: {filename}")

    if os.path.exists(filename):
        with open(filename, 'r') as f:
            data = json.load(f)

        frame_count = data['benchmark']['total_frames']
        print(f"  Total frames recorded: {frame_count}")

        if frame_count == 0:
            print("  NOTE: screenshot() does NOT produce benchmark frames")
        else:
            print(f"  screenshot() produced {frame_count} benchmark frames")

        # Clean up
        os.remove(filename)
        for i in range(5):
            if os.path.exists(f"/tmp/bench_test_{i}.png"):
                os.remove(f"/tmp/bench_test_{i}.png")
    print()

    # Test 3: Measure actual wall-clock time for headless operations
    print("Test 3: Wall-clock timing for headless operations")
    import time

    iterations = 10  # Keep low for test suite speed

    # Time step() calls
    start = time.perf_counter()
    for i in range(iterations):
        mcrfpy.step(0.016)
    step_time = time.perf_counter() - start
    print(f"  {iterations} step() calls: {step_time*1000:.2f}ms ({step_time*1000/iterations:.3f}ms each)")

    # Time screenshot calls
    start = time.perf_counter()
    for i in range(iterations):
        automation.screenshot(f"/tmp/speed_test.png")
    screenshot_time = time.perf_counter() - start
    print(f"  {iterations} screenshot() calls: {screenshot_time*1000:.2f}ms ({screenshot_time*1000/iterations:.3f}ms each)")

    # Time step + screenshot combined
    start = time.perf_counter()
    for i in range(iterations):
        mcrfpy.step(0.016)
        automation.screenshot(f"/tmp/speed_test.png")
    combined_time = time.perf_counter() - start
    print(f"  {iterations} step+screenshot cycles: {combined_time*1000:.2f}ms ({combined_time*1000/iterations:.3f}ms each)")

    # Clean up
    if os.path.exists("/tmp/speed_test.png"):
        os.remove("/tmp/speed_test.png")
    print()

    # Test 4: Throughput test with complex scene
    print("Test 4: Complex scene throughput")

    # Add more UI elements
    for i in range(50):
        f = mcrfpy.Frame(pos=(i * 10, i * 5), size=(50, 50))
        f.fill_color = mcrfpy.Color(i * 5, 100, 200)
        ui.append(f)

    iterations = 5  # Keep low for test suite speed
    start = time.perf_counter()
    for i in range(iterations):
        mcrfpy.step(0.016)
        automation.screenshot(f"/tmp/complex_test.png")
    complex_time = time.perf_counter() - start

    fps_equivalent = iterations / complex_time
    print(f"  {iterations} cycles with 51 UI elements: {complex_time*1000:.2f}ms")
    print(f"  Equivalent FPS: {fps_equivalent:.1f}")
    print(f"  Per-cycle time: {complex_time*1000/iterations:.3f}ms")

    # Clean up
    if os.path.exists("/tmp/complex_test.png"):
        os.remove("/tmp/complex_test.png")
    print()

    print("=== Headless Benchmark Tests Complete ===")
    return True

# Main execution
if __name__ == "__main__":
    try:
        if run_tests():
            print("\nPASS")
            sys.exit(0)
        else:
            print("\nFAIL")
            sys.exit(1)
    except Exception as e:
        print(f"\nFAIL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
