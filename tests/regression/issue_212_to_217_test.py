"""Regression tests for issues #212, #213, #214, #216, #217"""
import mcrfpy
import sys

passed = 0
failed = 0

def test(name, condition, expected=True):
    global passed, failed
    if condition == expected:
        print(f"  PASS: {name}")
        passed += 1
    else:
        print(f"  FAIL: {name}")
        failed += 1

print("Testing #212: GRID_MAX validation")
# Grid dimensions cannot exceed 8192
try:
    g = mcrfpy.Grid(grid_size=(10000, 10000))
    test("Grid rejects oversized dimensions", False)  # Should have raised
except ValueError as e:
    test("Grid rejects oversized dimensions", "8192" in str(e))

# ColorLayer dimensions cannot exceed 8192
try:
    cl = mcrfpy.ColorLayer(z_index=0, grid_size=(10000, 100))
    test("ColorLayer rejects oversized dimensions", False)
except ValueError as e:
    test("ColorLayer rejects oversized dimensions", "8192" in str(e))

# TileLayer dimensions cannot exceed 8192
try:
    tl = mcrfpy.TileLayer(z_index=0, grid_size=(100, 10000))
    test("TileLayer rejects oversized dimensions", False)
except ValueError as e:
    test("TileLayer rejects oversized dimensions", "8192" in str(e))

# Valid dimensions should work
try:
    g = mcrfpy.Grid(grid_size=(100, 100))
    test("Grid accepts valid dimensions", True)
except:
    test("Grid accepts valid dimensions", False)


print("\nTesting #213: Color component validation (0-255)")
# ColorLayer.fill with invalid color
try:
    cl = mcrfpy.ColorLayer(z_index=0, grid_size=(10, 10))
    cl.fill((300, 0, 0))
    test("ColorLayer.fill rejects color > 255", False)
except ValueError as e:
    test("ColorLayer.fill rejects color > 255", "0-255" in str(e))

try:
    cl = mcrfpy.ColorLayer(z_index=0, grid_size=(10, 10))
    cl.fill((-10, 0, 0))
    test("ColorLayer.fill rejects color < 0", False)
except ValueError as e:
    test("ColorLayer.fill rejects color < 0", "0-255" in str(e))

# Valid color should work
try:
    cl = mcrfpy.ColorLayer(z_index=0, grid_size=(10, 10))
    cl.fill((128, 64, 200, 255))
    test("ColorLayer.fill accepts valid color", True)
except:
    test("ColorLayer.fill accepts valid color", False)


print("\nTesting #216: entities_in_radius uses pos tuple/Vector")
try:
    g = mcrfpy.Grid(grid_size=(50, 50), pos=(0, 0), size=(500, 500))
    e = mcrfpy.Entity()
    e.draw_pos = (10, 10)
    g.entities.append(e)

    # New API: pos as tuple + radius
    result = g.entities_in_radius((10, 10), 5.0)
    test("entities_in_radius accepts (pos_tuple, radius)", len(result) == 1)

    # Also works with Vector
    result = g.entities_in_radius(mcrfpy.Vector(10, 10), 5.0)
    test("entities_in_radius accepts (Vector, radius)", len(result) == 1)

    # Old API should fail
    try:
        result = g.entities_in_radius(10, 10, 5.0)
        test("entities_in_radius rejects old (x, y, radius) API", False)
    except TypeError:
        test("entities_in_radius rejects old (x, y, radius) API", True)
except Exception as e:
    print(f"  ERROR in #216 tests: {e}")
    failed += 3


print("\nTesting #217: Entity __repr__ shows actual position")
try:
    e = mcrfpy.Entity()
    e.draw_pos = (5.5, 3.25)
    repr_str = repr(e)
    test("Entity repr shows draw_pos", "draw_pos=" in repr_str)
    test("Entity repr shows actual float x", "5.5" in repr_str)
    test("Entity repr shows actual float y", "3.25" in repr_str)

    # draw_pos should be accessible without grid
    pos = e.draw_pos
    test("draw_pos accessible without grid", abs(pos.x - 5.5) < 0.01)
except Exception as e:
    print(f"  ERROR in #217 tests: {e}")
    failed += 4


print(f"\n{'='*50}")
print(f"Results: {passed} passed, {failed} failed")

if failed > 0:
    sys.exit(1)
else:
    print("All tests passed!")
    sys.exit(0)
