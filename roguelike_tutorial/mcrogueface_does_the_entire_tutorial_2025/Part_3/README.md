# Part 3 - Generating a Dungeon

In Parts 1 and 2, we created a player that could move around and interact with a hand-crafted dungeon. Now it's time to generate dungeons procedurally - a core feature of any roguelike game!

## The Plan

We'll create a dungeon generator that:
1. Places rectangular rooms randomly
2. Ensures rooms don't overlap
3. Connects rooms with tunnels
4. Places the player in the first room

This is a classic approach used by many roguelikes, and it creates interesting, playable dungeons.

## Creating a Room Class

First, let's create a class to represent rectangular rooms:

```python
class RectangularRoom:
    """A rectangular room with its position and size"""
    
    def __init__(self, x, y, width, height):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height
        
    @property
    def center(self):
        """Return the center coordinates of the room"""
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        return center_x, center_y
    
    @property
    def inner(self):
        """Return the inner area of the room as a tuple of slices
        
        This property returns the area inside the walls.
        We'll add 1 to min coordinates and subtract 1 from max coordinates.
        """
        return self.x1 + 1, self.y1 + 1, self.x2 - 1, self.y2 - 1
    
    def intersects(self, other):
        """Return True if this room overlaps with another RectangularRoom"""
        return (
            self.x1 <= other.x2
            and self.x2 >= other.x1
            and self.y1 <= other.y2
            and self.y2 >= other.y1
        )
```

## Implementing Tunnel Generation

Since McRogueFace doesn't include line-drawing algorithms, let's implement simple L-shaped tunnels:

```python
def tunnel_between(start, end):
    """Return an L-shaped tunnel between two points"""
    x1, y1 = start
    x2, y2 = end
    
    # Randomly decide whether to go horizontal first or vertical first
    if random.random() < 0.5:
        # Horizontal, then vertical
        corner_x = x2
        corner_y = y1
    else:
        # Vertical, then horizontal
        corner_x = x1
        corner_y = y2
    
    # Generate the coordinates
    # First line: from start to corner
    for x in range(min(x1, corner_x), max(x1, corner_x) + 1):
        yield x, y1
    for y in range(min(y1, corner_y), max(y1, corner_y) + 1):
        yield corner_x, y
        
    # Second line: from corner to end
    for x in range(min(corner_x, x2), max(corner_x, x2) + 1):
        yield x, corner_y
    for y in range(min(corner_y, y2), max(corner_y, y2) + 1):
        yield x2, y
```

## The Dungeon Generator

Now let's update our GameMap class to generate dungeons:

```python
import random

class GameMap:
    """Manages the game world"""
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = None
        self.entities = []
        self.rooms = []  # Keep track of rooms for game logic
        
    def generate_dungeon(
        self,
        max_rooms,
        room_min_size,
        room_max_size,
        player
    ):
        """Generate a new dungeon map"""
        # Start with everything as walls
        self.fill_with_walls()
        
        for r in range(max_rooms):
            # Random width and height
            room_width = random.randint(room_min_size, room_max_size)
            room_height = random.randint(room_min_size, room_max_size)
            
            # Random position without going out of bounds
            x = random.randint(0, self.width - room_width - 1)
            y = random.randint(0, self.height - room_height - 1)
            
            # Create the room
            new_room = RectangularRoom(x, y, room_width, room_height)
            
            # Check if it intersects with any existing room
            if any(new_room.intersects(other_room) for other_room in self.rooms):
                continue  # This room intersects, so go to the next attempt
                
            # If we get here, it's a valid room
            
            # Carve out this room
            self.carve_room(new_room)
            
            # Place the player in the center of the first room
            if len(self.rooms) == 0:
                player.x, player.y = new_room.center
                if player._entity:
                    player._entity.x, player._entity.y = new_room.center
            else:
                # All rooms after the first:
                # Tunnel between this room and the previous one
                self.carve_tunnel(self.rooms[-1].center, new_room.center)
            
            # Finally, append the new room to the list
            self.rooms.append(new_room)
    
    def carve_room(self, room):
        """Carve out a room"""
        inner_x1, inner_y1, inner_x2, inner_y2 = room.inner
        
        for y in range(inner_y1, inner_y2):
            for x in range(inner_x1, inner_x2):
                self.set_tile(x, y, walkable=True, transparent=True,
                            sprite_index=46, color=(50, 50, 50))
    
    def carve_tunnel(self, start, end):
        """Carve a tunnel between two points"""
        for x, y in tunnel_between(start, end):
            self.set_tile(x, y, walkable=True, transparent=True,
                        sprite_index=46, color=(30, 30, 40))  # Slightly different color for tunnels
```

