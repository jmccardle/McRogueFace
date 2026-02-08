"""Test screen_to_world y_plane parameter (issue #245)"""
import mcrfpy
import sys

errors = []

vp = mcrfpy.Viewport3D(pos=(0,0), size=(320,240))
vp.set_grid_size(16, 16)
# Position camera above the Y=0 plane
vp.camera_pos = (0, 5, 5)
vp.camera_target = (0, 0, 0)

# Test 1: Default y_plane=0 works
r1 = vp.screen_to_world(160, 120)
if r1 is None:
    errors.append("screen_to_world with default y_plane returned None")

# Test 2: Explicit y_plane=0 matches default
r2 = vp.screen_to_world(160, 120, y_plane=0.0)
if r2 is None:
    errors.append("screen_to_world with y_plane=0 returned None")
elif r1 is not None:
    for i in range(3):
        if abs(r1[i] - r2[i]) > 0.001:
            errors.append(f"Default and explicit y_plane=0 differ: {r1} vs {r2}")
            break

# Test 3: Different y_plane gives different result
r3 = vp.screen_to_world(160, 120, y_plane=2.0)
if r3 is None:
    errors.append("screen_to_world with y_plane=2 returned None")
elif r1 is not None:
    if r1 == r3:
        errors.append("y_plane=0 and y_plane=2 should give different results")

# Test 4: y component matches y_plane
if r3 is not None:
    if abs(r3[1] - 2.0) > 0.001:
        errors.append(f"y component should be 2.0 for y_plane=2.0, got {r3[1]}")

# Test 5: Positional argument also works
r4 = vp.screen_to_world(160, 120, 3.0)
if r4 is None:
    errors.append("Positional y_plane argument returned None")
elif abs(r4[1] - 3.0) > 0.001:
    errors.append(f"y component should be 3.0, got {r4[1]}")

if errors:
    for err in errors:
        print(f"FAIL: {err}", file=sys.stderr)
    sys.exit(1)
else:
    print("PASS: screen_to_world y_plane (issue #245)", file=sys.stderr)
    sys.exit(0)
