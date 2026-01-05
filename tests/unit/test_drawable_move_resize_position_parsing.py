"""Test that Drawable.move() and Drawable.resize() accept flexible position arguments."""
import mcrfpy
import sys

def run_tests():
    """Test the new position parsing for move() and resize()."""
    errors = []
    
    # Create a test scene
    scene = mcrfpy.Scene("test_drawable_methods")
    
    # Create a Frame to test with (since Drawable is abstract)
    frame = mcrfpy.Frame(pos=(100, 100), size=(50, 50))
    scene.children.append(frame)
    
    # Test 1: move() with two separate arguments (original behavior)
    try:
        frame.x = 100
        frame.y = 100
        frame.move(10, 20)
        if not (frame.x == 110 and frame.y == 120):
            errors.append(f"move(10, 20) failed: got ({frame.x}, {frame.y}), expected (110, 120)")
        else:
            print("PASS: move(dx, dy) with two arguments works")
    except Exception as e:
        errors.append(f"move(10, 20) raised: {e}")
    
    # Test 2: move() with a tuple
    try:
        frame.x = 100
        frame.y = 100
        frame.move((15, 25))
        if not (frame.x == 115 and frame.y == 125):
            errors.append(f"move((15, 25)) failed: got ({frame.x}, {frame.y}), expected (115, 125)")
        else:
            print("PASS: move((dx, dy)) with tuple works")
    except Exception as e:
        errors.append(f"move((15, 25)) raised: {e}")
    
    # Test 3: move() with a list
    try:
        frame.x = 100
        frame.y = 100
        frame.move([5, 10])
        if not (frame.x == 105 and frame.y == 110):
            errors.append(f"move([5, 10]) failed: got ({frame.x}, {frame.y}), expected (105, 110)")
        else:
            print("PASS: move([dx, dy]) with list works")
    except Exception as e:
        errors.append(f"move([5, 10]) raised: {e}")
    
    # Test 4: move() with a Vector
    try:
        frame.x = 100
        frame.y = 100
        vec = mcrfpy.Vector(12, 18)
        frame.move(vec)
        if not (frame.x == 112 and frame.y == 118):
            errors.append(f"move(Vector(12, 18)) failed: got ({frame.x}, {frame.y}), expected (112, 118)")
        else:
            print("PASS: move(Vector) works")
    except Exception as e:
        errors.append(f"move(Vector) raised: {e}")
    
    # Test 5: resize() with two separate arguments (original behavior)
    try:
        frame.resize(200, 150)
        if not (frame.w == 200 and frame.h == 150):
            errors.append(f"resize(200, 150) failed: got ({frame.w}, {frame.h}), expected (200, 150)")
        else:
            print("PASS: resize(w, h) with two arguments works")
    except Exception as e:
        errors.append(f"resize(200, 150) raised: {e}")
    
    # Test 6: resize() with a tuple
    try:
        frame.resize((180, 120))
        if not (frame.w == 180 and frame.h == 120):
            errors.append(f"resize((180, 120)) failed: got ({frame.w}, {frame.h}), expected (180, 120)")
        else:
            print("PASS: resize((w, h)) with tuple works")
    except Exception as e:
        errors.append(f"resize((180, 120)) raised: {e}")
    
    # Test 7: resize() with a list
    try:
        frame.resize([100, 80])
        if not (frame.w == 100 and frame.h == 80):
            errors.append(f"resize([100, 80]) failed: got ({frame.w}, {frame.h}), expected (100, 80)")
        else:
            print("PASS: resize([w, h]) with list works")
    except Exception as e:
        errors.append(f"resize([100, 80]) raised: {e}")
    
    # Test 8: resize() with a Vector
    try:
        vec = mcrfpy.Vector(250, 200)
        frame.resize(vec)
        if not (frame.w == 250 and frame.h == 200):
            errors.append(f"resize(Vector(250, 200)) failed: got ({frame.w}, {frame.h}), expected (250, 200)")
        else:
            print("PASS: resize(Vector) works")
    except Exception as e:
        errors.append(f"resize(Vector) raised: {e}")
    
    # Test 9: move() with keyword argument pos
    try:
        frame.x = 100
        frame.y = 100
        frame.move(pos=(7, 13))
        if not (frame.x == 107 and frame.y == 113):
            errors.append(f"move(pos=(7, 13)) failed: got ({frame.x}, {frame.y}), expected (107, 113)")
        else:
            print("PASS: move(pos=(dx, dy)) with keyword works")
    except Exception as e:
        errors.append(f"move(pos=(7, 13)) raised: {e}")
    
    # Summary
    if errors:
        print("\nFAILURES:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("\nAll tests passed!")
        sys.exit(0)

# Run tests
run_tests()