## Complete Code

Here's the complete `game.py` with procedural dungeon generation:

```python
import mcrfpy
import random

class GameObject:
    """Base class for all game objects"""
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
        """Move by the given amount"""
        if not self.grid:
            return
        self.x += dx
        self.y += dy
        if self._entity:
            self._entity.x = self.x
            self._entity.y = self.y

class RectangularRoom:
    """A rectangular room with its position and size"""
    
    def __init__(self, x, y, width, height):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height
        
    @property
    def center(self):
        """Return the center coordinates of the room"""
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        return center_x, center_y
    
    @property
    def inner(self):
        """Return the inner area of the room"""
        return self.x1 + 1, self.y1 + 1, self.x2 - 1, self.y2 - 1
    
    def intersects(self, other):
        """Return True if this room overlaps with another"""
        return (
            self.x1 <= other.x2
            and self.x2 >= other.x1
            and self.y1 <= other.y2
            and self.y2 >= other.y1
        )

def tunnel_between(start, end):
    """Return an L-shaped tunnel between two points"""
    x1, y1 = start
    x2, y2 = end
    
    if random.random() < 0.5:
        corner_x = x2
        corner_y = y1
    else:
        corner_x = x1
        corner_y = y2
    
    # Generate the coordinates
    for x in range(min(x1, corner_x), max(x1, corner_x) + 1):
        yield x, y1
    for y in range(min(y1, corner_y), max(y1, corner_y) + 1):
        yield corner_x, y
    for x in range(min(corner_x, x2), max(corner_x, x2) + 1):
        yield x, corner_y
    for y in range(min(corner_y, y2), max(corner_y, y2) + 1):
        yield x2, y

class GameMap:
    """Manages the game world"""
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = None
        self.entities = []
        self.rooms = []
        
    def create_grid(self, tileset):
        """Create the McRogueFace grid"""
        self.grid = mcrfpy.Grid(grid_x=self.width, grid_y=self.height, texture=tileset)
                self.grid.position = (100, 100)
        self.grid.size = (800, 480)
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
    
    def generate_dungeon(self, max_rooms, room_min_size, room_max_size, player):
        """Generate a new dungeon map"""
        self.fill_with_walls()
        
        for r in range(max_rooms):
            room_width = random.randint(room_min_size, room_max_size)
            room_height = random.randint(room_min_size, room_max_size)
            
            x = random.randint(0, self.width - room_width - 1)
            y = random.randint(0, self.height - room_height - 1)
            
            new_room = RectangularRoom(x, y, room_width, room_height)
            
            if any(new_room.intersects(other_room) for other_room in self.rooms):
                continue
                
            self.carve_room(new_room)
            
            if len(self.rooms) == 0:
                player.x, player.y = new_room.center
                if player._entity:
                    player._entity.x, player._entity.y = new_room.center
            else:
                self.carve_tunnel(self.rooms[-1].center, new_room.center)
            
            self.rooms.append(new_room)
    
    def carve_room(self, room):
        """Carve out a room"""
        inner_x1, inner_y1, inner_x2, inner_y2 = room.inner
        
        for y in range(inner_y1, inner_y2):
            for x in range(inner_x1, inner_x2):
                self.set_tile(x, y, walkable=True, transparent=True,
                            sprite_index=46, color=(50, 50, 50))
    
    def carve_tunnel(self, start, end):
        """Carve a tunnel between two points"""
        for x, y in tunnel_between(start, end):
            self.set_tile(x, y, walkable=True, transparent=True,
                        sprite_index=46, color=(30, 30, 40))
    
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

class Engine:
    """Main game engine"""
    
    def __init__(self):
        self.game_map = None
        self.player = None
        self.entities = []
        
        mcrfpy.createScene("game")
        mcrfpy.setScene("game")
        
        window = mcrfpy.Window.get()
        window.title = "McRogueFace Roguelike - Part 3"
        
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
        self.game_map = GameMap(80, 45)
        grid = self.game_map.create_grid(self.tileset)
        self.ui.append(grid)
        
        # Create player (before dungeon generation)
        self.player = GameObject(0, 0, 64, (255, 255, 255), "Player", blocks=True)
        
        # Generate the dungeon
        self.game_map.generate_dungeon(
            max_rooms=30,
            room_min_size=6,
            room_max_size=10,
            player=self.player
        )
        
        # Add player to map
        self.game_map.add_entity(self.player)
        
        # Add some monsters in random rooms
        for i in range(5):
            if i < len(self.game_map.rooms) - 1:  # Don't spawn in first room
                room = self.game_map.rooms[i + 1]
                x, y = room.center
                
                # Create an orc
                orc = GameObject(x, y, 111, (63, 127, 63), "Orc", blocks=True)
                self.game_map.add_entity(orc)
                self.entities.append(orc)
    
    def handle_movement(self, dx, dy):
        """Handle player movement"""
        new_x = self.player.x + dx
        new_y = self.player.y + dy
        
        if not self.game_map.is_blocked(new_x, new_y):
            self.player.move(dx, dy)
    
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
            elif key == "Space":
                # Regenerate the dungeon
                self.regenerate_dungeon()
        
        mcrfpy.keypressScene(handle_keys)
    
    def regenerate_dungeon(self):
        """Generate a new dungeon"""
        # Clear existing entities
        self.game_map.entities.clear()
        self.game_map.rooms.clear()
        self.entities.clear()
        
        # Clear the entity list in the grid
        if self.game_map.grid:
            self.game_map.grid.entities.clear()
        
        # Regenerate
        self.game_map.generate_dungeon(
            max_rooms=30,
            room_min_size=6,
            room_max_size=10,
            player=self.player
        )
        
        # Re-add player
        self.game_map.add_entity(self.player)
        
        # Add new monsters
        for i in range(5):
            if i < len(self.game_map.rooms) - 1:
                room = self.game_map.rooms[i + 1]
                x, y = room.center
                orc = GameObject(x, y, 111, (63, 127, 63), "Orc", blocks=True)
                self.game_map.add_entity(orc)
                self.entities.append(orc)
    
    def setup_ui(self):
        """Setup UI elements"""
        title = mcrfpy.Caption("Procedural Dungeon Generation", 512, 30)
        title.font_size = 24
        title.fill_color = mcrfpy.Color(255, 255, 100)
        self.ui.append(title)
        
        instructions = mcrfpy.Caption("Arrow keys to move, SPACE to regenerate, ESC to quit", 512, 60)
        instructions.font_size = 16
        instructions.fill_color = mcrfpy.Color(200, 200, 200)
        self.ui.append(instructions)

# Create and run the game
engine = Engine()
print("Part 3: Procedural Dungeon Generation!")
print("Press SPACE to generate a new dungeon")
```

