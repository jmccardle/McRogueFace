import mcrfpy
mcrfpy.createScene("play")
ui = mcrfpy.sceneUI("play")
t = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16) # 12, 11)
font = mcrfpy.Font("assets/JetbrainsMono.ttf")

frame_color = (64, 64, 128)

grid = mcrfpy.Grid(20, 15, t, 10, 10, 800, 595)
grid.zoom = 2.0
entity_frame = mcrfpy.Frame(815, 10, 194, 595, fill_color = frame_color)
inventory_frame = mcrfpy.Frame(10, 610, 800, 143, fill_color = frame_color)
stats_frame = mcrfpy.Frame(815, 610, 194, 143, fill_color = frame_color)

begin_btn = mcrfpy.Frame(350,250,100,100, fill_color = (255,0,0))
begin_btn.children.append(mcrfpy.Caption(5, 5, "Begin", font))
def cos_keys(key, state):
    if key == 'M' and state == 'start':
        mapgen()
    elif state == "end": return
    elif key == "W":
        player.move("N")
    elif key == "A":
        player.move("W")
    elif key == "S":
        player.move("S")
    elif key == "D":
        player.move("E")


def cos_init(*args):
    if args[3] != "start": return
    mcrfpy.keypressScene(cos_keys)
    ui.remove(4)
    
begin_btn.click = cos_init

[ui.append(e) for e in (grid, entity_frame, inventory_frame, stats_frame, begin_btn)]

import random
def rcolor():
    return tuple([random.randint(0, 255) for i in range(3)]) # TODO list won't work with GridPoint.color, so had to cast to tuple

x_max, y_max = grid.grid_size
for x in range(x_max):
    for y in range(y_max):
        grid.at((x,y)).color = rcolor()

from math import pi, cos, sin
def mapgen(room_size_max = 7, room_size_min = 3, room_count = 4):
    # reset map
    for x in range(x_max):
        for y in range(y_max):
            grid.at((x, y)).walkable = False
            grid.at((x, y)).transparent= False
            grid.at((x,y)).tilesprite = random.choices([40, 28], weights=[.8, .2])[0]
    global cos_entities
    for e in cos_entities:
        e.e.position = (999,999) # TODO
        e.die()
    cos_entities = []

    #Dungeon generation
    centers = []
    attempts = 0
    while len(centers) < room_count:
    # Leaving this attempt here for later comparison. These rooms sucked.
    # overlapping, uninteresting hallways, crowded into the corners sometimes, etc.
        attempts += 1
        if attempts > room_count * 15: break
    #    room_left = random.randint(1, x_max)
    #    room_top = random.randint(1, y_max)

    # Take 2 - circular distribution of rooms
        angle_mid = (len(centers) / room_count) * 2 * pi + 0.785
        angle = random.uniform(angle_mid - 0.25, angle_mid + 0.25)
        radius = random.uniform(3, 14)
        room_left = int(radius * cos(angle)) + int(x_max/2)
        if room_left <= 1: room_left = 1
        if room_left > x_max - 1: room_left = x_max - 2
        room_top = int(radius * sin(angle)) + int(y_max/2)
        if room_top <= 1: room_top = 1
        if room_top > y_max - 1: room_top = y_max - 2
        room_w = random.randint(room_size_min, room_size_max)
        if room_w + room_left >= x_max: room_w = x_max - room_left - 2
        room_h = random.randint(room_size_min, room_size_max)
        if room_h + room_top >= y_max: room_h = y_max - room_top - 2
        #print(room_left, room_top, room_left + room_w, room_top + room_h)
        if any( # centers contained in this randomly generated room
            [c[0] >= room_left and c[0] <= room_left + room_w and c[1] >= room_top and c[1] <= room_top + room_h for c in centers]
            ):
            continue # re-randomize the room position
        centers.append(
                (int(room_left + (room_w/2)), int(room_top + (room_h/2)))
                )

        for x in range(room_w):
            for y in range(room_h):
                grid.at((room_left+x, room_top+y)).walkable=True
                grid.at((room_left+x, room_top+y)).transparent=True
                grid.at((room_left+x, room_top+y)).tilesprite = random.choice([48, 49, 50, 51, 52, 53])

        # generate a boulder
        if (room_w > 2 and room_h > 2):
            room_boulder_x, room_boulder_y = random.randint(room_left+1, room_left+room_w-1), random.randint(room_top+1, room_top+room_h-1)
            cos_entities.append(BoulderEntity(room_boulder_x, room_boulder_y))

    print(f"{room_count} rooms generated after {attempts} attempts.")
    #print(centers)
    # hallways
    pairs = []
    for c1 in centers:
        for c2 in centers:
            if c1 == c2: continue
            if (c2, c1) in pairs or (c1, c2) in pairs: continue
            left = min(c1[0], c2[0])
            right = max(c1[0], c2[0])
            top = min(c1[1], c2[1])
            bottom = max(c1[1], c2[1])

            corners = [(left, top), (left, bottom), (right, top), (right, bottom)]
            corners.remove(c1)
            corners.remove(c2)
            random.shuffle(corners)
            target, other = corners
            for x in range(target[0], other[0], -1 if target[0] > other[0] else 1):
                was_walkable = grid.at((x, target[1])).walkable
                grid.at((x, target[1])).walkable=True
                grid.at((x, target[1])).transparent=True
                if not was_walkable:
                    grid.at((x, target[1])).tilesprite = random.choices([0, 12, 24], weights=[.6, .3, .1])[0]
            for y in range(target[1], other[1], -1 if target[1] > other[1] else 1):
                was_walkable = grid.at((target[0], y)).walkable
                grid.at((target[0], y)).walkable=True
                grid.at((target[0], y)).transparent=True
                if not was_walkable:
                    grid.at((target[0], y)).tilesprite = random.choices([0, 12, 24], weights=[0.4, 0.3, 0.3])[0]
            pairs.append((c1, c2))


    # spawn exit and button
    spawn_points = []
    for x in range(x_max):
        for y in range(y_max):
            if grid.at((x, y)).walkable:
                spawn_points.append((x, y))
    random.shuffle(spawn_points)
    door_spawn, button_spawn = spawn_points[:2]
    cos_entities.append(ExitEntity(*door_spawn, *button_spawn))

    # respawn player
    global player
    if player:
        player.position = (999,999) # TODO - die() is broken and I don't know why 
    player = PlayerEntity()


    #for x in range(x_max):
    #    for y in range(y_max):
    #        if grid.at((x, y)).walkable:
    #            #grid.at((x,y)).tilesprite = random.choice([48, 49, 50, 51, 52, 53])
    #            pass
    #        else:
    #            #grid.at((x,y)).tilesprite = random.choices([40, 28], weights=[.8, .2])[0]

