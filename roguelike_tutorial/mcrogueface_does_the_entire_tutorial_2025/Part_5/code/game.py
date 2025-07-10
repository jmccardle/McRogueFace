import mcrfpy
import random

# Color configurations
COLORS_VISIBLE = {
    'wall': (100, 100, 100),    
    'floor': (50, 50, 50),      
    'tunnel': (30, 30, 40),     
}

# Actions
class Action:
    """Base class for all actions"""
    pass

class MovementAction(Action):
    """Action for moving an entity"""
    def __init__(self, dx, dy):
        self.dx = dx
        self.dy = dy

class WaitAction(Action):
    """Action for waiting/skipping turn"""
    pass

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

def spawn_enemies_in_room(room, game_map, max_enemies=2):
    """Spawn between 0 and max_enemies in a room"""
    number_of_enemies = random.randint(0, max_enemies)
    
    enemies_spawned = []
    
    for i in range(number_of_enemies):
        # Try to find a valid position
        attempts = 10
        while attempts > 0:
            # Random position within room bounds
            x = random.randint(room.x1 + 1, room.x2 - 1)
            y = random.randint(room.y1 + 1, room.y2 - 1)
            
            # Check if position is valid
            if not game_map.is_blocked(x, y):
                # 80% chance for orc, 20% for troll
                if random.random() < 0.8:
                    enemy = GameObject(x, y, 111, (63, 127, 63), "Orc", blocks=True)
                else:
                    enemy = GameObject(x, y, 84, (0, 127, 0), "Troll", blocks=True)
                
                game_map.add_entity(enemy)
                enemies_spawned.append(enemy)
                break
            
            attempts -= 1
    
    return enemies_spawned

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
        
        # Enable perspective rendering
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
    
    def generate_dungeon(self, max_rooms, room_min_size, room_max_size, player, max_enemies_per_room):
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
                # First room - place player
                player.x, player.y = new_room.center
                if player._entity:
                    player._entity.x, player._entity.y = new_room.center
            else:
                # All other rooms - add tunnel and enemies
                self.carve_tunnel(self.rooms[-1].center, new_room.center)
                spawn_enemies_in_room(new_room, self, max_enemies_per_room)
            
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
    
    def get_blocking_entity_at(self, x, y):
        """Return any blocking entity at the given position"""
        for entity in self.entities:
            if entity.blocks and entity.x == x and entity.y == y:
                return entity
        return None
    
    def is_blocked(self, x, y):
        """Check if a tile blocks movement"""
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return True
        
        if not self.grid.at(x, y).walkable:
            return True
        
        if self.get_blocking_entity_at(x, y):
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
        window.title = "McRogueFace Roguelike - Part 5"
        
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
            player=self.player,
            max_enemies_per_room=2
        )
        
        # Add player to map
        self.game_map.add_entity(self.player)
        
        # Store reference to all entities
        self.entities = [e for e in self.game_map.entities if e != self.player]
        
        # Initial FOV calculation
        self.player.update_fov()
    
    def handle_player_turn(self, action):
        """Process the player's action"""
        if isinstance(action, MovementAction):
            dest_x = self.player.x + action.dx
            dest_y = self.player.y + action.dy
            
            # Check what's at the destination
            target = self.game_map.get_blocking_entity_at(dest_x, dest_y)
            
            if target:
                # We bumped into something!
                print(f"You kick the {target.name} in the shins, much to its annoyance!")
                self.status_text.text = f"You kick the {target.name}!"
            elif not self.game_map.is_blocked(dest_x, dest_y):
                # Move the player
                self.player.move(action.dx, action.dy)
                self.status_text.text = ""
            else:
                # Bumped into a wall
                self.status_text.text = "Blocked!"
        
        elif isinstance(action, WaitAction):
            self.status_text.text = "You wait..."
    
    def setup_input(self):
        """Setup keyboard input handling"""
        def handle_keys(key, state):
            if state != "start":
                return
            
            action = None
            
            # Movement keys
            movement = {
                "Up": (0, -1), "Down": (0, 1),
                "Left": (-1, 0), "Right": (1, 0),
                "Num7": (-1, -1), "Num8": (0, -1), "Num9": (1, -1),
                "Num4": (-1, 0), "Num5": (0, 0), "Num6": (1, 0),
                "Num1": (-1, 1), "Num2": (0, 1), "Num3": (1, 1),
            }
            
            if key in movement:
                dx, dy = movement[key]
                if dx == 0 and dy == 0:
                    action = WaitAction()
                else:
                    action = MovementAction(dx, dy)
            elif key == "Period":
                action = WaitAction()
            elif key == "Escape":
                mcrfpy.setScene(None)
                return
            
            # Process the action
            if action:
                self.handle_player_turn(action)
        
        mcrfpy.keypressScene(handle_keys)
    
    def setup_ui(self):
        """Setup UI elements"""
        title = mcrfpy.Caption("Placing Enemies", 512, 30)
        title.font_size = 24
        title.fill_color = mcrfpy.Color(255, 255, 100)
        self.ui.append(title)
        
        instructions = mcrfpy.Caption("Arrow keys to move | . to wait | Bump into enemies! | ESC to quit", 512, 60)
        instructions.font_size = 16
        instructions.fill_color = mcrfpy.Color(200, 200, 200)
        self.ui.append(instructions)
        
        # Status text
        self.status_text = mcrfpy.Caption("", 512, 600)
        self.status_text.font_size = 18
        self.status_text.fill_color = mcrfpy.Color(255, 200, 200)
        self.ui.append(self.status_text)
        
        # Entity count
        entity_count = len(self.entities)
        count_text = mcrfpy.Caption(f"Enemies: {entity_count}", 900, 100)
        count_text.font_size = 14
        count_text.fill_color = mcrfpy.Color(150, 150, 255)
        self.ui.append(count_text)

# Create and run the game
engine = Engine()
print("Part 5: Placing Enemies!")
print("Try bumping into enemies - combat coming in Part 6!")