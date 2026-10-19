"""#521: TileLayer rejects tile indices that are not -1 or a cell of the texture."""
import sys
import mcrfpy


def fail(msg):
    print("FAIL", msg)
    sys.exit(1)


def raises(fn, needles, label):
    try:
        fn()
    except ValueError as e:
        for n in needles:
            if n not in str(e):
                fail("%s: message %r lacks %r" % (label, str(e), n))
        return
    except Exception as e:
        fail("%s: wrong exception %s: %s" % (label, type(e).__name__, e))
    fail("%s: did not raise" % label)


tex = mcrfpy.Texture.from_bytes(bytes(16 * 16 * 4), 16, 16, 8, 8)  # 4 sprites
grid = mcrfpy.Grid(grid_size=(4, 4), texture=tex)
layer = mcrfpy.TileLayer(name="t", z_index=0, texture=tex)
grid.add_layer(layer)

layer.set((0, 0), 3); layer.set((1, 0), -1)
layer.fill_rect((0, 1), (2, 2), 2)
layer[2, 0] = 0
if layer.at(0, 0) != 3 or layer.at(1, 0) != -1 or layer.at(0, 1) != 2:
    fail("valid indices were not stored")

raises(lambda: layer.set((0, 0), -5), ["-5", "-1"], "set -5")
raises(lambda: layer.set((0, 0), 4), ["4", "4 sprites", "0 to 3"], "set count")
raises(lambda: layer.set((0, 0), 10 ** 6), ["1000000"], "set 10**6")
raises(lambda: layer.fill(-2), ["-2"], "fill -2")
raises(lambda: layer.fill_rect((0, 0), (1, 1), -7), ["-7"], "fill_rect -7")
raises(lambda: layer.fill_rect((0, 0), (1, 1), 99), ["99"], "fill_rect 99")
try:
    layer[0, 0] = 4
except ValueError:
    pass
else:
    fail("subscript assignment of 4 did not raise")

hm = mcrfpy.HeightMap((4, 4), fill=0.5)
raises(lambda: layer.apply_threshold(hm, (0.0, 1.0), 4), ["4"], "apply_threshold 4")
raises(lambda: layer.apply_threshold(hm, (0.0, 1.0), -3), ["-3"], "apply_threshold -3")
raises(lambda: layer.apply_ranges(hm, [((0.0, 1.0), 2 ** 40 + 7)]), ["tile index"], "apply_ranges 2**40+7")
raises(lambda: layer.apply_ranges(hm, [((0.0, 1.0), 4)]), ["4"], "apply_ranges 4")
raises(lambda: layer.apply_ranges(hm, [((0.0, 1.0), -2)]), ["-2"], "apply_ranges -2")
# rejected calls changed nothing
if layer.at(0, 0) != 3: fail("a rejected call modified the layer")
layer.apply_ranges(hm, [((0.0, 1.0), 1)])
if layer.at(3, 3) != 1: fail("valid apply_ranges did not apply")
print("PASS")
sys.exit(0)
