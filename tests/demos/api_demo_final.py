#!/usr/bin/env python3
"""
McRogueFace API Demo - Final Version
====================================

Complete API demonstration with proper error handling.
Tests all constructors and methods systematically.
"""

import mcrfpy
import sys

def print_section(title):
    """Print a section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_test(name, success=True):
    """Print test result"""
    status = "✓" if success else "✗"
    print(f"  {status} {name}")

def test_colors():
    """Test Color API"""
    print_section("COLOR TESTS")
    
    try:
        # Basic constructors
        c1 = mcrfpy.Color(255, 0, 0)  # RGB
        print_test(f"Color(255,0,0) = ({c1.r},{c1.g},{c1.b},{c1.a})")
        
        c2 = mcrfpy.Color(100, 150, 200, 128)  # RGBA
        print_test(f"Color(100,150,200,128) = ({c2.r},{c2.g},{c2.b},{c2.a})")
        
        # Property modification
        c1.r = 128
        c1.g = 128
        c1.b = 128
        c1.a = 200
        print_test(f"Modified color = ({c1.r},{c1.g},{c1.b},{c1.a})")
        
    except Exception as e:
        print_test(f"Color test failed: {e}", False)

def test_frames():
    """Test Frame API"""
    print_section("FRAME TESTS")
    
    # Create scene
    mcrfpy.createScene("test")
    mcrfpy.setScene("test")
    ui = mcrfpy.sceneUI("test")
    
    try:
        # Constructors
        f1 = mcrfpy.Frame()
        print_test(f"Frame() at ({f1.x},{f1.y}) size ({f1.w},{f1.h})")
        
        f2 = mcrfpy.Frame(100, 50)
        print_test(f"Frame(100,50) at ({f2.x},{f2.y})")
        
        f3 = mcrfpy.Frame(200, 100, 150, 75)
        print_test(f"Frame(200,100,150,75) size ({f3.w},{f3.h})")
        
        # Properties
        f3.fill_color = mcrfpy.Color(100, 100, 200)
        f3.outline = 3
        f3.outline_color = mcrfpy.Color(255, 255, 0)
        f3.opacity = 0.8
        f3.visible = True
        f3.z_index = 5
        print_test(f"Frame properties set")
        
        # Add to scene
        ui.append(f3)
        print_test(f"Frame added to scene")
        
        # Children
        child = mcrfpy.Frame(10, 10, 50, 50)
        f3.children.append(child)
        print_test(f"Child added, count = {len(f3.children)}")
        
    except Exception as e:
        print_test(f"Frame test failed: {e}", False)

def test_captions():
    """Test Caption API"""
    print_section("CAPTION TESTS")
    
    ui = mcrfpy.sceneUI("test")
    
    try:
        # Constructors
        c1 = mcrfpy.Caption()
        print_test(f"Caption() text='{c1.text}'")
        
        c2 = mcrfpy.Caption("Hello World")
        print_test(f"Caption('Hello World') at ({c2.x},{c2.y})")
        
        c3 = mcrfpy.Caption("Test", 300, 200)
        print_test(f"Caption with position at ({c3.x},{c3.y})")
        
        # Properties
        c3.text = "Modified"
        c3.fill_color = mcrfpy.Color(255, 255, 0)
        c3.outline = 2
        c3.outline_color = mcrfpy.Color(0, 0, 0)
        print_test(f"Caption text='{c3.text}'")
        
        ui.append(c3)
        print_test("Caption added to scene")
        
    except Exception as e:
        print_test(f"Caption test failed: {e}", False)

def test_animations():
    """Test Animation API"""
    print_section("ANIMATION TESTS")
    
    ui = mcrfpy.sceneUI("test")
    
    try:
        # Create target
        frame = mcrfpy.Frame(50, 50, 100, 100)
        frame.fill_color = mcrfpy.Color(100, 100, 100)
        ui.append(frame)
        
        # Basic animations
        a1 = mcrfpy.Animation("x", 300.0, 2.0)
        print_test("Animation created (position)")
        
        a2 = mcrfpy.Animation("opacity", 0.5, 1.5, "easeInOut")
        print_test("Animation with easing")
        
        a3 = mcrfpy.Animation("fill_color", (255, 0, 0, 255), 2.0)
        print_test("Color animation (tuple)")
        
        # Start animations
        a1.start(frame)
        a2.start(frame)
        a3.start(frame)
        print_test("Animations started")
        
        # Check properties
        print_test(f"Duration = {a1.duration}")
        print_test(f"Elapsed = {a1.elapsed}")
        print_test(f"Complete = {a1.is_complete}")
        
    except Exception as e:
        print_test(f"Animation test failed: {e}", False)

def test_collections():
    """Test collection operations"""
    print_section("COLLECTION TESTS")
    
    ui = mcrfpy.sceneUI("test")
    
    try:
        # Clear scene
        while len(ui) > 0:
            ui.remove(ui[len(ui)-1])
        print_test(f"Scene cleared, length = {len(ui)}")
        
        # Add items
        for i in range(5):
            f = mcrfpy.Frame(i*100, 50, 80, 80)
            ui.append(f)
        print_test(f"Added 5 frames, length = {len(ui)}")
        
        # Access
        first = ui[0]
        print_test(f"Accessed ui[0] at ({first.x},{first.y})")
        
        # Iteration
        count = sum(1 for _ in ui)
        print_test(f"Iteration count = {count}")
        
    except Exception as e:
        print_test(f"Collection test failed: {e}", False)

def run_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("  McRogueFace API Test Suite")
    print("="*60)
    
    test_colors()
    test_frames()
    test_captions()
    test_animations()
    test_collections()
    
    print("\n" + "="*60)
    print("  Tests Complete")
    print("="*60)
    
    # Exit after delay
    def exit_program(runtime):
        print("\nExiting...")
        sys.exit(0)
    
    mcrfpy.setTimer("exit", exit_program, 3000)

# Run tests
print("Starting API tests...")
run_tests()