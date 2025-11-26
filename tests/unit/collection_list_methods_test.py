#!/usr/bin/env python3
"""Test for Python list-like methods on UICollection and EntityCollection.

Tests that remove(), pop(), insert(), index(), count() match Python list semantics.
"""

import mcrfpy
import sys


def test_uicollection_remove():
    """Test UICollection.remove() takes a value, not an index."""
    print("Testing UICollection.remove()...")

    mcrfpy.createScene("test_remove")
    ui = mcrfpy.sceneUI("test_remove")

    frame1 = mcrfpy.Frame(pos=(0, 0), size=(100, 100))
    frame2 = mcrfpy.Frame(pos=(100, 0), size=(100, 100))
    frame3 = mcrfpy.Frame(pos=(200, 0), size=(100, 100))

    ui.append(frame1)
    ui.append(frame2)
    ui.append(frame3)

    assert len(ui) == 3

    # Remove by value (like Python list)
    ui.remove(frame2)
    assert len(ui) == 2
    print("  [PASS] remove(element) works")

    # Verify frame2 is gone, but frame1 and frame3 remain
    assert ui[0] is not None
    assert ui[1] is not None

    # Try to remove something not in the list
    try:
        frame4 = mcrfpy.Frame(pos=(300, 0), size=(100, 100))
        ui.remove(frame4)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "not in" in str(e).lower()
        print("  [PASS] remove() raises ValueError when not found")

    # Try to pass an integer (should fail - no longer takes index)
    try:
        ui.remove(0)
        assert False, "Should have raised TypeError"
    except TypeError:
        print("  [PASS] remove(int) raises TypeError (correct - takes element, not index)")

    print("UICollection.remove() tests passed!")
    return True


def test_uicollection_pop():
    """Test UICollection.pop() removes and returns element at index."""
    print("\nTesting UICollection.pop()...")

    mcrfpy.createScene("test_pop")
    ui = mcrfpy.sceneUI("test_pop")

    frame1 = mcrfpy.Frame(pos=(0, 0), size=(100, 100))
    frame1.name = "first"
    frame2 = mcrfpy.Frame(pos=(100, 0), size=(100, 100))
    frame2.name = "second"
    frame3 = mcrfpy.Frame(pos=(200, 0), size=(100, 100))
    frame3.name = "third"

    ui.append(frame1)
    ui.append(frame2)
    ui.append(frame3)

    # pop() with no args removes last
    popped = ui.pop()
    assert popped.name == "third", f"Expected 'third', got '{popped.name}'"
    assert len(ui) == 2
    print("  [PASS] pop() removes last element")

    # pop(0) removes first
    popped = ui.pop(0)
    assert popped.name == "first", f"Expected 'first', got '{popped.name}'"
    assert len(ui) == 1
    print("  [PASS] pop(0) removes first element")

    # pop(-1) is same as pop()
    ui.append(mcrfpy.Frame(pos=(0, 0), size=(10, 10)))
    ui[-1].name = "new_last"
    popped = ui.pop(-1)
    assert popped.name == "new_last"
    print("  [PASS] pop(-1) removes last element")

    # pop from empty collection
    ui.pop()  # Remove last remaining element
    try:
        ui.pop()
        assert False, "Should have raised IndexError"
    except IndexError as e:
        assert "empty" in str(e).lower()
        print("  [PASS] pop() from empty raises IndexError")

    print("UICollection.pop() tests passed!")
    return True


