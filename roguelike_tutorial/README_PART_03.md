# Simple TCOD Tutorial Part 3 - Generating a dungeon

This is Part 3 of the Simple TCOD Tutorial adapted for McRogueFace. We now add procedural dungeon generation to create interesting, playable levels.

## Running the Code

From your tutorial build directory:
```bash
cd simple_tcod_tutorial/build
./mcrogueface scripts/main.py
```

## New Features

### Procedural Generation Module (`game/procgen.py`)

This dedicated module demonstrates separation of concerns - dungeon generation logic is kept separate from the game map implementation.

#### RectangularRoom Class
- **Clean Abstraction**: Represents a room with position and dimensions
- **Utility Properties**: 
  - `center` - Returns room center for connections
  - `inner` - Returns slice objects for efficient carving
- **Intersection Detection**: `intersects()` method prevents overlapping rooms

#### Tunnel Generation
- **L-Shaped Corridors**: Simple but effective connection method
- **Iterator Pattern**: `tunnel_between()` yields coordinates efficiently
- **Random Variation**: 50/50 chance of horizontal-first vs vertical-first

#### Dungeon Generation Algorithm
```python
def generate_dungeon(max_rooms, room_min_size, room_max_size, 
                    map_width, map_height, engine) -> GameMap:
```
- **Simple Algorithm**: Try to place random rooms, reject overlaps
- **Automatic Connection**: Each room connects to the previous one
- **Player Placement**: First room contains the player
- **Entity-Centric**: Uses `player.place()` for proper lifecycle

## Architecture Benefits

### Modular Design
- Generation logic separate from GameMap
- Easy to swap algorithms later
- Room class reusable for other features

### Forward Thinking
- Engine parameter anticipates entity spawning
- Room list available for future features
- Iterator-based tunnel generation is memory efficient

### Clean Integration
- Works seamlessly with existing entity placement
- Respects GameMap's tile management
- No special cases or hacks needed

## Visual Changes

- Map size increased to 80x45 for better dungeons
- Zoom reduced to 1.0 to see more of the map
- Random room layouts each time
- Connected rooms and corridors

## Algorithm Details

The generation follows these steps:
1. Start with a map filled with walls
2. Try to place up to `max_rooms` rooms
3. For each room attempt:
   - Generate random size and position
   - Check for intersections with existing rooms
   - If valid, carve out the room
   - Connect to previous room (if any)
4. Place player in center of first room

This simple algorithm creates playable dungeons while being easy to understand and modify.

## What's Next

Part 4 will add:
- Field of View (FOV) system
- Explored vs unexplored areas
- Light and dark tile rendering
- Torch radius around player

The modular dungeon generation makes it easy to add these visual features without touching the generation code.