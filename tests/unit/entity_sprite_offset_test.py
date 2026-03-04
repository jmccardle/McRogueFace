"""Test Entity sprite_offset property (#233 sub-feature 1)"""
import mcrfpy
import sys

passed = 0
failed = 0

def test(name, condition):
    global passed, failed
    if condition:
        passed += 1
    else:
        failed += 1
        print(f"FAIL: {name}")

# Setup: create a grid and texture for entity tests
scene = mcrfpy.Scene("test")
mcrfpy.current_scene = scene
tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
grid = mcrfpy.Grid(grid_size=(10, 10), texture=tex, pos=(0, 0), size=(160, 160))
scene.children.append(grid)

# Test 1: Default sprite_offset is (0, 0)
e = mcrfpy.Entity(grid_pos=(3, 3), texture=tex, sprite_index=0, grid=grid)
test("default sprite_offset is (0,0)",
     e.sprite_offset.x == 0.0 and e.sprite_offset.y == 0.0)

# Test 2: Set sprite_offset via tuple
e.sprite_offset = (-8, -16)
test("set sprite_offset via tuple",
     e.sprite_offset.x == -8.0 and e.sprite_offset.y == -16.0)

# Test 3: Read individual components
test("sprite_offset_x component", e.sprite_offset_x == -8.0)
test("sprite_offset_y component", e.sprite_offset_y == -16.0)

# Test 4: Set individual components
e.sprite_offset_x = 4.5
e.sprite_offset_y = -3.0
test("set sprite_offset_x", e.sprite_offset_x == 4.5)
test("set sprite_offset_y", e.sprite_offset_y == -3.0)
test("individual set reflects in vector",
     e.sprite_offset.x == 4.5 and e.sprite_offset.y == -3.0)

# Test 5: Constructor kwarg
e2 = mcrfpy.Entity(grid_pos=(1, 1), texture=tex, sprite_index=0,
                    grid=grid, sprite_offset=(-8, -16))
test("constructor kwarg sprite_offset",
     e2.sprite_offset.x == -8.0 and e2.sprite_offset.y == -16.0)

# Test 6: Constructor default when not specified
e3 = mcrfpy.Entity(grid_pos=(2, 2), texture=tex, sprite_index=0, grid=grid)
test("constructor default (0,0)",
     e3.sprite_offset.x == 0.0 and e3.sprite_offset.y == 0.0)

# Test 7: Animation support - verify property is animatable
try:
    e.animate("sprite_offset_x", -8.0, 0.5, "linear")
    test("animate sprite_offset_x accepted", True)
except Exception as ex:
    test(f"animate sprite_offset_x accepted: {ex}", False)

try:
    e.animate("sprite_offset_y", -16.0, 0.5, "linear")
    test("animate sprite_offset_y accepted", True)
except Exception as ex:
    test(f"animate sprite_offset_y accepted: {ex}", False)

# Test 8: Animation actually changes value (step the game loop)
e.sprite_offset_x = 0.0
e.animate("sprite_offset_x", 10.0, 0.1, "linear")
# Step enough to complete the animation
for _ in range(5):
    mcrfpy.step(0.05)
test("animation changes sprite_offset_x", abs(e.sprite_offset_x - 10.0) < 0.1)

# Test 9: Type errors
try:
    e.sprite_offset_x = "bad"
    test("type error on string", False)
except TypeError:
    test("type error on string", True)

# Summary
print(f"\n{passed} passed, {failed} failed out of {passed + failed} tests")
if failed:
    print("FAIL")
    sys.exit(1)
else:
    print("PASS")
    sys.exit(0)
