#!/usr/bin/env python3
"""
Cookbook Screenshot Showcase - Visual examples for cookbook recipes!

Generates beautiful screenshots for cookbook pages.
Run with: xvfb-run -a ./build/mcrogueface --headless --exec tests/demo/cookbook_showcase.py

In headless mode, automation.screenshot() is SYNCHRONOUS - no timer dance needed!
"""
import mcrfpy
from mcrfpy import automation
import sys
import os

# Output directory - in the docs site images folder
OUTPUT_DIR = "/opt/goblincorps/repos/mcrogueface.github.io/images/cookbook"

# Tile sprites from the labeled tileset
TILES = {
    'player_knight': 84,
    'player_mage': 85,
    'player_rogue': 86,
    'player_warrior': 87,
    'enemy_slime': 108,
    'enemy_orc': 120,
    'enemy_skeleton': 123,
    'floor_stone': 42,
    'wall_stone': 30,
    'wall_brick': 14,
    'torch': 72,
    'chest_closed': 89,
    'item_potion': 113,
}


def screenshot_health_bar():
    """Create a health bar showcase."""
    scene = mcrfpy.Scene("health_bar")

    # Dark background
    bg = mcrfpy.Frame(pos=(0, 0), size=(800, 600))
    bg.fill_color = mcrfpy.Color(20, 20, 30)
    scene.children.append(bg)

    # Title
    title = mcrfpy.Caption(text="Health Bar Recipe", pos=(50, 30))
    title.fill_color = mcrfpy.Color(255, 255, 255)
    title.font_size = 28
    scene.children.append(title)

    subtitle = mcrfpy.Caption(text="Nested frames for dynamic UI elements", pos=(50, 60))
    subtitle.fill_color = mcrfpy.Color(180, 180, 200)
    subtitle.font_size = 16
    scene.children.append(subtitle)

    # Example health bars at different levels
    y_start = 120
    bar_configs = [
        ("Player - Full Health", 100, 100, mcrfpy.Color(50, 200, 50)),
        ("Player - Damaged", 65, 100, mcrfpy.Color(200, 200, 50)),
        ("Player - Critical", 20, 100, mcrfpy.Color(200, 50, 50)),
        ("Boss - 3/4 Health", 750, 1000, mcrfpy.Color(150, 50, 150)),
    ]

    for i, (label, current, maximum, color) in enumerate(bar_configs):
        y = y_start + i * 100

        # Label
        lbl = mcrfpy.Caption(text=label, pos=(50, y))
        lbl.fill_color = mcrfpy.Color(220, 220, 220)
        lbl.font_size = 18
        scene.children.append(lbl)

        # Background bar
        bar_bg = mcrfpy.Frame(pos=(50, y + 30), size=(400, 30))
        bar_bg.fill_color = mcrfpy.Color(40, 40, 50)
        bar_bg.outline = 2
        bar_bg.outline_color = mcrfpy.Color(80, 80, 100)
        scene.children.append(bar_bg)

        # Fill bar (scaled to current/maximum)
        fill_width = int(400 * (current / maximum))
        bar_fill = mcrfpy.Frame(pos=(50, y + 30), size=(fill_width, 30))
        bar_fill.fill_color = color
        scene.children.append(bar_fill)

        # Text overlay
        hp_text = mcrfpy.Caption(text=f"{current}/{maximum}", pos=(60, y + 35))
        hp_text.fill_color = mcrfpy.Color(255, 255, 255)
        hp_text.font_size = 16
        scene.children.append(hp_text)

    scene.activate()
    output_path = os.path.join(OUTPUT_DIR, "ui_health_bar.png")
    automation.screenshot(output_path)
    print(f"  -> {output_path}")


