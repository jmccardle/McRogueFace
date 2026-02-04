# navigation_demo.py - Visual demo of 3D navigation system
# Shows pathfinding and FOV on terrain using VoxelPoint grid
# Includes 2D Grid minimap with ColorLayer visualization

import mcrfpy
import sys
import math

# Grid size
GRID_W, GRID_H = 40, 40

# Create demo scene
scene = mcrfpy.Scene("navigation_demo")

# Dark background frame
bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(15, 15, 25))
scene.children.append(bg)

# Title
title = mcrfpy.Caption(text="Navigation System Demo - Pathfinding & FOV", pos=(20, 10))
title.fill_color = mcrfpy.Color(255, 255, 255)
scene.children.append(title)

# Create the 3D viewport (left side, smaller)
viewport = mcrfpy.Viewport3D(
    pos=(20, 50),
    size=(480, 360),
    render_resolution=(320, 240),
    fov=60.0,
    camera_pos=(20.0, 35.0, 50.0),
    camera_target=(20.0, 0.0, 20.0),
    bg_color=mcrfpy.Color(100, 150, 200)
)
scene.children.append(viewport)

# Generate terrain using HeightMap
print("Generating terrain heightmap...")
hm = mcrfpy.HeightMap((GRID_W, GRID_H))
hm.mid_point_displacement(0.5, seed=42)
hm.normalize(0.0, 1.0)
hm.rain_erosion(drops=500, erosion=0.08, sedimentation=0.04, seed=42)
hm.normalize(0.0, 1.0)

# Shift terrain up so most is walkable land instead of water
# Add 0.3 offset, then renormalize to 0.1-1.0 range (keeps some water)
for y in range(GRID_H):
    for x in range(GRID_W):
        hm[x, y] = min(1.0, hm[x, y] + 0.3)

# Build terrain mesh
print("Building terrain mesh...")
vertex_count = viewport.build_terrain(
    layer_name="terrain",
    heightmap=hm,
    y_scale=8.0,
    cell_size=1.0
)
print(f"Terrain built with {vertex_count} vertices")

# Create color maps based on height for 3D terrain
r_map = mcrfpy.HeightMap((GRID_W, GRID_H))
g_map = mcrfpy.HeightMap((GRID_W, GRID_H))
b_map = mcrfpy.HeightMap((GRID_W, GRID_H))

for y in range(GRID_H):
    for x in range(GRID_W):
        h = hm[x, y]
        if h < 0.25:  # Water (unwalkable)
            r_map[x, y] = 0.2
            g_map[x, y] = 0.4
            b_map[x, y] = 0.8
        elif h < 0.6:  # Grass (walkable)
            r_map[x, y] = 0.2 + h * 0.2
            g_map[x, y] = 0.5 + h * 0.2
            b_map[x, y] = 0.1
        elif h < 0.8:  # Hills (walkable but costly)
            r_map[x, y] = 0.5
            g_map[x, y] = 0.4
            b_map[x, y] = 0.3
        else:  # Mountains (unwalkable)
            r_map[x, y] = 0.6
            g_map[x, y] = 0.6
            b_map[x, y] = 0.6

viewport.apply_terrain_colors("terrain", r_map, g_map, b_map)

# Initialize navigation grid
print("Setting up navigation grid...")
viewport.grid_size = (GRID_W, GRID_H)
viewport.cell_size = 1.0

# Apply heights from heightmap
viewport.apply_heightmap(hm, y_scale=8.0)

# Mark water as unwalkable (height < 0.25)
viewport.apply_threshold(hm, 0.0, 0.25, walkable=False)

# Mark mountains as unwalkable (height > 0.8)
viewport.apply_threshold(hm, 0.8, 1.0, walkable=False)

# Apply slope costs
viewport.set_slope_cost(max_slope=2.0, cost_multiplier=3.0)

# ============================================================================
# Create 2D Grid with ColorLayers (minimap on the right)
# ============================================================================
print("Creating 2D minimap grid...")

# Calculate cell size for minimap to fit nicely
minimap_width = 320
minimap_height = 320
cell_px = minimap_width // GRID_W  # 8 pixels per cell

# Create 2D Grid (no texture needed for color layers)
grid_2d = mcrfpy.Grid(
    grid_size=(GRID_W, GRID_H),
    pos=(520, 50),
    size=(minimap_width, minimap_height)
)
scene.children.append(grid_2d)

# Create and add terrain ColorLayer (z_index=0, bottom layer)
terrain_layer = mcrfpy.ColorLayer(z_index=0, name="terrain")
grid_2d.add_layer(terrain_layer)

