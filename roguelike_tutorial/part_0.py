"""
McRogueFace Tutorial - Part 0: Introduction to Scene, Texture, and Grid

This tutorial introduces the basic building blocks:
- Scene: A container for UI elements and game state
- Texture: Loading image assets for use in the game
- Grid: A tilemap component for rendering tile-based worlds
"""
import mcrfpy
import random

# Create and activate a new scene
mcrfpy.createScene("tutorial")
mcrfpy.setScene("tutorial")

# Load the texture (4x3 tiles, 64x48 pixels total, 16x16 per tile)
texture = mcrfpy.Texture("assets/tutorial2.png", 16, 16)

# Create a grid of tiles
# Each tile is 16x16 pixels, so with 3x zoom: 16*3 = 48 pixels per tile

grid_width, grid_height = 25, 20 # width, height in number of tiles

# calculating the size in pixels to fit the entire grid on-screen
zoom = 2.0
grid_size = grid_width * zoom * 16, grid_height * zoom * 16

# calculating the position to center the grid on the screen - assuming default 1024x768 resolution
grid_position = (1024 - grid_size[0]) / 2, (768 - grid_size[1]) / 2

grid = mcrfpy.Grid(
    pos=grid_position,
    grid_size=(grid_width, grid_height),
    texture=texture,
    size=grid_size,  # height and width on screen
)

grid.zoom = zoom
grid.center = (grid_width/2.0)*16, (grid_height/2.0)*16 # center on the middle of the central tile

# Define tile types
FLOOR_TILES = [0, 1, 2, 4, 5, 6, 8, 9, 10]
WALL_TILES = [3, 7, 11]

# Fill the grid with a simple pattern
for y in range(grid_height):
    for x in range(grid_width):
        # Create walls around the edges
        if x == 0 or x == grid_width-1 or y == 0 or y == grid_height-1:
            tile_index = random.choice(WALL_TILES)
        else:
            # Fill interior with floor tiles
            tile_index = random.choice(FLOOR_TILES)
        
        # Set the tile at this position
        point = grid.at(x, y)
        if point:
            point.tilesprite = tile_index

# Add the grid to the scene
mcrfpy.sceneUI("tutorial").append(grid)

# Add a title caption
title = mcrfpy.Caption((320, 10),
    text="McRogueFace Tutorial - Part 0",
)
title.fill_color = mcrfpy.Color(255, 255, 255, 255)
mcrfpy.sceneUI("tutorial").append(title)

# Add instructions
instructions = mcrfpy.Caption((280, 750),
    text="Scene + Texture + Grid = Tilemap!",
)
instructions.font_size=18
instructions.fill_color = mcrfpy.Color(200, 200, 200, 255)
mcrfpy.sceneUI("tutorial").append(instructions)

print("Tutorial Part 0 loaded!")
print(f"Created a {grid.grid_size[0]}x{grid.grid_size[1]} grid")
print(f"Grid positioned at ({grid.x}, {grid.y})")
