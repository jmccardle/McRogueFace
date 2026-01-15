#!/usr/bin/env python3
"""
Tutorial Screenshot Showcase - ALL THE SCREENSHOTS!

Generates beautiful screenshots for all tutorial parts.
Run with: xvfb-run -a ./build/mcrogueface --headless --exec tests/demo/tutorial_showcase.py

In headless mode, automation.screenshot() is SYNCHRONOUS - no timer dance needed!
"""
import mcrfpy
from mcrfpy import automation
import sys
import os

# Output directory
OUTPUT_DIR = "/opt/goblincorps/repos/mcrogueface.github.io/images/tutorials"

# Tile meanings from the labeled tileset - the FUN sprites!
TILES = {
    # Players - knights and heroes!
    'player_knight': 84,
    'player_mage': 85,
    'player_rogue': 86,
    'player_warrior': 87,
    'player_archer': 88,
    'player_alt1': 96,
    'player_alt2': 97,
    'player_alt3': 98,

    # Enemies - scary!
    'enemy_slime': 108,
    'enemy_bat': 109,
    'enemy_spider': 110,
    'enemy_rat': 111,
    'enemy_orc': 120,
    'enemy_troll': 121,
    'enemy_ghost': 122,
    'enemy_skeleton': 123,
    'enemy_demon': 124,
    'enemy_boss': 92,

    # Terrain
    'floor_stone': 42,
    'floor_wood': 49,
    'floor_grass': 48,
    'floor_dirt': 50,
    'wall_stone': 30,
    'wall_brick': 14,
    'wall_mossy': 28,

    # Items
    'item_potion': 113,
    'item_scroll': 114,
    'item_key': 115,
    'item_coin': 116,

    # Equipment
    'equip_sword': 101,
    'equip_shield': 102,
    'equip_helm': 103,
    'equip_armor': 104,

    # Chests and doors
    'chest_closed': 89,
    'chest_open': 90,
    'door_closed': 33,
    'door_open': 35,

    # Decorations
    'torch': 72,
    'barrel': 73,
    'skull': 74,
    'bones': 75,
}


class TutorialShowcase:
    """Creates beautiful showcase screenshots for tutorials."""

    def __init__(self, scene_name, output_name):
        self.scene = mcrfpy.Scene(scene_name)
        self.output_path = os.path.join(OUTPUT_DIR, output_name)
        self.grid = None

    def setup_grid(self, width, height, zoom=3.0):
        """Create a grid with nice defaults."""
        texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
        self.grid = mcrfpy.Grid(
            pos=(50, 80),
            size=(700, 500),
            grid_size=(width, height),
            texture=texture,
            zoom=zoom
        )
        self.grid.fill_color = mcrfpy.Color(20, 20, 30)
        self.scene.children.append(self.grid)
        self.texture = texture
        return self.grid

    def add_title(self, text, subtitle=None):
        """Add a title to the scene."""
        title = mcrfpy.Caption(text=text, pos=(50, 20))
        title.fill_color = mcrfpy.Color(255, 255, 255)
        title.font_size = 28
        self.scene.children.append(title)

        if subtitle:
            sub = mcrfpy.Caption(text=subtitle, pos=(50, 50))
            sub.fill_color = mcrfpy.Color(180, 180, 200)
            sub.font_size = 16
            self.scene.children.append(sub)

    def fill_floor(self, tile=None):
        """Fill grid with floor tiles."""
        if tile is None:
            tile = TILES['floor_stone']
        w, h = int(self.grid.grid_size[0]), int(self.grid.grid_size[1])
        for y in range(h):
            for x in range(w):
                self.grid.at(x, y).tilesprite = tile

    def add_walls(self, tile=None):
        """Add wall border."""
        if tile is None:
            tile = TILES['wall_stone']
        w, h = int(self.grid.grid_size[0]), int(self.grid.grid_size[1])
        for x in range(w):
            self.grid.at(x, 0).tilesprite = tile
            self.grid.at(x, 0).walkable = False
            self.grid.at(x, h-1).tilesprite = tile
            self.grid.at(x, h-1).walkable = False
        for y in range(h):
            self.grid.at(0, y).tilesprite = tile
            self.grid.at(0, y).walkable = False
            self.grid.at(w-1, y).tilesprite = tile
            self.grid.at(w-1, y).walkable = False

    def add_entity(self, x, y, sprite):
        """Add an entity to the grid."""
        entity = mcrfpy.Entity(
            grid_pos=(x, y),
            texture=self.texture,
            sprite_index=sprite
        )
        self.grid.entities.append(entity)
        return entity

    def center_on(self, x, y):
        """Center camera on a position."""
        self.grid.center = (x * 16 + 8, y * 16 + 8)

    def screenshot(self):
        """Take the screenshot - synchronous in headless mode!"""
        self.scene.activate()
        result = automation.screenshot(self.output_path)
        print(f"  -> {self.output_path} (result: {result})")
        return result


