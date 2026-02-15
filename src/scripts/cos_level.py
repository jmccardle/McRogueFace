import random
import mcrfpy
import cos_tiles as ct

t = mcrfpy.Texture("assets/kenney_TD_MR_IP.png", 16, 16)


class Level:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = mcrfpy.Grid(grid_size=(width, height), texture=t,
                                pos=(10, 5), size=(1014, 700))
        self.bsp = None
        self.leaves = []
        self.room_map = [[None] * height for _ in range(width)]

    def reset(self):
        """Initialize all cells as walls (unwalkable, opaque)."""
        for x in range(self.width):
            for y in range(self.height):
                self.grid.at((x, y)).walkable = False
                self.grid.at((x, y)).transparent = False
                self.grid.at((x, y)).tilesprite = 0
        self.room_map = [[None] * self.height for _ in range(self.width)]

    def leaf_center(self, leaf):
        """Get center coordinates of a BSP leaf."""
        x, y = int(leaf.pos[0]), int(leaf.pos[1])
        w, h = int(leaf.size[0]), int(leaf.size[1])
        return (x + w // 2, y + h // 2)

    def room_coord(self, leaf, margin=0):
        """Get a random walkable coordinate inside a leaf's carved room area."""
        x, y = int(leaf.pos[0]), int(leaf.pos[1])
        w, h = int(leaf.size[0]), int(leaf.size[1])
        # Room interior starts at (x+1, y+1) due to wall carving margin
        inner_x = x + 1 + margin
        inner_y = y + 1 + margin
        inner_max_x = x + w - 2 - margin
        inner_max_y = y + h - 2 - margin
        if inner_max_x <= inner_x:
            inner_x = inner_max_x = x + w // 2
        if inner_max_y <= inner_y:
            inner_y = inner_max_y = y + h // 2
        return (random.randint(inner_x, inner_max_x),
                random.randint(inner_y, inner_max_y))

    def dig_path(self, start, end):
        """Dig an L-shaped corridor between two points."""
        x1, x2 = min(start[0], end[0]), max(start[0], end[0])
        y1, y2 = min(start[1], end[1]), max(start[1], end[1])

        # Random L-shape corner
        tx, ty = (x1, y1) if random.random() >= 0.5 else (x2, y2)

        for x in range(x1, x2 + 1):
            if 0 <= x < self.width and 0 <= ty < self.height:
                self.grid.at((x, ty)).walkable = True
                self.grid.at((x, ty)).transparent = True
        for y in range(y1, y2 + 1):
            if 0 <= tx < self.width and 0 <= y < self.height:
                self.grid.at((tx, y)).walkable = True
                self.grid.at((tx, y)).transparent = True

    def generate(self, level_plan):
        """Generate a level using BSP room placement and corridor digging.

        Args:
            level_plan: list of tuples, each tuple is the features for one room.
                        Can also be a set of alternative plans.

        Returns:
            List of (feature_name, (x, y)) tuples for entity placement.
        """
        if type(level_plan) is set:
            level_plan = list(random.choice(list(level_plan)))
        target_rooms = len(level_plan)

        for attempt in range(10):
            self.reset()

            # 1. Create and split BSP
            self.bsp = mcrfpy.BSP(pos=(1, 1),
                                  size=(self.width - 2, self.height - 2))
            depth = max(2, target_rooms.bit_length() + 1)
            self.bsp.split_recursive(
                depth=depth,
                min_size=(4, 4),
                max_ratio=1.5
            )

            # 2. Get leaves - retry if not enough
            self.leaves = list(self.bsp.leaves())
            if len(self.leaves) < target_rooms:
                continue

            # 3. Carve rooms (1-cell wall margin from leaf edges)
            for leaf in self.leaves:
                lx, ly = int(leaf.pos[0]), int(leaf.pos[1])
                lw, lh = int(leaf.size[0]), int(leaf.size[1])
                for cx in range(lx + 1, lx + lw - 1):
                    for cy in range(ly + 1, ly + lh - 1):
                        if 0 <= cx < self.width and 0 <= cy < self.height:
                            self.grid.at((cx, cy)).walkable = True
                            self.grid.at((cx, cy)).transparent = True

            # 4. Build room map (cell -> leaf index)
            for i, leaf in enumerate(self.leaves):
                lx, ly = int(leaf.pos[0]), int(leaf.pos[1])
                lw, lh = int(leaf.size[0]), int(leaf.size[1])
                for cx in range(lx, lx + lw):
                    for cy in range(ly, ly + lh):
                        if 0 <= cx < self.width and 0 <= cy < self.height:
                            self.room_map[cx][cy] = i

            # 5. Carve corridors using BSP adjacency
            adj = self.bsp.adjacency
            connected = set()
            for i in range(len(adj)):
                for j in adj[i]:
                    edge = (min(i, j), max(i, j))
                    if edge in connected:
                        continue
                    connected.add(edge)
                    ci = self.leaf_center(self.leaves[i])
                    cj = self.leaf_center(self.leaves[j])
                    self.dig_path(ci, cj)

            # 6. Place features using level_plan
            feature_coords = []
            for room_num in range(min(target_rooms, len(self.leaves))):
                leaf = self.leaves[room_num]
                room_plan = level_plan[room_num]
                if type(room_plan) == str:
                    room_plan = [room_plan]

                for f in room_plan:
                    fcoord = None
                    used_coords = [c[1] for c in feature_coords]
                    for _ in range(100):
                        fc = self.room_coord(leaf)
                        if not self.grid.at(fc).walkable:
                            continue
                        if fc in used_coords:
                            continue
                        fcoord = fc
                        break
                    if fcoord is None:
                        # Fallback: leaf center, but only if not already used
                        fc = self.leaf_center(leaf)
                        if fc not in used_coords:
                            fcoord = fc
                        else:
                            # Last resort: scan all walkable cells in the room
                            lx, ly = int(leaf.pos[0]), int(leaf.pos[1])
                            lw, lh = int(leaf.size[0]), int(leaf.size[1])
                            for cx in range(lx + 1, lx + lw - 1):
                                for cy in range(ly + 1, ly + lh - 1):
                                    if (cx, cy) not in used_coords and \
                                       0 <= cx < self.width and \
                                       0 <= cy < self.height and \
                                       self.grid.at((cx, cy)).walkable:
                                        fcoord = (cx, cy)
                                        break
                                if fcoord is not None:
                                    break
                    if fcoord is None:
                        print(f"WARNING: Could not place '{f}' in room {room_num} - no free cells!")
                        fcoord = self.leaf_center(leaf)  # absolute last resort
                    feature_coords.append((f, fcoord))

            # 7. Solvability check
            spawn_pos = None
            boulder_positions = []
            button_positions = []
            exit_pos = None
            obstacle_positions = []
            for f, pos in feature_coords:
                if f == "spawn":
                    spawn_pos = pos
                elif f == "boulder":
                    boulder_positions.append(pos)
                elif f == "button":
                    button_positions.append(pos)
                elif f == "exit":
                    exit_pos = pos
                elif f == "treasure":
                    obstacle_positions.append(pos)

            if spawn_pos and boulder_positions and button_positions and exit_pos:
                # Check that no obstacle sits on a button
                buttons_blocked = any(
                    bp in obstacle_positions for bp in button_positions
                )
                if buttons_blocked:
                    print(f"Level attempt {attempt + 1}: button blocked by obstacle, retrying...")
                    continue

                from cos_solver import is_solvable
                if is_solvable(self.grid, spawn_pos, boulder_positions,
                               button_positions, exit_pos,
                               obstacles=obstacle_positions):
                    break
                print(f"Level attempt {attempt + 1}: unsolvable, retrying...")
            else:
                break  # No puzzle elements to verify

        # 8. Tile painting (WFC)
        possibilities = None
        while possibilities or possibilities is None:
            possibilities = ct.wfc_pass(self.grid, possibilities)

        return feature_coords
