#!/usr/bin/env python3
"""Audit current constructor argument handling for all UI classes"""

import mcrfpy
import sys

def audit_constructors():
    """Test current state of all UI constructors"""
    
    print("=== CONSTRUCTOR AUDIT ===\n")
    
    # Create test scene and texture
    mcrfpy.createScene("audit")
    texture = mcrfpy.Texture("assets/test_portraits.png", 32, 32)
    
    # Test Frame
    print("1. Frame Constructor Tests:")
    print("-" * 40)
    
    # No args
    try:
        f = mcrfpy.Frame()
        print("✓ Frame() - works")
    except Exception as e:
        print(f"✗ Frame() - {e}")
    
    # Traditional 4 args (x, y, w, h)
    try:
        f = mcrfpy.Frame(10, 20, 100, 50)
        print("✓ Frame(10, 20, 100, 50) - works")
    except Exception as e:
        print(f"✗ Frame(10, 20, 100, 50) - {e}")
    
    # Tuple pos + size
    try:
        f = mcrfpy.Frame((10, 20), (100, 50))
        print("✓ Frame((10, 20), (100, 50)) - works")
    except Exception as e:
        print(f"✗ Frame((10, 20), (100, 50)) - {e}")
    
    # Keywords
    try:
        f = mcrfpy.Frame(pos=(10, 20), size=(100, 50))
        print("✓ Frame(pos=(10, 20), size=(100, 50)) - works")
    except Exception as e:
        print(f"✗ Frame(pos=(10, 20), size=(100, 50)) - {e}")
    
    # Test Grid
    print("\n2. Grid Constructor Tests:")
    print("-" * 40)
    
    # No args
    try:
        g = mcrfpy.Grid()
        print("✓ Grid() - works")
    except Exception as e:
        print(f"✗ Grid() - {e}")
    
    # Grid size only
    try:
        g = mcrfpy.Grid((10, 10))
        print("✓ Grid((10, 10)) - works")
    except Exception as e:
        print(f"✗ Grid((10, 10)) - {e}")
    
    # Grid size + texture
    try:
        g = mcrfpy.Grid((10, 10), texture)
        print("✓ Grid((10, 10), texture) - works")
    except Exception as e:
        print(f"✗ Grid((10, 10), texture) - {e}")
    
    # Full positional (expected: pos, size, grid_size, texture)
    try:
        g = mcrfpy.Grid((0, 0), (320, 320), (10, 10), texture)
        print("✓ Grid((0, 0), (320, 320), (10, 10), texture) - works")
    except Exception as e:
        print(f"✗ Grid((0, 0), (320, 320), (10, 10), texture) - {e}")
    
    # Keywords
    try:
        g = mcrfpy.Grid(pos=(0, 0), size=(320, 320), grid_size=(10, 10), texture=texture)
        print("✓ Grid(pos=..., size=..., grid_size=..., texture=...) - works")
    except Exception as e:
        print(f"✗ Grid(pos=..., size=..., grid_size=..., texture=...) - {e}")
    
    # Test Sprite
    print("\n3. Sprite Constructor Tests:")
    print("-" * 40)
    
    # No args
    try:
        s = mcrfpy.Sprite()
        print("✓ Sprite() - works")
    except Exception as e:
        print(f"✗ Sprite() - {e}")
    
    # Position only
    try:
        s = mcrfpy.Sprite((10, 20))
        print("✓ Sprite((10, 20)) - works")
    except Exception as e:
        print(f"✗ Sprite((10, 20)) - {e}")
    
    # Position + texture
    try:
        s = mcrfpy.Sprite((10, 20), texture)
        print("✓ Sprite((10, 20), texture) - works")
    except Exception as e:
        print(f"✗ Sprite((10, 20), texture) - {e}")
    
    # Position + texture + sprite_index
    try:
        s = mcrfpy.Sprite((10, 20), texture, 5)
        print("✓ Sprite((10, 20), texture, 5) - works")
    except Exception as e:
        print(f"✗ Sprite((10, 20), texture, 5) - {e}")
    
    # Keywords
    try:
        s = mcrfpy.Sprite(pos=(10, 20), texture=texture, sprite_index=5)
        print("✓ Sprite(pos=..., texture=..., sprite_index=...) - works")
    except Exception as e:
        print(f"✗ Sprite(pos=..., texture=..., sprite_index=...) - {e}")
    
    # Test Caption
    print("\n4. Caption Constructor Tests:")
    print("-" * 40)
    
    # No args
    try:
        c = mcrfpy.Caption()
        print("✓ Caption() - works")
    except Exception as e:
        print(f"✗ Caption() - {e}")
    
    # Text only
    try:
        c = mcrfpy.Caption("Hello")
        print("✓ Caption('Hello') - works")
    except Exception as e:
        print(f"✗ Caption('Hello') - {e}")
    
    # Position + text (expected order: pos, font, text)
    try:
        c = mcrfpy.Caption((10, 20), "Hello")
        print("✓ Caption((10, 20), 'Hello') - works")
    except Exception as e:
        print(f"✗ Caption((10, 20), 'Hello') - {e}")
    
    # Position + font + text
    try:
        c = mcrfpy.Caption((10, 20), 16, "Hello")
        print("✓ Caption((10, 20), 16, 'Hello') - works")
    except Exception as e:
        print(f"✗ Caption((10, 20), 16, 'Hello') - {e}")
    
    # Keywords
    try:
        c = mcrfpy.Caption(pos=(10, 20), font=16, text="Hello")
        print("✓ Caption(pos=..., font=..., text=...) - works")
    except Exception as e:
        print(f"✗ Caption(pos=..., font=..., text=...) - {e}")
    
    # Test Entity
    print("\n5. Entity Constructor Tests:")
    print("-" * 40)
    
    # No args
    try:
        e = mcrfpy.Entity()
        print("✓ Entity() - works")
    except Exception as e:
        print(f"✗ Entity() - {e}")
    
    # Grid position only
    try:
        e = mcrfpy.Entity((5.0, 6.0))
        print("✓ Entity((5.0, 6.0)) - works")
    except Exception as e:
        print(f"✗ Entity((5.0, 6.0)) - {e}")
    
    # Grid position + texture
    try:
        e = mcrfpy.Entity((5.0, 6.0), texture)
        print("✓ Entity((5.0, 6.0), texture) - works")
    except Exception as e:
        print(f"✗ Entity((5.0, 6.0), texture) - {e}")
    
    # Grid position + texture + sprite_index
    try:
        e = mcrfpy.Entity((5.0, 6.0), texture, 3)
        print("✓ Entity((5.0, 6.0), texture, 3) - works")
    except Exception as e:
        print(f"✗ Entity((5.0, 6.0), texture, 3) - {e}")
    
    # Keywords
    try:
        e = mcrfpy.Entity(grid_pos=(5.0, 6.0), texture=texture, sprite_index=3)
        print("✓ Entity(grid_pos=..., texture=..., sprite_index=...) - works")
    except Exception as e:
        print(f"✗ Entity(grid_pos=..., texture=..., sprite_index=...) - {e}")
    
    print("\n=== AUDIT COMPLETE ===")

# Run audit
try:
    audit_constructors()
    print("\nPASS")
    sys.exit(0)
except Exception as e:
    print(f"\nFAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)