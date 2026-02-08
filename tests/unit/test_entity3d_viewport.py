"""Test Entity3D.viewport property (issue #244)"""
import mcrfpy
import sys

errors = []

# Test 1: Detached entity returns None
e = mcrfpy.Entity3D(pos=(0,0), scale=1.0)
if e.viewport is not None:
    errors.append("Detached entity viewport should be None")

# Test 2: Attached entity returns Viewport3D
vp = mcrfpy.Viewport3D(pos=(0,0), size=(100,100))
vp.set_grid_size(16, 16)
e2 = mcrfpy.Entity3D(pos=(5,5), scale=1.0)
vp.entities.append(e2)
v = e2.viewport
if v is None:
    errors.append("Attached entity viewport should not be None")
elif type(v).__name__ != 'Viewport3D':
    errors.append(f"Expected Viewport3D, got {type(v).__name__}")

# Test 3: Viewport properties are accessible
if v is not None:
    try:
        _ = v.w
        _ = v.h
    except Exception as ex:
        errors.append(f"Viewport properties not accessible: {ex}")

# Test 4: Multiple entities share same viewport
e3 = mcrfpy.Entity3D(pos=(3,3), scale=1.0)
vp.entities.append(e3)
v2 = e3.viewport
if v2 is None:
    errors.append("Second entity viewport should not be None")

if errors:
    for err in errors:
        print(f"FAIL: {err}", file=sys.stderr)
    sys.exit(1)
else:
    print("PASS: Entity3D.viewport (issue #244)", file=sys.stderr)
    sys.exit(0)
