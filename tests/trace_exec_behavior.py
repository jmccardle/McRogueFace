#!/usr/bin/env python3
"""Trace execution behavior to understand the >>> prompt"""
import mcrfpy
import sys
import traceback

print("=== Tracing Execution ===")
print(f"Python version: {sys.version}")
print(f"sys.argv: {sys.argv}")
print(f"__name__: {__name__}")

# Check if we're in interactive mode
print(f"sys.flags.interactive: {sys.flags.interactive}")
print(f"sys.flags.inspect: {sys.flags.inspect}")

# Check sys.ps1 (interactive prompt)
if hasattr(sys, 'ps1'):
    print(f"sys.ps1 exists: '{sys.ps1}'")
else:
    print("sys.ps1 not set (not in interactive mode)")

# Create a simple scene
mcrfpy.createScene("trace_test")
mcrfpy.setScene("trace_test")
print(f"Current scene: {mcrfpy.currentScene()}")

# Set a timer that should fire
def timer_test():
    print("\n!!! Timer fired successfully !!!")
    mcrfpy.delTimer("trace_timer")
    # Try to exit
    print("Attempting to exit...")
    mcrfpy.exit()

print("Setting timer...")
mcrfpy.setTimer("trace_timer", timer_test, 500)

print("\n=== Script execution complete ===")
print("If you see >>> after this, Python entered interactive mode")
print("The game loop should start now...")

# Try to ensure we don't enter interactive mode
if hasattr(sys, 'ps1'):
    del sys.ps1
    
# Explicitly NOT calling sys.exit() to let the game loop run