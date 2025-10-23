# Part 4: Field of View and Exploration

## Overview

Part 4 introduces the Field of View (FOV) system, transforming our fully-visible dungeon into an atmospheric exploration experience. We leverage McRogueFace's built-in FOV capabilities and perspective system for efficient rendering.

## What's New in Part 4

### Field of View System
- **FOV Calculation**: Using `Grid.compute_fov()` with configurable radius
- **Perspective System**: Grid tracks which entity is the viewer
- **Visibility States**: Unexplored (black), explored (dark), visible (lit)
- **Automatic Updates**: FOV recalculates on player movement

### Implementation Details

#### FOV with McRogueFace's Grid

Unlike TCOD which uses numpy arrays for visibility tracking, McRogueFace's Grid has built-in FOV support:

```python
# In GameMap.update_fov()
self.compute_fov(viewer_x, viewer_y, radius, light_walls=True, algorithm=mcrfpy.FOV_BASIC)
```

The Grid automatically:
- Tracks which tiles have been explored
- Applies appropriate color overlays (shroud, dark, light)
- Updates entity visibility based on FOV

#### Perspective System

McRogueFace uses a perspective-based rendering approach:

```python
# Set the viewer
self.game_map.perspective = self.player

# Grid automatically renders from this entity's viewpoint
```

This is more efficient than manually updating tile colors every turn.

#### Color Overlays

We define overlay colors but let the Grid handle application:

```python
# In tiles.py
SHROUD = mcrfpy.Color(0, 0, 0, 255)      # Unexplored
DARK = mcrfpy.Color(100, 100, 150, 128)  # Explored but not visible
LIGHT = mcrfpy.Color(255, 255, 255, 0)   # Currently visible
```

### Key Differences from TCOD

| TCOD Approach | McRogueFace Approach |
|---------------|----------------------|
| `visible` and `explored` numpy arrays | Grid's built-in FOV state |
| Manual tile color switching | Automatic overlay system |
| `tcod.map.compute_fov()` | `Grid.compute_fov()` |
| Render conditionals for each tile | Perspective-based rendering |

### Movement and FOV Updates

The action system now updates FOV after player movement:

```python
# In MovementAction.perform()
if self.entity == engine.player:
    engine.update_fov()
```

## Architecture Notes

### Why Grid Perspective?

The perspective system provides several benefits:
1. **Efficiency**: No per-tile color updates needed
2. **Flexibility**: Easy to switch viewpoints (for debugging or features)
3. **Automatic**: Grid handles all rendering details
4. **Clean**: Separates game logic from rendering concerns

### Entity Visibility

Entities automatically update their visibility state:

```python
# After FOV calculation
self.player.update_visibility()
```

This ensures entities are only rendered when visible to the current perspective.

## Files Modified

- `game/tiles.py`: Added FOV color overlay constants
- `game/game_map.py`: Added `update_fov()` method
- `game/engine.py`: Added FOV initialization and update method
- `game/actions.py`: Update FOV after player movement
- `main.py`: Updated part description

## What's Next

Part 5 will add enemies to our dungeon, introducing:
- Enemy entities with AI
- Combat system
- Turn-based gameplay
- Health and damage

The FOV system will make enemies appear and disappear as you explore, adding tension and strategy to the gameplay.

## Learning Points

1. **Leverage Framework Features**: Use McRogueFace's built-in systems rather than reimplementing
2. **Perspective-Based Design**: Think in terms of viewpoints, not global state
3. **Automatic Systems**: Let the framework handle rendering details
4. **Clean Integration**: FOV updates fit naturally into the action system

## Running Part 4

```bash
cd simple_tcod_tutorial/build
./mcrogueface scripts/main.py
```

You'll now see:
- Black unexplored areas
- Dark blue tint on previously seen areas
- Full brightness only in your field of view
- Smooth exploration as you move through the dungeon