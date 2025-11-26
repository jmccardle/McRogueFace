#!/usr/bin/env python3
import mcrfpy
import sys

# Test just the specific case that's failing
try:
    f = mcrfpy.Frame(x=15, y=25, w=150, h=250, outline=2.0, visible=True, opacity=0.5)
    print(f"Success: x={f.x}, y={f.y}, w={f.w}, h={f.h}")
    sys.exit(0)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    
    # Try to debug which argument is problematic
    print("\nTrying individual arguments:")
    try:
        f1 = mcrfpy.Frame(x=15)
        print("x=15 works")
    except Exception as e:
        print(f"x=15 failed: {e}")
        
    try:
        f2 = mcrfpy.Frame(visible=True)
        print("visible=True works")
    except Exception as e:
        print(f"visible=True failed: {e}")
        
    sys.exit(1)