def screenshot_fog_of_war():
    """Create a fog of war showcase."""
    scene = mcrfpy.Scene("fog_of_war")

    texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(
        pos=(50, 80),
        size=(700, 480),
        grid_size=(16, 12),
        texture=texture,
        zoom=2.8
    )
    grid.fill_color = mcrfpy.Color(0, 0, 0)  # Black for unknown areas
    scene.children.append(grid)

    # Title
    title = mcrfpy.Caption(text="Fog of War Recipe", pos=(50, 20))
    title.fill_color = mcrfpy.Color(255, 255, 255)
    title.font_size = 28
    scene.children.append(title)

    subtitle = mcrfpy.Caption(text="Visible, discovered, and unknown areas", pos=(50, 50))
    subtitle.fill_color = mcrfpy.Color(180, 180, 200)
    subtitle.font_size = 16
    scene.children.append(subtitle)

    # Fill floor
    for y in range(12):
        for x in range(16):
            grid.at(x, y).tilesprite = TILES['floor_stone']

    # Add walls
    for x in range(16):
        grid.at(x, 0).tilesprite = TILES['wall_stone']
        grid.at(x, 11).tilesprite = TILES['wall_stone']
    for y in range(12):
        grid.at(0, y).tilesprite = TILES['wall_stone']
        grid.at(15, y).tilesprite = TILES['wall_stone']

    # Interior walls (to break LOS)
    for y in range(3, 8):
        grid.at(8, y).tilesprite = TILES['wall_brick']

    # Player (mage with light)
    player = mcrfpy.Entity(grid_pos=(4, 6), texture=texture, sprite_index=TILES['player_mage'])
    grid.entities.append(player)

    # Hidden enemies on the other side
    enemy1 = mcrfpy.Entity(grid_pos=(12, 4), texture=texture, sprite_index=TILES['enemy_orc'])
    grid.entities.append(enemy1)
    enemy2 = mcrfpy.Entity(grid_pos=(13, 8), texture=texture, sprite_index=TILES['enemy_skeleton'])
    grid.entities.append(enemy2)

    # Torch in visible area
    torch = mcrfpy.Entity(grid_pos=(2, 3), texture=texture, sprite_index=TILES['torch'])
    grid.entities.append(torch)

    grid.center = (4 * 16 + 8, 6 * 16 + 8)

    scene.activate()
    output_path = os.path.join(OUTPUT_DIR, "grid_fog_of_war.png")
    automation.screenshot(output_path)
    print(f"  -> {output_path}")


