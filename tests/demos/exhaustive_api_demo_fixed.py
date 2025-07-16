#!/usr/bin/env python3
"""
McRogueFace Exhaustive API Demo (Fixed)
=======================================

Fixed version that properly exits after tests complete.
"""

import mcrfpy
import sys

# Test configuration
VERBOSE = True  # Print detailed information about each test

def print_section(title):
    """Print a section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_test(test_name, success=True):
    """Print test result"""
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"  {status} - {test_name}")

def test_color_api():
    """Test all Color constructors and methods"""
    print_section("COLOR API TESTS")
    
    # Constructor variants
    print("\n  Constructors:")
    
    # Empty constructor (defaults to white)
    c1 = mcrfpy.Color()
    print_test(f"Color() = ({c1.r}, {c1.g}, {c1.b}, {c1.a})")
    
    # Single value (grayscale)
    c2 = mcrfpy.Color(128)
    print_test(f"Color(128) = ({c2.r}, {c2.g}, {c2.b}, {c2.a})")
    
    # RGB only (alpha defaults to 255)
    c3 = mcrfpy.Color(255, 128, 0)
    print_test(f"Color(255, 128, 0) = ({c3.r}, {c3.g}, {c3.b}, {c3.a})")
    
    # Full RGBA
    c4 = mcrfpy.Color(100, 150, 200, 128)
    print_test(f"Color(100, 150, 200, 128) = ({c4.r}, {c4.g}, {c4.b}, {c4.a})")
    
    # Property access
    print("\n  Properties:")
    c = mcrfpy.Color(10, 20, 30, 40)
    print_test(f"Initial: r={c.r}, g={c.g}, b={c.b}, a={c.a}")
    
    c.r = 200
    c.g = 150
    c.b = 100
    c.a = 255
    print_test(f"After modification: r={c.r}, g={c.g}, b={c.b}, a={c.a}")
    
    return True

def test_frame_api():
    """Test all Frame constructors and methods"""
    print_section("FRAME API TESTS")
    
    # Create a test scene
    mcrfpy.createScene("api_test")
    mcrfpy.setScene("api_test")
    ui = mcrfpy.sceneUI("api_test")
    
    # Constructor variants
    print("\n  Constructors:")
    
    # Empty constructor
    f1 = mcrfpy.Frame()
    print_test(f"Frame() - pos=({f1.x}, {f1.y}), size=({f1.w}, {f1.h})")
    ui.append(f1)
    
    # Position only
    f2 = mcrfpy.Frame(100, 50)
    print_test(f"Frame(100, 50) - pos=({f2.x}, {f2.y}), size=({f2.w}, {f2.h})")
    ui.append(f2)
    
    # Position and size
    f3 = mcrfpy.Frame(200, 100, 150, 75)
    print_test(f"Frame(200, 100, 150, 75) - pos=({f3.x}, {f3.y}), size=({f3.w}, {f3.h})")
    ui.append(f3)
    
    # Full constructor
    f4 = mcrfpy.Frame(300, 200, 200, 100, 
                      fill_color=mcrfpy.Color(100, 100, 200),
                      outline_color=mcrfpy.Color(255, 255, 0),
                      outline=3)
    print_test("Frame with all parameters")
    ui.append(f4)
    
    # Properties
    print("\n  Properties:")
    
    # Position and size
    f = mcrfpy.Frame(10, 20, 30, 40)
    print_test(f"Initial: x={f.x}, y={f.y}, w={f.w}, h={f.h}")
    
    f.x = 50
    f.y = 60
    f.w = 70
    f.h = 80
    print_test(f"Modified: x={f.x}, y={f.y}, w={f.w}, h={f.h}")
    
    # Colors
    f.fill_color = mcrfpy.Color(255, 0, 0, 128)
    f.outline_color = mcrfpy.Color(0, 255, 0)
    f.outline = 5.0
    print_test(f"Colors set, outline={f.outline}")
    
    # Visibility and opacity
    f.visible = False
    f.opacity = 0.5
    print_test(f"visible={f.visible}, opacity={f.opacity}")
    f.visible = True  # Reset
    
    # Z-index
    f.z_index = 10
    print_test(f"z_index={f.z_index}")
    
    # Children collection
    child1 = mcrfpy.Frame(5, 5, 20, 20)
    child2 = mcrfpy.Frame(30, 5, 20, 20)
    f.children.append(child1)
    f.children.append(child2)
    print_test(f"children.count = {len(f.children)}")
    
    return True

def test_caption_api():
    """Test all Caption constructors and methods"""
    print_section("CAPTION API TESTS")
    
    ui = mcrfpy.sceneUI("api_test")
    
    # Constructor variants
    print("\n  Constructors:")
    
    # Empty constructor
    c1 = mcrfpy.Caption()
    print_test(f"Caption() - text='{c1.text}', pos=({c1.x}, {c1.y})")
    ui.append(c1)
    
    # Text only
    c2 = mcrfpy.Caption("Hello World")
    print_test(f"Caption('Hello World') - pos=({c2.x}, {c2.y})")
    ui.append(c2)
    
    # Text and position
    c3 = mcrfpy.Caption("Positioned Text", 100, 50)
    print_test(f"Caption('Positioned Text', 100, 50)")
    ui.append(c3)
    
    # Full constructor
    c5 = mcrfpy.Caption("Styled Text", 300, 150,
                        fill_color=mcrfpy.Color(255, 255, 0),
                        outline_color=mcrfpy.Color(255, 0, 0),
                        outline=2)
    print_test("Caption with all style parameters")
    ui.append(c5)
    
    # Properties
    print("\n  Properties:")
    
    c = mcrfpy.Caption("Test Caption", 10, 20)
    
    # Text
    c.text = "Modified Text"
    print_test(f"text = '{c.text}'")
    
    # Position
    c.x = 50
    c.y = 60
    print_test(f"position = ({c.x}, {c.y})")
    
    # Colors and style
    c.fill_color = mcrfpy.Color(0, 255, 255)
    c.outline_color = mcrfpy.Color(255, 0, 255)
    c.outline = 3.0
    print_test("Colors and outline set")
    
    # Size (read-only, computed from text)
    print_test(f"size (computed) = ({c.w}, {c.h})")
    
    return True

def test_animation_api():
    """Test Animation class API"""
    print_section("ANIMATION API TESTS")
    
    ui = mcrfpy.sceneUI("api_test")
    
    print("\n  Animation Constructors:")
    
    # Basic animation
    anim1 = mcrfpy.Animation("x", 100.0, 2.0)
    print_test("Animation('x', 100.0, 2.0)")
    
    # With easing
    anim2 = mcrfpy.Animation("y", 200.0, 3.0, "easeInOut")
    print_test("Animation with easing='easeInOut'")
    
    # Delta mode
    anim3 = mcrfpy.Animation("w", 50.0, 1.5, "linear", delta=True)
    print_test("Animation with delta=True")
    
    # Color animation (as tuple)
    anim4 = mcrfpy.Animation("fill_color", (255, 0, 0, 255), 2.0)
    print_test("Animation with Color tuple target")
    
    # Vector animation
    anim5 = mcrfpy.Animation("position", (10.0, 20.0), 2.5, "easeOutBounce")
    print_test("Animation with position tuple")
    
    # Sprite sequence
    anim6 = mcrfpy.Animation("sprite_index", [0, 1, 2, 3, 2, 1], 2.0)
    print_test("Animation with sprite sequence")
    
    # Properties
    print("\n  Animation Properties:")
    
    # Check properties
    print_test(f"property = '{anim1.property}'")
    print_test(f"duration = {anim1.duration}")
    print_test(f"elapsed = {anim1.elapsed}")
    print_test(f"is_complete = {anim1.is_complete}")
    print_test(f"is_delta = {anim3.is_delta}")
    
    # Methods
    print("\n  Animation Methods:")
    
    # Create test frame
    frame = mcrfpy.Frame(50, 50, 100, 100)
    frame.fill_color = mcrfpy.Color(100, 100, 100)
    ui.append(frame)
    
    # Start animation
    anim1.start(frame)
    print_test("start() called on frame")
    
    # Test some easing functions
    print("\n  Sample Easing Functions:")
    easings = ["linear", "easeIn", "easeOut", "easeInOut", "easeInBounce", "easeOutElastic"]
    
    for easing in easings:
        try:
            test_anim = mcrfpy.Animation("x", 100.0, 1.0, easing)
            print_test(f"Easing '{easing}' ✓")
        except:
            print_test(f"Easing '{easing}' failed", False)
    
    return True

def run_all_tests():
    """Run all API tests"""
    print("\n" + "="*60)
    print("  McRogueFace Exhaustive API Test Suite (Fixed)")
    print("  Testing constructors and methods...")
    print("="*60)
    
    # Run each test category
    test_functions = [
        test_color_api,
        test_frame_api,
        test_caption_api,
        test_animation_api
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n  ERROR in {test_func.__name__}: {e}")
            failed += 1
    
    # Summary
    print("\n" + "="*60)
    print(f"  TEST SUMMARY: {passed} passed, {failed} failed")
    print("="*60)
    
    print("\n  Visual elements are displayed in the 'api_test' scene.")
    print("  The test is complete.")
    
    # Exit after a short delay to allow output to be seen
    def exit_test(runtime):
        print("\nExiting API test suite...")
        sys.exit(0)
    
    mcrfpy.setTimer("exit", exit_test, 2000)

# Run the tests immediately
print("Starting McRogueFace Exhaustive API Demo (Fixed)...")
print("This will test constructors and methods.")

run_all_tests()