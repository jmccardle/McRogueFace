# tiled_demo.py - Visual demo of Tiled integration
# Shows premade maps, Wang auto-tiling, and procgen terrain
#
# Usage:
#   Headless:     cd build && ./mcrogueface --headless --exec ../tests/demo/screens/tiled_demo.py
#   Interactive:  cd build && ./mcrogueface --exec ../tests/demo/screens/tiled_demo.py

import mcrfpy
from mcrfpy import automation
import sys

# -- Asset Paths -------------------------------------------------------
PUNY_BASE = "/home/john/Development/7DRL2026_Liber_Noster_jmccardle/assets_sources/PUNY_WORLD_v1/PUNY_WORLD_v1"
TSX_PATH = PUNY_BASE + "/Tiled/punyworld-overworld-tiles.tsx"

# -- Load Shared Assets ------------------------------------------------
print("Loading Puny World tileset...")
tileset = mcrfpy.TileSetFile(TSX_PATH)
texture = tileset.to_texture()
overworld_ws = tileset.wang_set("overworld")
Terrain = overworld_ws.terrain_enum()

print(f"  Tileset: {tileset.name}")
print(f"  Tiles: {tileset.tile_count} ({tileset.columns} cols, {tileset.tile_width}x{tileset.tile_height}px)")
print(f"  Wang set: {overworld_ws.name} ({overworld_ws.type}, {overworld_ws.color_count} colors)")
print(f"  Terrain enum members: {[t.name for t in Terrain]}")

# -- Helper: Iterative terrain expansion ----------------------------------
def iterative_terrain(hm, wang_set, width, height, passes):
    """Build a DiscreteMap by iteratively splitting terrains outward from
    a valid binary map. Each pass splits one terrain on each end of the
    chain, validates with wang_set.resolve(), and reverts invalid cells
    to their previous value.

    hm:     HeightMap (normalized 0-1)
    passes: list of (threshold, lo_old, lo_new, hi_old, hi_new) tuples.
            Each pass says: cells currently == lo_old with height < threshold
            become lo_new; cells currently == hi_old with height >= threshold
            become hi_new.

    Returns (DiscreteMap, stats_dict).
    """
    dm = mcrfpy.DiscreteMap((width, height))

    # Pass 0: binary split - everything is one of two terrains
    p0 = passes[0]
    thresh, lo_terrain, hi_terrain = p0
    for y in range(height):
        for x in range(width):
            if hm.get(x, y) < thresh:
                dm.set(x, y, int(lo_terrain))
            else:
                dm.set(x, y, int(hi_terrain))

    # Validate pass 0 and fix any invalid cells (rare edge cases like
    # checkerboard patterns at the binary boundary)
    results = wang_set.resolve(dm)
    inv = sum(1 for r in results if r == -1)
    if inv > 0:
        # Fix by flipping invalid cells to the other terrain
        for y in range(height):
            for x in range(width):
                if results[y * width + x] == -1:
                    val = dm.get(x, y)
                    if val == int(lo_terrain):
                        dm.set(x, y, int(hi_terrain))
                    else:
                        dm.set(x, y, int(lo_terrain))
        results2 = wang_set.resolve(dm)
        inv = sum(1 for r in results2 if r == -1)
    stats = {"pass0_invalid": inv}

    # Subsequent passes: split outward
    for pi, (thresh, lo_old, lo_new, hi_old, hi_new) in enumerate(passes[1:], 1):
        # Save current state so we can revert invalid cells
        prev = [dm.get(x, y) for y in range(height) for x in range(width)]

        # Track which cells were changed this pass
        changed = set()
        for y in range(height):
            for x in range(width):
                val = dm.get(x, y)
                h = hm.get(x, y)
                if val == int(lo_old) and h < thresh:
                    dm.set(x, y, int(lo_new))
                    changed.add((x, y))
                elif val == int(hi_old) and h >= thresh:
                    dm.set(x, y, int(hi_new))
                    changed.add((x, y))

        # Iteratively revert changed cells that cause invalid tiles.
        # A changed cell should be reverted if:
        #   - It is itself invalid, OR
        #   - It is a neighbor of an invalid UN-changed cell (it broke
        #     a pre-existing valid cell by being placed next to it)
        dirs8 = [(-1,-1),(0,-1),(1,-1),(-1,0),(1,0),(-1,1),(0,1),(1,1)]
        total_reverted = 0
        for revert_round in range(30):
            results = wang_set.resolve(dm)
            to_revert = set()
            for y in range(height):
                for x in range(width):
                    if results[y * width + x] != -1:
                        continue
                    if (x, y) in changed:
                        # This changed cell is invalid - revert it
                        to_revert.add((x, y))
                    else:
                        # Pre-existing cell is now invalid - revert its
                        # changed neighbors to restore it
                        for dx, dy in dirs8:
                            nx, ny = x+dx, y+dy
                            if (nx, ny) in changed:
                                to_revert.add((nx, ny))

            if not to_revert:
                break

            for (x, y) in to_revert:
                dm.set(x, y, prev[y * width + x])
                changed.discard((x, y))
                total_reverted += 1

        results_final = wang_set.resolve(dm)
        remaining = sum(1 for r in results_final if r == -1)
        stats[f"pass{pi}_kept"] = len(changed)
        stats[f"pass{pi}_reverted"] = total_reverted
        stats[f"pass{pi}_remaining"] = remaining

    return dm, stats