def screenshot_combat_melee():
    """Create a melee combat showcase."""
    scene = mcrfpy.Scene("combat_melee")

    texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(
        pos=(50, 80),
        size=(700, 480),
        grid_size=(12, 9),
        texture=texture,
        zoom=3.5
    )
    grid.fill_color = mcrfpy.Color(20, 20, 30)
    scene.children.append(grid)

    # Title
    title = mcrfpy.Caption(text="Melee Combat Recipe", pos=(50, 20))
    title.fill_color = mcrfpy.Color(255, 255, 255)
    title.font_size = 28
    scene.children.append(title)

    subtitle = mcrfpy.Caption(text="Bump-to-attack mechanics with damage calculation", pos=(50, 50))
    subtitle.fill_color = mcrfpy.Color(180, 180, 200)
    subtitle.font_size = 16
    scene.children.append(subtitle)

    # Fill with dirt floor (battle arena feel)
    for y in range(9):
        for x in range(12):
            grid.at(x, y).tilesprite = 50  # dirt

    # Brick walls
    for x in range(12):
        grid.at(x, 0).tilesprite = TILES['wall_brick']
        grid.at(x, 8).tilesprite = TILES['wall_brick']
    for y in range(9):
        grid.at(0, y).tilesprite = TILES['wall_brick']
        grid.at(11, y).tilesprite = TILES['wall_brick']

    # Player knight engaging orc!
    player = mcrfpy.Entity(grid_pos=(4, 4), texture=texture, sprite_index=TILES['player_knight'])
    grid.entities.append(player)

    enemy = mcrfpy.Entity(grid_pos=(6, 4), texture=texture, sprite_index=TILES['enemy_orc'])
    grid.entities.append(enemy)

    # Fallen enemy (bones)
    bones = mcrfpy.Entity(grid_pos=(8, 6), texture=texture, sprite_index=75)  # bones
    grid.entities.append(bones)

    # Potion for healing
    potion = mcrfpy.Entity(grid_pos=(3, 2), texture=texture, sprite_index=TILES['item_potion'])
    grid.entities.append(potion)

    grid.center = (5 * 16 + 8, 4 * 16 + 8)

    # Combat log UI
    log_frame = mcrfpy.Frame(pos=(50, 520), size=(700, 60))
    log_frame.fill_color = mcrfpy.Color(30, 30, 40, 220)
    log_frame.outline = 1
    log_frame.outline_color = mcrfpy.Color(60, 60, 80)
    scene.children.append(log_frame)

    msg1 = mcrfpy.Caption(text="You hit the Orc for 8 damage!", pos=(10, 10))
    msg1.fill_color = mcrfpy.Color(255, 200, 100)
    msg1.font_size = 14
    log_frame.children.append(msg1)

    msg2 = mcrfpy.Caption(text="The Orc hits you for 4 damage!", pos=(10, 30))
    msg2.fill_color = mcrfpy.Color(255, 100, 100)
    msg2.font_size = 14
    log_frame.children.append(msg2)

    scene.activate()
    output_path = os.path.join(OUTPUT_DIR, "combat_melee.png")
    automation.screenshot(output_path)
    print(f"  -> {output_path}")


def screenshot_dungeon_generator():
    """Create a dungeon generator showcase."""
    scene = mcrfpy.Scene("dungeon_gen")

    texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(
        pos=(50, 80),
        size=(700, 480),
        grid_size=(24, 16),
        texture=texture,
        zoom=2.0
    )
    grid.fill_color = mcrfpy.Color(10, 10, 15)
    scene.children.append(grid)

    # Title
    title = mcrfpy.Caption(text="Dungeon Generator Recipe", pos=(50, 20))
    title.fill_color = mcrfpy.Color(255, 255, 255)
    title.font_size = 28
    scene.children.append(title)

    subtitle = mcrfpy.Caption(text="Procedural rooms connected by corridors", pos=(50, 50))
    subtitle.fill_color = mcrfpy.Color(180, 180, 200)
    subtitle.font_size = 16
    scene.children.append(subtitle)

    # Fill with walls
    for y in range(16):
        for x in range(24):
            grid.at(x, y).tilesprite = TILES['wall_stone']

    # Carve rooms
    rooms = [
        (2, 2, 6, 5),    # Room 1
        (10, 2, 7, 5),   # Room 2
        (18, 3, 5, 4),   # Room 3
        (2, 9, 5, 5),    # Room 4
        (10, 10, 6, 5),  # Room 5
        (18, 9, 5, 6),   # Room 6
    ]

    for rx, ry, rw, rh in rooms:
        for y in range(ry, ry + rh):
            for x in range(rx, rx + rw):
                if x < 24 and y < 16:
                    grid.at(x, y).tilesprite = TILES['floor_stone']

    # Carve corridors (horizontal and vertical)
    # Room 1 to Room 2
    for x in range(7, 11):
        grid.at(x, 4).tilesprite = 50  # dirt corridor
    # Room 2 to Room 3
    for x in range(16, 19):
        grid.at(x, 4).tilesprite = 50
    # Room 1 to Room 4
    for y in range(6, 10):
        grid.at(4, y).tilesprite = 50
    # Room 2 to Room 5
    for y in range(6, 11):
        grid.at(13, y).tilesprite = 50
    # Room 3 to Room 6
    for y in range(6, 10):
        grid.at(20, y).tilesprite = 50
    # Room 5 to Room 6
    for x in range(15, 19):
        grid.at(x, 12).tilesprite = 50

    # Add player in first room
    player = mcrfpy.Entity(grid_pos=(4, 4), texture=texture, sprite_index=TILES['player_knight'])
    grid.entities.append(player)

    # Add decorations
    grid.entities.append(mcrfpy.Entity(grid_pos=(3, 3), texture=texture, sprite_index=TILES['torch']))
    grid.entities.append(mcrfpy.Entity(grid_pos=(12, 4), texture=texture, sprite_index=TILES['torch']))
    grid.entities.append(mcrfpy.Entity(grid_pos=(19, 11), texture=texture, sprite_index=TILES['chest_closed']))
    grid.entities.append(mcrfpy.Entity(grid_pos=(13, 12), texture=texture, sprite_index=TILES['enemy_slime']))
    grid.entities.append(mcrfpy.Entity(grid_pos=(20, 5), texture=texture, sprite_index=TILES['enemy_skeleton']))

    grid.center = (12 * 16, 8 * 16)

    scene.activate()
    output_path = os.path.join(OUTPUT_DIR, "grid_dungeon_generator.png")
    automation.screenshot(output_path)
    print(f"  -> {output_path}")


