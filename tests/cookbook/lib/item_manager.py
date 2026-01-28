#!/usr/bin/env python3
"""Item Manager - Coordinates item pickup/drop across multiple widgets

This module provides:
    - ItemManager: Central coordinator for item transfers
    - ItemSlot: Frame-based equipment slot widget
    - Item: Data class for item properties

The manager allows entities to move between:
    - Grid widgets (inventory, shop displays)
    - ItemSlot widgets (equipment slots)
    - The cursor (when held)

Usage:
    manager = ItemManager()
    manager.register_grid("inventory", inventory_grid)
    manager.register_slot("weapon", weapon_slot)

    # Widgets call manager methods on click:
    manager.pickup_from_grid("inventory", cell_pos)
    manager.drop_to_slot("weapon")
"""
import mcrfpy


class ItemEntity(mcrfpy.Entity):
    """Entity subclass that can hold item data."""

    def __init__(self):
        super().__init__()
        self.item = None  # Will be set after adding to grid


class Item:
    """Data class representing an item's properties."""

    def __init__(self, sprite_index, name, **stats):
        """
        Args:
            sprite_index: Texture sprite index
            name: Display name
            **stats: Arbitrary stats (atk, def, int, price, etc.)
        """
        self.sprite_index = sprite_index
        self.name = name
        self.stats = stats

    def __repr__(self):
        return f"Item({self.name}, sprite={self.sprite_index})"

    @property
    def price(self):
        return self.stats.get('price', 0)

    @property
    def atk(self):
        return self.stats.get('atk', 0)

    @property
    def def_(self):
        return self.stats.get('def', 0)

    @property
    def slot_type(self):
        """Equipment slot this item fits in (weapon, shield, etc.)"""
        return self.stats.get('slot_type', None)


class ItemSlot(mcrfpy.Frame):
    """A frame that can hold a single item (for equipment slots)."""

    def __init__(self, pos, size=(64, 64), slot_type=None,
                 empty_color=(60, 60, 70), valid_color=(60, 100, 60),
                 invalid_color=(100, 60, 60), filled_color=(80, 80, 90)):
        """
        Args:
            pos: Position tuple (x, y)
            size: Size tuple (w, h)
            slot_type: Type of items this slot accepts (e.g., 'weapon', 'shield')
            empty_color: Color when empty and not hovered
            valid_color: Color when valid item is hovering
            invalid_color: Color when invalid item is hovering
            filled_color: Color when containing an item
        """
        super().__init__(pos, size, fill_color=empty_color, outline=2, outline_color=(100, 100, 120))

        self.slot_type = slot_type
        self.empty_color = empty_color
        self.valid_color = valid_color
        self.invalid_color = invalid_color
        self.filled_color = filled_color

        # Item stored in this slot
        self.item = None
        self.item_sprite = None

        # Manager reference (set by manager.register_slot)
        self.manager = None
        self.slot_name = None

        # Setup sprite for displaying item
        sprite_scale = min(size[0], size[1]) / 16.0 * 0.8  # 80% of slot size
        self.item_sprite = mcrfpy.Sprite(
            pos=(size[0] * 0.1, size[1] * 0.1),
            texture=mcrfpy.default_texture,
            sprite_index=0
        )
        self.item_sprite.scale = sprite_scale
        self.item_sprite.visible = False
        self.children.append(self.item_sprite)

        # Setup events
        self.on_click = self._on_click
        self.on_enter = self._on_enter
        self.on_exit = self._on_exit

    def set_item(self, item):
        """Set the item in this slot."""
        self.item = item
        if item:
            self.item_sprite.sprite_index = item.sprite_index
            self.item_sprite.visible = True
            self.fill_color = self.filled_color
        else:
            self.item_sprite.visible = False
            self.fill_color = self.empty_color

    def clear(self):
        """Remove item from slot."""
        self.set_item(None)

    def can_accept(self, item):
        """Check if this slot can accept the given item."""
        if self.slot_type is None:
            return True  # Accepts anything
        if item is None:
            return True
        return item.slot_type == self.slot_type

    def _on_click(self, pos, button, action):
        if action != "start" or button != "left":
            return
        if self.manager:
            self.manager.handle_slot_click(self.slot_name)

    def _on_enter(self, pos, *args):
        if self.manager and self.manager.held_item:
            if self.can_accept(self.manager.held_item):
                self.fill_color = self.valid_color
            else:
                self.fill_color = self.invalid_color

    def _on_exit(self, pos, *args):
        if self.item:
            self.fill_color = self.filled_color
        else:
            self.fill_color = self.empty_color


