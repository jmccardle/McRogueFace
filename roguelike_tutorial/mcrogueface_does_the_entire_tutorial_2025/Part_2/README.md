# Part 2 - The Generic Entity, the Render Functions, and the Map

In Part 1, we created a player character that could move around a simple room. Now it's time to build a proper architecture for our roguelike. We'll create a flexible entity system, a proper map structure, and organize our code for future expansion.

## Understanding Game Architecture

Before diving into code, let's understand the architecture we're building:

1. **Entities**: Anything that can exist in the game world (player, monsters, items)
2. **Game Map**: The dungeon structure with tiles that can be walls or floors
3. **Game Engine**: Coordinates everything - entities, map, input, and rendering

In McRogueFace, we'll adapt these concepts to work with the engine's scene-based architecture.

## Creating a Flexible Entity System

While McRogueFace provides a built-in `Entity` class, we'll create a wrapper to add game-specific functionality:

```python
class GameObject:
    """Base class for all game objects (player, monsters, items)"""
    
    def __init__(self, x, y, sprite_index, color, name, blocks=False):
        self.x = x
        self.y = y
        self.sprite_index = sprite_index
        self.color = color
        self.name = name
        self.blocks = blocks  # Does this entity block movement?
        self._entity = None  # The McRogueFace entity
        self.grid = None     # Reference to the grid
    
    def attach_to_grid(self, grid):
        """Attach this game object to a McRogueFace grid"""
        self.grid = grid
        self._entity = mcrfpy.Entity(x=self.x, y=self.y, grid=grid)
        self._entity.sprite_index = self.sprite_index
        self._entity.color = self.color
    
    def move(self, dx, dy):
        """Move by the given amount if possible"""
        if not self.grid:
            return
        
        new_x = self.x + dx
        new_y = self.y + dy
        
        # Update our position
        self.x = new_x
        self.y = new_y
        
        # Update the visual entity
        if self._entity:
            self._entity.x = new_x
            self._entity.y = new_y
    
    def destroy(self):
        """Remove this entity from the game"""
        if self._entity and self.grid:
            # Find and remove from grid's entity list
            for i, entity in enumerate(self.grid.entities):
                if entity == self._entity:
                    del self.grid.entities[i]
                    break
            self._entity = None
```

## Building the Game Map

Let's create a proper map class that manages our dungeon:

```python
class GameMap:
    """Manages the game world"""
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = None
        self.entities = []  # List of GameObjects
        
    def create_grid(self, tileset):
        """Create the McRogueFace grid"""
        self.grid = mcrfpy.Grid(grid_x=self.width, grid_y=self.height, texture=tileset)
                self.grid.position = (100, 100)
        self.grid.size = (800, 480)
        
        # Initialize all tiles as walls
        self.fill_with_walls()
        
        return self.grid
    
    def fill_with_walls(self):
        """Fill the entire map with wall tiles"""
        for y in range(self.height):
            for x in range(self.width):
                self.set_tile(x, y, walkable=False, transparent=False, 
                            sprite_index=35, color=(100, 100, 100))
    
    def set_tile(self, x, y, walkable, transparent, sprite_index, color):
        """Set properties for a specific tile"""
        if 0 <= x < self.width and 0 <= y < self.height:
            cell = self.grid.at(x, y)
            cell.walkable = walkable
            cell.transparent = transparent
            cell.sprite_index = sprite_index
            cell.color = mcrfpy.Color(*color)
    
    def create_room(self, x1, y1, x2, y2):
        """Carve out a room in the map"""
        # Make sure coordinates are in the right order
        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)
        
        # Carve out floor tiles
        for y in range(y1, y2 + 1):
            for x in range(x1, x2 + 1):
                self.set_tile(x, y, walkable=True, transparent=True,
                            sprite_index=46, color=(50, 50, 50))
    
    def create_tunnel_h(self, x1, x2, y):
        """Create a horizontal tunnel"""
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.set_tile(x, y, walkable=True, transparent=True,
                        sprite_index=46, color=(50, 50, 50))
    
    def create_tunnel_v(self, y1, y2, x):
        """Create a vertical tunnel"""
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.set_tile(x, y, walkable=True, transparent=True,
                        sprite_index=46, color=(50, 50, 50))
    
    def is_blocked(self, x, y):
        """Check if a tile blocks movement"""
        # Check map boundaries
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return True
        
        # Check if tile is walkable
        if not self.grid.at(x, y).walkable:
            return True
        
        # Check if any blocking entity is at this position
        for entity in self.entities:
            if entity.blocks and entity.x == x and entity.y == y:
                return True
        
        return False
    
    def add_entity(self, entity):
        """Add a GameObject to the map"""
        self.entities.append(entity)
        entity.attach_to_grid(self.grid)
    
    def get_blocking_entity_at(self, x, y):
        """Return any blocking entity at the given position"""
        for entity in self.entities:
            if entity.blocks and entity.x == x and entity.y == y:
                return entity
        return None
```

