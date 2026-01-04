#!/usr/bin/env python3
"""Generate documentation screenshots for McRogueFace UI elements"""
import mcrfpy
from mcrfpy import automation
import sys
import os

# Crypt of Sokoban color scheme
FRAME_COLOR = mcrfpy.Color(64, 64, 128)
SHADOW_COLOR = mcrfpy.Color(64, 64, 86)
BOX_COLOR = mcrfpy.Color(96, 96, 160)
WHITE = mcrfpy.Color(255, 255, 255)
BLACK = mcrfpy.Color(0, 0, 0)
GREEN = mcrfpy.Color(0, 255, 0)
RED = mcrfpy.Color(255, 0, 0)

# Create texture for sprites
sprite_texture = mcrfpy.Texture("assets/kenney_TD_MR_IP.png", 16, 16)

# Output directory - create it during setup
output_dir = "mcrogueface.github.io/images"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

def create_caption(x, y, text, font_size=16, text_color=WHITE, outline_color=BLACK):
    """Helper function to create captions with common settings"""
    caption = mcrfpy.Caption(mcrfpy.Vector(x, y), text=text)
    caption.size = font_size
    caption.fill_color = text_color
    caption.outline_color = outline_color
    return caption

def create_caption_example():
    """Create a scene showing Caption UI element examples"""
    caption_example = mcrfpy.Scene("caption_example")
    ui = caption_example.children
    
    # Background frame
    bg = mcrfpy.Frame(0, 0, 800, 600, fill_color=FRAME_COLOR)
    ui.append(bg)
    
    # Title caption
    title = create_caption(200, 50, "Caption Examples", 32)
    ui.append(title)
    
    # Different sized captions
    caption1 = create_caption(100, 150, "Large Caption (24pt)", 24)
    ui.append(caption1)
    
    caption2 = create_caption(100, 200, "Medium Caption (18pt)", 18, GREEN)
    ui.append(caption2)
    
    caption3 = create_caption(100, 240, "Small Caption (14pt)", 14, RED)
    ui.append(caption3)
    
    # Caption with background
    caption_bg = mcrfpy.Frame(100, 300, 300, 50, fill_color=BOX_COLOR)
    ui.append(caption_bg)
    caption4 = create_caption(110, 315, "Caption with Background", 16)
    ui.append(caption4)

def create_sprite_example():
    """Create a scene showing Sprite UI element examples"""
    sprite_example = mcrfpy.Scene("sprite_example")
    ui = sprite_example.children
    
    # Background frame
    bg = mcrfpy.Frame(0, 0, 800, 600, fill_color=FRAME_COLOR)
    ui.append(bg)
    
    # Title
    title = create_caption(250, 50, "Sprite Examples", 32)
    ui.append(title)
    
    # Create a grid background for sprites
    sprite_bg = mcrfpy.Frame(100, 150, 600, 300, fill_color=BOX_COLOR)
    ui.append(sprite_bg)
    
    # Player sprite (84)
    player_label = create_caption(150, 180, "Player", 14)
    ui.append(player_label)
    player_sprite = mcrfpy.Sprite(150, 200, sprite_texture, 84, 3.0)
    ui.append(player_sprite)
    
    # Enemy sprites
    enemy_label = create_caption(250, 180, "Enemies", 14)
    ui.append(enemy_label)
    enemy1 = mcrfpy.Sprite(250, 200, sprite_texture, 123, 3.0)  # Basic enemy
    ui.append(enemy1)
    enemy2 = mcrfpy.Sprite(300, 200, sprite_texture, 107, 3.0)  # Different enemy
    ui.append(enemy2)
    
    # Boulder sprite (66)
    boulder_label = create_caption(400, 180, "Boulder", 14)
    ui.append(boulder_label)
    boulder_sprite = mcrfpy.Sprite(400, 200, sprite_texture, 66, 3.0)
    ui.append(boulder_sprite)
    
    # Exit sprites
    exit_label = create_caption(500, 180, "Exit States", 14)
    ui.append(exit_label)
    exit_locked = mcrfpy.Sprite(500, 200, sprite_texture, 45, 3.0)  # Locked
    ui.append(exit_locked)
    exit_open = mcrfpy.Sprite(550, 200, sprite_texture, 21, 3.0)  # Open
    ui.append(exit_open)
    
    # Item sprites
    item_label = create_caption(150, 300, "Items", 14)
    ui.append(item_label)
    treasure = mcrfpy.Sprite(150, 320, sprite_texture, 89, 3.0)  # Treasure
    ui.append(treasure)
    sword = mcrfpy.Sprite(200, 320, sprite_texture, 222, 3.0)  # Sword
    ui.append(sword)
    potion = mcrfpy.Sprite(250, 320, sprite_texture, 175, 3.0)  # Potion
    ui.append(potion)
    
    # Button sprite
    button_label = create_caption(350, 300, "Button", 14)
    ui.append(button_label)
    button = mcrfpy.Sprite(350, 320, sprite_texture, 250, 3.0)
    ui.append(button)

