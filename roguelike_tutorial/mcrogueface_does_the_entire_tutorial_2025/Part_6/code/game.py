import mcrfpy
import random

# Color configurations
COLORS_VISIBLE = {
    'wall': (100, 100, 100),    
    'floor': (50, 50, 50),      
    'tunnel': (30, 30, 40),     
}

# Message colors
COLOR_PLAYER_ATK = (230, 230, 230)
COLOR_ENEMY_ATK = (255, 200, 200)
COLOR_PLAYER_DIE = (255, 100, 100)
COLOR_ENEMY_DIE = (255, 165, 0)

# Actions
class Action:
    """Base class for all actions"""
    pass

class MovementAction(Action):
    """Action for moving an entity"""
    def __init__(self, dx, dy):
        self.dx = dx
        self.dy = dy

class MeleeAction(Action):
    """Action for melee attacks"""
    def __init__(self, attacker, target):
        self.attacker = attacker
        self.target = target
    
    def perform(self):
        """Execute the attack"""
        if not self.target.is_alive:
            return None
        
        damage = self.attacker.power - self.target.defense
        
        if damage > 0:
            attack_desc = f"{self.attacker.name} attacks {self.target.name} for {damage} damage!"
            self.target.take_damage(damage)
            
            # Choose color based on attacker
            if self.attacker.name == "Player":
                color = COLOR_PLAYER_ATK
            else:
                color = COLOR_ENEMY_ATK
                
            return attack_desc, color
        else:
            attack_desc = f"{self.attacker.name} attacks {self.target.name} but does no damage."
            return attack_desc, (150, 150, 150)

class WaitAction(Action):
    """Action for waiting/skipping turn"""
    pass

class GameObject:
    """Base class for all game objects"""
    def __init__(self, x, y, sprite_index, color, name, 
                 blocks=False, hp=0, defense=0, power=0):
        self.x = x
        self.y = y
        self.sprite_index = sprite_index
        self.color = color
        self.name = name
        self.blocks = blocks
        self._entity = None
        self.grid = None
        
        # Combat stats
        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.power = power
        
    @property
    def is_alive(self):
        """Returns True if this entity can act"""
        return self.hp > 0
    
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
    
    def take_damage(self, amount):
        """Apply damage to this entity"""
        self.hp -= amount
            
        # Check for death
        if self.hp <= 0:
            self.die()
    
    def die(self):
        """Handle entity death"""
        if self.name == "Player":
            # Player death
            self.sprite_index = 64  # Stay as @
            self.color = (127, 0, 0)  # Dark red
            if self._entity:
                self._entity.color = mcrfpy.Color(127, 0, 0)
        else:
            # Enemy death
            self.sprite_index = 37  # % character for corpse
            self.color = (127, 0, 0)  # Dark red
            self.blocks = False  # Corpses don't block
            self.name = f"remains of {self.name}"
            
            if self._entity:
                self._entity.sprite_index = 37
                self._entity.color = mcrfpy.Color(127, 0, 0)

# Entity factories
def create_player(x, y):
    """Create the player entity"""
    return GameObject(
        x=x, y=y,
        sprite_index=64,  # @
        color=(255, 255, 255),
        name="Player",
        blocks=True,
        hp=30,
        defense=2,
        power=5
    )

def create_orc(x, y):
    """Create an orc enemy"""
    return GameObject(
        x=x, y=y,
        sprite_index=111,  # o
        color=(63, 127, 63),
        name="Orc",
        blocks=True,
        hp=10,
        defense=0,
        power=3
    )

