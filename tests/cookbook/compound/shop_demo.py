#!/usr/bin/env python3
"""Shop Demo - Multi-grid item transfer with equipment slots

Interactive controls:
    Left click: Pick up / Place item
    Right click: Cancel pickup
    ESC: Return to menu

This demonstrates:
    - ItemManager coordinating multiple grids and slots
    - Different zoom levels for shop vs inventory
    - Equipment slots with type restrictions
    - Item tooltips
    - Transaction tracking (gold display)
"""
import mcrfpy
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.item_manager import ItemManager, ItemSlot, Item, ITEM_DATABASE, get_item


class ShopDemo:
    """Demo showing a shop interface with inventory and equipment."""

    def __init__(self):
        self.scene = mcrfpy.Scene("shop_demo")
        self.ui = self.scene.children
        self.manager = None
        self.gold = 100

        # UI elements for updates
        self.gold_display = None
        self.tooltip = None
        self.item_stats = None

        self.setup()

    def setup(self):
        """Build the shop UI."""
        # Background
        bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=(25, 22, 30))
        self.ui.append(bg)

        # Title
        title = mcrfpy.Caption(
            text="The Adventurer's Shop",
            pos=(512, 25),
            font_size=32,
            fill_color=(255, 220, 100)
        )
        title.outline = 2
        title.outline_color = (80, 60, 0)
        self.ui.append(title)

        # Gold display
        self.gold_display = mcrfpy.Caption(
            text=f"Gold: {self.gold}",
            pos=(900, 25),
            font_size=20,
            fill_color=(255, 215, 0)
        )
        self.ui.append(self.gold_display)

        # Initialize item manager
        self.manager = ItemManager(self.scene)
        self.manager.on_pickup = self._on_pickup
        self.manager.on_drop = self._on_drop

        # Create shop grid (left side, zoomed in)
        self._create_shop_grid()

        # Create player inventory (right side)
        self._create_inventory_grid()

        # Create equipment slots (center)
        self._create_equipment_slots()

        # Tooltip area
        self._create_tooltip_area()

        # Instructions
        instr = mcrfpy.Caption(
            text="Left click: Pick up/Place | Right click: Cancel | Items show stats on hover",
            pos=(512, 740),
            font_size=14,
            fill_color=(150, 150, 150)
        )
        self.ui.append(instr)

    def _create_shop_grid(self):
        """Create the shop's item display grid."""
        # Shop panel
        shop_panel = mcrfpy.Frame(
            pos=(20, 70),
            size=(300, 400),
            fill_color=(40, 35, 50),
            outline=2,
            outline_color=(80, 70, 100)
        )
        self.ui.append(shop_panel)

        shop_label = mcrfpy.Caption(
            text="Shop Inventory",
            pos=(170, 90),
            font_size=18,
            fill_color=(200, 180, 255)
        )
        self.ui.append(shop_label)

        # Shop grid (larger cells for better visibility)
        grid_size = (4, 4)
        cell_size = 64  # Zoomed in
        grid_pixel_size = (grid_size[0] * cell_size, grid_size[1] * cell_size)

        shop_grid = mcrfpy.Grid(
            pos=(40, 120),
            size=grid_pixel_size,
            grid_size=grid_size,
            texture=mcrfpy.default_texture,
            zoom=4.0
        )

        # Fill tile layer with floor tiles
        tile_layer = shop_grid.layers[0]
        tile_layer.fill(46)

        # Add color layer with slight tint
        color_layer = shop_grid.add_layer('color', z_index=-1)
        for y in range(grid_size[1]):
            for x in range(grid_size[0]):
                color_layer.set((x, y), (180, 170, 200, 80))

        self.ui.append(shop_grid)
        self.manager.register_grid("shop", shop_grid, {})

        # Stock the shop
        shop_items = [
            ('longsword', (0, 0)),
            ('shield', (1, 0)),
            ('axe', (2, 0)),
            ('wand', (3, 0)),
            ('health_potion', (0, 1)),
            ('mana_potion', (1, 1)),
            ('str_potion', (2, 1)),
            ('staff', (3, 1)),
            ('buckler', (0, 2)),
            ('hammer', (1, 2)),
            ('spear', (2, 2)),
            ('double_axe', (3, 2)),
        ]

        for item_name, pos in shop_items:
            item = get_item(item_name)
            if item:
                self.manager.add_item_to_grid("shop", pos, item)

    def _create_inventory_grid(self):
        """Create the player's inventory grid."""
        # Inventory panel
        inv_panel = mcrfpy.Frame(
            pos=(704, 70),
            size=(300, 400),
            fill_color=(35, 40, 50),
            outline=2,
            outline_color=(70, 80, 100)
        )
        self.ui.append(inv_panel)

        inv_label = mcrfpy.Caption(
            text="Your Inventory",
            pos=(854, 90),
            font_size=18,
            fill_color=(180, 200, 255)
        )
        self.ui.append(inv_label)

        # Inventory grid (smaller cells, more slots)
        grid_size = (5, 6)
        cell_size = 48
        grid_pixel_size = (grid_size[0] * cell_size, grid_size[1] * cell_size)

        inv_grid = mcrfpy.Grid(
            pos=(729, 120),
            size=grid_pixel_size,
            grid_size=grid_size,
            texture=mcrfpy.default_texture,
            zoom=3.0
        )

        # Fill tile layer with floor tiles
        tile_layer = inv_grid.layers[0]
        tile_layer.fill(46)

        # Add color layer with slight tint
        color_layer = inv_grid.add_layer('color', z_index=-1)
        for y in range(grid_size[1]):
            for x in range(grid_size[0]):
                color_layer.set((x, y), (170, 180, 200, 80))

        self.ui.append(inv_grid)
        self.manager.register_grid("inventory", inv_grid, {})

        # Give player starting items
        starting_items = [
            ('shortsword', (0, 0)),
            ('lesser_health', (1, 0)),
            ('lesser_health', (2, 0)),
        ]

        for item_name, pos in starting_items:
            item = get_item(item_name)
            if item:
                self.manager.add_item_to_grid("inventory", pos, item)

    def _create_equipment_slots(self):
        """Create equipment slots in the center."""
        # Equipment panel
        equip_panel = mcrfpy.Frame(
            pos=(362, 70),
            size=(300, 400),
            fill_color=(45, 40, 35),
            outline=2,
            outline_color=(100, 90, 70)
        )
        self.ui.append(equip_panel)

        equip_label = mcrfpy.Caption(
            text="Equipment",
            pos=(512, 90),
            font_size=18,
            fill_color=(255, 220, 180)
        )
        self.ui.append(equip_label)

        # Character silhouette placeholder
        char_frame = mcrfpy.Frame(
            pos=(437, 150),
            size=(150, 200),
            fill_color=(60, 55, 50),
            outline=1,
            outline_color=(100, 95, 85)
        )
        self.ui.append(char_frame)

        char_label = mcrfpy.Caption(
            text="[Character]",
            pos=(512, 240),
            font_size=14,
            fill_color=(120, 115, 105)
        )
        self.ui.append(char_label)

        # Equipment slots around the character
        slot_size = (64, 64)

        # Weapon slot (left of character)
        weapon_slot = ItemSlot(
            pos=(382, 200),
            size=slot_size,
            slot_type='weapon',
            empty_color=(80, 60, 60),
            valid_color=(60, 100, 60),
            invalid_color=(100, 60, 60),
            filled_color=(100, 80, 80)
        )
        self.ui.append(weapon_slot)
        self.manager.register_slot("weapon", weapon_slot)

        weapon_label = mcrfpy.Caption(
            text="Weapon",
            pos=(414, 270),
            font_size=12,
            fill_color=(200, 180, 180)
        )
        self.ui.append(weapon_label)

        # Shield slot (right of character)
        shield_slot = ItemSlot(
            pos=(578, 200),
            size=slot_size,
            slot_type='shield',
            empty_color=(60, 60, 80),
            valid_color=(60, 100, 60),
            invalid_color=(100, 60, 60),
            filled_color=(80, 80, 100)
        )
        self.ui.append(shield_slot)
        self.manager.register_slot("shield", shield_slot)

        shield_label = mcrfpy.Caption(
            text="Shield",
            pos=(610, 270),
            font_size=12,
            fill_color=(180, 180, 200)
        )
        self.ui.append(shield_label)

        # Consumable slot (below character)
        consumable_slot = ItemSlot(
            pos=(480, 360),
            size=slot_size,
            slot_type='consumable',
            empty_color=(60, 80, 60),
            valid_color=(60, 100, 60),
            invalid_color=(100, 60, 60),
            filled_color=(80, 100, 80)
        )
        self.ui.append(consumable_slot)
        self.manager.register_slot("consumable", consumable_slot)

        consumable_label = mcrfpy.Caption(
            text="Quick Item",
            pos=(512, 430),
            font_size=12,
            fill_color=(180, 200, 180)
        )
        self.ui.append(consumable_label)

    def _create_tooltip_area(self):
        """Create area for item tooltips."""
        # Tooltip panel
        tooltip_panel = mcrfpy.Frame(
            pos=(20, 490),
            size=(984, 100),
            fill_color=(30, 30, 40),
            outline=1,
            outline_color=(60, 60, 80)
        )
        self.ui.append(tooltip_panel)

        # Item name
        self.tooltip = mcrfpy.Caption(
            text="Hover over an item to see details",
            pos=(512, 510),
            font_size=18,
            fill_color=(180, 180, 180)
        )
        self.ui.append(self.tooltip)

        # Item stats
        self.item_stats = mcrfpy.Caption(
            text="",
            pos=(512, 545),
            font_size=14,
            fill_color=(150, 150, 180)
        )
        self.ui.append(self.item_stats)

        # Status message
        self.status = mcrfpy.Caption(
            text="",
            pos=(512, 610),
            font_size=16,
            fill_color=(100, 255, 100)
        )
        self.ui.append(self.status)

    def _format_item_stats(self, item):
        """Format item stats for display."""
        stats = []
        if item.atk > 0:
            stats.append(f"+{item.atk} ATK")
        if item.def_ > 0:
            stats.append(f"+{item.def_} DEF")
        if item.stats.get('int_', 0) > 0:
            stats.append(f"+{item.stats['int_']} INT")
        if item.stats.get('range_', 0) > 0:
            stats.append(f"+{item.stats['range_']} Range")
        if item.stats.get('two_handed'):
            stats.append("(Two-handed)")

        stats_str = " | ".join(stats) if stats else "No combat stats"
        return f"{stats_str}  |  Price: {item.price} gold"

    def _on_pickup(self, item, source, pos):
        """Called when item is picked up."""
        self.tooltip.text = f"Holding: {item.name}"
        self.tooltip.fill_color = (100, 200, 255)
        self.item_stats.text = self._format_item_stats(item)

    def _on_drop(self, item, target, pos):
        """Called when item is dropped."""
        self.tooltip.text = f"Placed: {item.name}"
        self.tooltip.fill_color = (100, 255, 100)
        self.item_stats.text = ""

        # Simple transaction feedback (in full version, would handle gold)
        if target == "shop":
            self.status.text = f"Returned {item.name} to shop"
        elif target == "inventory":
            self.status.text = f"Added {item.name} to inventory"
        elif target in ("weapon", "shield", "consumable"):
            self.status.text = f"Equipped {item.name}"

    def on_key(self, key, state):
        """Handle keyboard input."""
        if state != "start":
            return

        if key == "Escape":
            if self.manager.held_item:
                self.manager.cancel_pickup()
                self.tooltip.text = "Cancelled"
                self.tooltip.fill_color = (200, 150, 100)
                self.item_stats.text = ""
                return

            try:
                from cookbook_main import main
                main()
            except:
                sys.exit(0)

    def activate(self):
        """Activate the demo scene."""
        self.scene.on_key = self.on_key
        mcrfpy.current_scene = self.scene


def main():
    """Run the demo."""
    demo = ShopDemo()
    demo.activate()

    # Headless screenshot
    try:
        if mcrfpy.headless_mode():
            from mcrfpy import automation
            # Pick up an item for the screenshot
            demo.manager._pickup_from_grid("shop", (0, 0))
            demo.manager.cursor_frame.x = 450
            demo.manager.cursor_frame.y = 200

            mcrfpy.Timer("screenshot", lambda rt: (
                automation.screenshot("screenshots/compound/shop_demo.png"),
                sys.exit(0)
            ), 100)
    except AttributeError:
        pass


if __name__ == "__main__":
    main()
