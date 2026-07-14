#!/usr/bin/env python3
"""Test that method documentation is properly accessible in Python.

Rot repair: this test used to only *print* what it found (so a missing
docstring silently "passed"), and it probed the pre-#350 API surface
(setScene/createScene/sceneUI/currentScene, the module-level audio
functions). It now asserts against the current mcrfpy API and fails loudly
on any missing docstring.
"""

import mcrfpy
import sys
import types
import io
import contextlib

failures = []

def check(condition, message):
    if condition:
        print(f"  PASS: {message}")
    else:
        print(f"  FAIL: {message}")
        failures.append(message)

def test_module_doc():
    """Test module-level documentation."""
    print("=== Module Documentation ===")
    doc = mcrfpy.__doc__
    check(bool(doc and doc.strip()), "mcrfpy has a module docstring")
    check(bool(doc and 'McRogueFace' in doc), "module docstring names McRogueFace")
    print()

def test_method_docs():
    """Every public module-level function must be documented."""
    print("=== Method Documentation ===")

    # Current module-level API (audio moved to Sound/Music/SoundBuffer classes;
    # setScene/createScene/currentScene/sceneUI replaced by mcrfpy.Scene).
    methods = [
        'bresenham', 'end_benchmark', 'exit', 'find', 'find_all', 'get_metrics',
        'lock', 'log_benchmark', 'set_dev_console', 'set_scale',
        'start_benchmark', 'step',
    ]

    for method_name in methods:
        check(hasattr(mcrfpy, method_name), f"mcrfpy.{method_name} exists")
        method = getattr(mcrfpy, method_name, None)
        doc = getattr(method, '__doc__', None)
        check(bool(doc and doc.strip()), f"mcrfpy.{method_name} has documentation")

    # Nothing public may be undocumented, even if not listed above.
    for name in dir(mcrfpy):
        if name.startswith('_'):
            continue
        obj = getattr(mcrfpy, name)
        if isinstance(obj, types.BuiltinFunctionType):
            check(bool(obj.__doc__), f"module function {name} has documentation")
    print()

def test_class_docs():
    """Test class documentation."""
    print("=== Class Documentation ===")

    classes = ['Frame', 'Caption', 'Sprite', 'Grid', 'GridView', 'GridData',
               'Entity', 'Color', 'Vector', 'Texture', 'Font', 'Timer', 'Scene']

    for class_name in classes:
        check(hasattr(mcrfpy, class_name), f"mcrfpy.{class_name} exists")
        cls = getattr(mcrfpy, class_name, None)
        doc = getattr(cls, '__doc__', None)
        check(bool(doc and doc.strip()), f"class {class_name} has documentation")
        if doc:
            print(f"    {class_name}: {doc.strip().splitlines()[0][:70]}")
    print()

def test_property_docs():
    """Every getset property on the core drawables must be documented."""
    print("=== Property Documentation ===")

    frame_props = ['x', 'y', 'w', 'h', 'fill_color', 'outline_color', 'outline',
                   'children', 'visible', 'z_index']
    for prop_name in frame_props:
        prop = getattr(mcrfpy.Frame, prop_name, None)
        check(prop is not None, f"Frame.{prop_name} exists")
        check(bool(prop is not None and prop.__doc__),
              f"Frame.{prop_name} has documentation")

    # No getset descriptor on the core types may be undocumented.
    for class_name in ['Frame', 'Caption', 'Sprite', 'Grid', 'Entity',
                       'Color', 'Vector', 'Timer']:
        cls = getattr(mcrfpy, class_name)
        for prop_name, prop in vars(cls).items():
            if isinstance(prop, types.GetSetDescriptorType):
                check(bool(prop.__doc__),
                      f"{class_name}.{prop_name} has documentation")
    print()

def test_method_signatures():
    """Test that docstrings carry a usable signature line."""
    print("=== Method Signatures ===")

    doc = mcrfpy.find.__doc__
    check(bool(doc and 'find(name: str, scene: str = None)' in doc),
          "find() signature present in docstring")

    doc = mcrfpy.step.__doc__
    check(bool(doc and 'step(' in doc), "step() signature present in docstring")

    doc = mcrfpy.Timer.__doc__
    check(bool(doc and 'Timer(' in doc), "Timer signature present in class doc")

    doc = mcrfpy.Scene.__doc__
    check(bool(doc and 'Scene(' in doc), "Scene signature present in class doc")

    # Bound method documentation (animation is now an object method, #229).
    doc = mcrfpy.Frame.animate.__doc__
    check(bool(doc and 'animate(' in doc),
          "Frame.animate() signature present in docstring")
    print()

def test_help_output():
    """Test Python help() function output."""
    print("=== Help Function Test ===")

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        help(mcrfpy.find)
    help_text = buffer.getvalue()
    check('Find the first UI element' in help_text,
          "help(mcrfpy.find) contains its documentation")

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        help(mcrfpy.Frame)
    help_text = buffer.getvalue()
    check('Frame' in help_text and 'animate' in help_text,
          "help(mcrfpy.Frame) lists the class and its methods")
    print()

def main():
    """Run all documentation tests."""
    print("McRogueFace Documentation Tests")
    print("===============================\n")

    test_module_doc()
    test_method_docs()
    test_class_docs()
    test_property_docs()
    test_method_signatures()
    test_help_output()

    if failures:
        print(f"\nFAIL: {len(failures)} documentation check(s) failed:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)

    print("\nDocumentation tests complete!")
    print("PASS")
    sys.exit(0)

if __name__ == '__main__':
    main()