# Fill terrain layer with colors matching the heightmap
for y in range(GRID_H):
    for x in range(GRID_W):
        h = hm[x, y]
        if h < 0.25:  # Water
            terrain_layer.set((x, y), mcrfpy.Color(50, 100, 200))
        elif h < 0.6:  # Grass
            green = int(100 + h * 100)
            terrain_layer.set((x, y), mcrfpy.Color(50, green, 30))
        elif h < 0.8:  # Hills
            terrain_layer.set((x, y), mcrfpy.Color(130, 100, 70))
        else:  # Mountains
            terrain_layer.set((x, y), mcrfpy.Color(150, 150, 150))

# Create and add path ColorLayer (z_index=1, on top of terrain)
path_layer = mcrfpy.ColorLayer(z_index=1, name="path")
grid_2d.add_layer(path_layer)
# Initialize transparent
path_layer.fill(mcrfpy.Color(0, 0, 0, 0))

# Create and add FOV ColorLayer (z_index=2, on top of path)
fov_layer = mcrfpy.ColorLayer(z_index=2, name="fov")
grid_2d.add_layer(fov_layer)
# Initialize transparent
fov_layer.fill(mcrfpy.Color(0, 0, 0, 0))

# ============================================================================
# State for demo
# ============================================================================
path_start = [10, 20]
path_end = [30, 20]
current_path = []
fov_visible = []
show_fov = [True]
show_path = [True]

def clear_path_layer():
    """Clear the path visualization layer"""
    path_layer.fill(mcrfpy.Color(0, 0, 0, 0))

def clear_fov_layer():
    """Clear the FOV visualization layer"""
    fov_layer.fill(mcrfpy.Color(0, 0, 0, 0))

def update_path_visualization():
    """Update path layer to show current path"""
    clear_path_layer()
    if not show_path[0]:
        return

    # Draw path in yellow
    for x, z in current_path:
        path_layer.set((x, z), mcrfpy.Color(255, 255, 0, 200))

    # Draw start point in green
    path_layer.set((path_start[0], path_start[1]), mcrfpy.Color(0, 255, 0, 255))

    # Draw end point in red
    path_layer.set((path_end[0], path_end[1]), mcrfpy.Color(255, 0, 0, 255))

def update_fov_visualization():
    """Update FOV layer to show visible cells"""
    clear_fov_layer()
    if not show_fov[0]:
        return

    # Draw visible cells in semi-transparent blue
    for x, z in fov_visible:
        # Don't overwrite start/end markers
        if [x, z] != path_start and [x, z] != path_end:
            fov_layer.set((x, z), mcrfpy.Color(100, 200, 255, 80))

def update_path():
    """Recompute path between start and end"""
    global current_path
    current_path = viewport.find_path(tuple(path_start), tuple(path_end))
    print(f"Path: {len(current_path)} steps")
    update_path_visualization()

def update_fov():
    """Recompute FOV from start position"""
    global fov_visible
    fov_visible = viewport.compute_fov(tuple(path_start), radius=8)
    print(f"FOV: {len(fov_visible)} cells visible")
    update_fov_visualization()

# Initial computation
update_path()
update_fov()

# ============================================================================
# Info panel
# ============================================================================
info_y = 390

# Status labels
start_label = mcrfpy.Caption(text=f"Start (green): ({path_start[0]}, {path_start[1]})", pos=(520, info_y))
start_label.fill_color = mcrfpy.Color(100, 255, 100)
scene.children.append(start_label)

end_label = mcrfpy.Caption(text=f"End (red): ({path_end[0]}, {path_end[1]})", pos=(520, info_y + 22))
end_label.fill_color = mcrfpy.Color(255, 100, 100)
scene.children.append(end_label)

path_label = mcrfpy.Caption(text=f"Path (yellow): {len(current_path)} steps", pos=(520, info_y + 44))
path_label.fill_color = mcrfpy.Color(255, 255, 100)
scene.children.append(path_label)

fov_label = mcrfpy.Caption(text=f"FOV (blue): {len(fov_visible)} cells", pos=(520, info_y + 66))
fov_label.fill_color = mcrfpy.Color(100, 200, 255)
scene.children.append(fov_label)

# Terrain legend
legend_y = info_y + 100
legend_title = mcrfpy.Caption(text="Terrain Legend:", pos=(520, legend_y))
legend_title.fill_color = mcrfpy.Color(200, 200, 200)
scene.children.append(legend_title)

legends = [
    ("Water (blue)", mcrfpy.Color(50, 100, 200), "unwalkable"),
    ("Grass (green)", mcrfpy.Color(80, 150, 30), "walkable"),
    ("Hills (brown)", mcrfpy.Color(130, 100, 70), "costly"),
    ("Mountains (gray)", mcrfpy.Color(150, 150, 150), "unwalkable"),
]

for i, (name, color, desc) in enumerate(legends):
    cap = mcrfpy.Caption(text=f"  {name}: {desc}", pos=(520, legend_y + 22 + i * 20))
    cap.fill_color = color
    scene.children.append(cap)

