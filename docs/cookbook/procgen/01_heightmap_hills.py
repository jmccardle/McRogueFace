"""HeightMap Hills and Craters Demo

Demonstrates: add_hill, dig_hill
Creates volcanic terrain with mountains and craters using ColorLayer visualization.
"""
import mcrfpy
from mcrfpy import automation

# Full screen grid: 60x48 tiles at 16x16 = 960x768
GRID_WIDTH, GRID_HEIGHT = 64, 48
CELL_SIZE = 16

def height_to_color(h):
    """Convert height value to terrain color."""
    if h < 0.1:
        return mcrfpy.Color(20, 40, int(80 + h * 400))
    elif h < 0.3:
        t = (h - 0.1) / 0.2
        return mcrfpy.Color(int(40 + t * 30), int(60 + t * 40), 30)
    elif h < 0.5:
        t = (h - 0.3) / 0.2
        return mcrfpy.Color(int(70 - t * 20), int(100 + t * 50), int(30 + t * 20))
    elif h < 0.7:
        t = (h - 0.5) / 0.2
        return mcrfpy.Color(int(120 + t * 40), int(100 + t * 30), int(60 + t * 20))
    elif h < 0.85:
        t = (h - 0.7) / 0.15
        return mcrfpy.Color(int(140 + t * 40), int(130 + t * 40), int(120 + t * 40))
    else:
        t = (h - 0.85) / 0.15
        return mcrfpy.Color(int(180 + t * 75), int(180 + t * 75), int(180 + t * 75))

# Setup scene
scene = mcrfpy.Scene("hills_demo")

# Create grid with color layer
grid = mcrfpy.Grid(
    grid_size=(GRID_WIDTH, GRID_HEIGHT),
    pos=(0, 0),
    size=(GRID_WIDTH * CELL_SIZE, GRID_HEIGHT * CELL_SIZE),
    layers={}
)
grid.fill_color = mcrfpy.Color(0, 0, 0)
color_layer = grid.add_layer("color", z_index=-1)
scene.children.append(grid)

# Create heightmap
hmap = mcrfpy.HeightMap((GRID_WIDTH, GRID_HEIGHT), fill=0.3)

# Add volcanic mountains - large hills
hmap.add_hill((15, 24), 18.0, 0.6)  # Central volcano base
hmap.add_hill((15, 24), 10.0, 0.3)  # Volcano peak
hmap.add_hill((45, 15), 12.0, 0.5)  # Eastern mountain
hmap.add_hill((35, 38), 14.0, 0.45) # Southern mountain
hmap.add_hill((8, 10), 8.0, 0.35)   # Small northern hill

# Create craters using dig_hill
hmap.dig_hill((15, 24), 5.0, 0.1)   # Volcanic crater
hmap.dig_hill((45, 15), 4.0, 0.25)  # Eastern crater
hmap.dig_hill((25, 30), 6.0, 0.05)  # Impact crater (deep)
hmap.dig_hill((50, 40), 3.0, 0.2)   # Small crater

# Add some smaller features for variety
for i in range(8):
    x = 5 + (i * 7) % 55
    y = 5 + (i * 11) % 40
    hmap.add_hill((x, y), float(3 + (i % 4)), 0.15)

# Normalize to use full color range
hmap.normalize(0.0, 1.0)

# Apply heightmap to color layer
for y in range(GRID_HEIGHT):
    for x in range(GRID_WIDTH):
        h = hmap.get((x, y))
        color_layer.set((x, y), height_to_color(h))

# Title
title = mcrfpy.Caption(text="HeightMap: add_hill + dig_hill (volcanic terrain)", pos=(10, 10))
title.fill_color = mcrfpy.Color(255, 255, 255)
title.outline = 1
title.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(title)

scene.activate()

# Take screenshot directly (works in headless mode)
automation.screenshot("procgen_01_heightmap_hills.png")
print("Screenshot saved: procgen_01_heightmap_hills.png")
