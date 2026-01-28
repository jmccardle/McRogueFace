#!/usr/bin/env python3
"""Click to Pick Up Demo - Toggle-based inventory interaction

Interactive controls:
    Left click on item: Pick up item (cursor changes)
    Left click on empty cell: Place item
    Right click: Cancel pickup
    ESC: Return to menu

This demonstrates:
    - Click-to-toggle pickup mode (not hold-to-drag)
    - Cursor sprite following mouse
    - ColorLayer for cell highlighting
    - Inventory organization pattern
"""
import mcrfpy
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Item data for sprites
ITEMS = [
    (103, "Shortsword"),
    (104, "Longsword"),
    (117, "Hammer"),
    (119, "Axe"),
    (101, "Buckler"),
    (102, "Shield"),
    (115, "Health Pot"),
    (116, "Mana Pot"),
    (129, "Wand"),
    (130, "Staff"),
    (114, "Str Potion"),
    (127, "Lesser HP"),
]


class ClickPickupDemo:
    """Demo showing click-to-pickup inventory interaction."""

    def __init__(self):
        self.scene = mcrfpy.Scene("demo_click_pickup")
        self.ui = self.scene.children
        self.grid = None
        self.tile_layer = None
        self.color_layer = None

        # Pickup state
        self.held_entity = None
        self.pickup_cell = None
        self.cursor_sprite = None
        self.last_hover_cell = None

        # Track occupied cells
        self.occupied_cells = {}  # (x, y) -> entity

        self.setup()

    def setup(self):
        """Build the demo UI."""
        # Background
        bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=(25, 20, 30))
        self.ui.append(bg)

        # Title
        title = mcrfpy.Caption(
            text="Click to Pick Up",
            pos=(512, 30),
            font_size=28,
            fill_color=(255, 255, 255)
        )
        title.outline = 2
        title.outline_color = (0, 0, 0)
        self.ui.append(title)

        # Status caption
        self.status = mcrfpy.Caption(
            text="Click an item to pick it up",
            pos=(512, 70),
            font_size=16,
            fill_color=(180, 180, 180)
        )
        self.ui.append(self.status)

        # Create inventory grid - zoom in constructor for proper centering
        grid_size = (8, 6)
        cell_size = 64
        grid_pixel_size = (grid_size[0] * cell_size, grid_size[1] * cell_size)
        grid_pos = ((1024 - grid_pixel_size[0]) // 2, 140)

        self.grid = mcrfpy.Grid(
            pos=grid_pos,
            size=grid_pixel_size,
            grid_size=grid_size,
            texture=mcrfpy.default_texture,
            zoom=4.0  # 16px * 4 = 64px per cell
        )

        # Get tile layer and fill with slot tiles
        self.tile_layer = self.grid.layers[0]
        self.tile_layer.fill(46)  # Floor/slot tile

        # Add color layer for highlighting
        self.color_layer = self.grid.add_layer('color', z_index=-1)
        # Initialize with slight tint
        for y in range(grid_size[1]):
            for x in range(grid_size[0]):
                self.color_layer.set((x, y), (200, 200, 200, 50))

        # Add event handlers
        self.grid.on_click = self._on_grid_click
        self.grid.on_cell_enter = self._on_cell_enter
        self.grid.on_move = self._on_grid_move

        self.ui.append(self.grid)

        # Populate with items
        self._populate_grid()

        # Create cursor sprite (initially invisible)
        # This is a Frame with a Sprite child, positioned outside the grid
        self.cursor_frame = mcrfpy.Frame(
            pos=(0, 0),
            size=(64, 64),
            fill_color=(0, 0, 0, 0),  # Transparent
            outline=0
        )
        self.cursor_sprite = mcrfpy.Sprite(
            pos=(0, 0),
            texture=mcrfpy.default_texture,
            sprite_index=0
        )
        self.cursor_sprite.scale = 4.0
        self.cursor_sprite.visible = False
        self.cursor_frame.children.append(self.cursor_sprite)
        self.ui.append(self.cursor_frame)

        # Item name display
        self.item_name = mcrfpy.Caption(
            text="",
            pos=(512, 560),
            font_size=18,
            fill_color=(255, 220, 100)
        )
        self.ui.append(self.item_name)

        # Instructions
        instr = mcrfpy.Caption(
            text="Left click: Pick up / Place | Right click: Cancel | ESC to exit",
            pos=(512, 700),
            font_size=14,
            fill_color=(150, 150, 150)
        )
        self.ui.append(instr)

    def _populate_grid(self):
        """Add items to the grid."""
        # Place items in a pattern
        positions = [
            (0, 0), (2, 0), (4, 1), (6, 0),
            (1, 2), (3, 2), (5, 2), (7, 3),
            (0, 4), (2, 4), (4, 5), (6, 5),
        ]

        for i, (x, y) in enumerate(positions):
            if i >= len(ITEMS):
                break
            sprite_idx, name = ITEMS[i]
            entity = mcrfpy.Entity()
            self.grid.entities.append(entity)
            entity.grid_pos = (x, y)  # Use grid_pos for tile coordinates
            entity.sprite_index = sprite_idx
            entity.name = name  # Store name for display
            self.occupied_cells[(x, y)] = entity

    def _get_grid_cell(self, screen_pos):
        """Convert screen position to grid cell coordinates."""
        cell_size = 16 * self.grid.zoom
        x = int((screen_pos[0] - self.grid.x) / cell_size)
        y = int((screen_pos[1] - self.grid.y) / cell_size)
        grid_w, grid_h = self.grid.grid_size
        if 0 <= x < grid_w and 0 <= y < grid_h:
            return (x, y)
        return None

    def _on_grid_click(self, pos, button, action):
        """Handle grid click."""
        if action != "start":
            return

        cell = self._get_grid_cell(pos)
        if cell is None:
            return

        x, y = cell

        if button == "right":
            # Cancel pickup
            if self.held_entity:
                self._cancel_pickup()
            return

        if button != "left":
            return

        if self.held_entity is None:
            # Try to pick up
            if cell in self.occupied_cells:
                self._pickup_item(cell)
        else:
            # Try to place
            if cell not in self.occupied_cells:
                self._place_item(cell)
            elif cell == self.pickup_cell:
                # Clicked on original cell - cancel
                self._cancel_pickup()

    def _pickup_item(self, cell):
        """Pick up item from cell."""
        entity = self.occupied_cells[cell]
        self.held_entity = entity
        self.pickup_cell = cell

        # Hide the entity
        entity.visible = False

        # Mark source cell yellow
        self.color_layer.set(cell, (255, 255, 100, 200))

        # Setup cursor sprite
        self.cursor_sprite.sprite_index = entity.sprite_index
        self.cursor_sprite.visible = True

        # Update status
        name = getattr(entity, 'name', 'Item')
        self.status.text = f"Holding: {name}"
        self.status.fill_color = (100, 200, 255)
        self.item_name.text = name

    def _place_item(self, cell):
        """Place held item in cell."""
        x, y = cell

        # Move entity to new position
        self.held_entity.grid_pos = (x, y)
        self.held_entity.visible = True

        # Update tracking
        del self.occupied_cells[self.pickup_cell]
        self.occupied_cells[cell] = self.held_entity

        # Clear source cell highlight
        self.color_layer.set(self.pickup_cell, (200, 200, 200, 50))

        # Clear hover highlight
        if self.last_hover_cell and self.last_hover_cell != self.pickup_cell:
            self.color_layer.set(self.last_hover_cell, (200, 200, 200, 50))

        # Hide cursor
        self.cursor_sprite.visible = False

        # Update status
        self.status.text = f"Placed at ({x}, {y})"
        self.status.fill_color = (100, 255, 100)
        self.item_name.text = ""

        self.held_entity = None
        self.pickup_cell = None
        self.last_hover_cell = None

    def _cancel_pickup(self):
        """Cancel current pickup operation."""
        if self.held_entity:
            # Restore entity visibility
            self.held_entity.visible = True

            # Clear source cell highlight
            self.color_layer.set(self.pickup_cell, (200, 200, 200, 50))

            # Clear hover highlight
            if self.last_hover_cell and self.last_hover_cell != self.pickup_cell:
                self.color_layer.set(self.last_hover_cell, (200, 200, 200, 50))

            # Hide cursor
            self.cursor_sprite.visible = False

            self.status.text = "Cancelled"
            self.status.fill_color = (200, 150, 100)
            self.item_name.text = ""

            self.held_entity = None
            self.pickup_cell = None
            self.last_hover_cell = None

    def _on_cell_enter(self, cell_pos):
        """Handle cell hover."""
        x, y = int(cell_pos[0]), int(cell_pos[1])
        cell = (x, y)

        # Show item name on hover (when not holding)
        if self.held_entity is None:
            if cell in self.occupied_cells:
                entity = self.occupied_cells[cell]
                name = getattr(entity, 'name', 'Item')
                self.item_name.text = name
            else:
                self.item_name.text = ""
            return

        # Clear previous hover highlight (if different from source)
        if self.last_hover_cell and self.last_hover_cell != self.pickup_cell:
            self.color_layer.set(self.last_hover_cell, (200, 200, 200, 50))

        # Highlight current cell (if different from source)
        if cell != self.pickup_cell:
            if cell in self.occupied_cells:
                self.color_layer.set(cell, (255, 100, 100, 200))  # Red - can't place
            else:
                self.color_layer.set(cell, (100, 255, 100, 200))  # Green - can place

        self.last_hover_cell = cell

    def _on_grid_move(self, pos):
        """Update cursor sprite position.

        Note: #230 - on_move now only receives position, not button/action
        """
        if self.cursor_sprite.visible:
            # Position cursor centered on mouse
            self.cursor_frame.x = pos[0] - 32
            self.cursor_frame.y = pos[1] - 32

    def on_key(self, key, state):
        """Handle keyboard input."""
        if state != "start":
            return

        if key == "Escape":
            if self.held_entity:
                self._cancel_pickup()
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
    demo = ClickPickupDemo()
    demo.activate()

    # Headless screenshot
    try:
        if mcrfpy.headless_mode():
            from mcrfpy import automation
            # Simulate picking up an item for screenshot
            demo._pickup_item((0, 0))
            demo.cursor_frame.x = 300
            demo.cursor_frame.y = 350

            mcrfpy.Timer("screenshot", lambda rt: (
                automation.screenshot("screenshots/primitives/click_pickup.png"),
                sys.exit(0)
            ), 100)
    except AttributeError:
        pass


if __name__ == "__main__":
    main()