# -- Helper: Info Panel -------------------------------------------------
def make_info_panel(scene, lines, x=560, y=60, w=220, h=None):
    """Create a semi-transparent info panel with text lines."""
    if h is None:
        h = len(lines) * 22 + 20
    panel = mcrfpy.Frame(pos=(x, y), size=(w, h),
                         fill_color=mcrfpy.Color(20, 20, 30, 220),
                         outline_color=mcrfpy.Color(80, 80, 120),
                         outline=1.5)
    scene.children.append(panel)
    for i, text in enumerate(lines):
        cap = mcrfpy.Caption(text=text, pos=(10, 10 + i * 22))
        cap.fill_color = mcrfpy.Color(200, 200, 220)
        panel.children.append(cap)
    return panel


# ======================================================================
# SCREEN 1: Premade Tiled Map
# ======================================================================
print("\nSetting up Screen 1: Premade Map...")
scene1 = mcrfpy.Scene("tiled_premade")

bg1 = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(10, 10, 15))
scene1.children.append(bg1)

title1 = mcrfpy.Caption(text="Premade Tiled Map (50x50, 3 layers)", pos=(20, 10))
title1.fill_color = mcrfpy.Color(255, 255, 255)
scene1.children.append(title1)

# Load samplemap1
tm1 = mcrfpy.TileMapFile(PUNY_BASE + "/Tiled/samplemap1.tmj")
print(f"  Map: {tm1.width}x{tm1.height}, layers: {tm1.tile_layer_names}")

grid1 = mcrfpy.Grid(grid_size=(tm1.width, tm1.height),
                     pos=(20, 50), size=(520, 520), layers=[])
grid1.fill_color = mcrfpy.Color(30, 30, 50)

# Add a tile layer for each map layer, bottom-up z ordering
layer_names_1 = tm1.tile_layer_names
for i, name in enumerate(layer_names_1):
    z = -(len(layer_names_1) - i)
    layer = mcrfpy.TileLayer(name=name, z_index=z, texture=texture)
    grid1.add_layer(layer)
    tm1.apply_to_tile_layer(layer, name, tileset_index=0)
    print(f"  Applied layer '{name}' (z_index={z})")

# Center camera on map center (pixels = tiles * tile_size)
grid1.center = (tm1.width * tileset.tile_width // 2,
                tm1.height * tileset.tile_height // 2)
scene1.children.append(grid1)

make_info_panel(scene1, [
    f"Tileset: {tileset.name}",
    f"Tile size: {tileset.tile_width}x{tileset.tile_height}",
    f"Tile count: {tileset.tile_count}",
    f"Map size: {tm1.width}x{tm1.height}",
    "",
    "Layers:",
] + [f"  {name}" for name in layer_names_1] + [
    "",
    "Wang sets:",
    f"  {overworld_ws.name} ({overworld_ws.type})",
    f"  pathways (edge)",
])

nav1 = mcrfpy.Caption(text="[1] Premade  [2] Procgen  [3] Side-by-Side  [ESC] Quit", pos=(20, 740))
nav1.fill_color = mcrfpy.Color(120, 120, 150)
scene1.children.append(nav1)


# ======================================================================
# SCREEN 2: Procedural Wang Auto-Tile (2-layer approach)
# ======================================================================
print("\nSetting up Screen 2: Procgen Wang Terrain (2-layer)...")
scene2 = mcrfpy.Scene("tiled_procgen")

bg2 = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(10, 10, 15))
scene2.children.append(bg2)

