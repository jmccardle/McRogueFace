"""#514: texture factories raise instead of returning an empty Texture."""
import sys
import mcrfpy

def expect(exc, fn, needle):
    try:
        fn()
    except exc as e:
        assert needle in str(e), "%r lacks %r" % (str(e), needle)
        return
    raise AssertionError("no %s raised" % exc.__name__)

# Over the GPU's maximum texture size: ValueError naming the limit.
expect(ValueError, lambda: mcrfpy.Texture.from_bytes(bytes(4 * 100000), 100000, 1, 1, 1), "maximum texture size")

# Bad sprite sizes: ValueError, no division by zero.
px = bytes(4 * 16 * 16)
expect(ValueError, lambda: mcrfpy.Texture.from_bytes(px, 16, 16, 0, 16), "sprite size")
expect(ValueError, lambda: mcrfpy.Texture.from_bytes(px, 16, 16, 16, 32), "sprite size")

ok = mcrfpy.Texture.from_bytes(px, 16, 16, 8, 8)
assert ok.sprite_count == 4
expect(ValueError, lambda: mcrfpy.Texture.composite([ok], 0, 8), "sprite size")
print("PASS")
sys.exit(0)