def create_frame_example():
    """Create a scene showing Frame UI element examples"""
    frame_example = mcrfpy.Scene("frame_example")
    ui = frame_example.children
    
    # Background
    bg = mcrfpy.Frame(0, 0, 800, 600, fill_color=SHADOW_COLOR)
    ui.append(bg)
    
    # Title
    title = create_caption(250, 30, "Frame Examples", 32)
    ui.append(title)
    
    # Basic frame
    frame1 = mcrfpy.Frame(50, 100, 200, 150, fill_color=FRAME_COLOR)
    ui.append(frame1)
    label1 = create_caption(60, 110, "Basic Frame", 16)
    ui.append(label1)
    
    # Frame with outline
    frame2 = mcrfpy.Frame(300, 100, 200, 150, fill_color=BOX_COLOR, 
                         outline_color=WHITE, outline=2.0)
    ui.append(frame2)
    label2 = create_caption(310, 110, "Frame with Outline", 16)
    ui.append(label2)
    
    # Nested frames
    frame3 = mcrfpy.Frame(550, 100, 200, 150, fill_color=FRAME_COLOR,
                         outline_color=WHITE, outline=1)
    ui.append(frame3)
    inner_frame = mcrfpy.Frame(570, 130, 160, 90, fill_color=BOX_COLOR)
    ui.append(inner_frame)
    label3 = create_caption(560, 110, "Nested Frames", 16)
    ui.append(label3)
    
    # Complex layout with frames
    main_frame = mcrfpy.Frame(50, 300, 700, 250, fill_color=FRAME_COLOR,
                             outline_color=WHITE, outline=2)
    ui.append(main_frame)
    
    # Add some UI elements inside
    ui_label = create_caption(60, 310, "Complex UI Layout", 18)
    ui.append(ui_label)
    
    # Status panel
    status_frame = mcrfpy.Frame(70, 350, 150, 180, fill_color=BOX_COLOR)
    ui.append(status_frame)
    status_label = create_caption(80, 360, "Status", 14)
    ui.append(status_label)
    
    # Inventory panel
    inv_frame = mcrfpy.Frame(240, 350, 300, 180, fill_color=BOX_COLOR)
    ui.append(inv_frame)
    inv_label = create_caption(250, 360, "Inventory", 14)
    ui.append(inv_label)
    
    # Actions panel
    action_frame = mcrfpy.Frame(560, 350, 170, 180, fill_color=BOX_COLOR)
    ui.append(action_frame)
    action_label = create_caption(570, 360, "Actions", 14)
    ui.append(action_label)

def create_grid_example():
    """Create a scene showing Grid UI element examples"""
    grid_example = mcrfpy.Scene("grid_example")
    ui = grid_example.children
    
    # Background
    bg = mcrfpy.Frame(0, 0, 800, 600, fill_color=FRAME_COLOR)
    ui.append(bg)
    
    # Title
    title = create_caption(250, 30, "Grid Example", 32)
    ui.append(title)
    
    # Create a grid showing a small dungeon
    grid = mcrfpy.Grid(20, 15, sprite_texture, 
                      mcrfpy.Vector(100, 100), mcrfpy.Vector(320, 240))
    
    # Set up dungeon tiles
    # Floor tiles (index 48)
    # Wall tiles (index 3)
    for x in range(20):
        for y in range(15):
            if x == 0 or x == 19 or y == 0 or y == 14:
                # Walls around edge
                grid.at((x, y)).tilesprite = 3
                grid.at((x, y)).walkable = False
            else:
                # Floor
                grid.at((x, y)).tilesprite = 48
                grid.at((x, y)).walkable = True
    
    # Add some internal walls
    for x in range(5, 15):
        grid.at((x, 7)).tilesprite = 3
        grid.at((x, 7)).walkable = False
    for y in range(3, 8):
        grid.at((10, y)).tilesprite = 3
        grid.at((10, y)).walkable = False
    
    # Add a door
    grid.at((10, 7)).tilesprite = 131  # Door tile
    grid.at((10, 7)).walkable = True
    
    # Add to UI
    ui.append(grid)
    
    # Label
    grid_label = create_caption(100, 480, "20x15 Grid with 2x scale - Simple Dungeon Layout", 16)
    ui.append(grid_label)

