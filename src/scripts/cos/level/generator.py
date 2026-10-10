"""Level generation using the engine's mcrfpy.BSP.

Replaces the 7DRL's hand-rolled BinaryRoomNode/RoomGraph (~200 lines)
with the engine's built-in BSP that provides split_recursive(),
adjacency graphs, and wall-tile queries.
"""

import random
import mcrfpy
from cos import Resources
from cos.constants import GRID_POS, GRID_SIZE


class Level:
    """A generated dungeon level.

    Uses mcrfpy.BSP for room partitioning and the engine's adjacency
    graph for hallway connectivity. Each level owns its Grid.

    Attributes:
        width, height: grid dimensions in tiles
        grid: the mcrfpy.Grid for this level
        bsp: the mcrfpy.BSP used for room generation
        rooms: list of BSPNode leaves after generation
    """

    def __init__(self, width, height):
        self.width = width
        self.height = height
        res = Resources()
        self.grid = mcrfpy.Grid(
            grid_size=(width, height), texture=res.tileset,
            pos=GRID_POS, size=GRID_SIZE,
        )
        self.bsp = None
        self.rooms = []

    def reset(self):
        """Clear the grid to all-walkable, all-transparent."""
        for x in range(self.width):
            for y in range(self.height):
                cell = self.grid.at((x, y))
                cell.walkable = True
                cell.transparent = True
                cell.tilesprite = 0

    def generate(self, level_plan):
        """Generate a complete level from a plan.

        Args:
            level_plan: list of room content tuples, or a set of
                alternative arrangements (one chosen at random).
                Example: [("spawn", "button", "boulder"), ("exit",)]

        Returns:
            list of (feature_name, (x, y)) placement coordinates.
        """
        self.reset()

        # Handle random choice from alternative arrangements
        if isinstance(level_plan, set):
            level_plan = random.choice(list(level_plan))

        target_rooms = len(level_plan)

        # -- BSP room partitioning ----------------------------------------
        # Engine BSP replaces the manual BinaryRoomNode.split() loop.
        # We leave a 1-tile border around the entire level.
        self.bsp = mcrfpy.BSP(pos=(0, 0), size=(self.width, self.height))

        # Split until we have enough rooms.
        # min_size prevents rooms too small for features.
        # max_ratio prevents long narrow corridors.
        depth = self._depth_for_rooms(target_rooms)
        self.bsp.split_recursive(depth=depth, min_size=(4, 4), max_ratio=1.8)

        self.rooms = list(self.bsp)
        # If we got more rooms than needed, trim to target count.
        # BSP splitting is exponential, so we may overshoot.
        while len(self.rooms) > target_rooms and len(self.rooms) > 1:
            # Remove the smallest room
            self.rooms.sort(key=lambda r: r.size[0] * r.size[1])
            self.rooms.pop(0)

        # -- Wall the rooms -----------------------------------------------
        self._wall_rooms()

        # -- Dig hallways between adjacent rooms --------------------------
        self._dig_hallways()

        # -- Place features in rooms --------------------------------------
        feature_coords = self._place_features(level_plan)

        # -- Tile painting ------------------------------------------------
        # TODO: Replace with Wang tiles when tileset is designed in Tiled.
        # For now, use the ported WFC tile rules.
        from cos.level.tiles import paint_tiles
        paint_tiles(self.grid)

        return feature_coords

    def _depth_for_rooms(self, target):
        """Estimate BSP depth needed for target room count.

        BSP splitting creates ~2^depth leaves. We want at least
        target_rooms leaves but not too many more.
        """
        depth = 1
        while (2 ** depth) < target:
            depth += 1
        return depth

    def _wall_rooms(self):
        """Set wall tiles (non-walkable) on room borders and level edges."""
        for room in self.rooms:
            rx, ry = int(room.pos[0]), int(room.pos[1])
            rw, rh = int(room.size[0]), int(room.size[1])

            # Top and bottom walls
            for x in range(rx, rx + rw):
                if 0 <= x < self.width and 0 <= ry < self.height:
                    self.grid.at((x, ry)).walkable = False
                    self.grid.at((x, ry)).transparent = False

            # Left wall
            for y in range(ry, ry + rh):
                if 0 <= rx < self.width and 0 <= y < self.height:
                    self.grid.at((rx, y)).walkable = False
                    self.grid.at((rx, y)).transparent = False

        # Level boundary
        for x in range(self.width):
            self.grid.at((x, self.height - 1)).walkable = False
            self.grid.at((x, self.height - 1)).transparent = False
        for y in range(self.height):
            self.grid.at((self.width - 1, y)).walkable = False
            self.grid.at((self.width - 1, y)).transparent = False

    def _dig_hallways(self):
        """Connect adjacent rooms with L-shaped hallways.

        Uses the BSP adjacency graph instead of the 7DRL's sequential
        room connection (which could leave disconnected rooms).
        """
        adjacency = self.bsp.adjacency
        connected = set()

        for i, room in enumerate(self.rooms):
            if i >= len(adjacency):
                break
            neighbors = adjacency[i]
            for neighbor_idx in range(len(neighbors)):
                # The adjacency tuple contains neighbor leaf indices
                j = neighbors[neighbor_idx]
                pair = (min(i, j), max(i, j))
                if pair in connected:
                    continue
                connected.add(pair)

                if j < len(self.rooms):
                    start = self._room_interior_point(self.rooms[i])
                    end = self._room_interior_point(self.rooms[j])
                    self._dig_path(start, end)

    def _room_interior_point(self, room, margin=1):
        """Pick a random walkable point inside a room, avoiding walls."""
        rx, ry = int(room.pos[0]), int(room.pos[1])
        rw, rh = int(room.size[0]), int(room.size[1])

        # Shrink by margin to avoid walls
        x0 = rx + margin + 1
        y0 = ry + margin + 1
        x1 = rx + rw - margin - 1
        y1 = ry + rh - margin - 1

        x0 = max(x0, 1)
        y0 = max(y0, 1)
        x1 = min(x1, self.width - 2)
        y1 = min(y1, self.height - 2)

        if x0 > x1:
            x0 = x1 = (rx + rw // 2)
        if y0 > y1:
            y0 = y1 = (ry + rh // 2)

        return (random.randint(x0, x1), random.randint(y0, y1))

    def _dig_path(self, start, end):
        """Dig an L-shaped path between two points."""
        x1, y1 = min(start[0], end[0]), min(start[1], end[1])
        x2, y2 = max(start[0], end[0]), max(start[1], end[1])

        # Pick a random corner for the L-bend
        corner_x, corner_y = (
            (x1, y1) if random.random() >= 0.5 else (x2, y2)
        )

        # Horizontal segment
        for x in range(x1, x2 + 1):
            if 0 <= x < self.width and 0 <= corner_y < self.height:
                cell = self.grid.at((x, corner_y))
                cell.walkable = True
                cell.transparent = True

        # Vertical segment
        for y in range(y1, y2 + 1):
            if 0 <= corner_x < self.width and 0 <= y < self.height:
                cell = self.grid.at((corner_x, y))
                cell.walkable = True
                cell.transparent = True

    def _place_features(self, level_plan):
        """Place entity spawn points in rooms according to the plan.

        Returns a list of (feature_name, (x, y)) tuples.
        """
        feature_coords = []
        used_positions = set()

        for room_idx, room_plan in enumerate(level_plan):
            if room_idx >= len(self.rooms):
                break
            room = self.rooms[room_idx]

            # Normalize single-string plans to tuples
            if isinstance(room_plan, str):
                room_plan = (room_plan,)

            for feature in room_plan:
                pos = self._find_walkable_position(room, used_positions)
                if pos is not None:
                    feature_coords.append((feature, pos))
                    used_positions.add(pos)

        return feature_coords

    def _find_walkable_position(self, room, used, max_attempts=50):
        """Find a random walkable, unoccupied position inside a room."""
        for _ in range(max_attempts):
            pos = self._room_interior_point(room, margin=0)
            if pos in used:
                continue
            if not self.grid.at(pos).walkable:
                continue
            return pos
        return None