def part01_grid_movement():
    """Part 1: Grid Movement - Knight in a dungeon room."""
    showcase = TutorialShowcase("part01", "part_01_grid_movement.png")
    showcase.setup_grid(12, 9, zoom=3.5)
    showcase.add_title("Part 1: The '@' and the Dungeon Grid",
                       "Creating a grid, placing entities, handling input")

    showcase.fill_floor(TILES['floor_stone'])
    showcase.add_walls(TILES['wall_stone'])

    # Add the player (a cool knight, not boring @)
    showcase.add_entity(6, 4, TILES['player_knight'])

    # Add some decorations to make it interesting
    showcase.add_entity(2, 2, TILES['torch'])
    showcase.add_entity(9, 2, TILES['torch'])
    showcase.add_entity(2, 6, TILES['barrel'])
    showcase.add_entity(9, 6, TILES['skull'])

    showcase.center_on(6, 4)
    showcase.screenshot()


def part02_tiles_collision():
    """Part 2: Tiles and Collision - Walls and walkability."""
    showcase = TutorialShowcase("part02", "part_02_tiles_collision.png")
    showcase.setup_grid(14, 10, zoom=3.0)
    showcase.add_title("Part 2: Tiles, Collision, and Walkability",
                       "Different tile types and blocking movement")

    showcase.fill_floor(TILES['floor_stone'])
    showcase.add_walls(TILES['wall_brick'])

    # Create some interior walls to show collision
    for y in range(2, 5):
        showcase.grid.at(5, y).tilesprite = TILES['wall_stone']
        showcase.grid.at(5, y).walkable = False
    for y in range(5, 8):
        showcase.grid.at(9, y).tilesprite = TILES['wall_stone']
        showcase.grid.at(9, y).walkable = False

    # Add a door
    showcase.grid.at(5, 5).tilesprite = TILES['door_closed']
    showcase.grid.at(5, 5).walkable = False

    # Player navigating the maze
    showcase.add_entity(3, 4, TILES['player_warrior'])

    # Chest as goal
    showcase.add_entity(11, 5, TILES['chest_closed'])

    showcase.center_on(7, 5)
    showcase.screenshot()


def part03_dungeon_generation():
    """Part 3: Dungeon Generation - Procedural rooms and corridors."""
    showcase = TutorialShowcase("part03", "part_03_dungeon_generation.png")
    showcase.setup_grid(20, 14, zoom=2.5)
    showcase.add_title("Part 3: Procedural Dungeon Generation",
                       "Random rooms connected by corridors")

    # Fill with walls first
    for y in range(14):
        for x in range(20):
            showcase.grid.at(x, y).tilesprite = TILES['wall_stone']
            showcase.grid.at(x, y).walkable = False

    # Carve out two rooms
    # Room 1 (left)
    for y in range(3, 8):
        for x in range(2, 8):
            showcase.grid.at(x, y).tilesprite = TILES['floor_stone']
            showcase.grid.at(x, y).walkable = True

    # Room 2 (right)
    for y in range(6, 12):
        for x in range(12, 18):
            showcase.grid.at(x, y).tilesprite = TILES['floor_stone']
            showcase.grid.at(x, y).walkable = True

    # Corridor connecting them
    for x in range(7, 13):
        showcase.grid.at(x, 6).tilesprite = TILES['floor_dirt']
        showcase.grid.at(x, 6).walkable = True
    for y in range(6, 9):
        showcase.grid.at(12, y).tilesprite = TILES['floor_dirt']
        showcase.grid.at(12, y).walkable = True

    # Player in first room
    showcase.add_entity(4, 5, TILES['player_knight'])

    # Some loot in second room
    showcase.add_entity(14, 9, TILES['chest_closed'])
    showcase.add_entity(16, 8, TILES['item_potion'])

    # Torches
    showcase.add_entity(3, 3, TILES['torch'])
    showcase.add_entity(6, 3, TILES['torch'])
    showcase.add_entity(13, 7, TILES['torch'])

    showcase.center_on(10, 7)
    showcase.screenshot()


def part04_fov():
    """Part 4: Field of View - Showing explored vs visible areas."""
    showcase = TutorialShowcase("part04", "part_04_fov.png")
    showcase.setup_grid(16, 12, zoom=2.8)
    showcase.add_title("Part 4: Field of View and Fog of War",
                       "What the player can see vs. the unknown")

    showcase.fill_floor(TILES['floor_stone'])
    showcase.add_walls(TILES['wall_brick'])

    # Some interior pillars to block sight
    for pos in [(5, 4), (5, 7), (10, 5), (10, 8)]:
        showcase.grid.at(pos[0], pos[1]).tilesprite = TILES['wall_mossy']
        showcase.grid.at(pos[0], pos[1]).walkable = False

    # Player with "light"
    showcase.add_entity(8, 6, TILES['player_mage'])

    # Hidden enemy (player wouldn't see this!)
    showcase.add_entity(12, 3, TILES['enemy_ghost'])

    # Visible enemies
    showcase.add_entity(3, 5, TILES['enemy_bat'])
    showcase.add_entity(6, 8, TILES['enemy_spider'])

    showcase.center_on(8, 6)
    showcase.screenshot()