def create_entity_example():
    """Create a scene showing Entity examples in a Grid"""
    entity_example = mcrfpy.Scene("entity_example")
    ui = entity_example.children
    
    # Background
    bg = mcrfpy.Frame(0, 0, 800, 600, fill_color=FRAME_COLOR)
    ui.append(bg)
    
    # Title
    title = create_caption(200, 30, "Entity Collection Example", 32)
    ui.append(title)
    
    # Create a grid for the entities
    grid = mcrfpy.Grid(15, 10, sprite_texture,
                      mcrfpy.Vector(150, 100), mcrfpy.Vector(360, 240))
    
    # Set all tiles to floor
    for x in range(15):
        for y in range(10):
            grid.at((x, y)).tilesprite = 48
            grid.at((x, y)).walkable = True
    
    # Add walls
    for x in range(15):
        grid.at((x, 0)).tilesprite = 3
        grid.at((x, 0)).walkable = False
        grid.at((x, 9)).tilesprite = 3
        grid.at((x, 9)).walkable = False
    for y in range(10):
        grid.at((0, y)).tilesprite = 3
        grid.at((0, y)).walkable = False
        grid.at((14, y)).tilesprite = 3
        grid.at((14, y)).walkable = False
    
    ui.append(grid)
    
    # Add entities to the grid
    # Player entity
    player = mcrfpy.Entity(mcrfpy.Vector(3, 3), sprite_texture, 84, grid)
    grid.entities.append(player)
    
    # Enemy entities
    enemy1 = mcrfpy.Entity(mcrfpy.Vector(7, 4), sprite_texture, 123, grid)
    grid.entities.append(enemy1)
    
    enemy2 = mcrfpy.Entity(mcrfpy.Vector(10, 6), sprite_texture, 107, grid)
    grid.entities.append(enemy2)
    
    # Boulder
    boulder = mcrfpy.Entity(mcrfpy.Vector(5, 5), sprite_texture, 66, grid)
    grid.entities.append(boulder)
    
    # Treasure
    treasure = mcrfpy.Entity(mcrfpy.Vector(12, 2), sprite_texture, 89, grid)
    grid.entities.append(treasure)
    
    # Exit (locked)
    exit_door = mcrfpy.Entity(mcrfpy.Vector(12, 8), sprite_texture, 45, grid)
    grid.entities.append(exit_door)
    
    # Button
    button = mcrfpy.Entity(mcrfpy.Vector(3, 7), sprite_texture, 250, grid)
    grid.entities.append(button)
    
    # Items
    sword = mcrfpy.Entity(mcrfpy.Vector(8, 2), sprite_texture, 222, grid)
    grid.entities.append(sword)
    
    potion = mcrfpy.Entity(mcrfpy.Vector(6, 8), sprite_texture, 175, grid)
    grid.entities.append(potion)
    
    # Label
    entity_label = create_caption(150, 500, "Grid with Entity Collection - Game Objects", 16)
    ui.append(entity_label)

