"""Regression test for issue #183: .parent quirks

Tests:
1. Newly-created drawable has parent None
2. Setting same parent twice doesn't duplicate children
3. Setting parent removes from old collection
4. Setting parent to None removes from parent collection
5. Grid parent handling works correctly
6. Moving from Frame to Grid works
7. Scene-level elements return Scene object from .parent
8. Setting parent to None removes from scene's children
9. Moving from scene to Frame works
10. Moving from Frame to scene works (via scene.children.append)
11. Direct .parent = scene assignment works
12. .parent = scene removes from Frame and adds to Scene

Note: Parent comparison uses repr() or child containment checking
since child.parent returns a new Python wrapper object each time.
"""
import mcrfpy
import sys


def same_drawable(a, b):
    """Check if two drawable wrappers point to the same C++ object.

    Since get_parent creates new Python wrappers, we can't use == or is.
    Instead, verify by checking that modifications to one affect the other.
    """
    if a is None or b is None:
        return a is None and b is None
    # Modify a property on 'a' and verify it changes on 'b'
    original_x = b.x
    test_value = original_x + 12345.0
    a.x = test_value
    result = b.x == test_value
    a.x = original_x  # Restore
    return result


def test_new_drawable_parent_none():
    """Newly-created drawable has parent None"""
    frame = mcrfpy.Frame(pos=(0,0), size=(100,100))
    assert frame.parent is None, f"Expected None, got {frame.parent}"
    print("PASS: New drawable has parent None")


def test_no_duplicate_on_same_parent():
    """Setting same parent twice doesn't duplicate children"""
    parent = mcrfpy.Frame(pos=(0,0), size=(200,200))
    child = mcrfpy.Frame(pos=(10,10), size=(50,50))

    # Add child to parent
    parent.children.append(child)
    initial_count = len(parent.children)

    # Set same parent again via property
    child.parent = parent

    # Should not duplicate
    assert len(parent.children) == initial_count, \
        f"Expected {initial_count} children, got {len(parent.children)} - duplicate was added!"
    print("PASS: Setting same parent twice doesn't duplicate")


def test_parent_removes_from_old_collection():
    """Setting parent removes from old collection"""
    parent1 = mcrfpy.Frame(pos=(0,0), size=(200,200))
    parent2 = mcrfpy.Frame(pos=(100,0), size=(200,200))  # Different x to distinguish
    child = mcrfpy.Frame(pos=(10,10), size=(50,50))

    # Add to parent1
    parent1.children.append(child)
    assert len(parent1.children) == 1, "Child should be in parent1"
    assert child.parent is not None, "parent should not be None"
    assert same_drawable(child.parent, parent1), "parent should be parent1"

    # Move to parent2
    child.parent = parent2

    # Should be removed from parent1 and added to parent2
    assert len(parent1.children) == 0, f"Expected 0 children in parent1, got {len(parent1.children)}"
    assert len(parent2.children) == 1, f"Expected 1 child in parent2, got {len(parent2.children)}"
    assert same_drawable(child.parent, parent2), "parent should be parent2"
    print("PASS: Setting parent removes from old collection")


def test_parent_none_removes_from_collection():
    """Setting parent to None removes from parent's collection"""
    parent = mcrfpy.Frame(pos=(0,0), size=(200,200))
    child = mcrfpy.Frame(pos=(10,10), size=(50,50))

    # Add child to parent
    parent.children.append(child)
    assert len(parent.children) == 1, "Child should be in parent"

    # Set parent to None
    child.parent = None

    # Should be removed from parent
    assert len(parent.children) == 0, f"Expected 0 children, got {len(parent.children)}"
    assert child.parent is None, "parent should be None"
    print("PASS: Setting parent to None removes from collection")


def test_grid_parent_handling():
    """Grid parent handling works correctly"""
    grid = mcrfpy.Grid(grid_size=(10,10), pos=(0,0), size=(200,200))
    child = mcrfpy.Frame(pos=(10,10), size=(50,50))

    # Add child to grid
    grid.children.append(child)
    assert len(grid.children) == 1, "Child should be in grid"
    assert child.parent is not None, "parent should not be None"

    # Set same parent again (should not duplicate)
    child.parent = grid
    assert len(grid.children) == 1, f"Expected 1 child, got {len(grid.children)} - duplicate was added!"

    # Move to a frame
    frame = mcrfpy.Frame(pos=(0,0), size=(200,200))
    child.parent = frame

    # Should be removed from grid and added to frame
    assert len(grid.children) == 0, f"Expected 0 children in grid, got {len(grid.children)}"
    assert len(frame.children) == 1, f"Expected 1 child in frame, got {len(frame.children)}"
    assert same_drawable(child.parent, frame), "parent should be frame"
    print("PASS: Grid parent handling works correctly")


def test_move_from_frame_to_grid():
    """Moving from Frame parent to Grid parent works"""
    frame = mcrfpy.Frame(pos=(0,0), size=(200,200))
    grid = mcrfpy.Grid(grid_size=(10,10), pos=(100,0), size=(200,200))  # Different x
    child = mcrfpy.Caption(text="Test", pos=(10,10))

    # Add to frame
    frame.children.append(child)
    assert len(frame.children) == 1

    # Move to grid
    child.parent = grid

    assert len(frame.children) == 0, f"Expected 0 children in frame, got {len(frame.children)}"
    assert len(grid.children) == 1, f"Expected 1 child in grid, got {len(grid.children)}"
    # Note: Caption doesn't have x property, so just check parent is not None
    assert child.parent is not None, "parent should not be None"
    print("PASS: Moving from Frame to Grid works")