def part05_enemies():
    """Part 5: Enemies - A dungeon full of monsters."""
    showcase = TutorialShowcase("part05", "part_05_enemies.png")
    showcase.setup_grid(18, 12, zoom=2.5)
    showcase.add_title("Part 5: Adding Enemies",
                       "Different monster types with AI behavior")

    showcase.fill_floor(TILES['floor_stone'])
    showcase.add_walls(TILES['wall_stone'])

    # The hero
    showcase.add_entity(3, 5, TILES['player_warrior'])

    # A variety of enemies
    showcase.add_entity(7, 3, TILES['enemy_slime'])
    showcase.add_entity(10, 6, TILES['enemy_bat'])
    showcase.add_entity(8, 8, TILES['enemy_spider'])
    showcase.add_entity(14, 4, TILES['enemy_orc'])
    showcase.add_entity(15, 8, TILES['enemy_skeleton'])
    showcase.add_entity(12, 5, TILES['enemy_rat'])

    # Boss at the end
    showcase.add_entity(15, 6, TILES['enemy_boss'])

    # Some decorations
    showcase.add_entity(5, 2, TILES['bones'])
    showcase.add_entity(13, 9, TILES['skull'])
    showcase.add_entity(2, 8, TILES['torch'])
    showcase.add_entity(16, 2, TILES['torch'])

    showcase.center_on(9, 5)
    showcase.screenshot()


def part06_combat():
    """Part 6: Combat - Battle in progress!"""
    showcase = TutorialShowcase("part06", "part_06_combat.png")
    showcase.setup_grid(14, 10, zoom=3.0)
    showcase.add_title("Part 6: Combat System",
                       "HP, attack, defense, and turn-based fighting")

    showcase.fill_floor(TILES['floor_dirt'])
    showcase.add_walls(TILES['wall_brick'])

    # Battle scene - player vs enemy
    showcase.add_entity(5, 5, TILES['player_knight'])
    showcase.add_entity(8, 5, TILES['enemy_orc'])

    # Fallen enemies (show combat has happened)
    showcase.add_entity(4, 3, TILES['bones'])
    showcase.add_entity(9, 7, TILES['skull'])

    # Equipment the player has
    showcase.add_entity(3, 6, TILES['equip_shield'])
    showcase.add_entity(10, 4, TILES['item_potion'])

    showcase.center_on(6, 5)
    showcase.screenshot()


def part07_ui():
    """Part 7: User Interface - Health bars and menus."""
    showcase = TutorialShowcase("part07", "part_07_ui.png")
    showcase.setup_grid(12, 8, zoom=3.0)
    showcase.add_title("Part 7: User Interface",
                       "Health bars, message logs, and menus")

    showcase.fill_floor(TILES['floor_wood'])
    showcase.add_walls(TILES['wall_brick'])

    # Player
    showcase.add_entity(6, 4, TILES['player_rogue'])

    # Some items to interact with
    showcase.add_entity(4, 3, TILES['chest_open'])
    showcase.add_entity(8, 5, TILES['item_coin'])

    # Add UI overlay example - health bar frame
    ui_frame = mcrfpy.Frame(pos=(50, 520), size=(200, 40))
    ui_frame.fill_color = mcrfpy.Color(40, 40, 50, 200)
    ui_frame.outline = 2
    ui_frame.outline_color = mcrfpy.Color(80, 80, 100)
    showcase.scene.children.append(ui_frame)

    # Health label
    hp_label = mcrfpy.Caption(text="HP: 45/50", pos=(10, 10))
    hp_label.fill_color = mcrfpy.Color(255, 100, 100)
    hp_label.font_size = 18
    ui_frame.children.append(hp_label)

    # Health bar background
    hp_bg = mcrfpy.Frame(pos=(90, 12), size=(100, 16))
    hp_bg.fill_color = mcrfpy.Color(60, 20, 20)
    ui_frame.children.append(hp_bg)

    # Health bar fill
    hp_fill = mcrfpy.Frame(pos=(90, 12), size=(90, 16))  # 90% health
    hp_fill.fill_color = mcrfpy.Color(200, 50, 50)
    ui_frame.children.append(hp_fill)

    showcase.center_on(6, 4)
    showcase.screenshot()


def main():
    """Generate all showcase screenshots!"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=== Tutorial Screenshot Showcase ===")
    print(f"Output: {OUTPUT_DIR}\n")

    showcases = [
        ('Part 1: Grid Movement', part01_grid_movement),
        ('Part 2: Tiles & Collision', part02_tiles_collision),
        ('Part 3: Dungeon Generation', part03_dungeon_generation),
        ('Part 4: Field of View', part04_fov),
        ('Part 5: Enemies', part05_enemies),
        ('Part 6: Combat', part06_combat),
        ('Part 7: UI', part07_ui),
    ]

    for name, func in showcases:
        print(f"Generating {name}...")
        try:
            func()
        except Exception as e:
            print(f"  ERROR: {e}")

    print("\n=== All screenshots generated! ===")
    sys.exit(0)


main()
