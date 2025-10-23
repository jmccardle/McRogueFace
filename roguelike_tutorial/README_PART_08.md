# Part 8: Items and Inventory

## Overview

Part 8 transforms our roguelike into a proper loot-driven game by adding items that can be collected, managed, and used. We implement a flexible inventory system with capacity limits, create consumable items like healing potions, and build UI for inventory management.

## What's New in Part 8

### Parent-Child Entity Architecture

#### Flexible Entity Ownership
Entities now have parent containers, allowing them to exist in different contexts:
```python
class Entity(mcrfpy.Entity):
    def __init__(self, parent: Optional[Union[GameMap, Inventory]] = None):
        self.parent = parent
    
    @property
    def gamemap(self) -> Optional[GameMap]:
        """Get the GameMap through the parent chain"""
        if isinstance(self.parent, Inventory):
            return self.parent.gamemap
        return self.parent
```

Benefits:
- Items can exist in the world or in inventories
- Clean ownership transfer when picking up/dropping
- Automatic visibility management

### Inventory System

#### Container-Based Design
The inventory acts like a specialized entity container:
```python
class Inventory:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.items: List[Item] = []
        self.parent: Optional[Actor] = None
    
    def add_item(self, item: Item) -> None:
        if len(self.items) >= self.capacity:
            raise Impossible("Your inventory is full.")
        
        # Transfer ownership
        self.items.append(item)
        item.parent = self
        item.visible = False  # Hide from map
```

Features:
- Capacity limits (26 items for letter selection)
- Clean item transfer between world and inventory
- Automatic visual management

### Item System

#### Item Entity Class
Items are entities with consumable components:
```python
class Item(Entity):
    def __init__(self, consumable: Optional = None):
        super().__init__(blocks_movement=False)
        self.consumable = consumable
        if consumable:
            consumable.parent = self
```

#### Consumable Components
Modular system for item effects:
```python
class HealingConsumable(Consumable):
    def activate(self, action: ItemAction) -> None:
        if consumer.hp >= consumer.max_hp:
            raise Impossible("You are already at full health.")
        
        amount_recovered = min(self.amount, consumer.max_hp - consumer.hp)
        consumer.hp += amount_recovered
        self.consume()  # Remove item after use
```

### Exception-Driven Feedback

#### Clean Error Handling
Using exceptions for user feedback:
```python
class Impossible(Exception):
    """Action cannot be performed"""
    pass

class PickupAction(Action):
    def perform(self, engine: Engine) -> None:
        if not items_here:
            raise Impossible("There is nothing here to pick up.")
        
        try:
            inventory.add_item(item)
            engine.message_log.add_message(f"You picked up the {item.name}!")
        except Impossible as e:
            engine.message_log.add_message(str(e))
```

Benefits:
- Consistent error messaging
- Clean control flow
- Centralized feedback handling

### Inventory UI

#### Modal Inventory Screen
Interactive inventory management:
```python
class InventoryEventHandler(BaseEventHandler):
    def create_ui(self) -> None:
        # Semi-transparent background
        self.background = mcrfpy.Frame(pos=(100, 100), size=(400, 400))
        self.background.fill_color = mcrfpy.Color(0, 0, 0, 200)
        
        # List items with letter keys
        for i, item in enumerate(inventory.items):
            item_caption = mcrfpy.Caption(
                pos=(20, 80 + i * 20),
                text=f"{chr(ord('a') + i)}) {item.name}"
            )
```

Features:
- Letter-based selection (a-z)
- Separate handlers for use/drop
- ESC to cancel
- Visual feedback

### Enhanced Actions

#### Item Actions
New actions for item management:
```python
class PickupAction(Action):
    """Pick up items at current location"""

class ItemAction(Action):
    """Base for item usage actions"""
    
class DropAction(ItemAction):
    """Drop item from inventory"""
```

Each action:
- Self-validates
- Provides feedback
- Triggers enemy turns

## Architecture Improvements

### Component Relationships
Parent-based component system:
```python
# Components know their parent
consumable.parent = item
item.parent = inventory
inventory.parent = actor
actor.parent = gamemap
gamemap.engine = engine
```

Benefits:
- Access to game context from any component
- Clean ownership transfer
- Simplified entity lifecycle

### Input Handler States
Modal UI through handler switching:
```python
# Main game
engine.current_handler = MainGameEventHandler(engine)

# Open inventory
engine.current_handler = InventoryActivateHandler(engine)

# Back to game
engine.current_handler = MainGameEventHandler(engine)
```

### Entity Lifecycle Management
Proper creation and cleanup:
```python
# Item spawning
item = entity_factories.health_potion(x, y, texture)
item.place(x, y, dungeon)

# Pickup
inventory.add_item(item)  # Removes from map

# Drop
inventory.drop(item)  # Returns to map

# Death
actor.die()  # Drops all items
```

## Key Implementation Details

### Visibility Management
Items hide/show based on container:
```python
def add_item(self, item):
    item.visible = False  # Hide when in inventory

def drop(self, item):
    item.visible = True  # Show when on map
```

### Inventory Capacity
Limited to alphabet keys:
```python
if len(inventory.items) >= 26:
    raise Impossible("Your inventory is full.")
```

### Item Generation
Procedural item placement:
```python
def place_entities(room, dungeon, max_monsters, max_items, texture):
    # Place 0-2 items per room
    number_of_items = random.randint(0, max_items)
    
    for _ in range(number_of_items):
        if space_available:
            item = entity_factories.health_potion(x, y, texture)
            item.place(x, y, dungeon)
```

## Files Modified

- `game/entity.py`: Added parent system, Item class, inventory to Actor
- `game/inventory.py`: New inventory container system
- `game/consumable.py`: New consumable component system
- `game/exceptions.py`: New Impossible exception
- `game/actions.py`: Added PickupAction, ItemAction, DropAction
- `game/input_handlers.py`: Added InventoryEventHandler classes
- `game/engine.py`: Added current_handler, inventory UI methods
- `game/procgen.py`: Added item generation
- `game/entity_factories.py`: Added health_potion factory
- `game/ui.py`: Updated help text with inventory controls
- `main.py`: Updated to Part 8, handler management

## What's Next

Part 9 will add ranged attacks and targeting:
- Targeting UI for selecting enemies
- Ranged damage items (lightning staff)
- Area-of-effect items (fireball staff)
- Confusion effects

## Learning Points

1. **Container Architecture**: Entity ownership through parent relationships
2. **Component Systems**: Modular, reusable components with parent references
3. **Exception Handling**: Clean error propagation and user feedback
4. **Modal UI**: State-based input handling for different screens
5. **Item Systems**: Flexible consumable architecture for varied effects
6. **Lifecycle Management**: Proper entity creation, transfer, and cleanup

## Running Part 8

```bash
cd simple_tcod_tutorial/build
./mcrogueface scripts/main.py
```

New features to try:
- Press G to pick up healing potions
- Press I to open inventory and use items
- Press O to drop items from inventory
- Heal yourself when injured in combat
- Manage limited inventory space (26 slots)
- Items drop from dead enemies

## Design Principles

### Flexibility Through Composition
- Items gain behavior through consumable components
- Easy to add new item types
- Reusable effect system

### Clean Ownership Transfer
- Entities always have clear parent
- Automatic visibility management
- No orphaned entities

### User-Friendly Feedback
- Clear error messages
- Consistent UI patterns
- Intuitive controls

The inventory system provides the foundation for equipment, spells, and complex item interactions in future parts!