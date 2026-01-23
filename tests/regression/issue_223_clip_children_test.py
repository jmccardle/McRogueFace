"""Test clip_children positioning and toggling fixes (#223, #224, #225, #226)

Issue #223: Frame appears at wrong position with clip_children
Issue #224: Stale rendering after toggling clip_children off
Issue #225: Child changes don't update parent's cached texture
Issue #226: Zero-size frame with clip_children causes inconsistent state

This test verifies the property/positioning behavior. Visual rendering verification
requires a game loop and should be done with the demo system.
"""
import mcrfpy
import sys

errors = []

# Test 1: Position with clip_children=True (#223)
frame = mcrfpy.Frame(pos=(100, 100), size=(200, 200), clip_children=True)
if frame.x != 100:
    errors.append(f"#223 Test 1: Expected x=100, got {frame.x}")
if frame.y != 100:
    errors.append(f"#223 Test 1: Expected y=100, got {frame.y}")

# Add a child
child = mcrfpy.Caption(text="Hello", pos=(10, 10))
frame.children.append(child)

# Test 2: Toggle clip_children off (#224)
frame.clip_children = False
if frame.x != 100:
    errors.append(f"#224 Test 2 after toggle off: Expected x=100, got {frame.x}")
if frame.y != 100:
    errors.append(f"#224 Test 2 after toggle off: Expected y=100, got {frame.y}")

# Toggle back on
frame.clip_children = True
if frame.x != 100:
    errors.append(f"#224 Test 2 after toggle on: Expected x=100, got {frame.x}")

# Test 3: Zero-size frame with clip_children (#226)
zero_frame = mcrfpy.Frame(pos=(50, 50), size=(0, 0), clip_children=True)
if zero_frame.x != 50:
    errors.append(f"#226 Test 3: Expected x=50, got {zero_frame.x}")
if zero_frame.y != 50:
    errors.append(f"#226 Test 3: Expected y=50, got {zero_frame.y}")

# Test 4: cache_subtree toggle similar to clip_children
cache_frame = mcrfpy.Frame(pos=(200, 200), size=(100, 100), cache_subtree=True)
if cache_frame.x != 200:
    errors.append(f"Test 4: Expected x=200, got {cache_frame.x}")

cache_frame.cache_subtree = False
if cache_frame.x != 200:
    errors.append(f"Test 4 after toggle: Expected x=200, got {cache_frame.x}")

# Test 5: Both clip_children and cache_subtree
both_frame = mcrfpy.Frame(pos=(300, 300), size=(100, 100), clip_children=True, cache_subtree=True)

# Turn off clip_children (cache_subtree should keep texture active)
both_frame.clip_children = False
if both_frame.x != 300:
    errors.append(f"Test 5 after clip toggle: Expected x=300, got {both_frame.x}")

# Turn off cache_subtree too
both_frame.cache_subtree = False
if both_frame.x != 300:
    errors.append(f"Test 5 after full toggle: Expected x=300, got {both_frame.x}")

# Test 6: Moving a frame with clip_children
frame.x = 150
frame.y = 150
if frame.x != 150:
    errors.append(f"Test 6: Expected x=150, got {frame.x}")
if frame.y != 150:
    errors.append(f"Test 6: Expected y=150, got {frame.y}")

# Test 7: Child modification (dirty propagation #225)
# This tests that modifying a child marks the parent dirty
# We can't directly test render_dirty flag from Python, but we can verify
# that the API doesn't crash and positions stay correct
frame2 = mcrfpy.Frame(pos=(400, 400), size=(100, 100), clip_children=True)
child2 = mcrfpy.Caption(text="Test", pos=(5, 5))
frame2.children.append(child2)

# Modify child text
child2.text = "Changed"
if frame2.x != 400:
    errors.append(f"Test 7: Expected x=400 after child change, got {frame2.x}")

# Report results
if errors:
    print("FAIL: " + "; ".join(errors))
    sys.exit(1)
else:
    print("PASS: clip_children positioning and toggling tests")
    sys.exit(0)
