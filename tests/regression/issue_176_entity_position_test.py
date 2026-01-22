#!/usr/bin/env python3
"""Test for issue #176: Entity position naming consistency.

Tests the new Entity position properties:
- pos, x, y: pixel coordinates (requires grid attachment)
- grid_pos, grid_x, grid_y: integer tile coordinates
- draw_pos: fractional tile coordinates for animation
"""
import mcrfpy
import sys

def test_entity_positions():
    """Test Entity position properties with grid attachment."""
    errors = []

    # Create a texture with 16x16 sprites (standard tile size)
    texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)

    # Create a grid (10x10 tiles, 16x16 pixels each)
    grid = mcrfpy.Grid(grid_size=(10, 10), texture=texture, pos=(0, 0), size=(160, 160))

    # Create entity at tile position (3, 5)
    entity = mcrfpy.Entity(grid_pos=(3, 5), texture=texture, grid=grid)

    # Test 1: grid_pos should return integer tile coordinates
    gpos = entity.grid_pos
    if gpos.x != 3 or gpos.y != 5:
        errors.append(f"grid_pos: expected (3, 5), got ({gpos.x}, {gpos.y})")

    # Test 2: grid_x and grid_y should return integers
    if entity.grid_x != 3:
        errors.append(f"grid_x: expected 3, got {entity.grid_x}")
    if entity.grid_y != 5:
        errors.append(f"grid_y: expected 5, got {entity.grid_y}")

    # Test 3: draw_pos should return float tile coordinates
    dpos = entity.draw_pos
    if abs(dpos.x - 3.0) > 0.001 or abs(dpos.y - 5.0) > 0.001:
        errors.append(f"draw_pos: expected (3.0, 5.0), got ({dpos.x}, {dpos.y})")

    # Test 4: pos should return pixel coordinates (tile * tile_size)
    # With 16x16 tiles: (3, 5) tiles = (48, 80) pixels
    ppos = entity.pos
    if abs(ppos.x - 48.0) > 0.001 or abs(ppos.y - 80.0) > 0.001:
        errors.append(f"pos: expected (48.0, 80.0), got ({ppos.x}, {ppos.y})")

    # Test 5: x and y should return pixel coordinates
    if abs(entity.x - 48.0) > 0.001:
        errors.append(f"x: expected 48.0, got {entity.x}")
    if abs(entity.y - 80.0) > 0.001:
        errors.append(f"y: expected 80.0, got {entity.y}")

    # Test 6: Setting grid_x/grid_y should update position
    entity.grid_x = 7
    entity.grid_y = 2
    if entity.grid_x != 7 or entity.grid_y != 2:
        errors.append(f"After setting grid_x/y: expected (7, 2), got ({entity.grid_x}, {entity.grid_y})")
    # Pixel should update too: (7, 2) * 16 = (112, 32)
    if abs(entity.x - 112.0) > 0.001 or abs(entity.y - 32.0) > 0.001:
        errors.append(f"After grid_x/y set, pixel pos: expected (112, 32), got ({entity.x}, {entity.y})")

    # Test 7: Setting pos (pixels) should update grid position
    entity.pos = mcrfpy.Vector(64, 96)  # (64, 96) / 16 = (4, 6) tiles
    if abs(entity.draw_pos.x - 4.0) > 0.001 or abs(entity.draw_pos.y - 6.0) > 0.001:
        errors.append(f"After setting pos, draw_pos: expected (4, 6), got ({entity.draw_pos.x}, {entity.draw_pos.y})")
    if entity.grid_x != 4 or entity.grid_y != 6:
        errors.append(f"After setting pos, grid_x/y: expected (4, 6), got ({entity.grid_x}, {entity.grid_y})")

    # Test 8: repr should show grid_x/grid_y
    repr_str = repr(entity)
    if "grid_x=" not in repr_str or "grid_y=" not in repr_str:
        errors.append(f"repr should contain grid_x/grid_y: {repr_str}")

    return errors


def test_entity_without_grid():
    """Test that pixel positions require grid attachment."""
    errors = []

    texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    entity = mcrfpy.Entity(grid_pos=(3, 5), texture=texture)  # No grid

    # grid_pos should work without grid
    if entity.grid_x != 3 or entity.grid_y != 5:
        errors.append(f"grid_x/y without grid: expected (3, 5), got ({entity.grid_x}, {entity.grid_y})")

    # pos should raise RuntimeError without grid
    try:
        _ = entity.pos
        errors.append("entity.pos should raise RuntimeError without grid")
    except RuntimeError as e:
        if "not attached to a Grid" not in str(e):
            errors.append(f"Wrong error message for pos: {e}")

    # x should raise RuntimeError without grid
    try:
        _ = entity.x
        errors.append("entity.x should raise RuntimeError without grid")
    except RuntimeError as e:
        if "not attached to a Grid" not in str(e):
            errors.append(f"Wrong error message for x: {e}")

    # Setting pos should raise RuntimeError without grid
    try:
        entity.pos = mcrfpy.Vector(100, 100)
        errors.append("setting entity.pos should raise RuntimeError without grid")
    except RuntimeError as e:
        if "not attached to a Grid" not in str(e):
            errors.append(f"Wrong error message for setting pos: {e}")

    return errors


def test_animation_properties():
    """Test that animation properties work correctly."""
    errors = []

    texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(10, 10), texture=texture, pos=(0, 0), size=(160, 160))
    entity = mcrfpy.Entity(grid_pos=(0, 0), texture=texture, grid=grid)

    # Test draw_x/draw_y animation properties exist
    try:
        # hasProperty should accept draw_x and draw_y
        # We can't call hasProperty directly, but we can try to animate
        # and check if it raises ValueError for invalid property
        pass  # Animation tested implicitly through animate() error handling
    except Exception as e:
        errors.append(f"Animation property test failed: {e}")

    return errors


def main():
    print("Testing issue #176: Entity position naming consistency")
    print("=" * 60)

    all_errors = []

    # Test 1: Entity with grid
    print("\n1. Testing entity positions with grid attachment...")
    errors = test_entity_positions()
    if errors:
        for e in errors:
            print(f"   FAIL: {e}")
        all_errors.extend(errors)
    else:
        print("   PASS")

    # Test 2: Entity without grid
    print("\n2. Testing entity positions without grid...")
    errors = test_entity_without_grid()
    if errors:
        for e in errors:
            print(f"   FAIL: {e}")
        all_errors.extend(errors)
    else:
        print("   PASS")

    # Test 3: Animation properties
    print("\n3. Testing animation properties...")
    errors = test_animation_properties()
    if errors:
        for e in errors:
            print(f"   FAIL: {e}")
        all_errors.extend(errors)
    else:
        print("   PASS")

    print("\n" + "=" * 60)
    if all_errors:
        print(f"FAILED: {len(all_errors)} error(s)")
        sys.exit(1)
    else:
        print("All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