def create_combined_example():
    """Create a scene showing all UI elements combined"""
    combined_example = mcrfpy.Scene("combined_example")
    ui = combined_example.children
    
    # Background
    bg = mcrfpy.Frame(0, 0, 800, 600, fill_color=SHADOW_COLOR)
    ui.append(bg)
    
    # Title
    title = create_caption(200, 20, "McRogueFace UI Elements", 28)
    ui.append(title)
    
    # Main game area frame
    game_frame = mcrfpy.Frame(20, 70, 500, 400, fill_color=FRAME_COLOR,
                             outline_color=WHITE, outline=2)
    ui.append(game_frame)
    
    # Grid inside game frame
    grid = mcrfpy.Grid(12, 10, sprite_texture,
                      mcrfpy.Vector(30, 80), mcrfpy.Vector(480, 400))
    for x in range(12):
        for y in range(10):
            if x == 0 or x == 11 or y == 0 or y == 9:
                grid.at((x, y)).tilesprite = 3
                grid.at((x, y)).walkable = False
            else:
                grid.at((x, y)).tilesprite = 48
                grid.at((x, y)).walkable = True
    
    # Add some entities
    player = mcrfpy.Entity(mcrfpy.Vector(2, 2), sprite_texture, 84, grid)
    grid.entities.append(player)
    enemy = mcrfpy.Entity(mcrfpy.Vector(8, 6), sprite_texture, 123, grid)
    grid.entities.append(enemy)
    boulder = mcrfpy.Entity(mcrfpy.Vector(5, 4), sprite_texture, 66, grid)
    grid.entities.append(boulder)
    
    ui.append(grid)
    
    # Status panel
    status_frame = mcrfpy.Frame(540, 70, 240, 200, fill_color=BOX_COLOR,
                               outline_color=WHITE, outline=1)
    ui.append(status_frame)
    
    status_title = create_caption(550, 80, "Status", 20)
    ui.append(status_title)
    
    hp_label = create_caption(550, 120, "HP: 10/10", 16, GREEN)
    ui.append(hp_label)
    
    level_label = create_caption(550, 150, "Level: 1", 16)
    ui.append(level_label)
    
    # Inventory panel
    inv_frame = mcrfpy.Frame(540, 290, 240, 180, fill_color=BOX_COLOR,
                            outline_color=WHITE, outline=1)
    ui.append(inv_frame)
    
    inv_title = create_caption(550, 300, "Inventory", 20)
    ui.append(inv_title)
    
    # Add some item sprites
    item1 = mcrfpy.Sprite(560, 340, sprite_texture, 222, 2.0)
    ui.append(item1)
    item2 = mcrfpy.Sprite(610, 340, sprite_texture, 175, 2.0)
    ui.append(item2)
    
    # Message log
    log_frame = mcrfpy.Frame(20, 490, 760, 90, fill_color=BOX_COLOR,
                            outline_color=WHITE, outline=1)
    ui.append(log_frame)
    
    log_msg = create_caption(30, 500, "Welcome to McRogueFace!", 14)
    ui.append(log_msg)

# Set up all the scenes
print("Creating UI example scenes...")
create_caption_example()
create_sprite_example()
create_frame_example()
create_grid_example()
create_entity_example()
create_combined_example()

# Screenshot state
current_screenshot = 0
screenshots = [
    ("caption_example", "ui_caption_example.png"),
    ("sprite_example", "ui_sprite_example.png"),
    ("frame_example", "ui_frame_example.png"),
    ("grid_example", "ui_grid_example.png"),
    ("entity_example", "ui_entity_example.png"),
    ("combined_example", "ui_combined_example.png")
]

def take_screenshots(timer, runtime):
    """Timer callback to take screenshots sequentially"""
    global current_screenshot

    if current_screenshot >= len(screenshots):
        print("\nAll screenshots captured successfully!")
        print(f"Screenshots saved to: {output_dir}/")
        mcrfpy.exit()
        return

    scene_name, filename = screenshots[current_screenshot]

    # Switch to the scene
    mcrfpy.current_scene = scene_name

    # Take screenshot after a short delay to ensure rendering
    def capture(t, r):
        global current_screenshot
        full_path = f"{output_dir}/{filename}"
        result = automation.screenshot(full_path)
        print(f"Screenshot {current_screenshot + 1}/{len(screenshots)}: {filename} - {'Success' if result else 'Failed'}")

        current_screenshot += 1

        # Schedule next screenshot
        global next_screenshot_timer
        next_screenshot_timer = mcrfpy.Timer("next_screenshot", take_screenshots, 200, once=True)

    # Give scene time to render
    global capture_timer
    capture_timer = mcrfpy.Timer("capture", capture, 100, once=True)

# Start with the first scene
caption_example.activate()

# Start the screenshot process
print(f"\nStarting screenshot capture of {len(screenshots)} scenes...")
start_timer = mcrfpy.Timer("start", take_screenshots, 500, once=True)

# Safety timeout
def safety_exit(timer, runtime):
    print("\nERROR: Safety timeout reached! Exiting...")
    mcrfpy.exit()

safety_timer = mcrfpy.Timer("safety", safety_exit, 30000, once=True)

print("Setup complete. Game loop starting...")