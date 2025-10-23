# Simple TCOD Tutorial Part 1 - Drawing the player sprite and moving it around

This is Part 1 of the Simple TCOD Tutorial adapted for McRogueFace. It implements the sophisticated, refactored TCOD tutorial approach with professional architecture from day one.

## Running the Code

From your tutorial build directory (separate from the engine development build):
```bash
cd simple_tcod_tutorial/build
./mcrogueface scripts/main.py
```

Note: The `scripts` folder should be a symlink to your `simple_tcod_tutorial` directory.

## Architecture Overview

### Package Structure
```
simple_tcod_tutorial/
├── main.py              # Entry point - ties everything together
├── game/               # Game package with proper separation
│   ├── __init__.py     
│   ├── entity.py       # Entity class - all game objects
│   ├── engine.py       # Engine class - game coordinator
│   ├── actions.py      # Action classes - command pattern
│   └── input_handlers.py # Input handling - extensible system
```

### Key Concepts Demonstrated

1. **Entity-Centric Design**
   - Everything in the game is an Entity
   - Entities have position, appearance, and behavior
   - Designed to scale to items, NPCs, and effects

2. **Action-Based Command Pattern**
   - All player actions are Action objects
   - Separates input from game logic
   - Enables undo, replay, and AI using same system

3. **Professional Input Handling**
   - BaseEventHandler for different input contexts
   - Complete movement key support (arrows, numpad, vi, WASD)
   - Ready for menus, targeting, and other modes

4. **Engine as Coordinator**
   - Manages game state without becoming a god object
   - Delegates to appropriate systems
   - Clean boundaries between systems

5. **Type Safety**
   - Full type annotations throughout
   - Forward references with TYPE_CHECKING
   - Modern Python best practices

## Differences from Vanilla McRogueFace Tutorial

### Removed
- Animation system (instant movement instead)
- Complex UI elements (focus on core mechanics)
- Real-time features (pure turn-based)
- Visual effects (camera following, smooth scrolling)
- Entity color property (sprites handle appearance)

### Added
- Complete movement key support
- Professional architecture patterns
- Proper package structure
- Type annotations
- Action-based design
- Extensible handler system
- Proper exit handling (Escape/Q actually quits)

### Adapted
- Grid rendering with proper centering
- Simplified entity system (position + sprite ID)
- Using simple_tutorial.png sprite sheet (12 sprites)
- Floor tiles using ground sprites (indices 1 and 2)
- Direct sprite indices instead of character mapping

## Learning Objectives

Students completing Part 1 will understand:
- How to structure a game project professionally
- The value of entity-centric design
- Command pattern for game actions
- Input handling that scales to complex UIs
- Type-driven development in Python
- Architecture that grows without refactoring

## What's Next

Part 2 will add:
- The GameMap class for world representation
- Tile-based movement and collision
- Multiple entities in the world
- Basic terrain (walls and floors)
- Rendering order for entities

The architecture we've built in Part 1 makes these additions natural and painless, demonstrating the value of starting with good patterns.