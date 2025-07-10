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