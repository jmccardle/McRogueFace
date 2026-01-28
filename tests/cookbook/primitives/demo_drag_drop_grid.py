#!/usr/bin/env python3
"""Drag and Drop (Grid) Demo - Drag entities between grid cells

Interactive controls:
    Left click + drag: Move entity to new cell
    ESC: Return to menu

This demonstrates:
    - Grid entity dragging with on_click and on_cell_enter
    - ColorLayer for cell highlighting
    - Collision detection (can't drop on occupied cells)
    - Visual feedback during drag
"""
import mcrfpy
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Item data for sprites
ITEMS = [
    (103, "Shortsword"),   # +1 atk
    (104, "Longsword"),    # +2 atk
    (117, "Hammer"),       # +2 atk
    (119, "Axe"),          # +3 atk
    (101, "Buckler"),      # +1 def
    (102, "Shield"),       # +2 def
    (115, "Health Pot"),
    (116, "Mana Pot"),
    (129, "Wand"),         # +1 atk, +4 int
    (114, "Str Potion"),
]


class GridDragDropDemo:
    """Demo showing entity drag and drop on a grid."""

    def __init__(self):
        self.scene = mcrfpy.Scene("demo_drag_drop_grid")
        self.ui = self.scene.children
        self.grid = None
        self.tile_layer = None
        self.color_layer = None
        self.dragging_entity = None
        self.drag_start_cell = None
        self.occupied_cells = set()  # Track which cells have entities
        self.setup()

    def setup(self):
        """Build the demo UI."""
        # Background
        bg = mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=(20, 25, 30))
        self.ui.append(bg)

        # Title
        title = mcrfpy.Caption(
            text="Grid Drag & Drop",
            pos=(512, 30),
            font_size=28,
            fill_color=(255, 255, 255)
        )
        title.outline = 2
        title.outline_color = (0, 0, 0)
        self.ui.append(title)

        # Status caption
        self.status = mcrfpy.Caption(
            text="Click and drag items to rearrange",
            pos=(512, 70),
            font_size=16,
            fill_color=(180, 180, 180)
        )
        self.ui.append(self.status)

        # Create grid - zoom in constructor for proper centering
        grid_size = (10, 8)
        cell_size = 48
        grid_pixel_size = (grid_size[0] * cell_size, grid_size[1] * cell_size)
        grid_pos = ((1024 - grid_pixel_size[0]) // 2, 150)

        self.grid = mcrfpy.Grid(
            pos=grid_pos,
            size=grid_pixel_size,
            grid_size=grid_size,
            texture=mcrfpy.default_texture,
            zoom=3.0  # Each cell is 16px * 3 = 48px
        )

        # Get tile layer and fill with floor tiles
        self.tile_layer = self.grid.layers[0]
        self.tile_layer.fill(46)  # Floor tile

        # Add color layer for highlighting (above tiles, below entities)
        self.color_layer = self.grid.add_layer('color', z_index=-1)

        # Add event handlers
        self.grid.on_click = self._on_grid_click
        self.grid.on_cell_enter = self._on_cell_enter

        self.ui.append(self.grid)

        # Add some entities to the grid
        self._populate_grid()

        # Instructions
        instr = mcrfpy.Caption(
            text="Click to pick up, drag to move, release to drop | Red = occupied | ESC to exit",
            pos=(512, 700),
            font_size=14,
            fill_color=(150, 150, 150)
        )
        self.ui.append(instr)

    def _populate_grid(self):
        """Add entities to the grid in a scattered pattern."""
        # Place items at various positions
        positions = [
            (1, 1), (3, 1), (5, 2), (7, 1),
            (2, 4), (4, 3), (6, 5), (8, 4),
            (1, 6), (5, 6)
        ]

        for i, (x, y) in enumerate(positions):
            if i >= len(ITEMS):
                break
            sprite_idx, name = ITEMS[i]
            entity = mcrfpy.Entity()
            self.grid.entities.append(entity)
            entity.grid_pos = (x, y)  # Use grid_pos for tile coordinates
            entity.sprite_index = sprite_idx
            self.occupied_cells.add((x, y))

    def _get_entity_at(self, x, y):
        """Get entity at grid position, or None."""
        for entity in self.grid.entities:
            gp = entity.grid_pos
            ex, ey = int(gp[0]), int(gp[1])
            if ex == x and ey == y:
                return entity
        return None

    def _on_grid_click(self, pos, button, action):
        """Handle grid click for drag start/end."""
        if button != "left":
            return

        # Convert screen pos to grid cell
        grid_x = int((pos[0] - self.grid.x) / (16 * self.grid.zoom))
        grid_y = int((pos[1] - self.grid.y) / (16 * self.grid.zoom))

        # Bounds check
        grid_w, grid_h = self.grid.grid_size
        if not (0 <= grid_x < grid_w and 0 <= grid_y < grid_h):
            return

        if action == "start":
            # Start drag if there's an entity here
            entity = self._get_entity_at(grid_x, grid_y)
            if entity:
                self.dragging_entity = entity
                self.drag_start_cell = (grid_x, grid_y)
                self.status.text = f"Dragging from ({grid_x}, {grid_y})"
                self.status.fill_color = (100, 200, 255)

                # Highlight start cell yellow
                self.color_layer.set((grid_x, grid_y), (255, 255, 100, 200))

        elif action == "end":
            if self.dragging_entity:
                # Drop the entity
                target_cell = (grid_x, grid_y)

                if target_cell == self.drag_start_cell:
                    # Dropped in same cell - no change
                    self.status.text = "Cancelled - same cell"
                elif target_cell in self.occupied_cells:
                    # Can't drop on occupied cell
                    self.status.text = f"Can't drop on occupied cell ({grid_x}, {grid_y})"
                    self.status.fill_color = (255, 100, 100)
                else:
                    # Valid drop - move entity
                    self.occupied_cells.discard(self.drag_start_cell)
                    self.occupied_cells.add(target_cell)
                    self.dragging_entity.grid_pos = target_cell
                    self.status.text = f"Moved to ({grid_x}, {grid_y})"
                    self.status.fill_color = (100, 255, 100)

                # Clear all highlights
                self._clear_highlights()

                self.dragging_entity = None
                self.drag_start_cell = None

    def _on_cell_enter(self, cell_pos):
        """Handle cell hover during drag."""
        if not self.dragging_entity:
            return

        x, y = int(cell_pos[0]), int(cell_pos[1])

        # Clear previous highlights (except start cell)
        self._clear_highlights()

        # Re-highlight start cell
        if self.drag_start_cell:
            self.color_layer.set(self.drag_start_cell, (255, 255, 100, 200))

        # Highlight current cell
        if (x, y) != self.drag_start_cell:
            if (x, y) in self.occupied_cells:
                self.color_layer.set((x, y), (255, 100, 100, 200))  # Red - can't drop
            else:
                self.color_layer.set((x, y), (100, 255, 100, 200))  # Green - can drop
                # Move entity preview
                self.dragging_entity.grid_pos = (x, y)

    def _clear_highlights(self):
        """Clear all cell color highlights."""
        grid_w, grid_h = self.grid.grid_size
        for y in range(grid_h):
            for x in range(grid_w):
                self.color_layer.set((x, y), (0, 0, 0, 0))

    def on_key(self, key, state):
        """Handle keyboard input."""
        if state != "start":
            return
        if key == "Escape":
            # Cancel any drag in progress
            if self.dragging_entity and self.drag_start_cell:
                self.dragging_entity.grid_pos = self.drag_start_cell
                self._clear_highlights()
                self.dragging_entity = None
                self.drag_start_cell = None
                self.status.text = "Drag cancelled"
                return

            # Return to cookbook menu or exit
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
    demo = GridDragDropDemo()
    demo.activate()

    # Headless screenshot
    try:
        if mcrfpy.headless_mode():
            from mcrfpy import automation
            mcrfpy.Timer("screenshot", lambda rt: (
                automation.screenshot("screenshots/primitives/drag_drop_grid.png"),
                sys.exit(0)
            ), 100)
    except AttributeError:
        pass


if __name__ == "__main__":
    main()