def screenshot_floating_text():
    """Create a floating text/damage numbers showcase."""
    scene = mcrfpy.Scene("floating_text")

    texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(
        pos=(50, 100),
        size=(700, 420),
        grid_size=(12, 8),
        texture=texture,
        zoom=3.5
    )
    grid.fill_color = mcrfpy.Color(20, 20, 30)
    scene.children.append(grid)

    # Title
    title = mcrfpy.Caption(text="Floating Text Recipe", pos=(50, 20))
    title.fill_color = mcrfpy.Color(255, 255, 255)
    title.font_size = 28
    scene.children.append(title)

    subtitle = mcrfpy.Caption(text="Animated damage numbers and status messages", pos=(50, 50))
    subtitle.fill_color = mcrfpy.Color(180, 180, 200)
    subtitle.font_size = 16
    scene.children.append(subtitle)

    # Fill floor
    for y in range(8):
        for x in range(12):
            grid.at(x, y).tilesprite = TILES['floor_stone']

    # Walls
    for x in range(12):
        grid.at(x, 0).tilesprite = TILES['wall_stone']
        grid.at(x, 7).tilesprite = TILES['wall_stone']
    for y in range(8):
        grid.at(0, y).tilesprite = TILES['wall_stone']
        grid.at(11, y).tilesprite = TILES['wall_stone']

    # Player and enemy in combat
    player = mcrfpy.Entity(grid_pos=(4, 4), texture=texture, sprite_index=TILES['player_warrior'])
    grid.entities.append(player)

    enemy = mcrfpy.Entity(grid_pos=(7, 4), texture=texture, sprite_index=TILES['enemy_orc'])
    grid.entities.append(enemy)

    grid.center = (5.5 * 16, 4 * 16)

    # Floating damage numbers (as captions positioned over entities)
    # These would normally animate upward
    dmg1 = mcrfpy.Caption(text="-12", pos=(330, 240))
    dmg1.fill_color = mcrfpy.Color(255, 80, 80)
    dmg1.font_size = 24
    scene.children.append(dmg1)

    dmg2 = mcrfpy.Caption(text="-5", pos=(500, 260))
    dmg2.fill_color = mcrfpy.Color(255, 100, 100)
    dmg2.font_size = 20
    scene.children.append(dmg2)

    crit = mcrfpy.Caption(text="CRITICAL!", pos=(280, 200))
    crit.fill_color = mcrfpy.Color(255, 200, 50)
    crit.font_size = 18
    scene.children.append(crit)

    heal = mcrfpy.Caption(text="+8", pos=(320, 280))
    heal.fill_color = mcrfpy.Color(100, 255, 100)
    heal.font_size = 20
    scene.children.append(heal)

    scene.activate()
    output_path = os.path.join(OUTPUT_DIR, "effects_floating_text.png")
    automation.screenshot(output_path)
    print(f"  -> {output_path}")


