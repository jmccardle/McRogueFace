# ldtk_demo.py - Visual demo of LDtk import system
# Shows prebuilt level content and procedural generation via auto-rules
# Uses the official LDtk TopDown example with real sprite art
#
# Usage:
#   Headless:     cd build && ./mcrogueface --headless --exec ../tests/demo/screens/ldtk_demo.py
#   Interactive:  cd build && ./mcrogueface --exec ../tests/demo/screens/ldtk_demo.py

import mcrfpy
from mcrfpy import automation
import sys

# -- Asset Paths -------------------------------------------------------
LDTK_PATH = "../tests/demo/ldtk/Typical_TopDown_example.ldtk"

# -- Load Project ------------------------------------------------------
print("Loading LDtk TopDown example...")
proj = mcrfpy.LdtkProject(LDTK_PATH)
ts = proj.tileset("TopDown_by_deepnight")
texture = ts.to_texture()
rs = proj.ruleset("Collisions")
Terrain = rs.terrain_enum()

print(f"  Project: v{proj.version}")
print(f"  Tileset: {ts.name} ({ts.tile_count} tiles, {ts.tile_width}x{ts.tile_height}px)")
print(f"  Ruleset: {rs.name} ({rs.rule_count} rules, {rs.group_count} groups)")
print(f"  Terrain values: {[t.name for t in Terrain]}")
print(f"  Levels: {proj.level_names}")


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
# SCREEN 1: Prebuilt Level Content (all 3 levels)
# ======================================================================
print("\nSetting up Screen 1: Prebuilt Levels...")
scene1 = mcrfpy.Scene("ldtk_prebuilt")

bg1 = mcrfpy.Frame(pos=(0, 0), size=(1024, 768),
                    fill_color=mcrfpy.Color(10, 10, 15))
scene1.children.append(bg1)

title1 = mcrfpy.Caption(text="LDtk Prebuilt Levels (auto-layer tiles from editor)",
                         pos=(20, 10))
title1.fill_color = mcrfpy.Color(255, 255, 255)
scene1.children.append(title1)

