#!/usr/bin/env python3
"""Test for UICollection.find() and EntityCollection.find() methods.

Tests issue #40 (search and replace by name) and #41 (.find on collections).
"""

import mcrfpy
import sys

def test_uicollection_find():
    """Test UICollection.find() with exact and wildcard matches."""
    print("Testing UICollection.find()...")

    # Create a scene with named elements
    mcrfpy.createScene("test_find")
    ui = mcrfpy.sceneUI("test_find")

    # Create frames with names
    frame1 = mcrfpy.Frame(pos=(0, 0), size=(100, 100))
    frame1.name = "main_frame"
    ui.append(frame1)

    frame2 = mcrfpy.Frame(pos=(100, 0), size=(100, 100))
    frame2.name = "sidebar_frame"
    ui.append(frame2)

    frame3 = mcrfpy.Frame(pos=(200, 0), size=(100, 100))
    frame3.name = "player_status"
    ui.append(frame3)

    caption1 = mcrfpy.Caption(text="Hello", pos=(0, 200))
    caption1.name = "player_name"
    ui.append(caption1)

    # Create an unnamed element
    unnamed = mcrfpy.Caption(text="Unnamed", pos=(0, 250))
    ui.append(unnamed)

    # Test exact match - found
    result = ui.find("main_frame")
    assert result is not None, "Exact match should find element"
    assert result.name == "main_frame", f"Found wrong element: {result.name}"
    print("  [PASS] Exact match found")

    # Test exact match - not found
    result = ui.find("nonexistent")
    assert result is None, "Should return None when not found"
    print("  [PASS] Not found returns None")

    # Test prefix wildcard (starts with)
    results = ui.find("player*")
    assert isinstance(results, list), "Wildcard should return list"
    assert len(results) == 2, f"Expected 2 matches, got {len(results)}"
    names = [r.name for r in results]
    assert "player_status" in names, "player_status should match player*"
    assert "player_name" in names, "player_name should match player*"
    print("  [PASS] Prefix wildcard works")

    # Test suffix wildcard (ends with)
    results = ui.find("*_frame")
    assert isinstance(results, list), "Wildcard should return list"
    assert len(results) == 2, f"Expected 2 matches, got {len(results)}"
    names = [r.name for r in results]
    assert "main_frame" in names
    assert "sidebar_frame" in names
    print("  [PASS] Suffix wildcard works")

    # Test contains wildcard
    results = ui.find("*bar*")
    assert isinstance(results, list), "Wildcard should return list"
    assert len(results) == 1, f"Expected 1 match, got {len(results)}"
    assert results[0].name == "sidebar_frame"
    print("  [PASS] Contains wildcard works")

    # Test match all
    results = ui.find("*")
    # Should match all named elements (4 named + 1 unnamed with empty name)
    assert isinstance(results, list), "Match all should return list"
    assert len(results) == 5, f"Expected 5 matches, got {len(results)}"
    print("  [PASS] Match all wildcard works")

    # Test empty pattern matches elements with empty names (unnamed elements)
    result = ui.find("")
    # The unnamed caption has an empty name, so exact match should find it
    assert result is not None, "Empty name exact match should find the unnamed element"
    print("  [PASS] Empty pattern finds unnamed elements")

    print("UICollection.find() tests passed!")
    return True


def test_entitycollection_find():
    """Test EntityCollection.find() with exact and wildcard matches."""
    print("\nTesting EntityCollection.find()...")

    # Create a grid with entities
    mcrfpy.createScene("test_entity_find")
    ui = mcrfpy.sceneUI("test_entity_find")

    grid = mcrfpy.Grid(grid_size=(10, 10), pos=(0, 0), size=(400, 400))
    ui.append(grid)

    # Add named entities
    player = mcrfpy.Entity(grid_pos=(1, 1))
    player.name = "player"
    grid.entities.append(player)

    enemy1 = mcrfpy.Entity(grid_pos=(2, 2))
    enemy1.name = "enemy_goblin"
    grid.entities.append(enemy1)

    enemy2 = mcrfpy.Entity(grid_pos=(3, 3))
    enemy2.name = "enemy_orc"
    grid.entities.append(enemy2)

    item = mcrfpy.Entity(grid_pos=(4, 4))
    item.name = "item_sword"
    grid.entities.append(item)

    # Test exact match
    result = grid.entities.find("player")
    assert result is not None, "Should find player"
    assert result.name == "player"
    print("  [PASS] Entity exact match works")

    # Test not found
    result = grid.entities.find("boss")
    assert result is None, "Should return None when not found"
    print("  [PASS] Entity not found returns None")

    # Test prefix wildcard
    results = grid.entities.find("enemy*")
    assert isinstance(results, list)
    assert len(results) == 2, f"Expected 2 enemies, got {len(results)}"
    print("  [PASS] Entity prefix wildcard works")

    # Test suffix wildcard
    results = grid.entities.find("*_orc")
    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0].name == "enemy_orc"
    print("  [PASS] Entity suffix wildcard works")

    print("EntityCollection.find() tests passed!")
    return True


def test_recursive_find():
    """Test recursive find in nested Frame children."""
    print("\nTesting recursive find in nested frames...")

    mcrfpy.createScene("test_recursive")
    ui = mcrfpy.sceneUI("test_recursive")

    # Create nested structure
    parent = mcrfpy.Frame(pos=(0, 0), size=(400, 400))
    parent.name = "parent"
    ui.append(parent)

    child = mcrfpy.Frame(pos=(10, 10), size=(200, 200))
    child.name = "child_frame"
    parent.children.append(child)

    grandchild = mcrfpy.Caption(text="Deep", pos=(5, 5))
    grandchild.name = "deep_caption"
    child.children.append(grandchild)

    # Non-recursive find should not find nested elements
    result = ui.find("deep_caption")
    assert result is None, "Non-recursive find should not find nested element"
    print("  [PASS] Non-recursive doesn't find nested elements")

    # Recursive find should find nested elements
    result = ui.find("deep_caption", recursive=True)
    assert result is not None, "Recursive find should find nested element"
    assert result.name == "deep_caption"
    print("  [PASS] Recursive find locates nested elements")

    # Recursive wildcard should find all matches
    results = ui.find("*_frame", recursive=True)
    assert isinstance(results, list)
    names = [r.name for r in results]
    assert "child_frame" in names, "Should find child_frame"
    print("  [PASS] Recursive wildcard finds nested matches")

    print("Recursive find tests passed!")
    return True


if __name__ == "__main__":
    try:
        all_passed = True
        all_passed &= test_uicollection_find()
        all_passed &= test_entitycollection_find()
        all_passed &= test_recursive_find()

        if all_passed:
            print("\n" + "="*50)
            print("All find() tests PASSED!")
            print("="*50)
            sys.exit(0)
        else:
            print("\nSome tests FAILED!")
            sys.exit(1)
    except Exception as e:
        print(f"\nTest failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
