"""Dungeon Generation Demo - BSP + Corridors

Demonstrates BSP dungeon generation with:
1. Create BSP and split recursively
2. Visualize all BSP partitions (educational)
3. Extract leaf nodes as rooms
4. Shrink leaves to create room margins
5. Build adjacency graph (which rooms neighbor)
6. Connect adjacent rooms with corridors
7. Composite rooms + corridors
"""

import mcrfpy
from typing import List, Dict, Tuple, Set
from ..core.demo_base import ProcgenDemoBase, StepDef, LayerDef
from ..core.parameter import Parameter


class DungeonDemo(ProcgenDemoBase):
    """Interactive BSP dungeon generation demo."""

    name = "Dungeon (BSP)"
    description = "Binary Space Partitioning with adjacency-based corridors"
    MAP_SIZE = (128, 96)  # Smaller for better visibility of rooms

    def define_steps(self) -> List[StepDef]:
        """Define the generation steps."""
        return [
            StepDef("Create BSP tree", self.step_create_bsp,
                   "Initialize BSP and split recursively"),
            StepDef("Show all partitions", self.step_show_partitions,
                   "Visualize the full BSP tree structure"),
            StepDef("Extract rooms", self.step_extract_rooms,
                   "Get leaf nodes as potential room spaces"),
            StepDef("Shrink rooms", self.step_shrink_rooms,
                   "Add margins between rooms"),
            StepDef("Build adjacency", self.step_build_adjacency,
                   "Find which rooms are neighbors"),
            StepDef("Dig corridors", self.step_dig_corridors,
                   "Connect adjacent rooms with corridors"),
            StepDef("Composite", self.step_composite,
                   "Combine rooms and corridors for final dungeon"),
        ]

    def define_parameters(self) -> List[Parameter]:
        """Define configurable parameters."""
        return [
            Parameter(
                name="seed",
                display="Seed",
                type="int",
                default=42,
                min_val=0,
                max_val=99999,
                step=1,
                affects_step=0,
                description="Random seed for BSP splits"
            ),
            Parameter(
                name="depth",
                display="BSP Depth",
                type="int",
                default=4,
                min_val=2,
                max_val=6,
                step=1,
                affects_step=0,
                description="BSP recursion depth"
            ),
            Parameter(
                name="min_room_w",
                display="Min Room W",
                type="int",
                default=8,
                min_val=4,
                max_val=16,
                step=2,
                affects_step=0,
                description="Minimum room width"
            ),
            Parameter(
                name="min_room_h",
                display="Min Room H",
                type="int",
                default=6,
                min_val=4,
                max_val=12,
                step=2,
                affects_step=0,
                description="Minimum room height"
            ),
            Parameter(
                name="shrink",
                display="Room Shrink",
                type="int",
                default=2,
                min_val=0,
                max_val=4,
                step=1,
                affects_step=3,
                description="Room inset from leaf bounds"
            ),
            Parameter(
                name="corridor_width",
                display="Corridor W",
                type="int",
                default=2,
                min_val=1,
                max_val=3,
                step=1,
                affects_step=5,
                description="Corridor thickness"
            ),
        ]

    def define_layers(self) -> List[LayerDef]:
        """Define visualization layers."""
        return [
            LayerDef("final", "Final Dungeon", "color", z_index=-1, visible=True,
                    description="Combined rooms and corridors"),
            LayerDef("bsp_tree", "BSP Tree", "color", z_index=0, visible=False,
                    description="All BSP partition boundaries"),
            LayerDef("rooms", "Rooms Only", "color", z_index=1, visible=False,
                    description="Room areas without corridors"),
            LayerDef("corridors", "Corridors", "color", z_index=2, visible=False,
                    description="Corridor paths only"),
            LayerDef("adjacency", "Adjacency", "color", z_index=3, visible=False,
                    description="Lines between adjacent room centers"),
        ]

    def __init__(self):
        """Initialize dungeon demo."""
        super().__init__()

        # BSP data
        self.bsp = None
        self.leaves = []
        self.rooms = []  # List of (x, y, w, h) tuples
        self.room_centers = []  # List of (cx, cy) tuples
        self.adjacencies = []  # List of (room_idx_1, room_idx_2) pairs

        # HeightMaps for visualization
        self.hmap_rooms = self.create_heightmap("rooms", 0.0)
        self.hmap_corridors = self.create_heightmap("corridors", 0.0)

    def _clear_layers(self):
        """Clear all visualization layers."""
        for layer in self.layers.values():
            layer.fill(mcrfpy.Color(30, 28, 26))

    def _draw_rect(self, layer, x, y, w, h, color, outline_only=False, alpha=None):
        """Draw a rectangle on a layer."""
        map_w, map_h = self.MAP_SIZE
        # Apply alpha if specified
        if alpha is not None:
            color = mcrfpy.Color(color.r, color.g, color.b, alpha)
        if outline_only:
            # Draw just the outline
            for px in range(x, x + w):
                if 0 <= px < map_w:
                    if 0 <= y < map_h:
                        layer.set((px, y), color)
                    if 0 <= y + h - 1 < map_h:
                        layer.set((px, y + h - 1), color)
            for py in range(y, y + h):
                if 0 <= py < map_h:
                    if 0 <= x < map_w:
                        layer.set((x, py), color)
                    if 0 <= x + w - 1 < map_w:
                        layer.set((x + w - 1, py), color)
        else:
            # Fill the rectangle
            for py in range(y, y + h):
                for px in range(x, x + w):
                    if 0 <= px < map_w and 0 <= py < map_h:
                        layer.set((px, py), color)

    def _draw_line(self, layer, x0, y0, x1, y1, color, width=1, alpha=None):
        """Draw a line on a layer using Bresenham's algorithm."""
        map_w, map_h = self.MAP_SIZE
        # Apply alpha if specified
        if alpha is not None:
            color = mcrfpy.Color(color.r, color.g, color.b, alpha)
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            # Draw width around center point
            for wo in range(-(width // 2), width // 2 + 1):
                for ho in range(-(width // 2), width // 2 + 1):
                    px, py = x0 + wo, y0 + ho
                    if 0 <= px < map_w and 0 <= py < map_h:
                        layer.set((px, py), color)

            if x0 == x1 and y0 == y1:
                break

            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    # === Step Implementations ===

    def step_create_bsp(self):
        """Step 1: Create and split BSP tree."""
        seed = self.get_param("seed")
        depth = self.get_param("depth")
        min_w = self.get_param("min_room_w")
        min_h = self.get_param("min_room_h")

        w, h = self.MAP_SIZE

        # Create BSP covering the map (with margin)
        margin = 2
        self.bsp = mcrfpy.BSP(
            pos=(margin, margin),
            size=(w - margin * 2, h - margin * 2)
        )

        # Split recursively
        self.bsp.split_recursive(
            depth=depth,
            min_size=(min_w, min_h),
            seed=seed
        )

        # Clear and show initial state
        self._clear_layers()
        final = self.get_layer("final")
        final.fill(mcrfpy.Color(30, 28, 26))

        # Draw BSP root bounds
        bsp_layer = self.get_layer("bsp_tree")
        bsp_layer.fill(mcrfpy.Color(30, 28, 26))
        x, y = self.bsp.pos
        w, h = self.bsp.size
        self._draw_rect(bsp_layer, x, y, w, h, mcrfpy.Color(80, 80, 100), outline_only=True)

    def step_show_partitions(self):
        """Step 2: Visualize all BSP partitions."""
        bsp_layer = self.get_layer("bsp_tree")
        bsp_layer.fill(mcrfpy.Color(30, 28, 26, 128))  # alpha=128 for overlay

        # Color palette for different depths (alpha=128 for overlay)
        depth_colors = [
            mcrfpy.Color(120, 60, 60, 128),
            mcrfpy.Color(60, 120, 60, 128),
            mcrfpy.Color(60, 60, 120, 128),
            mcrfpy.Color(120, 120, 60, 128),
            mcrfpy.Color(120, 60, 120, 128),
            mcrfpy.Color(60, 120, 120, 128),
        ]

        def draw_node(node, depth=0):
            """Recursively draw BSP nodes."""
            x, y = node.pos
            w, h = node.size
            color = depth_colors[depth % len(depth_colors)]

            # Draw outline
            self._draw_rect(bsp_layer, x, y, w, h, color, outline_only=True)

            # Draw children using left/right
            if node.left:
                draw_node(node.left, depth + 1)
            if node.right:
                draw_node(node.right, depth + 1)

        # Start from root
        root = self.bsp.root
        if root:
            draw_node(root)

        # Also show on final layer
        final = self.get_layer("final")
        # Copy bsp_tree to final
        w, h = self.MAP_SIZE
        for y in range(h):
            for x in range(w):
                c = bsp_layer.at(x, y)
                final.set((x, y), c)

    def step_extract_rooms(self):
        """Step 3: Extract leaf nodes as rooms."""
        # Get all leaves
        self.leaves = list(self.bsp.leaves())
        self.rooms = []
        self.room_centers = []

        rooms_layer = self.get_layer("rooms")
        rooms_layer.fill(mcrfpy.Color(30, 28, 26, 128))

        # Draw each leaf as a room (alpha=128 for overlay)
        room_colors = [
            mcrfpy.Color(100, 80, 60, 128),
            mcrfpy.Color(80, 100, 60, 128),
            mcrfpy.Color(60, 80, 100, 128),
            mcrfpy.Color(100, 100, 60, 128),
        ]

        for i, leaf in enumerate(self.leaves):
            x, y = leaf.pos
            w, h = leaf.size
            self.rooms.append((x, y, w, h))
            self.room_centers.append((x + w // 2, y + h // 2))

            color = room_colors[i % len(room_colors)]
            self._draw_rect(rooms_layer, x, y, w, h, color)

        # Also show on final
        final = self.get_layer("final")
        map_w, map_h = self.MAP_SIZE
        for y in range(map_h):
            for x in range(map_w):
                c = rooms_layer.at(x, y)
                final.set((x, y), c)

        print(f"Extracted {len(self.rooms)} rooms")

    def step_shrink_rooms(self):
        """Step 4: Shrink rooms to add margins."""
        shrink = self.get_param("shrink")

        rooms_layer = self.get_layer("rooms")
        rooms_layer.fill(mcrfpy.Color(30, 28, 26, 128))

        # Shrink each room
        shrunk_rooms = []
        shrunk_centers = []

        room_color = mcrfpy.Color(120, 100, 80, 128)  # alpha=128 for overlay

        for x, y, w, h in self.rooms:
            # Apply shrink
            nx = x + shrink
            ny = y + shrink
            nw = w - shrink * 2
            nh = h - shrink * 2

            # Ensure minimum size
            if nw >= 3 and nh >= 3:
                shrunk_rooms.append((nx, ny, nw, nh))
                shrunk_centers.append((nx + nw // 2, ny + nh // 2))
                self._draw_rect(rooms_layer, nx, ny, nw, nh, room_color)

                # Store in heightmap for later
                map_w, map_h = self.MAP_SIZE
                for py in range(ny, ny + nh):
                    for px in range(nx, nx + nw):
                        if 0 <= px < map_w and 0 <= py < map_h:
                            self.hmap_rooms[px, py] = 1.0

        self.rooms = shrunk_rooms
        self.room_centers = shrunk_centers

        # Update final
        final = self.get_layer("final")
        map_w, map_h = self.MAP_SIZE
        for y in range(map_h):
            for x in range(map_w):
                c = rooms_layer.at(x, y)
                final.set((x, y), c)

        print(f"Shrunk to {len(self.rooms)} valid rooms")

    def step_build_adjacency(self):
        """Step 5: Build adjacency graph between rooms."""
        self.adjacencies = []

        # Simple adjacency: rooms whose bounding boxes are close enough
        # In a real implementation, use BSP adjacency

        # For each pair of rooms, check if they share an edge
        for i in range(len(self.rooms)):
            for j in range(i + 1, len(self.rooms)):
                r1 = self.rooms[i]
                r2 = self.rooms[j]

                # Check if rooms are adjacent (share edge or close)
                if self._rooms_adjacent(r1, r2):
                    self.adjacencies.append((i, j))

        # Visualize adjacency lines (alpha=128 for overlay)
        adj_layer = self.get_layer("adjacency")
        adj_layer.fill(mcrfpy.Color(30, 28, 26, 128))

        line_color = mcrfpy.Color(200, 100, 100, 160)  # semi-transparent overlay
        for i, j in self.adjacencies:
            c1 = self.room_centers[i]
            c2 = self.room_centers[j]
            self._draw_line(adj_layer, c1[0], c1[1], c2[0], c2[1], line_color, width=1)

        # Show room centers as dots
        center_color = mcrfpy.Color(255, 200, 0, 200)  # more visible
        for cx, cy in self.room_centers:
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    px, py = cx + dx, cy + dy
                    map_w, map_h = self.MAP_SIZE
                    if 0 <= px < map_w and 0 <= py < map_h:
                        adj_layer.set((px, py), center_color)

        print(f"Found {len(self.adjacencies)} adjacencies")

    def _rooms_adjacent(self, r1, r2) -> bool:
        """Check if two rooms are adjacent."""
        x1, y1, w1, h1 = r1
        x2, y2, w2, h2 = r2

        # Horizontal adjacency (side by side)
        h_gap = max(x1, x2) - min(x1 + w1, x2 + w2)
        v_overlap = min(y1 + h1, y2 + h2) - max(y1, y2)

        if h_gap <= 4 and v_overlap > 2:
            return True

        # Vertical adjacency (stacked)
        v_gap = max(y1, y2) - min(y1 + h1, y2 + h2)
        h_overlap = min(x1 + w1, x2 + w2) - max(x1, x2)

        if v_gap <= 4 and h_overlap > 2:
            return True

        return False

    def step_dig_corridors(self):
        """Step 6: Connect adjacent rooms with corridors."""
        corridor_width = self.get_param("corridor_width")

        corridors_layer = self.get_layer("corridors")
        corridors_layer.fill(mcrfpy.Color(30, 28, 26, 128))  # alpha=128 for overlay

        corridor_color = mcrfpy.Color(90, 85, 75, 128)  # alpha=128 for overlay

        for i, j in self.adjacencies:
            c1 = self.room_centers[i]
            c2 = self.room_centers[j]

            # L-shaped corridor (horizontal then vertical)
            mid_x = c1[0]
            mid_y = c2[1]

            # Horizontal segment
            self._draw_line(corridors_layer, c1[0], c1[1], mid_x, mid_y,
                           corridor_color, width=corridor_width)
            # Vertical segment
            self._draw_line(corridors_layer, mid_x, mid_y, c2[0], c2[1],
                           corridor_color, width=corridor_width)

            # Store in heightmap
            map_w, map_h = self.MAP_SIZE
            # Mark corridor cells
            self._mark_line(c1[0], c1[1], mid_x, mid_y, corridor_width)
            self._mark_line(mid_x, mid_y, c2[0], c2[1], corridor_width)

        # Update final to show rooms + corridors
        final = self.get_layer("final")
        rooms_layer = self.get_layer("rooms")
        map_w, map_h = self.MAP_SIZE
        for y in range(map_h):
            for x in range(map_w):
                room_c = rooms_layer.at(x, y)
                corr_c = corridors_layer.at(x, y)
                # Prioritize rooms, then corridors, then background
                if room_c.r > 50 or room_c.g > 50 or room_c.b > 50:
                    final.set((x, y), room_c)
                elif corr_c.r > 50 or corr_c.g > 50 or corr_c.b > 50:
                    final.set((x, y), corr_c)
                else:
                    final.set((x, y), mcrfpy.Color(30, 28, 26))

    def _mark_line(self, x0, y0, x1, y1, width):
        """Mark corridor cells in heightmap."""
        map_w, map_h = self.MAP_SIZE
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            for wo in range(-(width // 2), width // 2 + 1):
                for ho in range(-(width // 2), width // 2 + 1):
                    px, py = x0 + wo, y0 + ho
                    if 0 <= px < map_w and 0 <= py < map_h:
                        self.hmap_corridors[px, py] = 1.0

            if x0 == x1 and y0 == y1:
                break

            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def step_composite(self):
        """Step 7: Create final composite dungeon."""
        final = self.get_layer("final")
        map_w, map_h = self.MAP_SIZE

        wall_color = mcrfpy.Color(40, 38, 35)
        floor_color = mcrfpy.Color(140, 130, 115)

        for y in range(map_h):
            for x in range(map_w):
                is_room = self.hmap_rooms[x, y] > 0.5
                is_corridor = self.hmap_corridors[x, y] > 0.5

                if is_room or is_corridor:
                    final.set((x, y), floor_color)
                else:
                    final.set((x, y), wall_color)


def main():
    """Run the dungeon demo standalone."""
    demo = DungeonDemo()
    demo.activate()


if __name__ == "__main__":
    main()
