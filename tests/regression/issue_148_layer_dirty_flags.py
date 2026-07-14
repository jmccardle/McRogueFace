#!/usr/bin/env python3
"""
Regression test for issue #148: Grid Layer Dirty Flags and RenderTexture Caching

Tests:
1. Dirty flag is initially set (layers start dirty)
2. Setting cell values marks layer dirty
3. Fill operation marks layer dirty
4. Texture change marks TileLayer dirty
5. Viewport changes (center/zoom) don't corrupt the cached texture
6. Performance / large-layer handling for static layers
7. Layer visibility toggle marks the layer dirty
8. Large grid stress test

REPAIR NOTE (API drift):
  * add_layer() no longer takes kwargs and no longer constructs the layer for you.
    Construct a TileLayer/ColorLayer and attach it: grid.add_layer(layer).
  * layer.set() takes a position TUPLE: layer.set((x, y), value) -- not set(x, y, value).
  * assets/kenney_ice.png does not exist; using kenney_tinydungeon.png.
  * step() is the clock and NEVER renders (#350); rendering is forced with
    automation.screenshot(), which costs zero simulation time.

REPAIR NOTE (real coverage):
  The original file punted on the actual subject of #148 -- it said "dirty flag
  behavior is internal" and only checked that the API didn't crash, so it proved
  nothing about caching. Dirty-flag behavior IS observable from Python now: the
  GridView caches its composed output and only re-renders when a layer's markDirty()
  bumps the grid's content_generation (#351). So a mutation that fails to set the
  dirty flag produces a byte-identical screenshot -- a stale cache. We render to PNG
  and compare hashes to assert invalidation actually happens.
"""
import mcrfpy
from mcrfpy import automation
import sys
import os
import hashlib
import tempfile

failures = []


def check(label, condition, detail=""):
    if condition:
        print(f"  PASS: {label}")
    else:
        print(f"  FAIL: {label} {detail}")
        failures.append(label)


_shot_n = [0]


def render_hash():
    """Force a render (screenshot) and hash the pixels.

    step() never renders, so this is the only way to observe what the grid's cached
    RenderTexture actually contains. Identical bytes across a mutation == stale cache
    == the dirty flag was not set.
    """
    _shot_n[0] += 1
    path = os.path.join(tempfile.gettempdir(), f"issue148_{_shot_n[0]}.png")
    automation.screenshot(path)
    with open(path, "rb") as f:
        h = hashlib.sha256(f.read()).hexdigest()
    os.remove(path)
    return h


print("=" * 60)
print("Issue #148 Regression Test: Layer Dirty Flags and Caching")
print("=" * 60)

# Create test scene
test = mcrfpy.Scene("test")
mcrfpy.current_scene = test
ui = test.children
texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)

# Create grid with larger size for performance testing
grid = mcrfpy.Grid(pos=(50, 50), size=(500, 400), grid_size=(50, 40), texture=texture)
ui.append(grid)

print("\n--- Test 1: Layer creation (starts dirty) ---")
# A grid built with grid_size= already carries a default tile layer; these are added
# on top of it. Layers attached at size (0,0) auto-resize to the grid.
color_layer = mcrfpy.ColorLayer(name="color", z_index=-1)
grid.add_layer(color_layer)
print("  ColorLayer created successfully")

tile_layer = mcrfpy.TileLayer(name="tile", z_index=-2, texture=texture)
grid.add_layer(tile_layer)
print("  TileLayer created successfully")

check("ColorLayer attached and retrievable by name", grid.layer("color") is not None)
check("TileLayer attached and retrievable by name", grid.layer("tile") is not None)
check("layer auto-resized to grid", color_layer.grid_size == (50, 40),
      f"got {color_layer.grid_size}")

print("\n--- Test 2: Fill operations work (and mark the layer dirty) ---")
color_layer.fill(mcrfpy.Color(128, 0, 128, 64))
check("ColorLayer.fill wrote every cell", color_layer.at((0, 0)) == mcrfpy.Color(128, 0, 128, 64)
      and color_layer.at((49, 39)) == mcrfpy.Color(128, 0, 128, 64),
      f"got {color_layer.at((0, 0))} / {color_layer.at((49, 39))}")

tile_layer.fill(5)
check("TileLayer.fill wrote every cell",
      tile_layer.at((0, 0)) == 5 and tile_layer.at((49, 39)) == 5,
      f"got {tile_layer.at((0, 0))} / {tile_layer.at((49, 39))}")

print("\n--- Test 3: Cell set operations work ---")
yellow = mcrfpy.Color(255, 255, 0, 128)
for cell in [(10, 10), (11, 10), (10, 11), (11, 11)]:
    color_layer.set(cell, yellow)
check("ColorLayer.set updated the 4 target cells",
      all(color_layer.at(c) == yellow for c in [(10, 10), (11, 10), (10, 11), (11, 11)]))
check("ColorLayer.set left neighbours untouched",
      color_layer.at((12, 10)) == mcrfpy.Color(128, 0, 128, 64),
      f"got {color_layer.at((12, 10))}")

for cell, idx in [((15, 15), 10), ((16, 15), 11), ((15, 16), 10), ((16, 16), 11)]:
    tile_layer.set(cell, idx)
check("TileLayer.set updated the 4 target cells",
      tile_layer.at((15, 15)) == 10 and tile_layer.at((16, 15)) == 11
      and tile_layer.at((15, 16)) == 10 and tile_layer.at((16, 16)) == 11)
check("TileLayer.set(-1) clears a tile",
      (tile_layer.set((20, 20), -1), tile_layer.at((20, 20)))[1] == -1,
      f"got {tile_layer.at((20, 20))}")