## Creating the Game Engine

Now let's build our game engine to tie everything together:

```python
class Engine:
    """Main game engine that manages game state"""
    
    def __init__(self):
        self.game_map = None
        self.player = None
        self.entities = []
        
        # Create the game scene
        mcrfpy.createScene("game")
        mcrfpy.setScene("game")
        
        # Configure window
        window = mcrfpy.Window.get()
        window.title = "McRogueFace Roguelike - Part 2"
        
        # Get UI container
        self.ui = mcrfpy.sceneUI("game")
        
        # Add background
        background = mcrfpy.Frame(0, 0, 1024, 768)
        background.fill_color = mcrfpy.Color(0, 0, 0)
        self.ui.append(background)
        
        # Load tileset
        self.tileset = mcrfpy.Texture("assets/sprites/ascii_tileset.png", 16, 16)
        
        # Create the game world
        self.setup_game()
        
        # Setup input handling
        self.setup_input()
        
        # Add UI elements
        self.setup_ui()
    
    def setup_game(self):
        """Initialize the game world"""
        # Create the map
        self.game_map = GameMap(50, 30)
        grid = self.game_map.create_grid(self.tileset)
        self.ui.append(grid)
        
        # Create some rooms
        self.game_map.create_room(10, 10, 20, 20)
        self.game_map.create_room(30, 15, 40, 25)
        self.game_map.create_room(15, 22, 25, 28)
        
        # Connect rooms with tunnels
        self.game_map.create_tunnel_h(20, 30, 15)
        self.game_map.create_tunnel_v(20, 22, 20)
        
        # Create player
        self.player = GameObject(15, 15, 64, (255, 255, 255), "Player", blocks=True)
        self.game_map.add_entity(self.player)
        
        # Create an NPC
        npc = GameObject(35, 20, 64, (255, 255, 0), "NPC", blocks=True)
        self.game_map.add_entity(npc)
        self.entities.append(npc)
        
        # Create some items (non-blocking)
        potion = GameObject(12, 12, 33, (255, 0, 255), "Potion", blocks=False)
        self.game_map.add_entity(potion)
        self.entities.append(potion)
    
    def handle_movement(self, dx, dy):
        """Handle player movement"""
        new_x = self.player.x + dx
        new_y = self.player.y + dy
        
        # Check if movement is blocked
        if not self.game_map.is_blocked(new_x, new_y):
            self.player.move(dx, dy)
        else:
            # Check if we bumped into an entity
            target = self.game_map.get_blocking_entity_at(new_x, new_y)
            if target:
                print(f"You bump into the {target.name}!")
    
    def setup_input(self):
        """Setup keyboard input handling"""
        def handle_keys(key, state):
            if state != "start":
                return
            
            # Movement keys
            movement = {
                "Up": (0, -1),
                "Down": (0, 1),
                "Left": (-1, 0),
                "Right": (1, 0),
                "Num7": (-1, -1),
                "Num8": (0, -1),
                "Num9": (1, -1),
                "Num4": (-1, 0),
                "Num6": (1, 0),
                "Num1": (-1, 1),
                "Num2": (0, 1),
                "Num3": (1, 1),
            }
            
            if key in movement:
                dx, dy = movement[key]
                self.handle_movement(dx, dy)
            elif key == "Escape":
                mcrfpy.setScene(None)
        
        mcrfpy.keypressScene(handle_keys)
    
    def setup_ui(self):
        """Setup UI elements"""
        # Title
        title = mcrfpy.Caption("McRogueFace Roguelike - Part 2", 512, 30)
        title.font_size = 24
        title.fill_color = mcrfpy.Color(255, 255, 100)
        self.ui.append(title)
        
        # Instructions
        instructions = mcrfpy.Caption("Explore the dungeon! ESC to quit", 512, 60)
        instructions.font_size = 16
        instructions.fill_color = mcrfpy.Color(200, 200, 200)
        self.ui.append(instructions)
```

