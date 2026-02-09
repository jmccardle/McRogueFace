"""Town Generation Demo - Voronoi Districts + Bezier Roads

Demonstrates town generation with:
1. Generate base terrain elevation
2. Add Voronoi districts using HeightMap.add_voronoi()
3. Find district centers
4. Connect centers with roads using HeightMap.dig_bezier()
5. Place building footprints in districts
6. Composite: terrain + roads + buildings
"""

import mcrfpy
import random
from typing import List, Tuple
from ..core.demo_base import ProcgenDemoBase, StepDef, LayerDef
from ..core.parameter import Parameter


class TownDemo(ProcgenDemoBase):
    """Interactive Voronoi town generation demo."""

    name = "Town"
    description = "Voronoi districts with Bezier roads and building placement"
    MAP_SIZE = (128, 96)  # Smaller for clearer visualization

    def define_steps(self) -> List[StepDef]:
        """Define the generation steps."""
        return [
            StepDef("Generate terrain", self.step_terrain,
                   "Create base terrain elevation"),
            StepDef("Create districts", self.step_districts,
                   "Add Voronoi districts for zoning"),
            StepDef("Find centers", self.step_find_centers,
                   "Locate district center points"),
            StepDef("Build roads", self.step_roads,
                   "Connect districts with Bezier roads"),
            StepDef("Place buildings", self.step_buildings,
                   "Add building footprints in districts"),
            StepDef("Composite", self.step_composite,
                   "Combine all layers for final town"),
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
                description="Random seed for all generation"
            ),
            Parameter(
                name="num_districts",
                display="Districts",
                type="int",
                default=12,
                min_val=5,
                max_val=25,
                step=1,
                affects_step=1,
                description="Number of Voronoi districts"
            ),
            Parameter(
                name="road_width",
                display="Road Width",
                type="float",
                default=2.0,
                min_val=1.0,
                max_val=4.0,
                step=0.5,
                affects_step=3,
                description="Bezier road thickness"
            ),
            Parameter(
                name="building_density",
                display="Building %",
                type="float",
                default=0.40,
                min_val=0.20,
                max_val=0.70,
                step=0.05,
                affects_step=4,
                description="Building coverage density"
            ),
            Parameter(
                name="building_min",
                display="Min Building",
                type="int",
                default=3,
                min_val=2,
                max_val=5,
                step=1,
                affects_step=4,
                description="Minimum building size"
            ),
            Parameter(
                name="building_max",
                display="Max Building",
                type="int",
                default=6,
                min_val=4,
                max_val=10,
                step=1,
                affects_step=4,
                description="Maximum building size"
            ),
        ]

    def define_layers(self) -> List[LayerDef]:
        """Define visualization layers."""
        return [
            LayerDef("final", "Final Town", "color", z_index=-1, visible=True,
                    description="Complete town composite"),
            LayerDef("districts", "Districts", "color", z_index=0, visible=False,
                    description="Voronoi district regions"),
            LayerDef("roads", "Roads", "color", z_index=1, visible=False,
                    description="Road network"),
            LayerDef("buildings", "Buildings", "color", z_index=2, visible=False,
                    description="Building footprints"),
            LayerDef("control_pts", "Control Points", "color", z_index=3, visible=False,
                    description="Bezier control points (educational)"),
        ]

    def __init__(self):
        """Initialize town demo."""
        super().__init__()

        # Working heightmaps
        self.hmap_terrain = self.create_heightmap("terrain", 0.0)
        self.hmap_districts = self.create_heightmap("districts", 0.0)
        self.hmap_roads = self.create_heightmap("roads", 0.0)
        self.hmap_buildings = self.create_heightmap("buildings", 0.0)

        # District data
        self.district_points = []  # Voronoi seed points
        self.district_centers = []  # Calculated centroids
        self.connections = []  # List of (idx1, idx2) for roads

        # Random state
        self.rng = None

    def _init_random(self):
        """Initialize random generator with seed."""
        seed = self.get_param("seed")
        self.rng = random.Random(seed)

    def _get_district_color(self, district_id: int) -> Tuple[int, int, int]:
        """Get a color for a district ID."""
        colors = [
            (180, 160, 120),  # Tan
            (160, 180, 130),  # Sage
            (170, 150, 140),  # Mauve
            (150, 170, 160),  # Seafoam
            (175, 165, 125),  # Sand
            (165, 175, 135),  # Moss
            (155, 155, 155),  # Gray
            (180, 150, 130),  # Terracotta
            (140, 170, 170),  # Teal
            (170, 160, 150),  # Warm gray
        ]
        return colors[district_id % len(colors)]

    # === Step Implementations ===

    def step_terrain(self):
        """Step 1: Generate base terrain."""
        self._init_random()
        seed = self.get_param("seed")

        # Create subtle terrain noise
        noise = mcrfpy.NoiseSource(
            dimensions=2,
            algorithm='simplex',
            seed=seed
        )

        self.hmap_terrain.fill(0.0)
        self.hmap_terrain.add_noise(
            noise,
            world_size=(15, 15),
            mode='fbm',
            octaves=4
        )
        self.hmap_terrain.normalize(0.3, 0.7)  # Keep in mid range

        # Visualize as subtle green-brown gradient
        final = self.get_layer("final")
        w, h = self.MAP_SIZE
        for y in range(h):
            for x in range(w):
                val = self.hmap_terrain[x, y]
                # Grass color range
                r = int(80 + val * 40)
                g = int(120 + val * 30)
                b = int(60 + val * 20)
                final.set((x, y), mcrfpy.Color(r, g, b))

    def step_districts(self):
        """Step 2: Create Voronoi districts."""
        num_districts = self.get_param("num_districts")
        w, h = self.MAP_SIZE

        # Generate random points for Voronoi seeds
        margin = 10
        self.district_points = []
        for i in range(num_districts):
            x = self.rng.randint(margin, w - margin)
            y = self.rng.randint(margin, h - margin)
            self.district_points.append((x, y))

        # Use add_voronoi to create district values
        # Each cell gets the ID of its nearest point
        self.hmap_districts.fill(0.0)

        for y in range(h):
            for x in range(w):
                min_dist = float('inf')
                nearest_id = 0
                for i, (px, py) in enumerate(self.district_points):
                    dist = (x - px) ** 2 + (y - py) ** 2
                    if dist < min_dist:
                        min_dist = dist
                        nearest_id = i + 1  # 1-indexed to distinguish from 0
                self.hmap_districts[x, y] = nearest_id

        # Visualize districts (alpha=128 for overlay)
        districts_layer = self.get_layer("districts")
        for y in range(h):
            for x in range(w):
                district_id = int(self.hmap_districts[x, y])
                if district_id > 0:
                    color = self._get_district_color(district_id - 1)
                    districts_layer.set((x, y), mcrfpy.Color(color[0], color[1], color[2], 128))
                else:
                    districts_layer.set((x, y), mcrfpy.Color(50, 50, 50, 128))

        # Also show on final
        final = self.get_layer("final")
        for y in range(h):
            for x in range(w):
                c = districts_layer.at(x, y)
                final.set((x, y), c)

    def step_find_centers(self):
        """Step 3: Find district center points."""
        num_districts = self.get_param("num_districts")
        w, h = self.MAP_SIZE

        # Calculate centroid of each district
        self.district_centers = []

        for did in range(1, num_districts + 1):
            sum_x, sum_y, count = 0, 0, 0
            for y in range(h):
                for x in range(w):
                    if int(self.hmap_districts[x, y]) == did:
                        sum_x += x
                        sum_y += y
                        count += 1

            if count > 0:
                cx = sum_x // count
                cy = sum_y // count
                self.district_centers.append((cx, cy))
            else:
                # Use the original point if district is empty
                if did - 1 < len(self.district_points):
                    self.district_centers.append(self.district_points[did - 1])

        # Build connections (minimum spanning tree-like)
        self.connections = []
        if len(self.district_centers) > 1:
            # Simple approach: connect each district to its nearest neighbor
            # that hasn't been connected yet (Prim's-like)
            connected = {0}  # Start with first district
            while len(connected) < len(self.district_centers):
                best_dist = float('inf')
                best_pair = None

                for i in connected:
                    for j in range(len(self.district_centers)):
                        if j in connected:
                            continue
                        ci = self.district_centers[i]
                        cj = self.district_centers[j]
                        dist = (ci[0] - cj[0]) ** 2 + (ci[1] - cj[1]) ** 2
                        if dist < best_dist:
                            best_dist = dist
                            best_pair = (i, j)

                if best_pair:
                    self.connections.append(best_pair)
                    connected.add(best_pair[1])

            # Add a few extra connections for redundancy
            for _ in range(min(3, len(self.district_centers) // 4)):
                i = self.rng.randint(0, len(self.district_centers) - 1)
                j = self.rng.randint(0, len(self.district_centers) - 1)
                if i != j and (i, j) not in self.connections and (j, i) not in self.connections:
                    self.connections.append((i, j))

        # Visualize centers and connections (alpha=128 for overlay)
        control_layer = self.get_layer("control_pts")
        control_layer.fill(mcrfpy.Color(30, 28, 26, 128))

        # Draw center points
        for cx, cy in self.district_centers:
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    px, py = cx + dx, cy + dy
                    if 0 <= px < w and 0 <= py < h:
                        control_layer.set((px, py), mcrfpy.Color(255, 200, 0, 200))

        # Draw connection lines
        for i, j in self.connections:
            c1 = self.district_centers[i]
            c2 = self.district_centers[j]
            self._draw_line(control_layer, c1[0], c1[1], c2[0], c2[1],
                           mcrfpy.Color(200, 100, 100, 160), 1)

    def _draw_line(self, layer, x0, y0, x1, y1, color, width):
        """Draw a line on a layer."""
        w, h = self.MAP_SIZE
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            for wo in range(-(width // 2), width // 2 + 1):
                for ho in range(-(width // 2), width // 2 + 1):
                    px, py = x0 + wo, y0 + ho
                    if 0 <= px < w and 0 <= py < h:
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

    def step_roads(self):
        """Step 4: Build roads between districts."""
        road_width = self.get_param("road_width")
        w, h = self.MAP_SIZE

        self.hmap_roads.fill(0.0)
        roads_layer = self.get_layer("roads")
        roads_layer.fill(mcrfpy.Color(30, 28, 26, 128))  # alpha=128 for overlay

        road_color = mcrfpy.Color(80, 75, 65, 160)  # alpha=160 for better visibility

        for i, j in self.connections:
            c1 = self.district_centers[i]
            c2 = self.district_centers[j]

            # Create bezier-like curve by adding a control point
            mid_x = (c1[0] + c2[0]) // 2
            mid_y = (c1[1] + c2[1]) // 2

            # Offset the midpoint slightly for curve
            offset_x = (c2[1] - c1[1]) // 8  # Perpendicular offset
            offset_y = -(c2[0] - c1[0]) // 8
            ctrl_x = mid_x + offset_x
            ctrl_y = mid_y + offset_y

            # Draw quadratic bezier approximation
            self._draw_bezier(roads_layer, c1, (ctrl_x, ctrl_y), c2,
                             road_color, int(road_width))

            # Also mark in heightmap
            self._mark_bezier(c1, (ctrl_x, ctrl_y), c2, int(road_width))

        # Update final with roads
        final = self.get_layer("final")
        districts_layer = self.get_layer("districts")
        for y in range(h):
            for x in range(w):
                if self.hmap_roads[x, y] > 0.5:
                    final.set((x, y), road_color)
                else:
                    c = districts_layer.at(x, y)
                    final.set((x, y), c)

    def _draw_bezier(self, layer, p0, p1, p2, color, width):
        """Draw a quadratic bezier curve."""
        w, h = self.MAP_SIZE
        # Approximate with line segments
        steps = 20
        prev = None
        for t in range(steps + 1):
            t = t / steps
            # Quadratic bezier formula
            x = int((1-t)**2 * p0[0] + 2*(1-t)*t * p1[0] + t**2 * p2[0])
            y = int((1-t)**2 * p0[1] + 2*(1-t)*t * p1[1] + t**2 * p2[1])

            if prev:
                self._draw_line(layer, prev[0], prev[1], x, y, color, width)
            prev = (x, y)

    def _mark_bezier(self, p0, p1, p2, width):
        """Mark bezier curve in roads heightmap."""
        w, h = self.MAP_SIZE
        steps = 20
        for t in range(steps + 1):
            t = t / steps
            x = int((1-t)**2 * p0[0] + 2*(1-t)*t * p1[0] + t**2 * p2[0])
            y = int((1-t)**2 * p0[1] + 2*(1-t)*t * p1[1] + t**2 * p2[1])

            for wo in range(-(width // 2), width // 2 + 1):
                for ho in range(-(width // 2), width // 2 + 1):
                    px, py = x + wo, y + ho
                    if 0 <= px < w and 0 <= py < h:
                        self.hmap_roads[px, py] = 1.0

    def step_buildings(self):
        """Step 5: Place building footprints."""
        density = self.get_param("building_density")
        min_size = self.get_param("building_min")
        max_size = self.get_param("building_max")
        w, h = self.MAP_SIZE

        self.hmap_buildings.fill(0.0)
        buildings_layer = self.get_layer("buildings")
        buildings_layer.fill(mcrfpy.Color(30, 28, 26, 128))  # alpha=128 for overlay

        # Building colors (alpha=160 for better visibility)
        building_colors = [
            mcrfpy.Color(140, 120, 100, 160),
            mcrfpy.Color(130, 130, 120, 160),
            mcrfpy.Color(150, 130, 110, 160),
            mcrfpy.Color(120, 120, 130, 160),
        ]

        # Attempt to place buildings
        attempts = int(w * h * density * 0.1)

        for _ in range(attempts):
            # Random position
            bx = self.rng.randint(5, w - max_size - 5)
            by = self.rng.randint(5, h - max_size - 5)
            bw = self.rng.randint(min_size, max_size)
            bh = self.rng.randint(min_size, max_size)

            # Check if location is valid (not on road, not overlapping)
            valid = True
            for py in range(by - 1, by + bh + 1):
                for px in range(bx - 1, bx + bw + 1):
                    if 0 <= px < w and 0 <= py < h:
                        if self.hmap_roads[px, py] > 0.5:
                            valid = False
                            break
                        if self.hmap_buildings[px, py] > 0.5:
                            valid = False
                            break
                if not valid:
                    break

            if not valid:
                continue

            # Place building
            color = self.rng.choice(building_colors)
            for py in range(by, by + bh):
                for px in range(bx, bx + bw):
                    if 0 <= px < w and 0 <= py < h:
                        self.hmap_buildings[px, py] = 1.0
                        buildings_layer.set((px, py), color)

    def step_composite(self):
        """Step 6: Create final composite."""
        final = self.get_layer("final")
        districts_layer = self.get_layer("districts")
        buildings_layer = self.get_layer("buildings")
        w, h = self.MAP_SIZE

        road_color = mcrfpy.Color(80, 75, 65)

        for y in range(h):
            for x in range(w):
                # Priority: buildings > roads > districts
                if self.hmap_buildings[x, y] > 0.5:
                    c = buildings_layer.at(x, y)
                    final.set((x, y), c)
                elif self.hmap_roads[x, y] > 0.5:
                    final.set((x, y), road_color)
                else:
                    c = districts_layer.at(x, y)
                    final.set((x, y), c)


def main():
    """Run the town demo standalone."""
    demo = TownDemo()
    demo.activate()


if __name__ == "__main__":
    main()