def create_troll(x, y):
    """Create a troll enemy"""
    return GameObject(
        x=x, y=y,
        sprite_index=84,  # T
        color=(0, 127, 0),
        name="Troll",
        blocks=True,
        hp=16,
        defense=1,
        power=4
    )

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
        attempts = 10
        while attempts > 0:
            x = random.randint(room.x1 + 1, room.x2 - 1)
            y = random.randint(room.y1 + 1, room.y2 - 1)
            
            if not game_map.is_blocked(x, y):
                # 80% chance for orc, 20% for troll
                if random.random() < 0.8:
                    enemy = create_orc(x, y)
                else:
                    enemy = create_troll(x, y)
                
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
        self.messages = []  # Simple message log
        self.max_messages = 5
        
        mcrfpy.createScene("game")
        mcrfpy.setScene("game")
        
        window = mcrfpy.Window.get()
        window.title = "McRogueFace Roguelike - Part 6"
        
        self.ui = mcrfpy.sceneUI("game")
        
        background = mcrfpy.Frame(0, 0, 1024, 768)
        background.fill_color = mcrfpy.Color(0, 0, 0)
        self.ui.append(background)
        
        self.tileset = mcrfpy.Texture("assets/sprites/ascii_tileset.png", 16, 16)
        
        self.setup_game()
        self.setup_input()
        self.setup_ui()
    
    def add_message(self, text, color=(255, 255, 255)):
        """Add a message to the log"""
        self.messages.append((text, color))
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)
        self.update_message_display()
    
    def update_message_display(self):
        """Update the message display"""
        # Clear old messages
        for caption in self.message_captions:
            # Remove from UI (McRogueFace doesn't have remove, so we hide it)
            caption.text = ""
        
        # Display current messages
        for i, (text, color) in enumerate(self.messages):
            if i < len(self.message_captions):
                self.message_captions[i].text = text
                self.message_captions[i].fill_color = mcrfpy.Color(*color)
    
    def setup_game(self):
        """Initialize the game world"""
        self.game_map = GameMap(80, 45)
        grid = self.game_map.create_grid(self.tileset)
        self.ui.append(grid)
        
        # Create player
        self.player = create_player(0, 0)
        
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
        
        # Welcome message
        self.add_message("Welcome to the dungeon!", (100, 100, 255))
    
    def handle_player_turn(self, action):
        """Process the player's action"""
        if not self.player.is_alive:
            return
            
        if isinstance(action, MovementAction):
            dest_x = self.player.x + action.dx
            dest_y = self.player.y + action.dy
            
            # Check what's at the destination
            target = self.game_map.get_blocking_entity_at(dest_x, dest_y)
            
            if target:
                # Attack!
                attack = MeleeAction(self.player, target)
                result = attack.perform()
                if result:
                    text, color = result
                    self.add_message(text, color)
                    
                    # Check if target died
                    if not target.is_alive:
                        death_msg = f"The {target.name.replace('remains of ', '')} is dead!"
                        self.add_message(death_msg, COLOR_ENEMY_DIE)
                        
            elif not self.game_map.is_blocked(dest_x, dest_y):
                # Move the player
                self.player.move(action.dx, action.dy)
                
        elif isinstance(action, WaitAction):
            pass  # Do nothing
        
        # Enemy turns
        self.handle_enemy_turns()
    
    def handle_enemy_turns(self):
        """Let all enemies take their turn"""
        for entity in self.entities:
            if entity.is_alive:
                # Simple AI: if player is adjacent, attack. Otherwise, do nothing.
                dx = entity.x - self.player.x
                dy = entity.y - self.player.y
                distance = abs(dx) + abs(dy)
                
                if distance == 1:  # Adjacent to player
                    attack = MeleeAction(entity, self.player)
                    result = attack.perform()
                    if result:
                        text, color = result
                        self.add_message(text, color)
                        
                        # Check if player died
                        if not self.player.is_alive:
                            self.add_message("You have died!", COLOR_PLAYER_DIE)
    
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
        title = mcrfpy.Caption("Combat System", 512, 30)
        title.font_size = 24
        title.fill_color = mcrfpy.Color(255, 255, 100)
        self.ui.append(title)
        
        instructions = mcrfpy.Caption("Attack enemies by bumping into them!", 512, 60)
        instructions.font_size = 16
        instructions.fill_color = mcrfpy.Color(200, 200, 200)
        self.ui.append(instructions)
        
        # Player stats
        self.hp_text = mcrfpy.Caption(f"HP: {self.player.hp}/{self.player.max_hp}", 50, 100)
        self.hp_text.font_size = 18
        self.hp_text.fill_color = mcrfpy.Color(255, 100, 100)
        self.ui.append(self.hp_text)
        
        # Message log
        self.message_captions = []
        for i in range(self.max_messages):
            caption = mcrfpy.Caption("", 50, 620 + i * 20)
            caption.font_size = 14
            caption.fill_color = mcrfpy.Color(200, 200, 200)
            self.ui.append(caption)
            self.message_captions.append(caption)
        
        # Timer to update HP display
        def update_stats(dt):
            self.hp_text.text = f"HP: {self.player.hp}/{self.player.max_hp}"
            if self.player.hp <= 0:
                self.hp_text.fill_color = mcrfpy.Color(127, 0, 0)
            elif self.player.hp < self.player.max_hp // 3:
                self.hp_text.fill_color = mcrfpy.Color(255, 100, 100)
            else:
                self.hp_text.fill_color = mcrfpy.Color(0, 255, 0)
        
        mcrfpy.setTimer("update_stats", update_stats, 100)

# Create and run the game
engine = Engine()
print("Part 6: Combat System!")
print("Attack enemies to defeat them, but watch your HP!")