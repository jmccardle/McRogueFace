#!/usr/bin/env python3
"""Test for UICollection - Related to issue #69 (Sequence Protocol)"""
import mcrfpy
import sys

failures = []

def check(label, condition, detail=""):
    if condition:
        print(f"[ok] {label}")
    else:
        msg = f"{label}{': ' + detail if detail else ''}"
        print(f"[FAIL] {msg}")
        failures.append(msg)

def test_UICollection():
    """Test UICollection sequence protocol compliance"""
    # Create test scene
    collection_test = mcrfpy.Scene("collection_test")
    collection_test.activate()
    ui = collection_test.children

    # Add various UI elements
    frame = mcrfpy.Frame(pos=(10, 10), size=(100, 100))
    caption = mcrfpy.Caption(pos=(120, 10), text="Test")
    caption.name = "Test"  # find() searches by name, not text
    # Skip sprite for now since it requires a texture

    ui.append(frame)
    ui.append(caption)

    print("Testing UICollection sequence protocol (Issue #69)...")

    # Test len()
    check("len() works", len(ui) == 2, f"expected 2, got {len(ui)}")

    # Test indexing
    check("indexing works",
          type(ui[0]).__name__ == "Frame" and type(ui[1]).__name__ == "Caption",
          f"got [{type(ui[0]).__name__}, {type(ui[1]).__name__}]")

    # Test negative indexing
    check("negative indexing works", type(ui[-1]).__name__ == "Caption",
          f"ui[-1] = {type(ui[-1]).__name__}")

    # Test slicing
    slice_items = ui[0:2]
    check("slicing works", len(slice_items) == 2, f"got {len(slice_items)} items")

    # Test iteration
    types = [type(item).__name__ for item in ui]
    check("iteration works", types == ["Frame", "Caption"], f"got {types}")

    # Test contains
    check("'in' operator works", frame in ui, "'in' returned False for existing item")

    # Test remove -- current API takes the Drawable itself (list.remove semantics),
    # not an index. pop(index) is the index-based removal.
    ui.remove(caption)
    check("remove(element) works", len(ui) == 1 and caption not in ui,
          f"now {len(ui)} items")

    # Test type preservation (Issue #76)
    parent_frame = mcrfpy.Frame(pos=(250, 10), size=(200, 200),
                                fill_color=mcrfpy.Color(200, 200, 200))
    child_caption = mcrfpy.Caption(pos=(10, 10), text="Child")
    parent_frame.children.append(child_caption)
    ui.append(parent_frame)

    retrieved = ui[-1]
    check("type preservation works", type(retrieved).__name__ == "Frame",
          f"got {type(retrieved).__name__} (Issue #76)")
    check("retrieved object identity preserved", retrieved is parent_frame)

    # Test find by name (Issue #41)
    parent_frame.name = "parent"
    found = ui.find("parent")
    check("find() by name works", found is parent_frame,
          f"got {found!r}")
    check("find() returns None for missing name", ui.find("nonexistent") is None)

test_UICollection()

if failures:
    print(f"FAIL ({len(failures)} check(s) failed)")
    sys.exit(1)
print("PASS")
sys.exit(0)
