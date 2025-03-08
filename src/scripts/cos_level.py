import random
import mcrfpy
import cos_tiles as ct

t = mcrfpy.Texture("assets/kenney_TD_MR_IP.png", 16, 16)

def binary_space_partition(x, y, w, h):
    d = random.choices(["vert", "horiz"], weights=[w/(w+h), h/(w+h)])[0]
    split = random.randint(30, 70) / 100.0
    if d == "vert":
        coord = int(w * split)
        return (x, y, coord, h), (x+coord, y, w-coord, h)
    else: # horizontal
        coord = int(h * split)
        return (x, y, w, coord), (x, y+coord, w, h-coord)

room_area = lambda x, y, w, h: w * h

class BinaryRoomNode:
    def __init__(self, xywh):
        self.data = xywh
        self.left = None
        self.right = None

    def __repr__(self):
        return f"<RoomNode {self.data}>"

    def center(self):
        x, y, w, h = self.data
        return (x + w // 2, y + h // 2)

    def split(self):
        new_data = binary_space_partition(*self.data)
        self.left = BinaryRoomNode(new_data[0])
        self.right = BinaryRoomNode(new_data[1])

    def walk(self):
        if self.left and self.right:
            return self.left.walk() + self.right.walk()
        return [self]

    def contains(self, pt):
        x, y, w, h = self.data
        tx, ty = pt
        return x <= tx <= x + w and y <= ty <= y + h

class RoomGraph:
    def __init__(self, xywh):
        self.root = BinaryRoomNode(xywh)

    def __repr__(self):
        return f"<RoomGraph, root={self.root}, {len(self.walk())} rooms>"

    def walk(self):
        w = self.root.walk() if self.root else []
        #print(w)
        return w

def room_coord(room, margin=0):
    x, y, w, h = room.data
    #print(x,y,w,h, f'{margin=}', end=';')
    w -= 1
    h -= 1
    margin += 1
    x += margin
    y += margin
    w -= margin
    h -= margin
    if w < 0: w = 0
    if h < 0: h = 0
    #print(x,y,w,h, end=' -> ')
    tx = x if w==0 else random.randint(x, x+w)
    ty = y if h==0 else random.randint(y, y+h)
    #print((tx, ty))
    return (tx, ty)

def adjacent_rooms(r, rooms):
    x, y, w, h = r.data
    adjacents = {}

    for i, other_r in enumerate(rooms):
        rx, ry, rw, rh = other_r.data
        if (rx, ry, rw, rh) == r:
            continue  # Skip self

        # Check vertical adjacency (above or below)
        if rx < x + w and x < rx + rw:  # Overlapping width
            if ry + rh == y:  # Above
                adjacents[i] = (x + w // 2, y - 1)
            elif y + h == ry:  # Below
                adjacents[i] = (x + w // 2, y + h + 1)

        # Check horizontal adjacency (left or right)
        if ry < y + h and y < ry + rh:  # Overlapping height
            if rx + rw == x:  # Left
                adjacents[i] = (x - 1, y + h // 2)
            elif x + w == rx:  # Right
                adjacents[i] = (x + w + 1, y + h // 2)

    return adjacents

class Level:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        #self.graph = [(0, 0, width, height)]
        self.graph = RoomGraph( (0, 0, width, height) )
        self.grid = mcrfpy.Grid(width, height, t, (10, 10), (1014, 758))
        self.highlighted = -1 #debug view feature
        self.walled_rooms = [] # for tracking "hallway rooms" vs "walled rooms"

    def fill(self, xywh, highlight = False):
        if highlight:
            ts = 0
        else:
            ts = room_area(*xywh) % 131
        X, Y, W, H = xywh
        for x in range(X, X+W):
            for y in range(Y, Y+H):
                self.grid.at((x, y)).tilesprite = ts

    def highlight(self, delta):
        rooms = self.graph.walk()
        if self.highlighted < len(rooms):
            #print(f"reset {self.highlighted}")
            self.fill(rooms[self.highlighted].data) # reset
        self.highlighted += delta
        print(f"highlight {self.highlighted}")
        self.highlighted = self.highlighted % len(rooms)
        self.fill(rooms[self.highlighted].data, highlight = True)

    def reset(self):
        self.graph = RoomGraph( (0, 0, self.width, self.height) )
        for x in range(self.width):
            for y in range(self.height):
                self.grid.at((x, y)).walkable = True
                self.grid.at((x, y)).transparent = True
                self.grid.at((x, y)).tilesprite = 0 #random.choice([40, 28])

    def split(self, single=False):
        if single:
            areas = {g.data: room_area(*g.data) for g in self.graph.walk()}
            largest = sorted(self.graph.walk(), key=lambda g: areas[g.data])[-1]
            largest.split()
        else:
            for room in self.graph.walk(): room.split()
        self.fill_rooms()

    def fill_rooms(self, features=None):
        rooms = self.graph.walk()
        #print(f"rooms: {len(rooms)}")
        for i, g in enumerate(rooms):
            X, Y, W, H = g.data
            #c = [random.randint(0, 255) for _ in range(3)]
            ts = room_area(*g.data) % 131 + i # modulo - consistent tile pick
            for x in range(X, X+W):
                for y in range(Y, Y+H):
                    self.grid.at((x, y)).tilesprite = ts

    def wall_rooms(self):
        self.walled_rooms = []
        rooms = self.graph.walk()
        for i, g in enumerate(rooms):
            # unwalled / hallways: not selected for small dungeons, first, last, and 65% of all other rooms
            if len(rooms) > 3 and i > 1 and i < len(rooms) - 2 and random.random() < 0.35:
                self.walled_rooms.append(False)
                continue
            self.walled_rooms.append(True)
            X, Y, W, H = g.data
            for x in range(X, X+W):
                self.grid.at((x, Y)).walkable = False
                #self.grid.at((x, Y+H-1)).walkable = False
            for y in range(Y, Y+H):
                self.grid.at((X, y)).walkable = False
                #self.grid.at((X+W-1, y)).walkable = False
        # boundary of entire level
        for x in range(0, self.width):
        #    self.grid.at((x, 0)).walkable = False
            self.grid.at((x, self.height-1)).walkable = False
        for y in range(0, self.height):
        #    self.grid.at((0, y)).walkable = False
            self.grid.at((self.width-1, y)).walkable = False

    def dig_path(self, start:"Tuple[int, int]", end:"Tuple[int, int]", walkable=True, color=None, sprite=None):
        print(f"Digging: {start} -> {end}")
        # get x1,y1 and x2,y2 coordinates: top left and bottom right points on the rect formed by two random points, one from each of the 2 rooms
        x1 = min([start[0], end[0]])
        x2 = max([start[0], end[0]])
        dw = x2 - x1
        y1 = min([start[1], end[1]])
        y2 = max([start[1], end[1]])
        dh = y2 - y1

        # random: top left or bottom right as the corner between the paths
        tx, ty = (x1, y1) if random.random() >= 0.5 else (x2, y2)

        for x in range(x1, x1+dw):
            try:
                if walkable:
                    self.grid.at((x, ty)).walkable = walkable
                if color:
                    self.grid.at((x, ty)).color = color
                if sprite is not None:
                    self.grid.at((x, ty)).tilesprite = sprite
            except:
                pass
        for y in range(y1, y1+dh):
            try:
                if walkable:
                    self.grid.at((tx, y)).walkable = True
                if color:
                    self.grid.at((tx, y)).color = color
                if sprite is not None:
                    self.grid.at((tx, y)).tilesprite = sprite
            except:
                pass

    def generate(self, level_plan): #target_rooms = 5, features=None):
        self.reset()
        target_rooms = len(level_plan)
        if type(level_plan) is set:
            level_plan = random.choice(list(level_plan))
        while len(self.graph.walk()) < target_rooms:
            self.split(single=len(self.graph.walk()) > target_rooms * .5)
            
        # Player path planning
        #self.fill_rooms()
        self.wall_rooms()
        rooms = self.graph.walk()
        feature_coords = []
        prev_room = None
        print(level_plan)
        for room_num, room in enumerate(rooms):
            room_plan = level_plan[room_num]
            if type(room_plan) == str: room_plan = [room_plan] # single item plans became single-character plans...
            for f in room_plan:
                #feature_coords.append((f, room_coord(room, margin=4 if f in ("boulder",) else 1)))
                # boulders are breaking my brain. If I can't get boulders away from walls with margin, I'm just going to dig them out.
                if f == "boulder":
                    x, y = room_coord(room, margin=0)
                    if x < 2: x += 1
                    if y < 2: y += 1
                    if x > self.grid.grid_size[0] - 2: x -= 1
                    if y > self.grid.grid_size[1] - 2: y -= 1
                    for _x in (1, 0, -1):
                        for _y in (1, 0, -1):
                            self.grid.at((x + _x, y + _y)).walkable = True
                    feature_coords.append((f, (x, y)))
                else:
                    feature_coords.append((f, room_coord(room, margin=0)))
                print(feature_coords[-1])

            ## Hallway generation
            # plow an inelegant path
            if prev_room:
                start = room_coord(prev_room, margin=2)
                end = room_coord(room, margin=2)
                self.dig_path(start, end, color=(0, 64, 0))
            prev_room = room

        # Tile painting
        possibilities = None
        while possibilities or possibilities is None:
            possibilities = ct.wfc_pass(self.grid, possibilities)

        ## "hallway room" repainting
        #for i, hall_room in enumerate(rooms):
        #    if self.walled_rooms[i]:
        #        print(f"walled room: {hall_room}")
        #        continue
        #    print(f"hall room: {hall_room}")
        #    x, y, w, h = hall_room.data
        #    for _x in range(x+1, x+w-1):
        #        for _y in range(y+1, y+h-1):
        #            self.grid.at((_x, _y)).walkable = False
        #            self.grid.at((_x, _y)).tilesprite = -1
        #            self.grid.at((_x, _y)).color = (0, 0, 0) # pit!
        #    targets = adjacent_rooms(hall_room, rooms)
        #    print(targets)
        #    for k, v in targets.items():
        #        self.dig_path(hall_room.center(), v, color=(64, 32, 32))
        #    for _, p in feature_coords:
        #        if hall_room.contains(p): self.dig_path(hall_room.center(), p, color=(92, 48, 48))

        return feature_coords
