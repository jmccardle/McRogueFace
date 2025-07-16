#!/usr/bin/env python3
"""Generate documentation screenshots for McRogueFace UI elements - Simple version"""
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

# Output directory
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

# Screenshot counter
screenshot_count = 0
total_screenshots = 4

def screenshot_and_continue(runtime):
    """Take a screenshot and move to the next scene"""
    global screenshot_count
    
    if screenshot_count == 0:
        # Caption example
        print("Creating Caption example...")
        mcrfpy.createScene("caption_example")
        ui = mcrfpy.sceneUI("caption_example")
        
        bg = mcrfpy.Frame(0, 0, 800, 600, fill_color=FRAME_COLOR)
        ui.append(bg)
        
        title = create_caption(200, 50, "Caption Examples", 32)
        ui.append(title)
        
        caption1 = create_caption(100, 150, "Large Caption (24pt)", 24)
        ui.append(caption1)
        
        caption2 = create_caption(100, 200, "Medium Caption (18pt)", 18, GREEN)
        ui.append(caption2)
        
        caption3 = create_caption(100, 240, "Small Caption (14pt)", 14, RED)
        ui.append(caption3)
        
        caption_bg = mcrfpy.Frame(100, 300, 300, 50, fill_color=BOX_COLOR)
        ui.append(caption_bg)
        caption4 = create_caption(110, 315, "Caption with Background", 16)
        ui.append(caption4)
        
        mcrfpy.setScene("caption_example")
        mcrfpy.setTimer("next1", lambda r: capture_screenshot("ui_caption_example.png"), 200)
        
    elif screenshot_count == 1:
        # Sprite example
        print("Creating Sprite example...")
        mcrfpy.createScene("sprite_example")
        ui = mcrfpy.sceneUI("sprite_example")
        
        bg = mcrfpy.Frame(0, 0, 800, 600, fill_color=FRAME_COLOR)
        ui.append(bg)
        
        title = create_caption(250, 50, "Sprite Examples", 32)
        ui.append(title)
        
        sprite_bg = mcrfpy.Frame(100, 150, 600, 300, fill_color=BOX_COLOR)
        ui.append(sprite_bg)
        
        player_label = create_caption(150, 180, "Player", 14)
        ui.append(player_label)
        player_sprite = mcrfpy.Sprite(150, 200, sprite_texture, 84, 3.0)
        ui.append(player_sprite)
        
        enemy_label = create_caption(250, 180, "Enemies", 14)
        ui.append(enemy_label)
        enemy1 = mcrfpy.Sprite(250, 200, sprite_texture, 123, 3.0)
        ui.append(enemy1)
        enemy2 = mcrfpy.Sprite(300, 200, sprite_texture, 107, 3.0)
        ui.append(enemy2)
        
        boulder_label = create_caption(400, 180, "Boulder", 14)
        ui.append(boulder_label)
        boulder_sprite = mcrfpy.Sprite(400, 200, sprite_texture, 66, 3.0)
        ui.append(boulder_sprite)
        
        exit_label = create_caption(500, 180, "Exit States", 14)
        ui.append(exit_label)
        exit_locked = mcrfpy.Sprite(500, 200, sprite_texture, 45, 3.0)
        ui.append(exit_locked)
        exit_open = mcrfpy.Sprite(550, 200, sprite_texture, 21, 3.0)
        ui.append(exit_open)
        
        mcrfpy.setScene("sprite_example")
        mcrfpy.setTimer("next2", lambda r: capture_screenshot("ui_sprite_example.png"), 200)
        
    elif screenshot_count == 2:
        # Frame example
        print("Creating Frame example...")
        mcrfpy.createScene("frame_example")
        ui = mcrfpy.sceneUI("frame_example")
        
        bg = mcrfpy.Frame(0, 0, 800, 600, fill_color=SHADOW_COLOR)
        ui.append(bg)
        
        title = create_caption(250, 30, "Frame Examples", 32)
        ui.append(title)
        
        frame1 = mcrfpy.Frame(50, 100, 200, 150, fill_color=FRAME_COLOR)
        ui.append(frame1)
        label1 = create_caption(60, 110, "Basic Frame", 16)
        ui.append(label1)
        
        frame2 = mcrfpy.Frame(300, 100, 200, 150, fill_color=BOX_COLOR, 
                             outline_color=WHITE, outline=2.0)
        ui.append(frame2)
        label2 = create_caption(310, 110, "Frame with Outline", 16)
        ui.append(label2)
        
        frame3 = mcrfpy.Frame(550, 100, 200, 150, fill_color=FRAME_COLOR,
                             outline_color=WHITE, outline=1)
        ui.append(frame3)
        inner_frame = mcrfpy.Frame(570, 130, 160, 90, fill_color=BOX_COLOR)
        ui.append(inner_frame)
        label3 = create_caption(560, 110, "Nested Frames", 16)
        ui.append(label3)
        
        mcrfpy.setScene("frame_example")
        mcrfpy.setTimer("next3", lambda r: capture_screenshot("ui_frame_example.png"), 200)
        
    elif screenshot_count == 3:
        # Grid example  
        print("Creating Grid example...")
        mcrfpy.createScene("grid_example")
        ui = mcrfpy.sceneUI("grid_example")
        
        bg = mcrfpy.Frame(0, 0, 800, 600, fill_color=FRAME_COLOR)
        ui.append(bg)
        
        title = create_caption(250, 30, "Grid Example", 32)
        ui.append(title)
        
        grid = mcrfpy.Grid(20, 15, sprite_texture, 
                          mcrfpy.Vector(100, 100), mcrfpy.Vector(320, 240))
        
        # Set up dungeon tiles
        for x in range(20):
            for y in range(15):
                if x == 0 or x == 19 or y == 0 or y == 14:
                    # Walls
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
        grid.at((10, 7)).tilesprite = 131
        grid.at((10, 7)).walkable = True
        
        ui.append(grid)
        
        grid_label = create_caption(100, 480, "20x15 Grid - Simple Dungeon Layout", 16)
        ui.append(grid_label)
        
        mcrfpy.setScene("grid_example")
        mcrfpy.setTimer("next4", lambda r: capture_screenshot("ui_grid_example.png"), 200)
        
    else:
        print("\nAll screenshots captured successfully!")
        print(f"Screenshots saved to: {output_dir}/")
        mcrfpy.exit()
        return
        
def capture_screenshot(filename):
    """Capture a screenshot"""
    global screenshot_count
    full_path = f"{output_dir}/{filename}"
    result = automation.screenshot(full_path)
    print(f"Screenshot {screenshot_count + 1}/{total_screenshots}: {filename} - {'Success' if result else 'Failed'}")
    screenshot_count += 1
    
    # Schedule next scene
    mcrfpy.setTimer("continue", screenshot_and_continue, 300)

# Start the process
print("Starting screenshot generation...")
mcrfpy.setTimer("start", screenshot_and_continue, 500)

# Safety timeout
mcrfpy.setTimer("safety", lambda r: mcrfpy.exit(), 30000)

print("Setup complete. Game loop starting...")