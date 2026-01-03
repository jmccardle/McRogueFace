#!/usr/bin/env python3
"""Test for --continue-after-exceptions behavior (Issue #133)

This test verifies that:
1. By default, unhandled exceptions in timer callbacks cause immediate exit with code 1
2. With --continue-after-exceptions, exceptions are logged but execution continues
"""

import mcrfpy
import sys

def timer_that_raises(runtime):
    """A timer callback that raises an exception"""
    raise ValueError("Intentional test exception")

# Create a test scene
test = mcrfpy.Scene("test")
test.activate()

# Schedule the timer - it will fire after 50ms
mcrfpy.setTimer("raise_exception", timer_that_raises, 50)

# This test expects:
# - Default behavior: exit with code 1 after first exception
# - With --continue-after-exceptions: continue running (would need timeout or explicit exit)
#
# The test runner should:
# 1. Run without --continue-after-exceptions and expect exit code 1
# 2. Run with --continue-after-exceptions and expect it to not exit immediately

print("Test initialized - timer will raise exception in 50ms")
