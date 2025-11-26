#!/usr/bin/env python3
import mcrfpy
import sys

try:
    frame = mcrfpy.Frame(name="test_frame")
    print(f"Frame name: {frame.name}")
    sys.exit(0)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)