## Putting It All Together

Here's the complete `game.py` file:

```python
import mcrfpy

class GameObject:
    """Base class for all game objects (player, monsters, items)"""
    
    def __init__(self, x, y, sprite_index, color, name, blocks=False):
        self.x = x
        self.y = y
        self.sprite_index = sprite_index
        self.color = color
        self.name = name
        self.blocks = blocks
        self._entity = None
        self.grid = None
    
    def attach_to_grid(self, grid):
        """Attach this game object to a McRogueFace grid"""
        self.grid = grid
        self._entity = mcrfpy.Entity(x=self.x, y=self.y, grid=grid)
        self._entity.sprite_index = self.sprite_index
        self._entity.color = mcrfpy.Color(*self.color)
    
    def move(self, dx, dy):
        """Move by the given amount if possible"""
        if not self.grid:
            return
        
        new_x = self.x + dx
        new_y = self.y + dy
        
        self.x = new_x
        self.y = new_y
        
        if self._entity:
            self._entity.x = new_x
            self._entity.y = new_y

class GameMap:
    """Manages the game world"""
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = None
        self.entities = []
        
    def create_grid(self, tileset):
        """Create the McRogueFace grid"""
        self.grid = mcrfpy.Grid(grid_x=self.width, grid_y=self.height, texture=tileset)
                self.grid.position = (100, 100)
        self.grid.size = (800, 480)
        self.fill_with_walls()
        return self.grid
    
    def fill_with_walls(self):
        """Fill the entire map with wall tiles"""
        for y in range(self.height):
            for x in range(self.width):
                self.set_tile(x, y, walkable=False, transparent=False, 
                            sprite_index=35, color=(100, 100, 100))
    
    def set_tile(self, x, y, walkable, transparent, sprite_index, color):
        """Set properties for a specific tile"""
        if 0 <= x < self.width and 0 <= y < self.height:
            cell = self.grid.at(x, y)
            cell.walkable = walkable
            cell.transparent = transparent
            cell.sprite_index = sprite_index
            cell.color = mcrfpy.Color(*color)
    
    def create_room(self, x1, y1, x2, y2):
        """Carve out a room in the map"""
        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)
        
        for y in range(y1, y2 + 1):
            for x in range(x1, x2 + 1):
                self.set_tile(x, y, walkable=True, transparent=True,
                            sprite_index=46, color=(50, 50, 50))
    
    def create_tunnel_h(self, x1, x2, y):
        """Create a horizontal tunnel"""
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.set_tile(x, y, walkable=True, transparent=True,
                        sprite_index=46, color=(50, 50, 50))
    
    def create_tunnel_v(self, y1, y2, x):
        """Create a vertical tunnel"""
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.set_tile(x, y, walkable=True, transparent=True,
                        sprite_index=46, color=(50, 50, 50))
    
    def is_blocked(self, x, y):
        """Check if a tile blocks movement"""
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return True
        
        if not self.grid.at(x, y).walkable:
            return True
        
        for entity in self.entities:
            if entity.blocks and entity.x == x and entity.y == y:
                return True
        
        return False
    
    def add_entity(self, entity):
        """Add a GameObject to the map"""
        self.entities.append(entity)
        entity.attach_to_grid(self.grid)
    
    def get_blocking_entity_at(self, x, y):
        """Return any blocking entity at the given position"""
        for entity in self.entities:
            if entity.blocks and entity.x == x and entity.y == y:
                return entity
        return None

class Engine:
    """Main game engine that manages game state"""
    
    def __init__(self):
        self.game_map = None
        self.player = None
        self.entities = []
        
        mcrfpy.createScene("game")
        mcrfpy.setScene("game")
        
        window = mcrfpy.Window.get()
        window.title = "McRogueFace Roguelike - Part 2"
        
        self.ui = mcrfpy.sceneUI("game")
        
        background = mcrfpy.Frame(0, 0, 1024, 768)
        background.fill_color = mcrfpy.Color(0, 0, 0)
        self.ui.append(background)
        
        self.tileset = mcrfpy.Texture("assets/sprites/ascii_tileset.png", 16, 16)
        
        self.setup_game()
        self.setup_input()
        self.setup_ui()
    
    def setup_game(self):
        """Initialize the game world"""
        self.game_map = GameMap(50, 30)
        grid = self.game_map.create_grid(self.tileset)
        self.ui.append(grid)
        
        self.game_map.create_room(10, 10, 20, 20)
        self.game_map.create_room(30, 15, 40, 25)
        self.game_map.create_room(15, 22, 25, 28)
        
        self.game_map.create_tunnel_h(20, 30, 15)
        self.game_map.create_tunnel_v(20, 22, 20)
        
        self.player = GameObject(15, 15, 64, (255, 255, 255), "Player", blocks=True)
        self.game_map.add_entity(self.player)
        
        npc = GameObject(35, 20, 64, (255, 255, 0), "NPC", blocks=True)
        self.game_map.add_entity(npc)
        self.entities.append(npc)
        
        potion = GameObject(12, 12, 33, (255, 0, 255), "Potion", blocks=False)
        self.game_map.add_entity(potion)
        self.entities.append(potion)
    
    def handle_movement(self, dx, dy):
        """Handle player movement"""
        new_x = self.player.x + dx
        new_y = self.player.y + dy
        
        if not self.game_map.is_blocked(new_x, new_y):
            self.player.move(dx, dy)
        else:
            target = self.game_map.get_blocking_entity_at(new_x, new_y)
            if target:
                print(f"You bump into the {target.name}!")
    
    def setup_input(self):
        """Setup keyboard input handling"""
        def handle_keys(key, state):
            if state != "start":
                return
            
            movement = {
                "Up": (0, -1), "Down": (0, 1),
                "Left": (-1, 0), "Right": (1, 0),
                "Num7": (-1, -1), "Num8": (0, -1), "Num9": (1, -1),
                "Num4": (-1, 0), "Num6": (1, 0),
                "Num1": (-1, 1), "Num2": (0, 1), "Num3": (1, 1),
            }
            
            if key in movement:
                dx, dy = movement[key]
                self.handle_movement(dx, dy)
            elif key == "Escape":
                mcrfpy.setScene(None)
        
        mcrfpy.keypressScene(handle_keys)
    
    def setup_ui(self):
        """Setup UI elements"""
        title = mcrfpy.Caption("McRogueFace Roguelike - Part 2", 512, 30)
        title.font_size = 24
        title.fill_color = mcrfpy.Color(255, 255, 100)
        self.ui.append(title)
        
        instructions = mcrfpy.Caption("Explore the dungeon! ESC to quit", 512, 60)
        instructions.font_size = 16
        instructions.fill_color = mcrfpy.Color(200, 200, 200)
        self.ui.append(instructions)

# Create and run the game
engine = Engine()
print("Part 2: Entities and Maps!")
```

