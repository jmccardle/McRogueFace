"""#522: ColorLayer.apply_ranges accepts a gradient given as two Color objects (or names)."""
import sys
import mcrfpy


def rgb(c):
    return (c.r, c.g, c.b, c.a)


def fail(msg):
    print("FAIL", msg)
    sys.exit(1)


grid = mcrfpy.Grid(grid_size=(3, 1), texture=mcrfpy.default_texture)
layer = mcrfpy.ColorLayer(name="c", z_index=0)
grid.add_layer(layer)
hm = mcrfpy.HeightMap((3, 1))
for x, v in enumerate((0.0, 0.5, 1.0)):
    hm[x, 0] = v

black, white = mcrfpy.Color(0, 0, 0), mcrfpy.Color(200, 200, 200)
layer.apply_ranges(hm, [((0.0, 1.0), (black, white))])
ref = mcrfpy.ColorLayer(name="r", z_index=1)
grid.add_layer(ref)
ref.apply_ranges(hm, [((0.0, 1.0), ((0, 0, 0), (200, 200, 200)))])
for x in range(3):
    if rgb(layer.at(x, 0)) != rgb(ref.at(x, 0)):
        fail("Color pair at %d: %r != tuple pair %r" % (x, rgb(layer.at(x, 0)), rgb(ref.at(x, 0))))
if rgb(layer.at(2, 0))[:3] != (200, 200, 200):
    fail("gradient end colour wrong: %r" % (rgb(layer.at(2, 0)),))

# names, and mixed forms
layer.apply_ranges(hm, [((0.0, 1.0), ("black", (200, 200, 200)))])
if rgb(layer.at(2, 0))[:3] != (200, 200, 200): fail("mixed pair")

# a single colour still works, and a bad colour in a pair gets an accurate error
layer.apply_ranges(hm, [((0.0, 1.0), mcrfpy.Color(1, 2, 3))])
if rgb(layer.at(1, 0))[:3] != (1, 2, 3): fail("fixed Color")
try:
    layer.apply_ranges(hm, [((0.0, 1.0), (black, "notacolour"))])
except (ValueError, TypeError) as e:
    if "notacolour" not in str(e): fail("error does not name the bad colour: %s" % e)
else:
    fail("bad colour in a pair did not raise")
print("PASS")
sys.exit(0)
