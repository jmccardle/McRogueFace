# Simple TCOD Tutorial Part 2 - The generic Entity, the map, and walls

This is Part 2 of the Simple TCOD Tutorial adapted for McRogueFace. Building on Part 1's foundation, we now introduce proper world representation and collision detection.

## Running the Code

From your tutorial build directory:
```bash
cd simple_tcod_tutorial/build
./mcrogueface scripts/main.py
```

## New Architecture Components

### GameMap Class (`game/game_map.py`)
The GameMap inherits from `mcrfpy.Grid` and adds:
- **Tile Management**: Uses Grid's built-in point system with walkable property
- **Entity Container**: Manages entity lifecycle with `add_entity()` and `remove_entity()`
- **Spatial Queries**: `get_entities_at()`, `get_blocking_entity_at()`, `is_walkable()`
- **Direct Integration**: Leverages Grid's walkable and tilesprite properties

### Tiles System (`game/tiles.py`)
- **Simple Tile Types**: Using NamedTuple for clean tile definitions
- **Tile Types**: Floor (walkable) and Wall (blocks movement)
- **Grid Integration**: Maps directly to Grid point properties
- **Future-Ready**: Includes transparency for FOV system in Part 4

### Entity Placement System
- **Bidirectional References**: Entities know their map, maps track their entities
- **`place()` Method**: Handles all bookkeeping when entities move between maps
- **Lifecycle Management**: Automatic cleanup when entities leave maps

## Key Changes from Part 1

### Engine Updates
- Replaced direct grid management with GameMap
- Engine creates and configures the GameMap
- Player is placed using the new `place()` method

### Movement System
- MovementAction now checks `is_walkable()` before moving
- Collision detection for both walls and blocking entities
- Clean separation between validation and execution

### Visual Changes
- Walls rendered as trees (sprite index 3)
- Border of walls around the map edge
- Floor tiles still use alternating pattern

## Architectural Benefits

### McRogueFace Integration
- **No NumPy Dependency**: Uses Grid's native tile management
- **Direct Walkability**: Grid points have built-in walkable property
- **Unified System**: Visual and logical tile data in one place

### Separation of Concerns
- **GameMap**: Knows about tiles and spatial relationships
- **Engine**: Coordinates high-level game state
- **Entity**: Manages its own lifecycle through `place()`
- **Actions**: Validate their own preconditions

### Extensibility
- Easy to add new tile types
- Simple to implement different map generation
- Ready for FOV, pathfinding, and complex queries
- Entity system scales to items and NPCs

### Type Safety
- TYPE_CHECKING imports prevent circular dependencies
- Proper type hints throughout
- Forward references maintain clean architecture

## What's Next

Part 3 will add:
- Procedural dungeon generation
- Room and corridor creation
- Multiple entities in the world
- Foundation for enemy placement

The architecture established in Part 2 makes these additions straightforward, demonstrating the value of proper design from the beginning.