# Instructions
instructions = mcrfpy.Caption(
    text="[WASD] Move start | [IJKL] Move end | [F] FOV | [P] Path | [Space] Orbit",
    pos=(20, 430)
)
instructions.fill_color = mcrfpy.Color(150, 150, 150)
scene.children.append(instructions)

# Status line
status = mcrfpy.Caption(text="Status: Navigation demo ready - orbit OFF", pos=(20, 455))
status.fill_color = mcrfpy.Color(100, 200, 100)
scene.children.append(status)

# ============================================================================
# Animation state - orbit disabled by default
# ============================================================================
animation_time = [0.0]
camera_orbit = [False]  # Disabled by default

def update_display():
    """Update info display"""
    start_label.text = f"Start (green): ({path_start[0]}, {path_start[1]})"
    end_label.text = f"End (red): ({path_end[0]}, {path_end[1]})"
    path_label.text = f"Path (yellow): {len(current_path)} steps"
    fov_label.text = f"FOV (blue): {len(fov_visible)} cells"

# Camera animation
def update_camera(timer, runtime):
    animation_time[0] += runtime / 1000.0

    if camera_orbit[0]:
        angle = animation_time[0] * 0.2
        radius = 35.0
        center_x = 20.0
        center_z = 20.0
        height = 25.0 + math.sin(animation_time[0] * 0.15) * 5.0

        x = center_x + math.cos(angle) * radius
        z = center_z + math.sin(angle) * radius

        viewport.camera_pos = (x, height, z)
        viewport.camera_target = (center_x, 2.0, center_z)

# Key handler
def on_key(key, state):
    if state != mcrfpy.InputState.PRESSED:
        return

    global current_path, fov_visible

    # Movement for start point (WASD)
    moved_start = False
    if key == mcrfpy.Key.W:
        path_start[1] = max(0, path_start[1] - 1)
        moved_start = True
    elif key == mcrfpy.Key.S:
        path_start[1] = min(GRID_H - 1, path_start[1] + 1)
        moved_start = True
    elif key == mcrfpy.Key.A:
        path_start[0] = max(0, path_start[0] - 1)
        moved_start = True
    elif key == mcrfpy.Key.D:
        path_start[0] = min(GRID_W - 1, path_start[0] + 1)
        moved_start = True

    # Movement for end point (IJKL)
    moved_end = False
    if key == mcrfpy.Key.I:
        path_end[1] = max(0, path_end[1] - 1)
        moved_end = True
    elif key == mcrfpy.Key.K:
        path_end[1] = min(GRID_H - 1, path_end[1] + 1)
        moved_end = True
    elif key == mcrfpy.Key.J:
        path_end[0] = max(0, path_end[0] - 1)
        moved_end = True
    elif key == mcrfpy.Key.L:
        path_end[0] = min(GRID_W - 1, path_end[0] + 1)
        moved_end = True

    # Toggle FOV display
    if key == mcrfpy.Key.F:
        show_fov[0] = not show_fov[0]
        update_fov_visualization()
        status.text = f"FOV display: {'ON' if show_fov[0] else 'OFF'}"

    # Toggle path display
    if key == mcrfpy.Key.P:
        show_path[0] = not show_path[0]
        update_path_visualization()
        status.text = f"Path display: {'ON' if show_path[0] else 'OFF'}"

    # Toggle camera orbit
    if key == mcrfpy.Key.SPACE:
        camera_orbit[0] = not camera_orbit[0]
        status.text = f"Camera orbit: {'ON' if camera_orbit[0] else 'OFF'}"

    # Quit
    if key == mcrfpy.Key.ESCAPE:
        mcrfpy.exit()

    # Update pathfinding and FOV if moved
    if moved_start or moved_end:
        update_path()
        if moved_start:
            update_fov()
        update_display()

        # Show cell info
        vp = viewport.at(path_start[0], path_start[1])
        status.text = f"Start cell: walkable={vp.walkable}, height={vp.height:.2f}, cost={vp.cost:.2f}"

# Set up scene
scene.on_key = on_key

# Create timer for camera animation
timer = mcrfpy.Timer("camera_update", update_camera, 16)

# Activate scene
mcrfpy.current_scene = scene

print()
print("Navigation Demo loaded!")
print(f"A {GRID_W}x{GRID_H} terrain with VoxelPoint navigation grid.")
print()
print("Left: 3D terrain view")
print("Right: 2D minimap with ColorLayer overlays")
print("  - Terrain layer shows heightmap colors")
print("  - Path layer shows computed A* path (yellow)")
print("  - FOV layer shows visible cells (blue tint)")
print()
print("Controls:")
print("  [WASD] Move start point (green)")
print("  [IJKL] Move end point (red)")
print("  [F] Toggle FOV display")
print("  [P] Toggle path display")
print("  [Space] Toggle camera orbit")
print("  [ESC] Quit")