def screenshot_message_log():
    """Create a message log showcase."""
    scene = mcrfpy.Scene("message_log")

    # Dark background
    bg = mcrfpy.Frame(pos=(0, 0), size=(800, 600))
    bg.fill_color = mcrfpy.Color(20, 20, 30)
    scene.children.append(bg)

    # Title
    title = mcrfpy.Caption(text="Message Log Recipe", pos=(50, 30))
    title.fill_color = mcrfpy.Color(255, 255, 255)
    title.font_size = 28
    scene.children.append(title)

    subtitle = mcrfpy.Caption(text="Scrollable combat and event messages", pos=(50, 60))
    subtitle.fill_color = mcrfpy.Color(180, 180, 200)
    subtitle.font_size = 16
    scene.children.append(subtitle)

    # Message log frame
    log_frame = mcrfpy.Frame(pos=(50, 100), size=(700, 400))
    log_frame.fill_color = mcrfpy.Color(30, 30, 40)
    log_frame.outline = 2
    log_frame.outline_color = mcrfpy.Color(60, 60, 80)
    scene.children.append(log_frame)

    # Sample messages with colors
    messages = [
        ("Welcome to the dungeon!", mcrfpy.Color(200, 200, 255)),
        ("You see a dark corridor ahead.", mcrfpy.Color(180, 180, 180)),
        ("A goblin appears!", mcrfpy.Color(255, 200, 100)),
        ("You hit the Goblin for 8 damage!", mcrfpy.Color(255, 255, 150)),
        ("The Goblin hits you for 3 damage!", mcrfpy.Color(255, 100, 100)),
        ("You hit the Goblin for 12 damage! Critical hit!", mcrfpy.Color(255, 200, 50)),
        ("The Goblin dies!", mcrfpy.Color(150, 255, 150)),
        ("You found a Healing Potion.", mcrfpy.Color(100, 200, 255)),
        ("An Orc blocks your path!", mcrfpy.Color(255, 150, 100)),
        ("You drink the Healing Potion. +15 HP", mcrfpy.Color(100, 255, 100)),
        ("You hit the Orc for 6 damage!", mcrfpy.Color(255, 255, 150)),
        ("The Orc hits you for 8 damage!", mcrfpy.Color(255, 100, 100)),
    ]

    for i, (msg, color) in enumerate(messages):
        caption = mcrfpy.Caption(text=msg, pos=(15, 15 + i * 30))
        caption.fill_color = color
        caption.font_size = 16
        log_frame.children.append(caption)

    # Scroll indicator
    scroll = mcrfpy.Caption(text="▼ More messages below", pos=(580, 370))
    scroll.fill_color = mcrfpy.Color(100, 100, 120)
    scroll.font_size = 12
    log_frame.children.append(scroll)

    scene.activate()
    output_path = os.path.join(OUTPUT_DIR, "ui_message_log.png")
    automation.screenshot(output_path)
    print(f"  -> {output_path}")


def main():
    """Generate all cookbook screenshots!"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=== Cookbook Screenshot Showcase ===")
    print(f"Output: {OUTPUT_DIR}\n")

    showcases = [
        ('Health Bar UI', screenshot_health_bar),
        ('Fog of War', screenshot_fog_of_war),
        ('Melee Combat', screenshot_combat_melee),
        ('Dungeon Generator', screenshot_dungeon_generator),
        ('Floating Text', screenshot_floating_text),
        ('Message Log', screenshot_message_log),
    ]

    for name, func in showcases:
        print(f"Generating {name}...")
        try:
            func()
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()

    print("\n=== All cookbook screenshots generated! ===")
    sys.exit(0)


main()
