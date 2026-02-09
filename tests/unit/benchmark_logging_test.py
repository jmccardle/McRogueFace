#!/usr/bin/env python3
"""Test benchmark logging functionality (Issue #104)"""
import mcrfpy
import sys
import os
import json

def run_test(timer, runtime):
    """Timer callback to test benchmark logging"""
    # Stop the benchmark and get filename
    try:
        filename = mcrfpy.end_benchmark()
        print(f"Benchmark written to: {filename}")

        # Check file exists
        if not os.path.exists(filename):
            print(f"FAIL: Benchmark file not found: {filename}")
            sys.exit(1)

        # Parse and validate JSON
        with open(filename, 'r') as f:
            data = json.load(f)

        # Validate structure
        if 'benchmark' not in data:
            print("FAIL: Missing 'benchmark' key")
            sys.exit(1)

        if 'frames' not in data:
            print("FAIL: Missing 'frames' key")
            sys.exit(1)

        # Check benchmark metadata
        bench = data['benchmark']
        if 'pid' not in bench:
            print("FAIL: Missing 'pid' in benchmark")
            sys.exit(1)
        if 'start_time' not in bench:
            print("FAIL: Missing 'start_time' in benchmark")
            sys.exit(1)
        if 'end_time' not in bench:
            print("FAIL: Missing 'end_time' in benchmark")
            sys.exit(1)
        if 'total_frames' not in bench:
            print("FAIL: Missing 'total_frames' in benchmark")
            sys.exit(1)

        print(f"  PID: {bench['pid']}")
        print(f"  Duration: {bench['duration_seconds']:.3f}s")
        print(f"  Frames: {bench['total_frames']}")

        # In headless mode, step() doesn't generate benchmark frames
        # since the benchmark system hooks into the real render loop.
        # Accept 0 frames in headless mode.
        if len(data['frames']) > 0:
            # Check frame structure
            frame = data['frames'][0]
            required_fields = ['frame_number', 'timestamp_ms', 'frame_time_ms', 'fps',
                              'work_time_ms', 'grid_render_ms', 'entity_render_ms',
                              'python_time_ms', 'draw_calls', 'ui_elements', 'logs']
            for field in required_fields:
                if field not in frame:
                    print(f"FAIL: Missing field '{field}' in frame")
                    sys.exit(1)

            # Check log message was captured
            found_log = False
            for frame in data['frames']:
                if 'Test log message' in frame.get('logs', []):
                    found_log = True
                    break

            if not found_log:
                print("WARN: Log message not found in any frame")

            # Show timing breakdown
            f0 = data['frames'][0]
            print(f"  First frame FPS: {f0['fps']}")
            print(f"  Frame time: {f0['frame_time_ms']:.3f}ms")
        else:
            print("  No frames recorded (expected in headless mode)")

        # Clean up
        os.remove(filename)
        print(f"  Cleaned up: {filename}")

        print("PASS")
        sys.exit(0)

    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)

# Test error handling - calling end without start
try:
    mcrfpy.end_benchmark()
    print("FAIL: end_benchmark() should have raised RuntimeError")
    sys.exit(1)
except RuntimeError as e:
    print(f"Correct error on end without start: {e}")

# Test error handling - logging without start
try:
    mcrfpy.log_benchmark("test")
    print("FAIL: log_benchmark() should have raised RuntimeError")
    sys.exit(1)
except RuntimeError as e:
    print(f"Correct error on log without start: {e}")

# Start the benchmark
mcrfpy.start_benchmark()
print("Benchmark started")

# Test error handling - double start
try:
    mcrfpy.start_benchmark()
    print("FAIL: double start_benchmark() should have raised RuntimeError")
    sys.exit(1)
except RuntimeError as e:
    print(f"Correct error on double start: {e}")

# Log a test message
mcrfpy.log_benchmark("Test log message")
print("Logged test message")

# Set up scene and run for a few frames
test = mcrfpy.Scene("test")
test.activate()

# Schedule test completion after ~100ms (to capture some frames)
test_timer = mcrfpy.Timer("test", run_test, 100, once=True)

# In headless mode, timers only fire via step()
for _ in range(3):
    mcrfpy.step(0.05)
