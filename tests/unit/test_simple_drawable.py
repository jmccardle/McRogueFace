#!/usr/bin/env python3
"""Simple test to isolate drawable issue"""
import mcrfpy
import sys

def simple_test(timer, runtime):
    timer.stop()
    
    try:
        # Test basic functionality
        frame = mcrfpy.Frame(pos=(10, 10), size=(100, 100))
        print(f"Frame created: visible={frame.visible}, opacity={frame.opacity}")
        
        bounds = frame.get_bounds()
        print(f"Bounds: {bounds}")
        
        frame.move(5, 5)
        print("Move completed")
        
        frame.resize(150, 150)
        print("Resize completed")
        
        print("PASS - No crash!")
    except Exception as e:
        print(f"ERROR: {e}")
    
    sys.exit(0)

test = mcrfpy.Scene("test")
simple_test_timer = mcrfpy.Timer("simple_test", simple_test, 100, once=True)