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

    def place_feature(self, leaf, feature_coords):
        """Find a unique walkable coordinate in the given leaf for a feature."""
        used_coords = [c[1] for c in feature_coords]
        # Try random positions first
        for _ in range(100):
            fc = self.room_coord(leaf)
            if not self.grid.at(fc).walkable:
                continue
            if fc in used_coords:
                continue
            return fc
        # Fallback: leaf center
        fc = self.leaf_center(leaf)
        if fc not in used_coords:
            return fc
        # Last resort: scan all walkable cells in the room
        lx, ly = int(leaf.pos[0]), int(leaf.pos[1])
        lw, lh = int(leaf.size[0]), int(leaf.size[1])
        for cx in range(lx + 1, lx + lw - 1):
            for cy in range(ly + 1, ly + lh - 1):
                if (cx, cy) not in used_coords and \
                   0 <= cx < self.width and \
                   0 <= cy < self.height and \
                   self.grid.at((cx, cy)).walkable:
                    return (cx, cy)
        return None

    def generate_boulder_by_pull(self, button_pos, min_pulls=3, max_pulls=20,
                                  min_distance=3, obstacles=None):
        """Generate a boulder position by reverse-solving from the button.

        Places the boulder on the button, then simulates reverse pushes
        (un-pushes) to move it away. The resulting puzzle is guaranteed
        solvable by reversing the sequence.

        A forward push in direction d means: player at B-d pushes boulder
        from B to B+d. To reverse this, boulder goes from B+d back to B,
        requiring B to be walkable and B-d (player's push position) to be
        walkable.

        Args:
            button_pos: (x, y) of the button
            min_pulls: minimum successful un-pushes for interesting puzzle
            max_pulls: maximum un-pushes to attempt
            min_distance: minimum manhattan distance from button to boulder
            obstacles: set of positions that block boulder movement

        Returns:
            (x, y) boulder position, or None if puzzle too trivial
        """
        w, h = self.width, self.height
        if obstacles is None:
            obstacles = set()

        boulder = button_pos
        pull_count = 0
        visited = {boulder}

        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        for _ in range(max_pulls * 3):
            random.shuffle(directions)

            pulled = False
            for dx, dy in directions:
                # Reversing a push in direction (dx, dy):
                # Boulder goes from current pos to current - d
                # Player was at current - 2d (needed to push)
                new_boulder = (boulder[0] - dx, boulder[1] - dy)
                player_push_pos = (boulder[0] - 2*dx, boulder[1] - 2*dy)

                nbx, nby = new_boulder
                ppx, ppy = player_push_pos

                # Bounds check
                if not (0 <= nbx < w and 0 <= nby < h):
                    continue
                if not (0 <= ppx < w and 0 <= ppy < h):
                    continue
                # Walkability
                if not self.grid.at(new_boulder).walkable:
                    continue
                if not self.grid.at(player_push_pos).walkable:
                    continue
                # Obstacles block boulder landing
                if new_boulder in obstacles:
                    continue
                # Avoid loops
                if new_boulder in visited:
                    continue

                boulder = new_boulder
                visited.add(boulder)
                pull_count += 1
                pulled = True
                break

            if not pulled:
                break
            if pull_count >= max_pulls:
                break

        dist = abs(boulder[0] - button_pos[0]) + abs(boulder[1] - button_pos[1])
        if pull_count < min_pulls or dist < min_distance:
            return None

        return boulder

    def generate(self, level_plan, min_pulls=3):
        """Generate a level using BSP room placement and corridor digging.

        Boulder placement is handled automatically via reverse-pull from
        the button position, guaranteeing solvability by construction.
        Any "boulder" entries in the level_plan are ignored.

        Args:
            level_plan: list of tuples, each tuple is the features for one room.
                        Can also be a set of alternative plans.
            min_pulls: minimum reverse-pull steps for the puzzle

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

            # 6. Place non-boulder features from level_plan
            feature_coords = []
            for room_num in range(min(target_rooms, len(self.leaves))):
                leaf = self.leaves[room_num]
                room_plan = level_plan[room_num]
                if type(room_plan) == str:
                    room_plan = [room_plan]

                for f in room_plan:
                    if f == "boulder":
                        continue  # Boulder auto-placed via reverse-pull
                    fcoord = self.place_feature(leaf, feature_coords)
                    if fcoord is None:
                        print(f"WARNING: Could not place '{f}' in room {room_num}")
                        fcoord = self.leaf_center(leaf)
                    feature_coords.append((f, fcoord))

            # 7. Generate boulder via reverse-pull from button
            button_pos = None
            for f, pos in feature_coords:
                if f == "button":
                    button_pos = pos
                    break

            if button_pos:
                obstacles = {pos for _, pos in feature_coords}
                boulder_pos = self.generate_boulder_by_pull(
                    button_pos,
                    min_pulls=min_pulls,
                    max_pulls=max(min_pulls * 4, 20),
                    min_distance=min_pulls,
                    obstacles=obstacles
                )
                if boulder_pos is None:
                    print(f"Level attempt {attempt + 1}: puzzle too trivial, retrying...")
                    continue
                feature_coords.append(("boulder", boulder_pos))

            break

        # 8. Tile painting (WFC)
        possibilities = None
        while possibilities or possibilities is None:
            possibilities = ct.wfc_pass(self.grid, possibilities)

        return feature_coords