print("\n--- Test 4: Texture change on TileLayer ---")
# Note: the .texture getter returns a fresh wrapper each call and Texture has no
# __eq__, so identity/equality can't be asserted -- compare the source path instead.
texture2 = mcrfpy.Texture("assets/kenney_TD_MR_IP.png", 16, 16)
tile_layer.texture = texture2
check("TileLayer.texture accepts a new texture",
      tile_layer.texture.source == "assets/kenney_TD_MR_IP.png",
      f"got {tile_layer.texture.source}")

tile_layer.texture = texture
check("TileLayer.texture restores the original",
      tile_layer.texture.source == "assets/kenney_tinydungeon.png",
      f"got {tile_layer.texture.source}")

print("\n--- Test 5: Dirty flags actually invalidate the cached RenderTexture ---")
# This is the core of #148. The grid caches its composed output; a mutation that does
# not set the dirty flag yields a byte-identical render (a stale cache).
# The ColorLayer (z=-1) composites OVER the TileLayer (z=-2), so it is kept
# translucent -- an opaque fill would occlude the tile layer and make the TileLayer
# invalidation checks below vacuous.
base = render_hash()
repeat = render_hash()
check("re-rendering an unchanged grid is stable", base == repeat)

color_layer.fill(mcrfpy.Color(255, 0, 0, 64))
after_fill = render_hash()
check("fill() invalidates the cache (render changed)", after_fill != base)

color_layer.set((0, 0), mcrfpy.Color(0, 255, 0, 64))
after_set = render_hash()
check("set() invalidates the cache (render changed)", after_set != after_fill)

tile_layer.fill(7)
after_tile_fill = render_hash()
check("TileLayer.fill() invalidates the cache", after_tile_fill != after_set)

tile_layer.set((5, 5), 12)
after_tile_set = render_hash()
check("TileLayer.set() invalidates the cache", after_tile_set != after_tile_fill)

# Bulk edit path (#328): the view is a 2-D int32 memoryview aliasing layer storage;
# on __exit__ the whole layer is conservatively invalidated.
with tile_layer.edit() as view:
    for y in range(40):
        for x in range(50):
            view[y, x] = 3
check("bulk edit() wrote through to layer storage", tile_layer.at((5, 5)) == 3,
      f"got {tile_layer.at((5, 5))}")
after_edit = render_hash()
check("bulk edit() invalidates the cache", after_edit != after_tile_set)

print("\n--- Test 6: Viewport changes (should use the cached texture) ---")
original_center = grid.center
original_zoom = grid.zoom
print(f"  Original center: {original_center}, zoom: {original_zoom}")

for i in range(10):
    grid.center = (100 + i * 20, 80 + i * 10)
check("center round-trips after 10 changes", grid.center == (280, 170),
      f"got {grid.center}")
panned = render_hash()
check("panning the viewport changes the rendered image", panned != after_edit)

for z in [1.0, 0.8, 1.2, 0.5, 1.5, 1.0]:
    grid.zoom = z
check("zoom round-trips after 6 changes", grid.zoom == 1.0, f"got {grid.zoom}")

# Restoring the viewport must restore the exact same image: the layer content never
# changed, so this exercises the cache-hit path (blit a different region, no re-render).
grid.center = original_center
grid.zoom = original_zoom
restored = render_hash()
check("restoring the viewport restores the identical image", restored == after_edit)

print("\n--- Test 7: Layer visibility toggle ---")
# The layer's own render() early-outs on `visible`, so hiding a layer must change the
# rendered output. It only does so if the setter invalidates the grid's cache.
visible_hash = render_hash()
color_layer.visible = False
check("visible attribute round-trips to False", color_layer.visible is False)
hidden_hash = render_hash()
check("hiding a layer changes the rendered image (dirty flag set)",
      hidden_hash != visible_hash,
      "-- layer.visible setter does not invalidate the grid cache (see notes)")

color_layer.visible = True
check("visible attribute round-trips to True", color_layer.visible is True)
reshown_hash = render_hash()
check("re-showing a layer restores the rendered image",
      reshown_hash == visible_hash,
      "-- layer.visible setter does not invalidate the grid cache (see notes)")

print("\n--- Test 8: Large grid stress test ---")
stress_scene = mcrfpy.Scene("stress")
stress_grid = mcrfpy.Grid(pos=(10, 10), size=(200, 150), grid_size=(200, 150), texture=texture)
stress_scene.children.append(stress_grid)
stress_layer = mcrfpy.ColorLayer(name="color", z_index=-1)
stress_grid.add_layer(stress_layer)

# 30,000 cells - should be handled via chunked texture caching
stress_layer.fill(mcrfpy.Color(0, 100, 200, 100))
for x in range(10):
    for y in range(10):
        stress_layer.set((x, y), mcrfpy.Color(255, 0, 0, 200))

check("30,000-cell layer filled", stress_layer.at((199, 149)) == mcrfpy.Color(0, 100, 200, 100),
      f"got {stress_layer.at((199, 149))}")
check("30,000-cell layer accepts per-cell sets",
      stress_layer.at((9, 9)) == mcrfpy.Color(255, 0, 0, 200),
      f"got {stress_layer.at((9, 9))}")

mcrfpy.current_scene = stress_scene
mcrfpy.step(0.016)
stress_render = render_hash()
check("large grid renders without crashing", len(stress_render) == 64)

# A static layer must be re-renderable from cache: identical bytes, no corruption.
check("static large layer renders identically from cache",
      render_hash() == stress_render)

print("\n" + "=" * 60)
if failures:
    print(f"FAIL - {len(failures)} check(s) failed:")
    for f in failures:
        print(f"  - {f}")
    print("=" * 60)
    sys.exit(1)

print("All tests PASSED")
print("=" * 60)
sys.exit(0)