## Understanding the Algorithm

Our dungeon generation algorithm is simple but effective:

1. **Start with solid walls** - The entire map begins filled with wall tiles
2. **Try to place rooms** - Generate random rooms and check for overlaps
3. **Connect with tunnels** - Each new room connects to the previous one
4. **Place entities** - The player starts in the first room, monsters in others

### Room Placement

The algorithm attempts to place `max_rooms` rooms, but may place fewer if many attempts result in overlapping rooms. This is called "rejection sampling" - we generate random rooms and reject ones that don't fit.

### Tunnel Design

Our L-shaped tunnels are simple but effective. They either go:
- Horizontal first, then vertical
- Vertical first, then horizontal

This creates variety while ensuring all rooms are connected.

## Experimenting with Parameters

Try adjusting these parameters to create different dungeon styles:

```python
# Sparse dungeon with large rooms
self.game_map.generate_dungeon(
    max_rooms=10,
    room_min_size=10,
    room_max_size=15,
    player=self.player
)

# Dense dungeon with small rooms
self.game_map.generate_dungeon(
    max_rooms=50,
    room_min_size=4,
    room_max_size=6,
    player=self.player
)
```

## Visual Enhancements

Notice how we gave tunnels a slightly different color:
- Rooms: `color=(50, 50, 50)` - Medium gray
- Tunnels: `color=(30, 30, 40)` - Darker with blue tint

This subtle difference helps players understand the dungeon layout.

## Exercises

1. **Different Room Shapes**: Create circular or cross-shaped rooms
2. **Better Tunnel Routing**: Implement A* pathfinding for more natural tunnels
3. **Room Types**: Create special rooms (treasure rooms, trap rooms)
4. **Dungeon Themes**: Use different tile sets and colors for different dungeon levels

## What's Next?

In Part 4, we'll implement Field of View (FOV) so the player can only see parts of the dungeon they've explored. This will add mystery and atmosphere to our procedurally generated dungeons!

Our dungeon generator is now creating unique, playable levels every time. The foundation of a true roguelike is taking shape!