def test_uicollection_insert():
    """Test UICollection.insert() inserts at given index."""
    print("\nTesting UICollection.insert()...")

    mcrfpy.createScene("test_insert")
    ui = mcrfpy.sceneUI("test_insert")

    frame1 = mcrfpy.Frame(pos=(0, 0), size=(100, 100))
    frame1.name = "first"
    frame3 = mcrfpy.Frame(pos=(200, 0), size=(100, 100))
    frame3.name = "third"

    ui.append(frame1)
    ui.append(frame3)

    # Insert in middle
    frame2 = mcrfpy.Frame(pos=(100, 0), size=(100, 100))
    frame2.name = "second"
    ui.insert(1, frame2)

    assert len(ui) == 3
    assert ui[0].name == "first"
    assert ui[1].name == "second"
    assert ui[2].name == "third"
    print("  [PASS] insert(1, element) inserts at index 1")

    # Insert at beginning
    frame0 = mcrfpy.Frame(pos=(0, 0), size=(50, 50))
    frame0.name = "zero"
    ui.insert(0, frame0)
    assert ui[0].name == "zero"
    print("  [PASS] insert(0, element) inserts at beginning")

    # Insert at end (index > len)
    frame_end = mcrfpy.Frame(pos=(0, 0), size=(50, 50))
    frame_end.name = "end"
    ui.insert(100, frame_end)  # Way past end
    assert ui[-1].name == "end"
    print("  [PASS] insert(100, element) appends when index > len")

    # Negative index
    frame_neg = mcrfpy.Frame(pos=(0, 0), size=(50, 50))
    frame_neg.name = "negative"
    current_len = len(ui)
    ui.insert(-1, frame_neg)  # Insert before last
    assert ui[-2].name == "negative"
    print("  [PASS] insert(-1, element) inserts before last")

    print("UICollection.insert() tests passed!")
    return True


def test_entitycollection_pop_insert():
    """Test EntityCollection.pop() and insert()."""
    print("\nTesting EntityCollection.pop() and insert()...")

    mcrfpy.createScene("test_entity_pop")
    ui = mcrfpy.sceneUI("test_entity_pop")

    grid = mcrfpy.Grid(grid_size=(10, 10), pos=(0, 0), size=(400, 400))
    ui.append(grid)

    e1 = mcrfpy.Entity(grid_pos=(1, 1))
    e1.name = "first"
    e2 = mcrfpy.Entity(grid_pos=(2, 2))
    e2.name = "second"
    e3 = mcrfpy.Entity(grid_pos=(3, 3))
    e3.name = "third"

    grid.entities.append(e1)
    grid.entities.append(e2)
    grid.entities.append(e3)

    # Test pop()
    popped = grid.entities.pop()
    assert popped.name == "third"
    assert len(grid.entities) == 2
    print("  [PASS] EntityCollection.pop() works")

    # Test pop(0)
    popped = grid.entities.pop(0)
    assert popped.name == "first"
    assert len(grid.entities) == 1
    print("  [PASS] EntityCollection.pop(0) works")

    # Test insert
    e_new = mcrfpy.Entity(grid_pos=(5, 5))
    e_new.name = "new"
    grid.entities.insert(0, e_new)
    assert grid.entities[0].name == "new"
    print("  [PASS] EntityCollection.insert() works")

    print("EntityCollection pop/insert tests passed!")
    return True


def test_index_and_count():
    """Test index() and count() methods."""
    print("\nTesting index() and count()...")

    mcrfpy.createScene("test_index_count")
    ui = mcrfpy.sceneUI("test_index_count")

    frame1 = mcrfpy.Frame(pos=(0, 0), size=(100, 100))
    frame2 = mcrfpy.Frame(pos=(100, 0), size=(100, 100))

    ui.append(frame1)
    ui.append(frame2)

    # index() returns integer
    idx = ui.index(frame1)
    assert idx == 0, f"Expected 0, got {idx}"
    assert isinstance(idx, int)
    print("  [PASS] index() returns integer")

    idx = ui.index(frame2)
    assert idx == 1
    print("  [PASS] index() finds correct position")

    # count() returns integer
    cnt = ui.count(frame1)
    assert cnt == 1
    assert isinstance(cnt, int)
    print("  [PASS] count() returns integer")

    # count of element not in collection
    frame3 = mcrfpy.Frame(pos=(200, 0), size=(100, 100))
    cnt = ui.count(frame3)
    assert cnt == 0
    print("  [PASS] count() returns 0 for element not in collection")

    print("index() and count() tests passed!")
    return True


if __name__ == "__main__":
    try:
        all_passed = True
        all_passed &= test_uicollection_remove()
        all_passed &= test_uicollection_pop()
        all_passed &= test_uicollection_insert()
        all_passed &= test_entitycollection_pop_insert()
        all_passed &= test_index_and_count()

        if all_passed:
            print("\n" + "="*50)
            print("All list-like method tests PASSED!")
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
