"""Test composite sprite_grid for multi-tile entities (#237)"""
import mcrfpy
import sys

def main():
    errors = []

    # Setup: create scene with grid
    scene = mcrfpy.Scene("test_sprite_grid")
    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(20, 20), texture=tex, pos=(0, 0), size=(320, 320))
    scene.children.append(grid)

    # Test 1: sprite_grid defaults to None
    e = mcrfpy.Entity(grid_pos=(5, 5), texture=tex, sprite_index=0)
    grid.entities.append(e)
    ent = grid.entities[0]
    if ent.sprite_grid is not None:
        errors.append(f"Test 1 FAIL: default sprite_grid should be None, got {ent.sprite_grid}")
    else:
        print("Test 1 PASS: sprite_grid defaults to None")

    # Test 2: set sprite_grid as nested list
    ent.tile_width = 3
    ent.tile_height = 2
    ent.sprite_grid = [
        [10, 11, 12],
        [20, 21, 22],
    ]
    sg = ent.sprite_grid
    if sg != [[10, 11, 12], [20, 21, 22]]:
        errors.append(f"Test 2 FAIL: expected nested list, got {sg}")
    else:
        print("Test 2 PASS: set/get nested sprite_grid works")

    # Test 3: set sprite_grid as flat list
    ent.sprite_grid = [1, 2, 3, 4, 5, 6]
    sg = ent.sprite_grid
    if sg != [[1, 2, 3], [4, 5, 6]]:
        errors.append(f"Test 3 FAIL: flat list should become nested, got {sg}")
    else:
        print("Test 3 PASS: flat list sprite_grid works")

    # Test 4: -1 means empty tile
    ent.sprite_grid = [
        [10, -1, 12],
        [-1, 21, -1],
    ]
    sg = ent.sprite_grid
    if sg != [[10, -1, 12], [-1, 21, -1]]:
        errors.append(f"Test 4 FAIL: -1 values not preserved, got {sg}")
    else:
        print("Test 4 PASS: -1 empty tiles preserved")

    # Test 5: set to None clears sprite_grid
    ent.sprite_grid = None
    if ent.sprite_grid is not None:
        errors.append(f"Test 5 FAIL: setting None should clear sprite_grid")
    else:
        print("Test 5 PASS: setting None clears sprite_grid")

    # Test 6: wrong size raises ValueError
    ent.tile_width = 2
    ent.tile_height = 2
    try:
        ent.sprite_grid = [1, 2, 3]  # 3 items, need 4
        errors.append("Test 6 FAIL: should raise ValueError for wrong flat size")
    except ValueError:
        print("Test 6 PASS: wrong flat size raises ValueError")

    # Test 7: wrong row count raises ValueError
    try:
        ent.sprite_grid = [[1, 2], [3, 4], [5, 6]]  # 3 rows, need 2
        errors.append("Test 7 FAIL: should raise ValueError for wrong row count")
    except ValueError:
        print("Test 7 PASS: wrong row count raises ValueError")

    # Test 8: wrong column count raises ValueError
    try:
        ent.sprite_grid = [[1, 2, 3], [4, 5, 6]]  # 3 cols, need 2
        errors.append("Test 8 FAIL: should raise ValueError for wrong column count")
    except ValueError:
        print("Test 8 PASS: wrong column count raises ValueError")

    # Test 9: sprite_grid with 1x1 entity
    ent.tile_width = 1
    ent.tile_height = 1
    ent.sprite_grid = [[5]]
    sg = ent.sprite_grid
    if sg != [[5]]:
        errors.append(f"Test 9 FAIL: 1x1 sprite_grid should work, got {sg}")
    else:
        print("Test 9 PASS: 1x1 sprite_grid works")

    # Test 10: tuple input works too
    ent.tile_width = 2
    ent.tile_height = 1
    ent.sprite_grid = (10, 11)
    sg = ent.sprite_grid
    if sg != [[10, 11]]:
        errors.append(f"Test 10 FAIL: tuple input should work, got {sg}")
    else:
        print("Test 10 PASS: tuple input works")

    # Summary
    if errors:
        print(f"\nFAILED: {len(errors)} errors:")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)
    else:
        print(f"\nAll tests passed!")
        print("PASS")
        sys.exit(0)

if __name__ == "__main__":
    main()
