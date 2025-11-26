#!/usr/bin/env python3
"""Test that method documentation is properly accessible in Python."""

import mcrfpy
import sys

def test_module_doc():
    """Test module-level documentation."""
    print("=== Module Documentation ===")
    print(f"Module: {mcrfpy.__name__}")
    print(f"Doc: {mcrfpy.__doc__[:100]}..." if mcrfpy.__doc__ else "No module doc")
    print()
    
def test_method_docs():
    """Test method documentation."""
    print("=== Method Documentation ===")
    
    # Test main API methods
    methods = [
        'createSoundBuffer', 'loadMusic', 'setMusicVolume', 'setSoundVolume',
        'playSound', 'getMusicVolume', 'getSoundVolume', 'sceneUI',
        'currentScene', 'setScene', 'createScene', 'keypressScene',
        'setTimer', 'delTimer', 'exit', 'setScale', 'find', 'findAll',
        'getMetrics'
    ]
    
    for method_name in methods:
        if hasattr(mcrfpy, method_name):
            method = getattr(mcrfpy, method_name)
            doc = method.__doc__
            if doc:
                # Extract first line of docstring
                first_line = doc.strip().split('\n')[0]
                print(f"{method_name}: {first_line}")
            else:
                print(f"{method_name}: NO DOCUMENTATION")
    print()

def test_class_docs():
    """Test class documentation."""
    print("=== Class Documentation ===")
    
    classes = ['Frame', 'Caption', 'Sprite', 'Grid', 'Entity', 'Color', 'Vector', 'Texture', 'Font']
    
    for class_name in classes:
        if hasattr(mcrfpy, class_name):
            cls = getattr(mcrfpy, class_name)
            doc = cls.__doc__
            if doc:
                # Extract first line
                first_line = doc.strip().split('\n')[0]
                print(f"{class_name}: {first_line[:80]}...")
            else:
                print(f"{class_name}: NO DOCUMENTATION")
    print()

def test_property_docs():
    """Test property documentation."""
    print("=== Property Documentation ===")
    
    # Test Frame properties
    if hasattr(mcrfpy, 'Frame'):
        frame_props = ['x', 'y', 'w', 'h', 'fill_color', 'outline_color', 'outline', 'children', 'visible', 'z_index']
        print("Frame properties:")
        for prop_name in frame_props:
            prop = getattr(mcrfpy.Frame, prop_name, None)
            if prop and hasattr(prop, '__doc__'):
                print(f"  {prop_name}: {prop.__doc__}")
    print()

def test_method_signatures():
    """Test that methods have correct signatures in docs."""
    print("=== Method Signatures ===")
    
    # Check a few key methods
    if hasattr(mcrfpy, 'setScene'):
        doc = mcrfpy.setScene.__doc__
        if doc and 'setScene(scene: str, transition: str = None, duration: float = 0.0)' in doc:
            print("✓ setScene signature correct")
        else:
            print("✗ setScene signature incorrect or missing")
    
    if hasattr(mcrfpy, 'setTimer'):
        doc = mcrfpy.setTimer.__doc__
        if doc and 'setTimer(name: str, handler: callable, interval: int)' in doc:
            print("✓ setTimer signature correct")
        else:
            print("✗ setTimer signature incorrect or missing")
    
    if hasattr(mcrfpy, 'find'):
        doc = mcrfpy.find.__doc__
        if doc and 'find(name: str, scene: str = None)' in doc:
            print("✓ find signature correct")
        else:
            print("✗ find signature incorrect or missing")
    print()

def test_help_output():
    """Test Python help() function output."""
    print("=== Help Function Test ===")
    print("Testing help(mcrfpy.setScene):")
    import io
    import contextlib
    
    # Capture help output
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        help(mcrfpy.setScene)
    
    help_text = buffer.getvalue()
    if 'transition to a different scene' in help_text:
        print("✓ Help text contains expected documentation")
    else:
        print("✗ Help text missing expected documentation")
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
    
    print("\nDocumentation tests complete!")
    sys.exit(0)

if __name__ == '__main__':
    main()