import mcrfpy
import random

# Color configurations for visibility
COLORS_VISIBLE = {
    'wall': (100, 100, 100),    
    'floor': (50, 50, 50),      
    'tunnel': (30, 30, 40),     
}

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
            # Update FOV when player moves
            if self.name == "Player":
                self.update_fov()
    
    def update_fov(self):
        """Update field of view from this entity's position"""
        if self._entity and self.grid:
            self._entity.update_fov(radius=8)

class RectangularRoom:
    """A rectangular room with its position and size"""
    
    def __init__(self, x, y, width, height):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height
        
    @property
    def center(self):
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        return center_x, center_y
    
    @property
    def inner(self):
        return self.x1 + 1, self.y1 + 1, self.x2 - 1, self.y2 - 1
    
    def intersects(self, other):
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
        
        # Enable perspective rendering (0 = first entity = player)
        self.grid.perspective = 0
        
        return self.grid
    
    def fill_with_walls(self):
        """Fill the entire map with wall tiles"""
        for y in range(self.height):
            for x in range(self.width):
                self.set_tile(x, y, walkable=False, transparent=False, 
                            sprite_index=35, tile_type='wall')
    
    def set_tile(self, x, y, walkable, transparent, sprite_index, tile_type):
        """Set properties for a specific tile"""
        if 0 <= x < self.width and 0 <= y < self.height:
            cell = self.grid.at(x, y)
            cell.walkable = walkable
            cell.transparent = transparent
            cell.sprite_index = sprite_index
            cell.color = mcrfpy.Color(*COLORS_VISIBLE[tile_type])
    
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
                            sprite_index=46, tile_type='floor')
    
    def carve_tunnel(self, start, end):
        """Carve a tunnel between two points"""
        for x, y in tunnel_between(start, end):
            self.set_tile(x, y, walkable=True, transparent=True,
                        sprite_index=46, tile_type='tunnel')
    
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
        self.fov_radius = 8
        
        mcrfpy.createScene("game")
        mcrfpy.setScene("game")
        
        window = mcrfpy.Window.get()
        window.title = "McRogueFace Roguelike - Part 4"
        
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
        
        # Create player
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
        
        # Add monsters in random rooms
        for i in range(10):
            if i < len(self.game_map.rooms) - 1:
                room = self.game_map.rooms[i + 1]
                x, y = room.center
                
                # Randomly offset from center
                x += random.randint(-2, 2)
                y += random.randint(-2, 2)
                
                # Make sure position is walkable
                if self.game_map.grid.at(x, y).walkable:
                    if i % 2 == 0:
                        # Create an orc
                        orc = GameObject(x, y, 111, (63, 127, 63), "Orc", blocks=True)
                        self.game_map.add_entity(orc)
                        self.entities.append(orc)
                    else:
                        # Create a troll
                        troll = GameObject(x, y, 84, (0, 127, 0), "Troll", blocks=True)
                        self.game_map.add_entity(troll)
                        self.entities.append(troll)
        
        # Initial FOV calculation
        self.player.update_fov()
    
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
            elif key == "v":
                # Toggle FOV on/off
                if self.game_map.grid.perspective == 0:
                    self.game_map.grid.perspective = -1  # Omniscient
                    print("FOV disabled - omniscient view")
                else:
                    self.game_map.grid.perspective = 0  # Player perspective
                    print("FOV enabled - player perspective")
            elif key == "Plus" or key == "Equals":
                # Increase FOV radius
                self.fov_radius = min(self.fov_radius + 1, 20)
                self.player._entity.update_fov(radius=self.fov_radius)
                print(f"FOV radius: {self.fov_radius}")
            elif key == "Minus":
                # Decrease FOV radius
                self.fov_radius = max(self.fov_radius - 1, 3)
                self.player._entity.update_fov(radius=self.fov_radius)
                print(f"FOV radius: {self.fov_radius}")
        
        mcrfpy.keypressScene(handle_keys)
    
    def setup_ui(self):
        """Setup UI elements"""
        title = mcrfpy.Caption("Field of View", 512, 30)
        title.font_size = 24
        title.fill_color = mcrfpy.Color(255, 255, 100)
        self.ui.append(title)
        
        instructions = mcrfpy.Caption("Arrow keys to move | V to toggle FOV | +/- to adjust radius | ESC to quit", 512, 60)
        instructions.font_size = 16
        instructions.fill_color = mcrfpy.Color(200, 200, 200)
        self.ui.append(instructions)
        
        # FOV indicator
        self.fov_text = mcrfpy.Caption(f"FOV Radius: {self.fov_radius}", 900, 100)
        self.fov_text.font_size = 14
        self.fov_text.fill_color = mcrfpy.Color(150, 200, 255)
        self.ui.append(self.fov_text)

# Create and run the game
engine = Engine()
print("Part 4: Field of View!")
print("Press V to toggle FOV on/off")
print("Press +/- to adjust FOV radius")