#131 - last sprite
#123, 124 - brown, grey rats
#121 - ghost
#114, 115, 116 - green, red, blue potion
#102 - shield
#98 - low armor guy, #97 - high armor guy
#89 - chest, #91 - empty chest
#84 - wizard
#82 - barrel
#66 - boulder
#64, 65 - graves
#48 - 53: ground (not going to figure out how they fit together tonight)
#42 - button-looking ground
#40 - basic solid wall
#36, 37, 38 - wall (left, middle, right)
#28 solid wall but with a grate
#21 - wide open door, 33 medium open, 45 closed door
#0 - basic dirt
class MyEntity:
    def __init__(self, x=0, y=0, sprite_num=86):
        self.e = mcrfpy.Entity(x, y, t, sprite_num)
        grid.entities.append(self.e)
    def die(self):
        for i in range(len(grid.entities)):
            e = grid.entities[i]
            if e == self.e:
                grid.entities.remove(i)
                break
    def bump(self, other, dx, dy):
        raise NotImplementedError

    def try_move(self, dx, dy):
        tx, ty = int(self.e.position[0] + dx), int(self.e.position[1] + dy)
        for e in cos_entities:
            if e.e.position == (tx, ty):
                #print(f"bumping {e}")
                return e.bump(self, dx, dy)
        if tx < 0 or tx >= x_max:
            #print("out of bounds horizontally")
            return False
        if ty < 0 or ty >= y_max:
            #print("out of bounds vertically")
            return False
        if grid.at((tx, ty)).walkable == True:
            #print("Motion!")
            self.e.position = (tx, ty)
            return True
        else:
            #print("Bonk")
            return False

    def _relative_move(self, dx, dy):
        tx, ty = int(self.e.position[0] + dx), int(self.e.position[1] + dy)
        self.e.position = (tx, ty)


    def move(self, direction):
        if direction == "N":
            self.try_move(0, -1)
        elif direction == "E":
            self.try_move(1, 0)
        elif direction == "S":
            self.try_move(0, 1)
        elif direction == "W":
            self.try_move(-1, 0)

cos_entities = []

class PlayerEntity(MyEntity):
    def __init__(self):
        # find spawn point
        spawn_points = []
        for x in range(x_max):
            for y in range(y_max):
                if grid.at((x, y)).walkable:
                    spawn_points.append((x, y))
        random.shuffle(spawn_points)
        for spawn in spawn_points:
            for e in cos_entities:
                if e.e.position == spawn: break
            else:
                break

        #print(f"spawn at {spawn}")
        super().__init__(spawn[0], spawn[1], sprite_num=84)

class BoulderEntity(MyEntity):
    def __init__(self, x, y):
        super().__init__(x, y, 66)

    def bump(self, other, dx, dy):
        if type(other) == BoulderEntity:
            #print("Boulders can't push boulders")
            return False
        tx, ty = int(self.e.position[0] + dx), int(self.e.position[1] + dy)
        # Is the boulder blocked the same direction as the bumper? If not, let's both move
        old_pos = int(self.e.position[0]), int(self.e.position[1])
        if self.try_move(dx, dy):
            other.e.position = old_pos
            return True

class ButtonEntity(MyEntity):
    def __init__(self, x, y, exit):
        super().__init__(x, y, 42)
        self.exit = exit

    def bump(self, other, dx, dy):
        if type(other) == BoulderEntity:
            self.exit.unlock()
        other._relative_move(dx, dy)
        return True

class ExitEntity(MyEntity):
    def __init__(self, x, y, bx, by):
        super().__init__(x, y, 45)
        self.my_button = ButtonEntity(bx, by, self)
        self.unlocked = False
        global cos_entities
        cos_entities.append(self.my_button)

    def unlock(self):
        self.e.sprite_number = 21
        self.unlocked = True

    def lock(self):
        self.e.sprite_number = 45
        self.unlocked = True

    def bump(self, other, dx, dy):
        if type(other) == BoulderEntity:
            return False
        if self.unlocked:
            other._relative_move(dx, dy)

player = None
