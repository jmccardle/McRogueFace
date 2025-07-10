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