title2 = mcrfpy.Caption(text="Procgen Wang Auto-Tile (60x60, 2 layers)", pos=(20, 10))
title2.fill_color = mcrfpy.Color(255, 255, 255)
scene2.children.append(title2)

W, H = 60, 60
T = Terrain  # shorthand

# Generate terrain heightmap using NoiseSource
noise = mcrfpy.NoiseSource(dimensions=2, seed=42)
hm = noise.sample(size=(W, H), mode="fbm", octaves=4, world_size=(4.0, 4.0))
hm.normalize(0.0, 1.0)

# -- Base terrain: iterative expansion from binary map --
# Pass 0: binary split at median -> SEAWATER_LIGHT / SAND
# Pass 1: split outward -> SEAWATER_MEDIUM from LIGHT, GRASS from SAND
# Pass 2: split outward -> SEAWATER_DEEP from MEDIUM, CLIFF from GRASS
base_passes = [
    # Pass 0: (threshold, lo_terrain, hi_terrain)
    (0.45, T.SEAWATER_LIGHT, T.SAND),
    # Pass 1+: (threshold, lo_old, lo_new, hi_old, hi_new)
    (0.30, T.SEAWATER_LIGHT, T.SEAWATER_MEDIUM, T.SAND, T.GRASS),
    (0.20, T.SEAWATER_MEDIUM, T.SEAWATER_DEEP, T.GRASS, T.CLIFF),
]
base_dm, base_stats = iterative_terrain(hm, overworld_ws, W, H, base_passes)
base_dm.enum_type = T
print(f"  Base terrain stats: {base_stats}")

# -- Tree overlay: separate noise, binary TREES/AIR --
tree_noise = mcrfpy.NoiseSource(dimensions=2, seed=999)
tree_hm = tree_noise.sample(size=(W, H), mode="fbm", octaves=3, world_size=(6.0, 6.0))
tree_hm.normalize(0.0, 1.0)

overlay_dm = mcrfpy.DiscreteMap((W, H))
overlay_dm.enum_type = T
for y in range(H):
    for x in range(W):
        base_val = base_dm.get(x, y)
        tree_h = tree_hm.get(x, y)
        # Trees only on GRASS, driven by separate noise
        if base_val == int(T.GRASS) and tree_h > 0.45:
            overlay_dm.set(x, y, int(T.TREES))
        else:
            overlay_dm.set(x, y, int(T.AIR))

# Validate overlay and revert invalid to AIR
overlay_results = overworld_ws.resolve(overlay_dm)
overlay_reverted = 0
for y in range(H):
    for x in range(W):
        if overlay_results[y * W + x] == -1:
            overlay_dm.set(x, y, int(T.AIR))
            overlay_reverted += 1
print(f"  Overlay: {overlay_reverted} tree cells reverted to AIR")

# Count terrain distribution
terrain_counts = {}
for t in T:
    if t == T.NONE:
        continue
    c = base_dm.count(int(t))
    if c > 0:
        terrain_counts[t.name] = c
tree_count = overlay_dm.count(int(T.TREES))
terrain_counts["TREES(overlay)"] = tree_count

print(f"  Terrain distribution: {terrain_counts}")

# Create grid with 2 layers and apply Wang auto-tiling
grid2 = mcrfpy.Grid(grid_size=(W, H), pos=(20, 50), size=(520, 520), layers=[])
grid2.fill_color = mcrfpy.Color(30, 30, 50)

base_layer2 = mcrfpy.TileLayer(name="base", z_index=-2, texture=texture)
grid2.add_layer(base_layer2)
overworld_ws.apply(base_dm, base_layer2)

overlay_layer2 = mcrfpy.TileLayer(name="trees", z_index=-1, texture=texture)
grid2.add_layer(overlay_layer2)
overworld_ws.apply(overlay_dm, overlay_layer2)

# Post-process overlay: AIR resolves to an opaque tile, set to -1 (transparent)
for y in range(H):
    for x in range(W):
        if overlay_dm.get(x, y) == int(T.AIR):
            overlay_layer2.set((x, y), -1)

