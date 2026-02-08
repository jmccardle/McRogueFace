"""Test Entity3D.animate() (issue #242)"""
import mcrfpy
import sys

errors = []

vp = mcrfpy.Viewport3D(pos=(0,0), size=(100,100))
vp.set_grid_size(16, 16)

# Test 1: Basic x animation
e = mcrfpy.Entity3D(pos=(0,0), scale=1.0)
vp.entities.append(e)
start_x = e.world_pos[0]
anim = e.animate('x', 10.0, 1.0, 'linear')
if anim is None:
    errors.append("animate() should return Animation object")
for _ in range(5):
    mcrfpy.step(0.25)
if abs(e.world_pos[0] - 10.0) > 0.5:
    errors.append(f"x animation: expected ~10.0, got {e.world_pos[0]}")

# Test 2: Scale animation
e2 = mcrfpy.Entity3D(pos=(0,0), scale=1.0)
vp.entities.append(e2)
e2.animate('scale', 5.0, 0.5, 'linear')
for _ in range(3):
    mcrfpy.step(0.25)
if abs(e2.scale - 5.0) > 0.5:
    errors.append(f"scale animation: expected ~5.0, got {e2.scale}")

# Test 3: Rotation animation
e3 = mcrfpy.Entity3D(pos=(0,0), scale=1.0)
vp.entities.append(e3)
e3.animate('rotation', 90.0, 0.5, 'easeInOut')
for _ in range(3):
    mcrfpy.step(0.25)
if abs(e3.rotation - 90.0) > 0.5:
    errors.append(f"rotation animation: expected ~90.0, got {e3.rotation}")

# Test 4: Delta animation
e4 = mcrfpy.Entity3D(pos=(3,3), scale=1.0)
vp.entities.append(e4)
start_x = e4.world_pos[0]
e4.animate('x', 2.0, 0.5, 'linear', delta=True)
for _ in range(3):
    mcrfpy.step(0.25)
expected = start_x + 2.0
if abs(e4.world_pos[0] - expected) > 0.5:
    errors.append(f"delta animation: expected ~{expected}, got {e4.world_pos[0]}")

# Test 5: Invalid property raises ValueError
try:
    e.animate('nonexistent', 1.0, 1.0, 'linear')
    errors.append("Invalid property should raise ValueError")
except ValueError:
    pass

# Test 6: Invalid target type raises TypeError
try:
    e.animate('x', "not_a_number", 1.0, 'linear')
    errors.append("String target should raise TypeError")
except TypeError:
    pass

# Test 7: Callback
callback_called = [False]
def on_complete(target, prop, value):
    callback_called[0] = True

e5 = mcrfpy.Entity3D(pos=(0,0), scale=1.0)
vp.entities.append(e5)
e5.animate('x', 5.0, 0.25, 'linear', callback=on_complete)
for _ in range(3):
    mcrfpy.step(0.15)
if not callback_called[0]:
    errors.append("Animation callback was not called")

# Test 8: Easing enum
e6 = mcrfpy.Entity3D(pos=(0,0), scale=1.0)
vp.entities.append(e6)
try:
    e6.animate('x', 5.0, 1.0, mcrfpy.Easing.EASE_IN_OUT)
except Exception as ex:
    errors.append(f"Easing enum should work: {ex}")
for _ in range(5):
    mcrfpy.step(0.25)

if errors:
    for err in errors:
        print(f"FAIL: {err}", file=sys.stderr)
    sys.exit(1)
else:
    print("PASS: Entity3D.animate() (issue #242)", file=sys.stderr)
    sys.exit(0)
