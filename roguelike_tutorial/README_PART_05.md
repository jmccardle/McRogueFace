# Part 5: Placing Enemies and Fighting Them

## Overview

Part 5 brings our dungeon to life with enemies! We add rats and spiders that populate the rooms, implement a combat system with melee attacks, and handle entity death by turning creatures into gravestones.

## What's New in Part 5

### Actor System
- **Actor Class**: Extends Entity with combat stats (HP, defense, power)
- **Combat Properties**: Health tracking, damage calculation, alive status
- **Death Handling**: Entities become gravestones when killed

### Enemy Types
Using our sprite sheet, we have two enemy types:
- **Rat** (sprite 5): 10 HP, 0 defense, 3 power - Common enemy
- **Spider** (sprite 4): 16 HP, 1 defense, 4 power - Tougher enemy

### Combat System

#### Bump-to-Attack
When the player tries to move into an enemy:
```python
# In MovementAction.perform()
target = engine.game_map.get_blocking_entity_at(dest_x, dest_y)
if target:
    if self.entity == engine.player:
        from game.entity import Actor
        if isinstance(target, Actor) and target != engine.player:
            return MeleeAction(self.entity, self.dx, self.dy).perform(engine)
```

#### Damage Calculation
Simple formula with defense reduction:
```python
damage = attacker.power - target.defense
```

#### Death System
Dead entities become gravestones:
```python
def die(self) -> None:
    """Handle death by becoming a gravestone."""
    self.sprite_index = 6  # Tombstone sprite
    self.blocks_movement = False
    self.name = f"Grave of {self.name}"
```

### Entity Factories

Factory functions create pre-configured entities:
```python
def rat(x: int, y: int, texture: mcrfpy.Texture) -> Actor:
    return Actor(
        x=x, y=y,
        sprite_id=5,  # Rat sprite
        texture=texture,
        name="Rat",
        hp=10, defense=0, power=3,
    )
```

### Dungeon Population

Enemies are placed randomly in rooms:
```python
def place_entities(room, dungeon, max_monsters, texture):
    number_of_monsters = random.randint(0, max_monsters)
    
    for _ in range(number_of_monsters):
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)
        
        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            # 80% rats, 20% spiders
            if random.random() < 0.8:
                monster = entity_factories.rat(x, y, texture)
            else:
                monster = entity_factories.spider(x, y, texture)
            monster.place(x, y, dungeon)
```

## Key Implementation Details

### FOV and Enemy Visibility
Enemies are automatically shown/hidden by the FOV system:
```python
def update_fov(self) -> None:
    # Update visibility for all entities
    for entity in self.game_map.entities:
        entity.update_visibility()
```

### Action System Extension
The action system now handles combat:
- **MovementAction**: Detects collision, triggers attack
- **MeleeAction**: New action for melee combat
- Actions remain decoupled from entity logic

### Gravestone System
Instead of removing dead entities:
- Sprite changes to tombstone (index 6)
- Name changes to "Grave of [Name]"
- No longer blocks movement
- Remains visible as dungeon decoration

## Architecture Notes

### Why Actor Extends Entity?
- Maintains entity hierarchy
- Combat stats only for creatures
- Future items/decorations won't have HP
- Clean separation of concerns

### Why Factory Functions?
- Centralized entity configuration
- Easy to add new enemy types
- Consistent stat management
- Type-safe entity creation

### Combat in Actions
Combat logic lives in actions, not entities:
- Entities store stats
- Actions perform combat
- Clean separation of data and behavior
- Extensible for future combat types

## Files Modified

- `game/entity.py`: Added Actor class with combat stats and death handling
- `game/entity_factories.py`: New module with entity creation functions
- `game/actions.py`: Added MeleeAction for combat
- `game/procgen.py`: Added enemy placement in rooms
- `game/engine.py`: Updated to use Actor type and handle all entity visibility
- `main.py`: Updated to use entity factories and Part 5 description

## What's Next

Part 6 will enhance the combat experience with:
- Health display UI
- Game over conditions
- Combat messages window
- More strategic combat mechanics

## Learning Points

1. **Entity Specialization**: Use inheritance to add features to specific entity types
2. **Factory Pattern**: Centralize object creation for consistency
3. **State Transformation**: Dead entities become decorations, not deletions
4. **Action Extensions**: Combat fits naturally into the action system
5. **Automatic Systems**: FOV handles entity visibility without special code

## Running Part 5

```bash
cd simple_tcod_tutorial/build
./mcrogueface scripts/main.py
```

You'll now encounter rats and spiders as you explore! Walk into them to attack. Dead enemies become gravestones that mark your battles.

## Sprite Adaptations

Following our sprite sheet (`sprite_sheet.md`), we made these thematic changes:
- Orcs → Rats (same stats, different sprite)
- Trolls → Spiders (same stats, different sprite)
- Corpses → Gravestones (all use same tombstone sprite)

The gameplay remains identical to the TCOD tutorial, just with different visual theming.