class ItemManager:
    """Coordinates item pickup and placement across multiple widgets."""

    def __init__(self, scene):
        """
        Args:
            scene: The mcrfpy.Scene to add cursor elements to
        """
        self.scene = scene
        self.grids = {}       # name -> (grid, {(x,y): Item})
        self.slots = {}       # name -> ItemSlot

        # Currently held item state
        self.held_item = None
        self.held_source = None      # ('grid', name, pos) or ('slot', name)
        self.held_entity = None      # For grid sources, the original entity

        # Cursor sprite setup
        self.cursor_frame = mcrfpy.Frame(
            pos=(0, 0),
            size=(64, 64),
            fill_color=(0, 0, 0, 0),
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
        scene.children.append(self.cursor_frame)

        # Callbacks for UI updates
        self.on_pickup = None       # Called when item picked up
        self.on_drop = None         # Called when item dropped
        self.on_cancel = None       # Called when pickup cancelled

    def register_grid(self, name, grid, items=None):
        """Register a grid for item management.

        Args:
            name: Unique name for this grid
            grid: mcrfpy.Grid instance
            items: Optional dict of {(x, y): Item} for initial items
        """
        item_map = items or {}

        # Add a color layer for highlighting if not present
        color_layer = grid.add_layer('color', z_index=-1)

        self.grids[name] = (grid, item_map, color_layer)

        # Setup grid event handlers
        grid.on_click = lambda pos, btn, act: self._on_grid_click(name, pos, btn, act)
        grid.on_cell_enter = lambda cell_pos: self._on_grid_cell_enter(name, cell_pos)
        grid.on_move = self._on_move

    def register_slot(self, name, slot):
        """Register an ItemSlot for item management.

        Args:
            name: Unique name for this slot
            slot: ItemSlot instance
        """
        self.slots[name] = slot
        slot.manager = self
        slot.slot_name = name

    def add_item_to_grid(self, grid_name, pos, item):
        """Add an item to a grid at the specified position.

        Args:
            grid_name: Name of registered grid
            pos: (x, y) cell position
            item: Item instance

        Returns:
            True if successful, False if cell occupied
        """
        if grid_name not in self.grids:
            return False

        grid, item_map, color_layer = self.grids[grid_name]

        if pos in item_map:
            return False  # Cell occupied

        # Create entity
        entity = ItemEntity()
        grid.entities.append(entity)
        entity.grid_pos = pos  # Use grid_pos for tile coordinates
        entity.sprite_index = item.sprite_index
        entity.item = item  # Store item reference on our subclass
        item_map[pos] = item

        return True

    def get_item_at(self, grid_name, pos):
        """Get item at grid position, or None."""
        if grid_name not in self.grids:
            return None
        grid, item_map, color_layer = self.grids[grid_name]
        return item_map.get(pos)

    def _get_entity_at(self, grid_name, pos):
        """Get entity at grid position."""
        grid, _, _ = self.grids[grid_name]
        for entity in grid.entities:
            gp = entity.grid_pos
            if (int(gp[0]), int(gp[1])) == pos:
                return entity
        return None

    def _on_grid_click(self, grid_name, pos, button, action):
        """Handle click on a registered grid."""
        if action != "start":
            return

        if button == "right":
            self.cancel_pickup()
            return

        if button != "left":
            return

        grid, item_map, color_layer = self.grids[grid_name]

        # Convert screen pos to cell
        cell_size = 16 * grid.zoom
        x = int((pos[0] - grid.x) / cell_size)
        y = int((pos[1] - grid.y) / cell_size)
        grid_w, grid_h = grid.grid_size

        if not (0 <= x < grid_w and 0 <= y < grid_h):
            return

        cell_pos = (x, y)

        if self.held_item is None:
            # Try to pick up
            if cell_pos in item_map:
                self._pickup_from_grid(grid_name, cell_pos)
        else:
            # Try to drop
            if cell_pos not in item_map:
                self._drop_to_grid(grid_name, cell_pos)

    def _pickup_from_grid(self, grid_name, pos):
        """Pick up item from grid cell."""
        grid, item_map, color_layer = self.grids[grid_name]
        item = item_map[pos]
        entity = self._get_entity_at(grid_name, pos)

        if entity:
            entity.visible = False

        self.held_item = item
        self.held_source = ('grid', grid_name, pos)
        self.held_entity = entity

        # Setup cursor
        self.cursor_sprite.sprite_index = item.sprite_index
        self.cursor_sprite.visible = True

        # Highlight source cell
        color_layer.set(pos, (255, 255, 100, 200))

        if self.on_pickup:
            self.on_pickup(item, grid_name, pos)

    def _drop_to_grid(self, grid_name, pos):
        """Drop held item to grid cell."""
        grid, item_map, color_layer = self.grids[grid_name]

        # Check if same grid and moving item
        if self.held_source[0] == 'grid':
            source_grid_name = self.held_source[1]
            source_pos = self.held_source[2]

            # Remove from source
            source_grid, source_map, source_color_layer = self.grids[source_grid_name]
            if source_pos in source_map:
                del source_map[source_pos]

            # Clear source highlight
            source_color_layer.set(source_pos, (0, 0, 0, 0))

            # Move or recreate entity
            if grid_name == source_grid_name and self.held_entity:
                # Same grid - just move entity
                self.held_entity.grid_pos = pos
                self.held_entity.visible = True
            else:
                # Different grid - remove old, create new
                if self.held_entity:
                    # Remove from source grid
                    for i, e in enumerate(source_grid.entities):
                        if e is self.held_entity:
                            source_grid.entities.pop(i)
                            break

                # Create in target grid
                entity = ItemEntity()
                grid.entities.append(entity)
                entity.grid_pos = pos  # Use grid_pos for tile coordinates
                entity.sprite_index = self.held_item.sprite_index
                entity.item = self.held_item
                self.held_entity = None

        elif self.held_source[0] == 'slot':
            # Moving from slot to grid
            slot_name = self.held_source[1]
            slot = self.slots[slot_name]
            slot.clear()

            # Create entity in grid
            entity = ItemEntity()
            grid.entities.append(entity)
            entity.grid_pos = pos  # Use grid_pos for tile coordinates
            entity.sprite_index = self.held_item.sprite_index
            entity.item = self.held_item

        # Add to target grid's item map
        item_map[pos] = self.held_item

        if self.on_drop:
            self.on_drop(self.held_item, grid_name, pos)

        # Clear held state
        self.cursor_sprite.visible = False
        self.held_item = None
        self.held_source = None
        self.held_entity = None

    def handle_slot_click(self, slot_name):
        """Handle click on a registered slot."""
        slot = self.slots[slot_name]

        if self.held_item is None:
            # Try to pick up from slot
            if slot.item:
                self._pickup_from_slot(slot_name)
        else:
            # Try to drop to slot
            if slot.can_accept(self.held_item):
                self._drop_to_slot(slot_name)

    def _pickup_from_slot(self, slot_name):
        """Pick up item from slot."""
        slot = self.slots[slot_name]
        item = slot.item

        self.held_item = item
        self.held_source = ('slot', slot_name)
        self.held_entity = None

        slot.clear()

        # Setup cursor
        self.cursor_sprite.sprite_index = item.sprite_index
        self.cursor_sprite.visible = True

        if self.on_pickup:
            self.on_pickup(item, slot_name, None)

    def _drop_to_slot(self, slot_name):
        """Drop held item to slot."""
        slot = self.slots[slot_name]

        # If slot has item, swap
        old_item = slot.item
        slot.set_item(self.held_item)

        # Clean up source
        if self.held_source[0] == 'grid':
            source_grid_name = self.held_source[1]
            source_pos = self.held_source[2]
            source_grid, source_map, source_color_layer = self.grids[source_grid_name]

            # Remove from source grid
            if source_pos in source_map:
                del source_map[source_pos]

            # Clear highlight
            source_color_layer.set(source_pos, (0, 0, 0, 0))

            # Remove entity
            if self.held_entity:
                for i, e in enumerate(source_grid.entities):
                    if e is self.held_entity:
                        source_grid.entities.pop(i)
                        break

            # If swapping, put old item in source position
            if old_item:
                self.add_item_to_grid(source_grid_name, source_pos, old_item)

        elif self.held_source[0] == 'slot':
            # Slot to slot swap
            source_slot_name = self.held_source[1]
            source_slot = self.slots[source_slot_name]
            if old_item:
                source_slot.set_item(old_item)

        if self.on_drop:
            self.on_drop(self.held_item, slot_name, None)

        # Clear held state
        self.cursor_sprite.visible = False
        self.held_item = None
        self.held_source = None
        self.held_entity = None

    def cancel_pickup(self):
        """Cancel current pickup and return item to source."""
        if not self.held_item:
            return

        if self.held_source[0] == 'grid':
            grid_name = self.held_source[1]
            pos = self.held_source[2]
            grid, item_map, color_layer = self.grids[grid_name]

            # Restore entity visibility
            if self.held_entity:
                self.held_entity.visible = True

            # Restore item map
            item_map[pos] = self.held_item

            # Clear highlight
            color_layer.set(pos, (0, 0, 0, 0))

        elif self.held_source[0] == 'slot':
            slot_name = self.held_source[1]
            slot = self.slots[slot_name]
            slot.set_item(self.held_item)

        if self.on_cancel:
            self.on_cancel(self.held_item)

        # Clear held state
        self.cursor_sprite.visible = False
        self.held_item = None
        self.held_source = None
        self.held_entity = None

    def _on_grid_cell_enter(self, grid_name, cell_pos):
        """Handle cell hover on registered grid."""
        if not self.held_item:
            return

        grid, item_map, color_layer = self.grids[grid_name]
        x, y = int(cell_pos[0]), int(cell_pos[1])

        # Don't highlight source cell
        if (self.held_source[0] == 'grid' and
            self.held_source[1] == grid_name and
            self.held_source[2] == (x, y)):
            return

        if (x, y) in item_map:
            color_layer.set((x, y), (255, 100, 100, 200))  # Red - occupied
        else:
            color_layer.set((x, y), (100, 255, 100, 200))  # Green - available

    def _on_move(self, pos, *args):
        """Update cursor position."""
        if self.cursor_sprite.visible:
            self.cursor_frame.x = pos[0] - 32
            self.cursor_frame.y = pos[1] - 32


# Predefined items using the texture sprites
ITEM_DATABASE = {
    'buckler': Item(101, "Buckler", def_=1, slot_type='shield', price=15),
    'shield': Item(102, "Shield", def_=2, slot_type='shield', price=30),
    'shortsword': Item(103, "Shortsword", atk=1, slot_type='weapon', price=20),
    'longsword': Item(104, "Longsword", atk=2, slot_type='weapon', price=40),
    'cleaver': Item(105, "Cleaver", atk=3, slot_type='weapon', two_handed=True, price=60),
    'buster': Item(106, "Buster Sword", atk=4, slot_type='weapon', two_handed=True, price=100),
    'training_sword': Item(107, "Training Sword", atk=2, slot_type='weapon', two_handed=True, price=25),
    'hammer': Item(117, "Hammer", atk=2, slot_type='weapon', price=35),
    'double_axe': Item(118, "Double Axe", atk=5, slot_type='weapon', two_handed=True, price=120),
    'axe': Item(119, "Axe", atk=3, slot_type='weapon', price=50),
    'wand': Item(129, "Wand", atk=1, int_=4, slot_type='weapon', price=45),
    'staff': Item(130, "Staff", atk=1, int_=7, slot_type='weapon', two_handed=True, price=80),
    'spear': Item(131, "Spear", atk=4, range_=1, slot_type='weapon', two_handed=True, price=55),
    'cloudy_potion': Item(113, "Cloudy Potion", slot_type='consumable', price=5),
    'str_potion': Item(114, "Strength Potion", slot_type='consumable', price=25),
    'health_potion': Item(115, "Health Potion", slot_type='consumable', price=15),
    'mana_potion': Item(116, "Mana Potion", slot_type='consumable', price=15),
    'lesser_cloudy': Item(125, "Lesser Cloudy Potion", slot_type='consumable', price=3),
    'lesser_str': Item(126, "Lesser Strength Potion", slot_type='consumable', price=12),
    'lesser_health': Item(127, "Lesser Health Potion", slot_type='consumable', price=8),
    'lesser_mana': Item(128, "Lesser Mana Potion", slot_type='consumable', price=8),
}


def get_item(name):
    """Get an item from the database by name."""
    return ITEM_DATABASE.get(name)
