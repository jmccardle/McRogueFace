#!/usr/bin/env python3
"""
Test #93: Vector arithmetic operations
"""

import mcrfpy
import sys
import math

def test_vector_arithmetic(runtime):
    """Test vector arithmetic operations"""
    
    all_pass = True
    
    # Test 1: Vector addition
    try:
        v1 = mcrfpy.Vector(3, 4)
        v2 = mcrfpy.Vector(1, 2)
        v3 = v1 + v2
        
        assert v3.x == 4 and v3.y == 6, f"Addition failed: {v3.x}, {v3.y}"
        print("+ Vector addition works correctly")
    except Exception as e:
        print(f"x Vector addition failed: {e}")
        all_pass = False
    
    # Test 2: Vector subtraction
    try:
        v1 = mcrfpy.Vector(5, 7)
        v2 = mcrfpy.Vector(2, 3)
        v3 = v1 - v2
        
        assert v3.x == 3 and v3.y == 4, f"Subtraction failed: {v3.x}, {v3.y}"
        print("+ Vector subtraction works correctly")
    except Exception as e:
        print(f"x Vector subtraction failed: {e}")
        all_pass = False
    
    # Test 3: Scalar multiplication
    try:
        v1 = mcrfpy.Vector(2, 3)
        v2 = v1 * 3
        v3 = 2 * v1  # Reverse multiplication
        
        assert v2.x == 6 and v2.y == 9, f"Scalar multiply failed: {v2.x}, {v2.y}"
        assert v3.x == 4 and v3.y == 6, f"Reverse multiply failed: {v3.x}, {v3.y}"
        print("+ Scalar multiplication works correctly")
    except Exception as e:
        print(f"x Scalar multiplication failed: {e}")
        all_pass = False
    
    # Test 4: Scalar division
    try:
        v1 = mcrfpy.Vector(10, 20)
        v2 = v1 / 5
        
        assert v2.x == 2 and v2.y == 4, f"Division failed: {v2.x}, {v2.y}"
        
        # Test division by zero
        try:
            v3 = v1 / 0
            print("x Division by zero should raise exception")
            all_pass = False
        except ZeroDivisionError:
            pass
        
        print("+ Scalar division works correctly")
    except Exception as e:
        print(f"x Scalar division failed: {e}")
        all_pass = False
    
    # Test 5: Negation
    try:
        v1 = mcrfpy.Vector(3, -4)
        v2 = -v1
        
        assert v2.x == -3 and v2.y == 4, f"Negation failed: {v2.x}, {v2.y}"
        print("+ Vector negation works correctly")
    except Exception as e:
        print(f"x Vector negation failed: {e}")
        all_pass = False
    
    # Test 6: Absolute value (magnitude)
    try:
        v1 = mcrfpy.Vector(3, 4)
        mag = abs(v1)
        
        assert abs(mag - 5.0) < 0.001, f"Absolute value failed: {mag}"
        print("+ Absolute value (magnitude) works correctly")
    except Exception as e:
        print(f"x Absolute value failed: {e}")
        all_pass = False
    
    # Test 7: Boolean check
    try:
        v1 = mcrfpy.Vector(0, 0)
        v2 = mcrfpy.Vector(1, 0)
        
        assert not bool(v1), "Zero vector should be False"
        assert bool(v2), "Non-zero vector should be True"
        print("+ Boolean check works correctly")
    except Exception as e:
        print(f"x Boolean check failed: {e}")
        all_pass = False
    
    # Test 8: Equality comparison
    try:
        v1 = mcrfpy.Vector(1.5, 2.5)
        v2 = mcrfpy.Vector(1.5, 2.5)
        v3 = mcrfpy.Vector(1.5, 2.6)
        
        assert v1 == v2, "Equal vectors should compare equal"
        assert v1 != v3, "Different vectors should not compare equal"
        print("+ Equality comparison works correctly")
    except Exception as e:
        print(f"x Equality comparison failed: {e}")
        all_pass = False
    
    # Test 9: magnitude() method
    try:
        v1 = mcrfpy.Vector(3, 4)
        mag = v1.magnitude()
        
        assert abs(mag - 5.0) < 0.001, f"magnitude() failed: {mag}"
        print("+ magnitude() method works correctly")
    except Exception as e:
        print(f"x magnitude() method failed: {e}")
        all_pass = False
    
    # Test 10: magnitude_squared() method
    try:
        v1 = mcrfpy.Vector(3, 4)
        mag_sq = v1.magnitude_squared()
        
        assert mag_sq == 25, f"magnitude_squared() failed: {mag_sq}"
        print("+ magnitude_squared() method works correctly")
    except Exception as e:
        print(f"x magnitude_squared() method failed: {e}")
        all_pass = False
    
    # Test 11: normalize() method
    try:
        v1 = mcrfpy.Vector(3, 4)
        v2 = v1.normalize()
        
        assert abs(v2.magnitude() - 1.0) < 0.001, f"normalize() magnitude failed: {v2.magnitude()}"
        assert abs(v2.x - 0.6) < 0.001, f"normalize() x failed: {v2.x}"
        assert abs(v2.y - 0.8) < 0.001, f"normalize() y failed: {v2.y}"
        
        # Test zero vector normalization
        v3 = mcrfpy.Vector(0, 0)
        v4 = v3.normalize()
        assert v4.x == 0 and v4.y == 0, "Zero vector normalize should remain zero"
        
        print("+ normalize() method works correctly")
    except Exception as e:
        print(f"x normalize() method failed: {e}")
        all_pass = False
    
    # Test 12: dot product
    try:
        v1 = mcrfpy.Vector(3, 4)
        v2 = mcrfpy.Vector(2, 1)
        dot = v1.dot(v2)
        
        assert dot == 10, f"dot product failed: {dot}"
        print("+ dot() method works correctly")
    except Exception as e:
        print(f"x dot() method failed: {e}")
        all_pass = False
    
    # Test 13: distance_to()
    try:
        v1 = mcrfpy.Vector(1, 1)
        v2 = mcrfpy.Vector(4, 5)
        dist = v1.distance_to(v2)
        
        assert abs(dist - 5.0) < 0.001, f"distance_to() failed: {dist}"
        print("+ distance_to() method works correctly")
    except Exception as e:
        print(f"x distance_to() method failed: {e}")
        all_pass = False
    
    # Test 14: angle()
    try:
        v1 = mcrfpy.Vector(1, 0)  # Points right
        v2 = mcrfpy.Vector(0, 1)  # Points up
        v3 = mcrfpy.Vector(-1, 0) # Points left
        v4 = mcrfpy.Vector(1, 1)  # 45 degrees
        
        a1 = v1.angle()
        a2 = v2.angle()
        a3 = v3.angle()
        a4 = v4.angle()
        
        assert abs(a1 - 0) < 0.001, f"Right angle failed: {a1}"
        assert abs(a2 - math.pi/2) < 0.001, f"Up angle failed: {a2}"
        assert abs(a3 - math.pi) < 0.001, f"Left angle failed: {a3}"
        assert abs(a4 - math.pi/4) < 0.001, f"45deg angle failed: {a4}"
        
        print("+ angle() method works correctly")
    except Exception as e:
        print(f"x angle() method failed: {e}")
        all_pass = False
    
    # Test 15: copy()
    try:
        v1 = mcrfpy.Vector(5, 10)
        v2 = v1.copy()
        
        assert v2.x == 5 and v2.y == 10, f"copy() values failed: {v2.x}, {v2.y}"
        
        # Modify v2 and ensure v1 is unchanged
        v2.x = 20
        assert v1.x == 5, "copy() should create independent object"
        
        print("+ copy() method works correctly")
    except Exception as e:
        print(f"x copy() method failed: {e}")
        all_pass = False
    
    # Test 16: Operations with invalid types
    try:
        v1 = mcrfpy.Vector(1, 2)
        
        # These should return NotImplemented
        result = v1 + "string"
        assert result is NotImplemented, "Invalid addition should return NotImplemented"
        
        result = v1 * [1, 2]
        assert result is NotImplemented, "Invalid multiplication should return NotImplemented"
        
        print("+ Type checking works correctly")
    except Exception as e:
        # Expected to fail with TypeError
        if "unsupported operand type" in str(e):
            print("+ Type checking works correctly")
        else:
            print(f"x Type checking failed: {e}")
            all_pass = False
    
    print(f"\n{'PASS' if all_pass else 'FAIL'}")
    sys.exit(0 if all_pass else 1)

# Run test
test = mcrfpy.Scene("test")
mcrfpy.setTimer("test", test_vector_arithmetic, 100)