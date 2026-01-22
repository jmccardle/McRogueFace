#!/usr/bin/env python3
"""Test for issues #184 (mcrfpy.window singleton) and #189 (hide non-instantiable classes)"""

import mcrfpy
import sys

errors = []

# Test #184: mcrfpy.window singleton exists
print("Testing #184: mcrfpy.window singleton...")

try:
    window = mcrfpy.window
    print(f"  mcrfpy.window exists: {window}")
except AttributeError as e:
    errors.append(f"#184 FAIL: mcrfpy.window not found: {e}")

# Check window has expected attributes
if hasattr(mcrfpy, 'window'):
    window = mcrfpy.window

    # Check for expected properties
    expected_attrs = ['resolution', 'fullscreen', 'vsync', 'title', 'visible']
    for attr in expected_attrs:
        if hasattr(window, attr):
            print(f"  window.{attr} = {getattr(window, attr)}")
        else:
            errors.append(f"#184 FAIL: mcrfpy.window missing attribute '{attr}'")

# Check that Window TYPE still exists (for isinstance checks)
if hasattr(mcrfpy, 'Window'):
    print(f"  mcrfpy.Window type exists: {mcrfpy.Window}")
    # Verify window is an instance of Window
    if isinstance(mcrfpy.window, mcrfpy.Window):
        print("  isinstance(mcrfpy.window, mcrfpy.Window) = True")
    else:
        errors.append("#184 FAIL: mcrfpy.window is not an instance of mcrfpy.Window")
else:
    errors.append("#184 FAIL: mcrfpy.Window type not found")

# Test #189: Hidden classes should NOT be accessible
print("\nTesting #189: Hidden classes should raise AttributeError...")

hidden_classes = [
    'EntityCollection',
    'UICollection',
    'UICollectionIter',
    'UIEntityCollectionIter',
    'GridPoint',
    'GridPointState'
]

for class_name in hidden_classes:
    try:
        cls = getattr(mcrfpy, class_name)
        errors.append(f"#189 FAIL: mcrfpy.{class_name} should be hidden but is accessible: {cls}")
    except AttributeError:
        print(f"  mcrfpy.{class_name} correctly raises AttributeError")

# Test that hidden classes still WORK (just not exported)
print("\nTesting that internal types still function correctly...")

# Create a scene to test UICollection
scene = mcrfpy.Scene("test_scene")
scene.activate()

# Test UICollection via .children
print("  Getting scene.children...")
children = scene.children
print(f"  scene.children works: {children}")
children_type = type(children)
print(f"  type(scene.children) = {children_type}")
if 'UICollection' in str(children_type):
    print("  UICollection type works correctly (internal use)")
else:
    errors.append(f"#189 FAIL: scene.children returned unexpected type: {children_type}")

# Test that Drawable IS still exported (should NOT be hidden)
print("\nTesting that Drawable is still exported...")
if hasattr(mcrfpy, 'Drawable'):
    print(f"  mcrfpy.Drawable exists: {mcrfpy.Drawable}")
else:
    errors.append("FAIL: mcrfpy.Drawable should still be exported but is missing")

# Summary
print("\n" + "="*60)
if errors:
    print("FAILURES:")
    for e in errors:
        print(f"  {e}")
    print(f"\nFAIL: {len(errors)} error(s)")
    sys.exit(1)
else:
    print("PASS: All tests passed for issues #184 and #189")
    sys.exit(0)