grid2.center = (W * tileset.tile_width // 2, H * tileset.tile_height // 2)
scene2.children.append(grid2)

# Info panel
info_lines = [
    "Iterative terrain expansion",
    f"Seed: 42 (base), 999 (trees)",
    f"Grid: {W}x{H}, 2 layers",
    "",
    "Base (3 passes):",
]
for name in ["SEAWATER_DEEP", "SEAWATER_MEDIUM", "SEAWATER_LIGHT",
             "SAND", "GRASS", "CLIFF"]:
    count = terrain_counts.get(name, 0)
    info_lines.append(f"  {name}: {count}")
info_lines.append("")
info_lines.append("Tree Overlay:")
info_lines.append(f"  TREES: {tree_count}")
info_lines.append(f"  reverted: {overlay_reverted}")

make_info_panel(scene2, info_lines)

nav2 = mcrfpy.Caption(text="[1] Premade  [2] Procgen  [3] Side-by-Side  [ESC] Quit", pos=(20, 740))
nav2.fill_color = mcrfpy.Color(120, 120, 150)
scene2.children.append(nav2)


# ======================================================================
# SCREEN 3: Side-by-Side Comparison
# ======================================================================
print("\nSetting up Screen 3: Side-by-Side...")
scene3 = mcrfpy.Scene("tiled_compare")

bg3 = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(10, 10, 15))
scene3.children.append(bg3)

title3 = mcrfpy.Caption(text="Premade vs Procedural", pos=(20, 10))
title3.fill_color = mcrfpy.Color(255, 255, 255)
scene3.children.append(title3)

# Left: Premade map (samplemap2, 30x30)
tm2 = mcrfpy.TileMapFile(PUNY_BASE + "/Tiled/samplemap2.tmj")
print(f"  Map2: {tm2.width}x{tm2.height}, layers: {tm2.tile_layer_names}")

left_label = mcrfpy.Caption(text="Premade (samplemap2)", pos=(20, 38))
left_label.fill_color = mcrfpy.Color(180, 220, 255)
scene3.children.append(left_label)

grid_left = mcrfpy.Grid(grid_size=(tm2.width, tm2.height),
                         pos=(20, 60), size=(380, 380), layers=[])
grid_left.fill_color = mcrfpy.Color(30, 30, 50)

for i, name in enumerate(tm2.tile_layer_names):
    z = -(len(tm2.tile_layer_names) - i)
    layer = mcrfpy.TileLayer(name=name, z_index=z, texture=texture)
    grid_left.add_layer(layer)
    tm2.apply_to_tile_layer(layer, name, tileset_index=0)