# Load all 3 levels side by side
level_grids = []
level_x_offset = 20
for li, lname in enumerate(proj.level_names):
    level = proj.level(lname)
    # Find the Collisions layer (has the auto_tiles)
    for layer_info in level["layers"]:
        if layer_info["name"] == "Collisions" and layer_info.get("auto_tiles"):
            lw, lh = layer_info["width"], layer_info["height"]
            auto_tiles = layer_info["auto_tiles"]

            # Label
            label = mcrfpy.Caption(
                text=f"{lname} ({lw}x{lh})",
                pos=(level_x_offset, 38))
            label.fill_color = mcrfpy.Color(180, 220, 255)
            scene1.children.append(label)

            # Create layer with prebuilt tiles
            prebuilt_layer = mcrfpy.TileLayer(
                name=f"prebuilt_{lname}", texture=texture,
                grid_size=(lw, lh))
            prebuilt_layer.fill(-1)
            for tile in auto_tiles:
                x, y = tile["x"], tile["y"]
                if 0 <= x < lw and 0 <= y < lh:
                    prebuilt_layer.set((x, y), tile["tile_id"])

            # Determine display size (scale to fit)
            max_w = 310 if li < 2 else 310
            max_h = 300
            scale = min(max_w / (lw * ts.tile_width),
                        max_h / (lh * ts.tile_height))
            disp_w = int(lw * ts.tile_width * scale)
            disp_h = int(lh * ts.tile_height * scale)

            grid = mcrfpy.Grid(
                grid_size=(lw, lh),
                pos=(level_x_offset, 60),
                size=(disp_w, disp_h),
                layers=[prebuilt_layer])
            grid.fill_color = mcrfpy.Color(30, 30, 50)
            grid.center = (lw * ts.tile_width // 2,
                           lh * ts.tile_height // 2)
            scene1.children.append(grid)

            level_grids.append((lname, lw, lh, len(auto_tiles)))
            level_x_offset += disp_w + 20
            break

# Info panel
info_lines = [
    "LDtk Prebuilt Content",
    "",
    f"Project: TopDown example",
    f"Version: {proj.version}",
    f"Tileset: {ts.name}",
    f"  {ts.tile_count} tiles, {ts.tile_width}x{ts.tile_height}px",
    "",
    "Levels loaded:",
]
for lname, lw, lh, natiles in level_grids:
    info_lines.append(f"  {lname}: {lw}x{lh}")
    info_lines.append(f"    auto_tiles: {natiles}")

make_info_panel(scene1, info_lines, x=20, y=400, w=400)

nav1 = mcrfpy.Caption(
    text="[1] Prebuilt  [2] Procgen  [3] Compare  [ESC] Quit",
    pos=(20, 740))
nav1.fill_color = mcrfpy.Color(120, 120, 150)
scene1.children.append(nav1)


# ======================================================================
# SCREEN 2: Procedural Generation via Auto-Rules
# ======================================================================
print("\nSetting up Screen 2: Procedural Generation...")
scene2 = mcrfpy.Scene("ldtk_procgen")

bg2 = mcrfpy.Frame(pos=(0, 0), size=(1024, 768),
                    fill_color=mcrfpy.Color(10, 10, 15))
scene2.children.append(bg2)

title2 = mcrfpy.Caption(
    text="LDtk Procedural Generation (auto-rules at runtime)",
    pos=(20, 10))
title2.fill_color = mcrfpy.Color(255, 255, 255)
scene2.children.append(title2)

# Generate a procedural dungeon using the LDtk Collisions rules
PW, PH = 32, 24

proc_dm = mcrfpy.DiscreteMap((PW, PH), fill=0)

# Fill everything with walls first
for y in range(PH):
    for x in range(PW):
        proc_dm.set(x, y, int(Terrain.WALLS))

# Carve out rooms as floor (value 0 = empty/floor in this tileset)
rooms = [
    (2, 2, 10, 6),     # Room 1: top-left
    (16, 2, 13, 6),    # Room 2: top-right
    (2, 12, 8, 10),    # Room 3: bottom-left
    (14, 11, 14, 11),  # Room 4: bottom-right
    (10, 8, 6, 5),     # Room 5: center
]
for rx, ry, rw, rh in rooms:
    for y in range(ry, min(ry + rh, PH)):
        for x in range(rx, min(rx + rw, PW)):
            proc_dm.set(x, y, 0)  # 0 = floor/empty

# Connect rooms with corridors
corridors = [
    # Horizontal corridors
    (11, 4, 16, 6),     # Room 1 -> Room 2
    (9, 12, 14, 14),    # Room 3 -> Room 4
    # Vertical corridors
    (5, 7, 7, 12),      # Room 1 -> Room 3
    (20, 7, 22, 11),    # Room 2 -> Room 4
    # Center connections
    (10, 9, 14, 11),    # Center -> Room 4
]
for cx1, cy1, cx2, cy2 in corridors:
    for y in range(cy1, min(cy2 + 1, PH)):
        for x in range(cx1, min(cx2 + 1, PW)):
            proc_dm.set(x, y, 0)

# Apply auto-rules
proc_layer = mcrfpy.TileLayer(
    name="procgen", texture=texture, grid_size=(PW, PH))
proc_layer.fill(-1)
rs.apply(proc_dm, proc_layer, seed=42)

# Stats
wall_count = sum(1 for y in range(PH) for x in range(PW)
                 if proc_dm.get(x, y) == int(Terrain.WALLS))
floor_count = PW * PH - wall_count
resolved = rs.resolve(proc_dm, seed=42)
matched = sum(1 for t in resolved if t >= 0)
unmatched = sum(1 for t in resolved if t == -1)

print(f"  Dungeon: {PW}x{PH}")
print(f"  Walls: {wall_count}, Floors: {floor_count}")
print(f"  Resolved: {matched} matched, {unmatched} unmatched")

# Display grid
disp_w2 = min(520, PW * ts.tile_width)
disp_h2 = min(520, PH * ts.tile_height)
scale2 = min(520 / (PW * ts.tile_width), 520 / (PH * ts.tile_height))
disp_w2 = int(PW * ts.tile_width * scale2)
disp_h2 = int(PH * ts.tile_height * scale2)

grid2 = mcrfpy.Grid(grid_size=(PW, PH),
                     pos=(20, 60), size=(disp_w2, disp_h2),
                     layers=[proc_layer])
grid2.fill_color = mcrfpy.Color(30, 30, 50)
grid2.center = (PW * ts.tile_width // 2, PH * ts.tile_height // 2)
scene2.children.append(grid2)

# Info panel
make_info_panel(scene2, [
    "Procedural Dungeon",
    "",
    f"Grid: {PW}x{PH}",
    f"Seed: 42",
    "",
    "Terrain counts:",
    f"  WALLS: {wall_count}",
    f"  FLOOR: {floor_count}",
    "",
    "Resolution:",
    f"  Matched:   {matched}/{PW*PH}",
    f"  Unmatched: {unmatched}",
    "",
    f"Rules: {rs.rule_count} total",
    f"Groups: {rs.group_count}",
    "",
    "5 rooms + corridors",
    "carved from solid walls",
], x=disp_w2 + 40, y=60, w=260)

nav2 = mcrfpy.Caption(
    text="[1] Prebuilt  [2] Procgen  [3] Compare  [ESC] Quit",
    pos=(20, 740))
nav2.fill_color = mcrfpy.Color(120, 120, 150)
scene2.children.append(nav2)


# ======================================================================
# SCREEN 3: Side-by-Side Comparison
# ======================================================================
print("\nSetting up Screen 3: Comparison...")
scene3 = mcrfpy.Scene("ldtk_compare")

bg3 = mcrfpy.Frame(pos=(0, 0), size=(1024, 768),
                    fill_color=mcrfpy.Color(10, 10, 15))
scene3.children.append(bg3)

title3 = mcrfpy.Caption(
    text="LDtk: Prebuilt vs Re-resolved (same tileset, same rules)",
    pos=(20, 10))
title3.fill_color = mcrfpy.Color(255, 255, 255)
scene3.children.append(title3)

# Use World_Level_1 (16x16, square, compact)
cmp_level = proj.level("World_Level_1")
cmp_layer = None
for layer in cmp_level["layers"]:
    if layer["name"] == "Collisions":
        cmp_layer = layer
        break

cw, ch = cmp_layer["width"], cmp_layer["height"]
cmp_auto_tiles = cmp_layer["auto_tiles"]
cmp_intgrid = cmp_layer["intgrid"]

# Left: Prebuilt tiles from editor
left_label = mcrfpy.Caption(text="Prebuilt (from LDtk editor)", pos=(20, 38))
left_label.fill_color = mcrfpy.Color(180, 220, 255)
scene3.children.append(left_label)

left_layer = mcrfpy.TileLayer(
    name="cmp_prebuilt", texture=texture, grid_size=(cw, ch))
left_layer.fill(-1)
for tile in cmp_auto_tiles:
    x, y = tile["x"], tile["y"]
    if 0 <= x < cw and 0 <= y < ch:
        left_layer.set((x, y), tile["tile_id"])

grid_left = mcrfpy.Grid(grid_size=(cw, ch),
                          pos=(20, 60), size=(350, 350),
                          layers=[left_layer])
grid_left.fill_color = mcrfpy.Color(30, 30, 50)
grid_left.center = (cw * ts.tile_width // 2, ch * ts.tile_height // 2)
scene3.children.append(grid_left)

# Right: Re-resolved using our engine
right_label = mcrfpy.Caption(
    text="Re-resolved (our engine, same IntGrid)", pos=(400, 38))
right_label.fill_color = mcrfpy.Color(180, 255, 220)
scene3.children.append(right_label)

cmp_dm = mcrfpy.DiscreteMap((cw, ch))
for y in range(ch):
    for x in range(cw):
        cmp_dm.set(x, y, cmp_intgrid[y * cw + x])

right_layer = mcrfpy.TileLayer(
    name="cmp_resolved", texture=texture, grid_size=(cw, ch))
right_layer.fill(-1)
rs.apply(cmp_dm, right_layer, seed=42)

grid_right = mcrfpy.Grid(grid_size=(cw, ch),
                           pos=(400, 60), size=(350, 350),
                           layers=[right_layer])
grid_right.fill_color = mcrfpy.Color(30, 30, 50)
grid_right.center = (cw * ts.tile_width // 2, ch * ts.tile_height // 2)
scene3.children.append(grid_right)

# Tile comparison stats
cmp_matched = 0
cmp_mismatched = 0
for y in range(ch):
    for x in range(cw):
        pre = left_layer.at(x, y)
        res = right_layer.at(x, y)
        if pre == res:
            cmp_matched += 1
        else:
            cmp_mismatched += 1

cmp_total = cw * ch
cmp_pct = (cmp_matched / cmp_total * 100) if cmp_total > 0 else 0
print(f"  Comparison Level_1: {cmp_matched}/{cmp_total} match ({cmp_pct:.0f}%)")

# Bottom: Another procgen with different seed
bot_label = mcrfpy.Caption(
    text="Procgen (new layout, seed=999)", pos=(20, 430))
bot_label.fill_color = mcrfpy.Color(255, 220, 180)
scene3.children.append(bot_label)

BW, BH = 16, 16
bot_dm = mcrfpy.DiscreteMap((BW, BH), fill=int(Terrain.WALLS))
# Diamond room shape
for y in range(BH):
    for x in range(BW):
        cx_d = abs(x - BW // 2)
        cy_d = abs(y - BH // 2)
        if cx_d + cy_d < 6:
            bot_dm.set(x, y, 0)  # floor
# Add some internal walls (pillars)
for px, py in [(6, 6), (9, 6), (6, 9), (9, 9)]:
    bot_dm.set(px, py, int(Terrain.WALLS))

bot_layer = mcrfpy.TileLayer(
    name="bot_procgen", texture=texture, grid_size=(BW, BH))
bot_layer.fill(-1)
rs.apply(bot_dm, bot_layer, seed=999)

grid_bot = mcrfpy.Grid(grid_size=(BW, BH),
                         pos=(20, 460), size=(250, 250),
                         layers=[bot_layer])
grid_bot.fill_color = mcrfpy.Color(30, 30, 50)
grid_bot.center = (BW * ts.tile_width // 2, BH * ts.tile_height // 2)
scene3.children.append(grid_bot)

# Info
make_info_panel(scene3, [
    "Tile-by-Tile Comparison",
    f"Level: World_Level_1 ({cw}x{ch})",
    "",
    f"  Matches:    {cmp_matched}/{cmp_total}",
    f"  Mismatches: {cmp_mismatched}/{cmp_total}",
    f"  Match rate: {cmp_pct:.0f}%",
    "",
    "Prebuilt has stacked tiles",
    "(shadows, outlines, etc.)",
    "Our engine picks last match",
    "per cell (single layer).",
    "",
    "Bottom: diamond room +",
    "4 pillars, seed=999",
], x=300, y=440, w=340)

nav3 = mcrfpy.Caption(
    text="[1] Prebuilt  [2] Procgen  [3] Compare  [ESC] Quit",
    pos=(20, 740))
nav3.fill_color = mcrfpy.Color(120, 120, 150)
scene3.children.append(nav3)


# ======================================================================
# Navigation & Screenshots
# ======================================================================
scenes = [scene1, scene2, scene3]
scene_names = ["prebuilt", "procgen", "compare"]

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

# Detect headless mode
is_headless = False
try:
    win = mcrfpy.Window.get()
    is_headless = "headless" in str(win).lower()
except:
    is_headless = True

if is_headless:
    for i, (sc, name) in enumerate(zip(scenes, scene_names)):
        mcrfpy.current_scene = sc
        for _ in range(3):
            mcrfpy.step(0.016)
        fname = f"ldtk_demo_{name}.png"
        automation.screenshot(fname)
        print(f"  Screenshot: {fname}")
    print("\nAll screenshots captured. Done!")
    sys.exit(0)
else:
    mcrfpy.current_scene = scene1
    print("\nLDtk Demo ready!")
    print("Press [1] [2] [3] to switch screens, [ESC] to quit")
