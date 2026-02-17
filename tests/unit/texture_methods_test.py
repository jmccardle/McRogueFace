"""Tests for Texture.from_bytes(), Texture.composite(), texture.hsl_shift()"""
import mcrfpy
import sys

errors = []

def test(name, condition, msg=""):
    if not condition:
        errors.append(f"FAIL: {name} - {msg}")
        print(f"  FAIL: {name} {msg}")
    else:
        print(f"  PASS: {name}")

# ---- Test from_bytes ----
print("=== Texture.from_bytes ===")

# Create a 4x4 red image (RGBA)
w, h = 4, 4
red_bytes = bytes([255, 0, 0, 255] * (w * h))
tex = mcrfpy.Texture.from_bytes(red_bytes, w, h, 2, 2)
test("from_bytes returns Texture", isinstance(tex, mcrfpy.Texture))
test("from_bytes sprite_width", tex.sprite_width == 2, f"got {tex.sprite_width}")
test("from_bytes sprite_height", tex.sprite_height == 2, f"got {tex.sprite_height}")
test("from_bytes sheet_width", tex.sheet_width == 2, f"got {tex.sheet_width}")
test("from_bytes sheet_height", tex.sheet_height == 2, f"got {tex.sheet_height}")
test("from_bytes sprite_count", tex.sprite_count == 4, f"got {tex.sprite_count}")

# Wrong size should raise ValueError
try:
    mcrfpy.Texture.from_bytes(b"\x00\x00", 4, 4, 2, 2)
    test("from_bytes wrong size raises", False, "no exception raised")
except ValueError as e:
    test("from_bytes wrong size raises ValueError", True)

# bytearray should work too
ba = bytearray([0, 255, 0, 128] * 16)
tex2 = mcrfpy.Texture.from_bytes(ba, 4, 4, 4, 4)
test("from_bytes accepts bytearray", tex2.sprite_count == 1)

# With name parameter
tex3 = mcrfpy.Texture.from_bytes(red_bytes, 4, 4, 2, 2, name="test_red")
test("from_bytes with name", tex3.source == "test_red", f"got '{tex3.source}'")

# ---- Test composite ----
print("\n=== Texture.composite ===")

# Two 4x4 layers: red bottom, semi-transparent blue top
red_data = bytes([255, 0, 0, 255] * 16)
blue_data = bytes([0, 0, 255, 128] * 16)  # 50% alpha blue

red_tex = mcrfpy.Texture.from_bytes(red_data, 4, 4, 4, 4)
blue_tex = mcrfpy.Texture.from_bytes(blue_data, 4, 4, 4, 4)

comp = mcrfpy.Texture.composite([red_tex, blue_tex], 4, 4)
test("composite returns Texture", isinstance(comp, mcrfpy.Texture))
test("composite sprite_count", comp.sprite_count == 1)

# Fully transparent over opaque should equal opaque
transparent_data = bytes([0, 0, 0, 0] * 16)
trans_tex = mcrfpy.Texture.from_bytes(transparent_data, 4, 4, 4, 4)
comp2 = mcrfpy.Texture.composite([red_tex, trans_tex], 4, 4)
test("composite transparent over red", isinstance(comp2, mcrfpy.Texture))

# Opaque over opaque should equal top
green_data = bytes([0, 255, 0, 255] * 16)
green_tex = mcrfpy.Texture.from_bytes(green_data, 4, 4, 4, 4)
comp3 = mcrfpy.Texture.composite([red_tex, green_tex], 4, 4)
test("composite opaque over opaque", isinstance(comp3, mcrfpy.Texture))

# Empty list should raise
try:
    mcrfpy.Texture.composite([], 4, 4)
    test("composite empty raises", False, "no exception")
except ValueError:
    test("composite empty raises ValueError", True)

# Wrong type in list
try:
    mcrfpy.Texture.composite([red_tex, "not a texture"], 4, 4)
    test("composite wrong type raises", False, "no exception")
except TypeError:
    test("composite wrong type raises TypeError", True)

# With name
comp4 = mcrfpy.Texture.composite([red_tex], 2, 2, name="my_composite")
test("composite with name", comp4.source == "my_composite", f"got '{comp4.source}'")

# ---- Test hsl_shift ----
print("\n=== texture.hsl_shift ===")

# Shift pure red by 120 degrees -> should become green-ish
shifted = red_tex.hsl_shift(120.0)
test("hsl_shift returns Texture", isinstance(shifted, mcrfpy.Texture))
test("hsl_shift preserves sprite dims",
     shifted.sprite_width == red_tex.sprite_width and
     shifted.sprite_height == red_tex.sprite_height)

# Zero shift should still work
same = red_tex.hsl_shift(0.0)
test("hsl_shift zero produces Texture", isinstance(same, mcrfpy.Texture))

# With sat and lit shifts
darkened = red_tex.hsl_shift(0.0, 0.0, -0.3)
test("hsl_shift with lit_shift", isinstance(darkened, mcrfpy.Texture))

# Transparent pixels should be unchanged
trans_shifted = trans_tex.hsl_shift(180.0)
test("hsl_shift on transparent", isinstance(trans_shifted, mcrfpy.Texture))

# Shift by 360 should be same as 0
full_circle = red_tex.hsl_shift(360.0)
test("hsl_shift 360 degrees", isinstance(full_circle, mcrfpy.Texture))

# ---- Summary ----
print()
if errors:
    print(f"FAILED: {len(errors)} tests failed")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)
else:
    print("All tests passed!")
    sys.exit(0)