grid_left.center = (tm2.width * tileset.tile_width // 2,
                     tm2.height * tileset.tile_height // 2)
scene3.children.append(grid_left)

# Right: Procgen island
right_label = mcrfpy.Caption(text="Procgen Island (2-layer Wang)", pos=(420, 38))
right_label.fill_color = mcrfpy.Color(180, 255, 220)
scene3.children.append(right_label)

IW, IH = 30, 30
island_noise = mcrfpy.NoiseSource(dimensions=2, seed=7777)
island_hm = island_noise.sample(size=(IW, IH), mode="fbm", octaves=3, world_size=(3.0, 3.0))
island_hm.normalize(0.0, 1.0)

# Create island shape: attenuate edges with radial gradient
for y in range(IH):
    for x in range(IW):
        dx = (x - IW / 2.0) / (IW / 2.0)
        dy = (y - IH / 2.0) / (IH / 2.0)
        dist = (dx * dx + dy * dy) ** 0.5
        falloff = max(0.0, 1.0 - dist * 1.2)
        h = island_hm.get(x, y) * falloff
        island_hm[x, y] = h

island_hm.normalize(0.0, 1.0)

# Iterative base terrain expansion (same technique as Screen 2)
island_passes_def = [
    (0.40, T.SEAWATER_LIGHT, T.SAND),
    (0.25, T.SEAWATER_LIGHT, T.SEAWATER_MEDIUM, T.SAND, T.GRASS),
    (0.15, T.SEAWATER_MEDIUM, T.SEAWATER_DEEP, T.GRASS, T.CLIFF),
]
island_base_dm, island_stats = iterative_terrain(
    island_hm, overworld_ws, IW, IH, island_passes_def)
island_base_dm.enum_type = T
print(f"  Island base stats: {island_stats}")

# Tree overlay with separate noise
island_tree_noise = mcrfpy.NoiseSource(dimensions=2, seed=8888)
island_tree_hm = island_tree_noise.sample(
    size=(IW, IH), mode="fbm", octaves=3, world_size=(4.0, 4.0))
island_tree_hm.normalize(0.0, 1.0)

island_overlay_dm = mcrfpy.DiscreteMap((IW, IH))
island_overlay_dm.enum_type = T
for y in range(IH):
    for x in range(IW):
        base_val = island_base_dm.get(x, y)
        tree_h = island_tree_hm.get(x, y)
        if base_val == int(T.GRASS) and tree_h > 0.50:
            island_overlay_dm.set(x, y, int(T.TREES))
        else:
            island_overlay_dm.set(x, y, int(T.AIR))

# Validate overlay
island_ov_results = overworld_ws.resolve(island_overlay_dm)
for y in range(IH):
    for x in range(IW):
        if island_ov_results[y * IW + x] == -1:
            island_overlay_dm.set(x, y, int(T.AIR))

grid_right = mcrfpy.Grid(grid_size=(IW, IH),
                          pos=(420, 60), size=(380, 380), layers=[])
grid_right.fill_color = mcrfpy.Color(30, 30, 50)

island_base_layer = mcrfpy.TileLayer(name="island_base", z_index=-2, texture=texture)
grid_right.add_layer(island_base_layer)
overworld_ws.apply(island_base_dm, island_base_layer)

island_overlay_layer = mcrfpy.TileLayer(name="island_trees", z_index=-1, texture=texture)
grid_right.add_layer(island_overlay_layer)
overworld_ws.apply(island_overlay_dm, island_overlay_layer)

# Post-process: make AIR cells transparent
for y in range(IH):
    for x in range(IW):
        if island_overlay_dm.get(x, y) == int(T.AIR):
            island_overlay_layer.set((x, y), -1)

grid_right.center = (IW * tileset.tile_width // 2, IH * tileset.tile_height // 2)
scene3.children.append(grid_right)

# Info for both
make_info_panel(scene3, [
    "Left: Premade Map",
    f"  samplemap2.tmj",
    f"  {tm2.width}x{tm2.height}, {len(tm2.tile_layer_names)} layers",
    "",
    "Right: Procgen Island",
    f"  {IW}x{IH}, seed=7777",
    "  Iterative terrain expansion",
    "  2-layer Wang auto-tile",
    "",
    "Same tileset, same engine",
    "Different workflows",
], x=200, y=460, w=400, h=None)

nav3 = mcrfpy.Caption(text="[1] Premade  [2] Procgen  [3] Side-by-Side  [ESC] Quit", pos=(20, 740))
nav3.fill_color = mcrfpy.Color(120, 120, 150)
scene3.children.append(nav3)


# ======================================================================
# Navigation & Screenshots
# ======================================================================
scenes = [scene1, scene2, scene3]
scene_names = ["premade", "procgen", "compare"]

# Keyboard navigation (all scenes share the same handler)
def on_key(key, action):
    if action != mcrfpy.InputState.PRESSED:
        return
    if key == mcrfpy.Key.NUM_1:
        mcrfpy.current_scene = scene1
    elif key == mcrfpy.Key.NUM_2:
        mcrfpy.current_scene = scene2
    elif key == mcrfpy.Key.NUM_3:
        mcrfpy.current_scene = scene3
    elif key == mcrfpy.Key.ESCAPE:
        mcrfpy.exit()

for s in scenes:
    s.on_key = on_key

# Detect headless mode and take screenshots synchronously
is_headless = False
try:
    win = mcrfpy.Window.get()
    is_headless = "headless" in str(win).lower()
except:
    is_headless = True

if is_headless:
    # Headless: use step() to advance simulation and take screenshots directly
    for i, (sc, name) in enumerate(zip(scenes, scene_names)):
        mcrfpy.current_scene = sc
        # Step a few frames to let the scene render
        for _ in range(3):
            mcrfpy.step(0.016)
        fname = f"tiled_demo_{name}.png"
        automation.screenshot(fname)
        print(f"  Screenshot: {fname}")
    print("\nAll screenshots captured. Done!")
    sys.exit(0)
else:
    # Interactive: start on screen 1
    mcrfpy.current_scene = scene1
    print("\nTiled Demo ready!")
    print("Press [1] [2] [3] to switch screens, [ESC] to quit")