def test_scene_parent_returns_scene_object():
    """Scene-level elements return Scene object from .parent"""
    scene = mcrfpy.Scene('test_scene_parent_return')

    child = mcrfpy.Frame(pos=(10,10), size=(50,50))
    scene.children.append(child)

    # .parent should return a Scene object, not None
    parent = child.parent
    assert parent is not None, "parent should not be None for scene-level element"
    assert type(parent).__name__ == 'Scene', f"Expected Scene, got {type(parent).__name__}"
    assert parent.name == 'test_scene_parent_return', f"Expected scene name 'test_scene_parent_return', got '{parent.name}'"
    print("PASS: Scene-level elements return Scene object from .parent")


def test_scene_parent_none_removes():
    """Setting parent to None removes from scene's children"""
    scene = mcrfpy.Scene('test_scene_remove')
    mcrfpy.current_scene = scene

    child = mcrfpy.Frame(pos=(10,10), size=(50,50))
    scene.children.append(child)
    assert len(scene.children) == 1, "Child should be in scene"

    # Set parent to None - should remove from scene
    child.parent = None

    assert len(scene.children) == 0, f"Expected 0 children in scene, got {len(scene.children)}"
    assert child.parent is None, "parent should be None"
    print("PASS: Scene parent=None removes from scene")


def test_scene_to_frame():
    """Moving from scene to Frame removes from scene, adds to Frame"""
    scene = mcrfpy.Scene('test_scene_to_frame')
    mcrfpy.current_scene = scene

    child = mcrfpy.Frame(pos=(10,10), size=(50,50))
    scene.children.append(child)
    assert len(scene.children) == 1

    # Move to a Frame
    parent_frame = mcrfpy.Frame(pos=(0,0), size=(200,200))
    child.parent = parent_frame

    assert len(scene.children) == 0, f"Expected 0 children in scene, got {len(scene.children)}"
    assert len(parent_frame.children) == 1, f"Expected 1 child in frame, got {len(parent_frame.children)}"
    print("PASS: Scene -> Frame movement works")


def test_frame_to_scene():
    """Moving from Frame to scene removes from Frame, adds to scene"""
    scene = mcrfpy.Scene('test_frame_to_scene')
    mcrfpy.current_scene = scene

    parent_frame = mcrfpy.Frame(pos=(0,0), size=(200,200))
    child = mcrfpy.Frame(pos=(10,10), size=(50,50))
    parent_frame.children.append(child)
    assert len(parent_frame.children) == 1

    # Move to scene via scene.children.append()
    scene.children.append(child)

    assert len(parent_frame.children) == 0, f"Expected 0 children in frame, got {len(parent_frame.children)}"
    assert len(scene.children) == 1, f"Expected 1 child in scene, got {len(scene.children)}"
    print("PASS: Frame -> Scene movement works")


def test_parent_assign_scene():
    """Setting .parent = scene directly adds to scene's children"""
    scene = mcrfpy.Scene('test_parent_assign_scene')
    frame = mcrfpy.Frame(pos=(10,10), size=(50,50))

    # Direct assignment: frame.parent = scene
    frame.parent = scene

    assert len(scene.children) == 1, f"Expected 1 child in scene, got {len(scene.children)}"
    assert frame.parent is not None, "parent should not be None"
    assert frame.parent.name == 'test_parent_assign_scene', f"Expected scene name, got '{frame.parent.name}'"
    print("PASS: Direct .parent = scene assignment works")


def test_parent_assign_scene_from_frame():
    """Setting .parent = scene removes from Frame and adds to Scene"""
    scene = mcrfpy.Scene('test_assign_scene_from_frame')
    parent_frame = mcrfpy.Frame(pos=(0,0), size=(200,200))
    child = mcrfpy.Frame(pos=(10,10), size=(50,50))

    parent_frame.children.append(child)
    assert len(parent_frame.children) == 1

    # Move via direct assignment
    child.parent = scene

    assert len(parent_frame.children) == 0, f"Expected 0 children in frame, got {len(parent_frame.children)}"
    assert len(scene.children) == 1, f"Expected 1 child in scene, got {len(scene.children)}"
    assert child.parent.name == 'test_assign_scene_from_frame'
    print("PASS: .parent = scene from Frame works")


def run_tests():
    """Run all tests"""
    print("Issue #183: .parent quirks regression test")
    print("=" * 50)

    try:
        test_new_drawable_parent_none()
        test_no_duplicate_on_same_parent()
        test_parent_removes_from_old_collection()
        test_parent_none_removes_from_collection()
        test_grid_parent_handling()
        test_move_from_frame_to_grid()

        # Scene parent tracking tests
        test_scene_parent_returns_scene_object()
        test_scene_parent_none_removes()
        test_scene_to_frame()
        test_frame_to_scene()
        test_parent_assign_scene()
        test_parent_assign_scene_from_frame()

        print("=" * 50)
        print("All tests PASSED!")
        sys.exit(0)
    except AssertionError as e:
        print(f"FAIL: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Run tests immediately (no game loop needed)
run_tests()
