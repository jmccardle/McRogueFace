#!/usr/bin/env python3
"""
Test #122: Parent-Child UI System
Test #102: Global Position Property
Test #116: Dirty Flag System (partial - propagation)
"""

import mcrfpy
import sys

def test_parent_property():
    """Test that children get parent reference when added to Frame"""
    print("Testing parent property...")

    # Create scene and get UI
    mcrfpy.createScene("test")
    ui = mcrfpy.sceneUI("test")

    # Create a parent frame
    parent = mcrfpy.Frame(pos=(100, 100), size=(200, 200))
    ui.append(parent)

    # Create a child caption
    child = mcrfpy.Caption(text="Child", pos=(10, 10))

    # Before adding, parent should be None
    assert child.parent is None, f"Child should have no parent before adding, got: {child.parent}"

    # Add child to parent
    parent.children.append(child)

    # After adding, parent should be set
    assert child.parent is not None, "Child should have parent after adding"
    # The parent should be the same Frame we added to
    # (checking by position since identity comparison is tricky)
    assert child.parent.x == parent.x, f"Parent x mismatch: {child.parent.x} vs {parent.x}"
    assert child.parent.y == parent.y, f"Parent y mismatch: {child.parent.y} vs {parent.y}"

    print("  - Parent property: PASS")


def test_global_position():
    """Test global position calculation through parent chain"""
    print("Testing global_position property...")

    # Create scene and get UI
    mcrfpy.createScene("test2")
    ui = mcrfpy.sceneUI("test2")

    # Create nested hierarchy:
    # root (50, 50)
    #   -> child1 (20, 20) -> global (70, 70)
    #       -> child2 (10, 10) -> global (80, 80)

    root = mcrfpy.Frame(pos=(50, 50), size=(200, 200))
    ui.append(root)

    child1 = mcrfpy.Frame(pos=(20, 20), size=(100, 100))
    root.children.append(child1)

    child2 = mcrfpy.Caption(text="Deep", pos=(10, 10))
    child1.children.append(child2)

    # Check global positions
    # root has no parent, global should equal local
    assert root.global_position.x == 50, f"Root global x: expected 50, got {root.global_position.x}"
    assert root.global_position.y == 50, f"Root global y: expected 50, got {root.global_position.y}"

    # child1 is at (20, 20) inside root at (50, 50) -> global (70, 70)
    assert child1.global_position.x == 70, f"Child1 global x: expected 70, got {child1.global_position.x}"
    assert child1.global_position.y == 70, f"Child1 global y: expected 70, got {child1.global_position.y}"

    # child2 is at (10, 10) inside child1 at global (70, 70) -> global (80, 80)
    assert child2.global_position.x == 80, f"Child2 global x: expected 80, got {child2.global_position.x}"
    assert child2.global_position.y == 80, f"Child2 global y: expected 80, got {child2.global_position.y}"

    print("  - Global position: PASS")


def test_parent_changes_on_move():
    """Test that moving child to different parent updates parent reference"""
    print("Testing parent changes on move...")

    mcrfpy.createScene("test3")
    ui = mcrfpy.sceneUI("test3")

    parent1 = mcrfpy.Frame(pos=(0, 0), size=(100, 100), fill_color=(255, 0, 0, 255))
    parent2 = mcrfpy.Frame(pos=(200, 0), size=(100, 100), fill_color=(0, 255, 0, 255))
    ui.append(parent1)
    ui.append(parent2)

    child = mcrfpy.Caption(text="Movable", pos=(5, 5))
    parent1.children.append(child)

    # Child should be in parent1
    assert child.parent is not None, "Child should have parent"
    assert child.parent.x == 0, f"Child parent should be parent1, x={child.parent.x}"

    # Move child to parent2 (should auto-remove from parent1)
    parent2.children.append(child)

    # Child should now be in parent2
    assert child.parent is not None, "Child should still have parent"
    assert child.parent.x == 200, f"Child parent should be parent2, x={child.parent.x}"

    # parent1 should have no children
    assert len(parent1.children) == 0, f"parent1 should have 0 children, has {len(parent1.children)}"

    # parent2 should have one child
    assert len(parent2.children) == 1, f"parent2 should have 1 child, has {len(parent2.children)}"

    print("  - Parent changes on move: PASS")


def test_remove_clears_parent():
    """Test that removing child clears parent reference"""
    print("Testing remove clears parent...")

    mcrfpy.createScene("test4")
    ui = mcrfpy.sceneUI("test4")

    parent = mcrfpy.Frame(pos=(0, 0), size=(100, 100))
    ui.append(parent)

    child = mcrfpy.Caption(text="Removable", pos=(5, 5))
    parent.children.append(child)

    assert child.parent is not None, "Child should have parent"

    # Remove child
    parent.children.remove(child)

    assert child.parent is None, f"Child should have no parent after remove, got: {child.parent}"
    assert len(parent.children) == 0, f"Parent should have no children after remove"

    print("  - Remove clears parent: PASS")


def test_scene_level_elements():
    """Test that scene-level elements have no parent"""
    print("Testing scene-level elements...")

    mcrfpy.createScene("test5")
    ui = mcrfpy.sceneUI("test5")

    frame = mcrfpy.Frame(pos=(10, 10), size=(50, 50))
    ui.append(frame)

    # Scene-level elements should have no parent
    assert frame.parent is None, f"Scene-level element should have no parent, got: {frame.parent}"

    # Global position should equal local position
    assert frame.global_position.x == 10, f"Global x should equal local x"
    assert frame.global_position.y == 10, f"Global y should equal local y"

    print("  - Scene-level elements: PASS")


def test_all_drawable_types():
    """Test parent/global_position on all drawable types"""
    print("Testing all drawable types...")

    mcrfpy.createScene("test6")
    ui = mcrfpy.sceneUI("test6")

    parent = mcrfpy.Frame(pos=(100, 100), size=(300, 300))
    ui.append(parent)

    # Test all types
    types_to_test = [
        ("Frame", mcrfpy.Frame(pos=(10, 10), size=(50, 50))),
        ("Caption", mcrfpy.Caption(text="Test", pos=(10, 70))),
        ("Sprite", mcrfpy.Sprite(pos=(10, 130))),  # May need texture
        ("Grid", mcrfpy.Grid(grid_size=(5, 5), pos=(10, 190), size=(80, 80))),
    ]

    for name, child in types_to_test:
        parent.children.append(child)
        assert child.parent is not None, f"{name} should have parent"
        # Global position should be local + parent's position
        expected_x = child.x + 100
        expected_y = child.y + 100
        assert child.global_position.x == expected_x, f"{name} global_x: expected {expected_x}, got {child.global_position.x}"
        assert child.global_position.y == expected_y, f"{name} global_y: expected {expected_y}, got {child.global_position.y}"

    print("  - All drawable types: PASS")


if __name__ == "__main__":
    try:
        test_parent_property()
        test_global_position()
        test_parent_changes_on_move()
        test_remove_clears_parent()
        test_scene_level_elements()
        test_all_drawable_types()

        print("\n=== All tests passed! ===")
        sys.exit(0)
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
