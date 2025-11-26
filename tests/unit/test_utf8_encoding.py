#!/usr/bin/env python3
"""
Test UTF-8 encoding support
"""

import mcrfpy
import sys

def test_utf8(runtime):
    """Test UTF-8 encoding in print statements"""
    
    # Test various unicode characters
    print("✓ Check mark works")
    print("✗ Cross mark works")
    print("🎮 Emoji works")
    print("日本語 Japanese works")
    print("Ñoño Spanish works")
    print("Привет Russian works")
    
    # Test in f-strings
    count = 5
    print(f"✓ Added {count} items")
    
    # Test unicode in error messages
    try:
        raise ValueError("❌ Error with unicode")
    except ValueError as e:
        print(f"✓ Exception handling works: {e}")
    
    print("\n✅ All UTF-8 tests passed!")
    sys.exit(0)

# Run test
mcrfpy.createScene("test")
mcrfpy.setTimer("test", test_utf8, 100)