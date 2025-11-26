#!/usr/bin/env python3
"""
Test #94: Color helper methods - from_hex, to_hex, lerp
"""

import mcrfpy
import sys

def test_color_helpers(runtime):
    """Test Color helper methods"""
    
    all_pass = True
    
    # Test 1: from_hex with # prefix
    try:
        c1 = mcrfpy.Color.from_hex("#FF0000")
        assert c1.r == 255 and c1.g == 0 and c1.b == 0 and c1.a == 255, f"from_hex('#FF0000') failed: {c1}"
        print("+ Color.from_hex('#FF0000') works")
    except Exception as e:
        print(f"x Color.from_hex('#FF0000') failed: {e}")
        all_pass = False
    
    # Test 2: from_hex without # prefix
    try:
        c2 = mcrfpy.Color.from_hex("00FF00")
        assert c2.r == 0 and c2.g == 255 and c2.b == 0 and c2.a == 255, f"from_hex('00FF00') failed: {c2}"
        print("+ Color.from_hex('00FF00') works")
    except Exception as e:
        print(f"x Color.from_hex('00FF00') failed: {e}")
        all_pass = False
    
    # Test 3: from_hex with alpha
    try:
        c3 = mcrfpy.Color.from_hex("#0000FF80")
        assert c3.r == 0 and c3.g == 0 and c3.b == 255 and c3.a == 128, f"from_hex('#0000FF80') failed: {c3}"
        print("+ Color.from_hex('#0000FF80') with alpha works")
    except Exception as e:
        print(f"x Color.from_hex('#0000FF80') failed: {e}")
        all_pass = False
    
    # Test 4: from_hex error handling
    try:
        c4 = mcrfpy.Color.from_hex("GGGGGG")
        print("x from_hex should fail on invalid hex")
        all_pass = False
    except ValueError as e:
        print("+ Color.from_hex() correctly rejects invalid hex")
    
    # Test 5: from_hex wrong length
    try:
        c5 = mcrfpy.Color.from_hex("FF00")
        print("x from_hex should fail on wrong length")
        all_pass = False
    except ValueError as e:
        print("+ Color.from_hex() correctly rejects wrong length")
    
    # Test 6: to_hex without alpha
    try:
        c6 = mcrfpy.Color(255, 128, 64)
        hex_str = c6.to_hex()
        assert hex_str == "#FF8040", f"to_hex() failed: {hex_str}"
        print("+ Color.to_hex() works")
    except Exception as e:
        print(f"x Color.to_hex() failed: {e}")
        all_pass = False
    
    # Test 7: to_hex with alpha
    try:
        c7 = mcrfpy.Color(255, 128, 64, 127)
        hex_str = c7.to_hex()
        assert hex_str == "#FF80407F", f"to_hex() with alpha failed: {hex_str}"
        print("+ Color.to_hex() with alpha works")
    except Exception as e:
        print(f"x Color.to_hex() with alpha failed: {e}")
        all_pass = False
    
    # Test 8: Round-trip hex conversion
    try:
        original_hex = "#ABCDEF"
        c8 = mcrfpy.Color.from_hex(original_hex)
        result_hex = c8.to_hex()
        assert result_hex == original_hex, f"Round-trip failed: {original_hex} -> {result_hex}"
        print("+ Hex round-trip conversion works")
    except Exception as e:
        print(f"x Hex round-trip failed: {e}")
        all_pass = False
    
    # Test 9: lerp at t=0
    try:
        red = mcrfpy.Color(255, 0, 0)
        blue = mcrfpy.Color(0, 0, 255)
        result = red.lerp(blue, 0.0)
        assert result.r == 255 and result.g == 0 and result.b == 0, f"lerp(t=0) failed: {result}"
        print("+ Color.lerp(t=0) returns start color")
    except Exception as e:
        print(f"x Color.lerp(t=0) failed: {e}")
        all_pass = False
    
    # Test 10: lerp at t=1
    try:
        red = mcrfpy.Color(255, 0, 0)
        blue = mcrfpy.Color(0, 0, 255)
        result = red.lerp(blue, 1.0)
        assert result.r == 0 and result.g == 0 and result.b == 255, f"lerp(t=1) failed: {result}"
        print("+ Color.lerp(t=1) returns end color")
    except Exception as e:
        print(f"x Color.lerp(t=1) failed: {e}")
        all_pass = False
    
    # Test 11: lerp at t=0.5
    try:
        red = mcrfpy.Color(255, 0, 0)
        blue = mcrfpy.Color(0, 0, 255)
        result = red.lerp(blue, 0.5)
        # Expect roughly (127, 0, 127)
        assert 126 <= result.r <= 128 and result.g == 0 and 126 <= result.b <= 128, f"lerp(t=0.5) failed: {result}"
        print("+ Color.lerp(t=0.5) returns midpoint")
    except Exception as e:
        print(f"x Color.lerp(t=0.5) failed: {e}")
        all_pass = False
    
    # Test 12: lerp with alpha
    try:
        c1 = mcrfpy.Color(255, 0, 0, 255)
        c2 = mcrfpy.Color(0, 255, 0, 0)
        result = c1.lerp(c2, 0.5)
        assert 126 <= result.r <= 128 and 126 <= result.g <= 128 and result.b == 0, f"lerp color components failed"
        assert 126 <= result.a <= 128, f"lerp alpha failed: {result.a}"
        print("+ Color.lerp() with alpha works")
    except Exception as e:
        print(f"x Color.lerp() with alpha failed: {e}")
        all_pass = False
    
    # Test 13: lerp clamps t < 0
    try:
        red = mcrfpy.Color(255, 0, 0)
        blue = mcrfpy.Color(0, 0, 255)
        result = red.lerp(blue, -0.5)
        assert result.r == 255 and result.g == 0 and result.b == 0, f"lerp(t<0) should clamp to 0"
        print("+ Color.lerp() clamps t < 0")
    except Exception as e:
        print(f"x Color.lerp(t<0) failed: {e}")
        all_pass = False
    
    # Test 14: lerp clamps t > 1
    try:
        red = mcrfpy.Color(255, 0, 0)
        blue = mcrfpy.Color(0, 0, 255)
        result = red.lerp(blue, 1.5)
        assert result.r == 0 and result.g == 0 and result.b == 255, f"lerp(t>1) should clamp to 1"
        print("+ Color.lerp() clamps t > 1")
    except Exception as e:
        print(f"x Color.lerp(t>1) failed: {e}")
        all_pass = False
    
    # Test 15: Practical use case - gradient
    try:
        start = mcrfpy.Color.from_hex("#FF0000")  # Red
        end = mcrfpy.Color.from_hex("#0000FF")    # Blue
        
        # Create 5-step gradient
        steps = []
        for i in range(5):
            t = i / 4.0
            color = start.lerp(end, t)
            steps.append(color.to_hex())
        
        assert steps[0] == "#FF0000", "Gradient start should be red"
        assert steps[4] == "#0000FF", "Gradient end should be blue"
        assert len(set(steps)) == 5, "All gradient steps should be unique"
        
        print("+ Gradient generation works correctly")
    except Exception as e:
        print(f"x Gradient generation failed: {e}")
        all_pass = False
    
    print(f"\n{'PASS' if all_pass else 'FAIL'}")
    sys.exit(0 if all_pass else 1)

# Run test
mcrfpy.createScene("test")
mcrfpy.setTimer("test", test_color_helpers, 100)