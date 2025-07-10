# Part 1 - Drawing the '@' Symbol and Moving It Around

In Part 0, we set up McRogueFace and created a simple "Hello Roguelike" scene. Now it's time to create the foundation of our game: a player character that can move around the screen.

In traditional roguelikes, the player is represented by the '@' symbol. We'll honor that tradition while taking advantage of McRogueFace's powerful sprite-based rendering system.

## Understanding McRogueFace's Architecture

Before we dive into code, let's understand two key concepts in McRogueFace:

### Grid - The Game World

A `Grid` represents your game world. It's a 2D array of tiles where each tile can be:
- **Walkable or not** (for collision detection)
- **Transparent or not** (for field of view, which we'll cover later)
- **Have a visual appearance** (sprite index and color)

Think of the Grid as the dungeon floor, walls, and other static elements.

### Entity - Things That Move

An `Entity` represents anything that can move around on the Grid:
- The player character
- Monsters
- Items (if you want them to be thrown or moved)
- Projectiles

Entities exist "on top of" the Grid and automatically handle smooth movement animation between tiles.

## Creating Our Game World

Let's start by creating a simple room for our player to move around in. Create a new `game.py`:

```python
import mcrfpy

# Define some constants for our tile types
FLOOR_TILE = 0
WALL_TILE = 1
PLAYER_SPRITE = 2

# Window configuration
mcrfpy.createScene("game")
mcrfpy.setScene("game")

# Configure window properties
window = mcrfpy.Window.get()
window.title = "McRogueFace Roguelike - Part 1"

# Get the UI container for our scene
ui = mcrfpy.sceneUI("game")

# Create a dark background
background = mcrfpy.Frame(0, 0, 1024, 768)
background.fill_color = mcrfpy.Color(0, 0, 0)
ui.append(background)
```

Now we need to set up our tileset. For this tutorial, we'll use ASCII-style sprites. McRogueFace comes with a built-in ASCII tileset:

```python
# Load the ASCII tileset
# This tileset has characters mapped to sprite indices
# For example: @ = 64, # = 35, . = 46
tileset = mcrfpy.Texture("assets/sprites/ascii_tileset.png", 16, 16)

# Create the game grid
# 50x30 tiles is a good size for a roguelike
GRID_WIDTH = 50
GRID_HEIGHT = 30

grid = mcrfpy.Grid(grid_x=GRID_WIDTH, grid_y=GRID_HEIGHT, texture=tileset)
grid.position = (100, 100)  # Position on screen
grid.size = (800, 480)      # Size in pixels

# Add the grid to our UI
ui.append(grid)
```

## Initializing the Game World

Now let's fill our grid with a simple room:

```python
def create_room():
    """Create a room with walls around the edges"""
    # Fill everything with floor tiles first
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            cell = grid.at(x, y)
            cell.walkable = True
            cell.transparent = True
            cell.sprite_index = 46  # '.' character
            cell.color = mcrfpy.Color(50, 50, 50)  # Dark gray floor
    
    # Create walls around the edges
    for x in range(GRID_WIDTH):
        # Top wall
        cell = grid.at(x, 0)
        cell.walkable = False
        cell.transparent = False
        cell.sprite_index = 35  # '#' character
        cell.color = mcrfpy.Color(100, 100, 100)  # Gray walls
        
        # Bottom wall
        cell = grid.at(x, GRID_HEIGHT - 1)
        cell.walkable = False
        cell.transparent = False
        cell.sprite_index = 35  # '#' character
        cell.color = mcrfpy.Color(100, 100, 100)
    
    for y in range(GRID_HEIGHT):
        # Left wall
        cell = grid.at(0, y)
        cell.walkable = False
        cell.transparent = False
        cell.sprite_index = 35  # '#' character
        cell.color = mcrfpy.Color(100, 100, 100)
        
        # Right wall
        cell = grid.at(GRID_WIDTH - 1, y)
        cell.walkable = False
        cell.transparent = False
        cell.sprite_index = 35  # '#' character
        cell.color = mcrfpy.Color(100, 100, 100)

# Create the room
create_room()
```

## Creating the Player

Now let's add our player character:

```python
# Create the player entity
player = mcrfpy.Entity(x=GRID_WIDTH // 2, y=GRID_HEIGHT // 2, grid=grid)
player.sprite_index = 64  # '@' character
player.color = mcrfpy.Color(255, 255, 255)  # White

# The entity is automatically added to the grid when we pass grid= parameter
# This is equivalent to: grid.entities.append(player)
```

## Handling Input

McRogueFace uses a callback system for input. For a turn-based roguelike, we only care about key presses, not releases:

```python
def handle_input(key, state):
    """Handle keyboard input for player movement"""
    # Only process key presses, not releases
    if state != "start":
        return
    
    # Movement deltas
    dx, dy = 0, 0
    
    # Arrow keys
    if key == "Up":
        dy = -1
    elif key == "Down":
        dy = 1
    elif key == "Left":
        dx = -1
    elif key == "Right":
        dx = 1
    
    # Numpad movement (for true roguelike feel!)
    elif key == "Num7":  # Northwest
        dx, dy = -1, -1
    elif key == "Num8":  # North
        dy = -1
    elif key == "Num9":  # Northeast
        dx, dy = 1, -1
    elif key == "Num4":  # West
        dx = -1
    elif key == "Num6":  # East
        dx = 1
    elif key == "Num1":  # Southwest
        dx, dy = -1, 1
    elif key == "Num2":  # South
        dy = 1
    elif key == "Num3":  # Southeast
        dx, dy = 1, 1
    
    # Escape to quit
    elif key == "Escape":
        mcrfpy.setScene(None)
        return
    
    # If there's movement, try to move the player
    if dx != 0 or dy != 0:
        move_player(dx, dy)

# Register the input handler
mcrfpy.keypressScene(handle_input)
```

## Implementing Movement with Collision Detection

Now let's implement the movement function with proper collision detection:

```python
def move_player(dx, dy):
    """Move the player if the destination is walkable"""
    # Calculate new position
    new_x = player.x + dx
    new_y = player.y + dy
    
    # Check bounds
    if new_x < 0 or new_x >= GRID_WIDTH or new_y < 0 or new_y >= GRID_HEIGHT:
        return
    
    # Check if the destination is walkable
    destination = grid.at(new_x, new_y)
    if destination.walkable:
        # Move the player
        player.x = new_x
        player.y = new_y
        # The entity will automatically animate to the new position!
```

## Adding Visual Polish

Let's add some UI elements to make our game look more polished:

```python
# Add a title
title = mcrfpy.Caption("McRogueFace Roguelike", 512, 30)
title.font_size = 24
title.fill_color = mcrfpy.Color(255, 255, 100)  # Yellow
ui.append(title)

# Add instructions
instructions = mcrfpy.Caption("Arrow Keys or Numpad to move, ESC to quit", 512, 60)
instructions.font_size = 16
instructions.fill_color = mcrfpy.Color(200, 200, 200)  # Light gray
ui.append(instructions)

# Add a status line at the bottom
status = mcrfpy.Caption("@ You", 100, 600)
status.font_size = 18
status.fill_color = mcrfpy.Color(255, 255, 255)
ui.append(status)
```

## Complete Code

Here's the complete `game.py` for Part 1:

```python
import mcrfpy

# Window configuration
mcrfpy.createScene("game")
mcrfpy.setScene("game")

window = mcrfpy.Window.get()
window.title = "McRogueFace Roguelike - Part 1"

# Get the UI container for our scene
ui = mcrfpy.sceneUI("game")

# Create a dark background
background = mcrfpy.Frame(0, 0, 1024, 768)
background.fill_color = mcrfpy.Color(0, 0, 0)
ui.append(background)

# Load the ASCII tileset
tileset = mcrfpy.Texture("assets/sprites/ascii_tileset.png", 16, 16)

# Create the game grid
GRID_WIDTH = 50
GRID_HEIGHT = 30

grid = mcrfpy.Grid(grid_x=GRID_WIDTH, grid_y=GRID_HEIGHT, texture=tileset)
grid.position = (100, 100)
grid.size = (800, 480)
ui.append(grid)

def create_room():
    """Create a room with walls around the edges"""
    # Fill everything with floor tiles first
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            cell = grid.at(x, y)
            cell.walkable = True
            cell.transparent = True
            cell.sprite_index = 46  # '.' character
            cell.color = mcrfpy.Color(50, 50, 50)  # Dark gray floor
    
    # Create walls around the edges
    for x in range(GRID_WIDTH):
        # Top wall
        cell = grid.at(x, 0)
        cell.walkable = False
        cell.transparent = False
        cell.sprite_index = 35  # '#' character
        cell.color = mcrfpy.Color(100, 100, 100)  # Gray walls
        
        # Bottom wall
        cell = grid.at(x, GRID_HEIGHT - 1)
        cell.walkable = False
        cell.transparent = False
        cell.sprite_index = 35  # '#' character
        cell.color = mcrfpy.Color(100, 100, 100)
    
    for y in range(GRID_HEIGHT):
        # Left wall
        cell = grid.at(0, y)
        cell.walkable = False
        cell.transparent = False
        cell.sprite_index = 35  # '#' character
        cell.color = mcrfpy.Color(100, 100, 100)
        
        # Right wall
        cell = grid.at(GRID_WIDTH - 1, y)
        cell.walkable = False
        cell.transparent = False
        cell.sprite_index = 35  # '#' character
        cell.color = mcrfpy.Color(100, 100, 100)

# Create the room
create_room()

# Create the player entity
player = mcrfpy.Entity(x=GRID_WIDTH // 2, y=GRID_HEIGHT // 2, grid=grid)
player.sprite_index = 64  # '@' character
player.color = mcrfpy.Color(255, 255, 255)  # White

def move_player(dx, dy):
    """Move the player if the destination is walkable"""
    # Calculate new position
    new_x = player.x + dx
    new_y = player.y + dy
    
    # Check bounds
    if new_x < 0 or new_x >= GRID_WIDTH or new_y < 0 or new_y >= GRID_HEIGHT:
        return
    
    # Check if the destination is walkable
    destination = grid.at(new_x, new_y)
    if destination.walkable:
        # Move the player
        player.x = new_x
        player.y = new_y

def handle_input(key, state):
    """Handle keyboard input for player movement"""
    # Only process key presses, not releases
    if state != "start":
        return
    
    # Movement deltas
    dx, dy = 0, 0
    
    # Arrow keys
    if key == "Up":
        dy = -1
    elif key == "Down":
        dy = 1
    elif key == "Left":
        dx = -1
    elif key == "Right":
        dx = 1
    
    # Numpad movement (for true roguelike feel!)
    elif key == "Num7":  # Northwest
        dx, dy = -1, -1
    elif key == "Num8":  # North
        dy = -1
    elif key == "Num9":  # Northeast
        dx, dy = 1, -1
    elif key == "Num4":  # West
        dx = -1
    elif key == "Num6":  # East
        dx = 1
    elif key == "Num1":  # Southwest
        dx, dy = -1, 1
    elif key == "Num2":  # South
        dy = 1
    elif key == "Num3":  # Southeast
        dx, dy = 1, 1
    
    # Escape to quit
    elif key == "Escape":
        mcrfpy.setScene(None)
        return
    
    # If there's movement, try to move the player
    if dx != 0 or dy != 0:
        move_player(dx, dy)

# Register the input handler
mcrfpy.keypressScene(handle_input)

# Add UI elements
title = mcrfpy.Caption("McRogueFace Roguelike", 512, 30)
title.font_size = 24
title.fill_color = mcrfpy.Color(255, 255, 100)
ui.append(title)

instructions = mcrfpy.Caption("Arrow Keys or Numpad to move, ESC to quit", 512, 60)
instructions.font_size = 16
instructions.fill_color = mcrfpy.Color(200, 200, 200)
ui.append(instructions)

status = mcrfpy.Caption("@ You", 100, 600)
status.font_size = 18
status.fill_color = mcrfpy.Color(255, 255, 255)
ui.append(status)

print("Part 1: The @ symbol moves!")
```

## Understanding What We've Built

Let's review the key concepts we've implemented:

1. **Grid-Entity Architecture**: The Grid represents our static world (floors and walls), while the Entity (player) moves on top of it.

2. **Collision Detection**: By checking the `walkable` property of grid cells, we prevent the player from walking through walls.

3. **Turn-Based Input**: By only responding to key presses (not releases), we've created true turn-based movement.

4. **Visual Feedback**: The Entity system automatically animates movement between tiles, giving smooth visual feedback.

## Exercises

Try these modifications to deepen your understanding:

1. **Add More Rooms**: Create multiple rooms connected by corridors
2. **Different Tile Types**: Add doors (walkable but different appearance)
3. **Sprint Movement**: Hold Shift to move multiple tiles at once
4. **Mouse Support**: Click a tile to pathfind to it (we'll cover pathfinding properly later)

## ASCII Sprite Reference

Here are some useful ASCII character indices for the default tileset:
- @ (player): 64
- # (wall): 35
- . (floor): 46
- + (door): 43
- ~ (water): 126
- % (item): 37
- ! (potion): 33

## What's Next?

In Part 2, we'll expand our world with:
- A proper Entity system for managing multiple objects
- NPCs that can also move around
- A more interesting map layout
- The beginning of our game architecture

The foundation is set - you have a player character that can move around a world with collision detection. This is the core of any roguelike game!