## Understanding the Architecture

### GameObject Class
Our `GameObject` class wraps McRogueFace's `Entity` and adds:
- Game logic properties (name, blocking)
- Position tracking independent of the visual entity
- Easy attachment/detachment from grids

### GameMap Class
The `GameMap` manages:
- The McRogueFace `Grid` for visual representation
- A list of all entities in the map
- Collision detection including entity blocking
- Map generation utilities (rooms, tunnels)

### Engine Class
The `Engine` coordinates everything:
- Scene and UI setup
- Game state management
- Input handling
- Entity-map interactions

## Key Improvements from Part 1

1. **Proper Entity Management**: Multiple entities can exist and interact
2. **Blocking Entities**: Some entities block movement, others don't
3. **Map Generation**: Tools for creating rooms and tunnels
4. **Collision System**: Checks both tiles and entities
5. **Organized Code**: Clear separation of concerns

## Exercises

1. **Add More Entity Types**: Create different sprites for monsters, items, and NPCs
2. **Entity Interactions**: Make items disappear when walked over
3. **Random Map Generation**: Place rooms and tunnels randomly
4. **Entity Properties**: Add health, damage, or other attributes to GameObjects

## What's Next?

In Part 3, we'll implement proper dungeon generation with:
- Procedurally generated rooms
- Smart tunnel routing
- Entity spawning
- The beginning of a real roguelike dungeon!

We now have a solid foundation with proper entity management and map structure. This architecture will serve us well as we add more complex features to our roguelike!