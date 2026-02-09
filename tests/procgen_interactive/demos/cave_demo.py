"""Cave Generation Demo - Cellular Automata

Demonstrates cellular automata cave generation with:
1. Random noise fill (based on seed + fill_percent)
2. Binary threshold application
3. Cellular automata smoothing passes
4. Flood fill to find connected regions
5. Keep largest connected region
"""

import mcrfpy
from typing import List
from ..core.demo_base import ProcgenDemoBase, StepDef, LayerDef
from ..core.parameter import Parameter


class CaveDemo(ProcgenDemoBase):
    """Interactive cellular automata cave generation demo."""

    name = "Cave Generation"
    description = "Cellular automata cave carving with noise and smoothing"
    MAP_SIZE = (256, 256)

    def define_steps(self) -> List[StepDef]:
        """Define the generation steps."""
        return [
            StepDef("Fill with noise", self.step_fill_noise,
                   "Initialize grid with random noise based on seed and fill percentage"),
            StepDef("Apply threshold", self.step_threshold,
                   "Convert noise to binary wall/floor based on threshold"),
            StepDef("Automata pass 1", self.step_automata_1,
                   "First cellular automata smoothing pass"),
            StepDef("Automata pass 2", self.step_automata_2,
                   "Second cellular automata smoothing pass"),
            StepDef("Automata pass 3", self.step_automata_3,
                   "Third cellular automata smoothing pass"),
            StepDef("Find regions", self.step_find_regions,
                   "Flood fill to identify connected regions"),
            StepDef("Keep largest", self.step_keep_largest,
                   "Keep only the largest connected region"),
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
                description="Random seed for noise generation"
            ),
            Parameter(
                name="fill_percent",
                display="Fill %",
                type="float",
                default=0.45,
                min_val=0.30,
                max_val=0.70,
                step=0.05,
                affects_step=0,
                description="Initial noise fill percentage"
            ),
            Parameter(
                name="threshold",
                display="Threshold",
                type="float",
                default=0.50,
                min_val=0.30,
                max_val=0.70,
                step=0.05,
                affects_step=1,
                description="Wall/floor threshold value"
            ),
            Parameter(
                name="wall_rule",
                display="Wall Rule",
                type="int",
                default=5,
                min_val=3,
                max_val=7,
                step=1,
                affects_step=2,
                description="Neighbors needed to become wall"
            ),
        ]

    def define_layers(self) -> List[LayerDef]:
        """Define visualization layers."""
        return [
            LayerDef("final", "Final Cave", "color", z_index=-1, visible=True,
                    description="Final cave result"),
            LayerDef("raw_noise", "Raw Noise", "color", z_index=0, visible=False,
                    description="Initial random noise"),
            LayerDef("regions", "Regions", "color", z_index=1, visible=False,
                    description="Connected regions colored by ID"),
        ]

    def __init__(self):
        """Initialize cave demo with heightmaps."""
        super().__init__()

        # Create working heightmaps
        self.hmap_noise = self.create_heightmap("noise", 0.0)
        self.hmap_binary = self.create_heightmap("binary", 0.0)
        self.hmap_regions = self.create_heightmap("regions", 0.0)

        # Region tracking
        self.region_ids = []  # List of (id, size) tuples
        self.largest_region_id = 0

        # Noise source
        self.noise = None

    def _apply_colors_to_layer(self, layer, hmap, wall_color, floor_color, alpha=255):
        """Apply binary wall/floor colors to a layer based on heightmap."""
        w, h = self.MAP_SIZE
        for y in range(h):
            for x in range(w):
                val = hmap[x, y]
                if val > 0.5:
                    c = mcrfpy.Color(wall_color.r, wall_color.g, wall_color.b, alpha)
                    layer.set((x, y), c)
                else:
                    c = mcrfpy.Color(floor_color.r, floor_color.g, floor_color.b, alpha)
                    layer.set((x, y), c)

    def _apply_gradient_to_layer(self, layer, hmap, alpha=255):
        """Apply gradient visualization to layer."""
        w, h = self.MAP_SIZE
        for y in range(h):
            for x in range(w):
                val = hmap[x, y]
                v = int(val * 255)
                layer.set((x, y), mcrfpy.Color(v, v, v, alpha))

    # === Step Implementations ===

    def step_fill_noise(self):
        """Step 1: Fill with random noise."""
        seed = self.get_param("seed")
        fill_pct = self.get_param("fill_percent")

        # Create noise source with seed
        self.noise = mcrfpy.NoiseSource(
            dimensions=2,
            algorithm='simplex',
            seed=seed
        )

        # Fill heightmap with noise
        self.hmap_noise.fill(0.0)
        self.hmap_noise.add_noise(
            self.noise,
            world_size=(50, 50),  # Higher frequency for cave-like noise
            mode='fbm',
            octaves=1
        )
        self.hmap_noise.normalize(0.0, 1.0)

        # Show on raw_noise layer (alpha=128 for overlay)
        layer = self.get_layer("raw_noise")
        self._apply_gradient_to_layer(layer, self.hmap_noise, alpha=128)

        # Also show on final layer (full opacity)
        final = self.get_layer("final")
        self._apply_gradient_to_layer(final, self.hmap_noise, alpha=255)

    def step_threshold(self):
        """Step 2: Apply binary threshold."""
        threshold = self.get_param("threshold")

        # Copy noise to binary and threshold
        self.hmap_binary.copy_from(self.hmap_noise)

        # Manual threshold since we want a specific cutoff
        w, h = self.MAP_SIZE
        for y in range(h):
            for x in range(w):
                if self.hmap_binary[x, y] >= threshold:
                    self.hmap_binary[x, y] = 1.0  # Wall
                else:
                    self.hmap_binary[x, y] = 0.0  # Floor

        # Visualize
        final = self.get_layer("final")
        wall = mcrfpy.Color(60, 55, 50)
        floor = mcrfpy.Color(140, 130, 115)
        self._apply_colors_to_layer(final, self.hmap_binary, wall, floor)

    def _run_automata_pass(self):
        """Run one cellular automata pass."""
        wall_rule = self.get_param("wall_rule")
        w, h = self.MAP_SIZE

        # Create copy of current state
        old_data = []
        for y in range(h):
            row = []
            for x in range(w):
                row.append(self.hmap_binary[x, y])
            old_data.append(row)

        # Apply rules
        for y in range(h):
            for x in range(w):
                # Count wall neighbors (including self)
                walls = 0
                for dy in range(-1, 2):
                    for dx in range(-1, 2):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < w and 0 <= ny < h:
                            if old_data[ny][nx] > 0.5:
                                walls += 1
                        else:
                            # Out of bounds counts as wall
                            walls += 1

                # Apply rule: if neighbors >= wall_rule, become wall
                if walls >= wall_rule:
                    self.hmap_binary[x, y] = 1.0
                else:
                    self.hmap_binary[x, y] = 0.0

        # Visualize
        final = self.get_layer("final")
        wall = mcrfpy.Color(60, 55, 50)
        floor = mcrfpy.Color(140, 130, 115)
        self._apply_colors_to_layer(final, self.hmap_binary, wall, floor)

    def step_automata_1(self):
        """Step 3: First automata pass."""
        self._run_automata_pass()

    def step_automata_2(self):
        """Step 4: Second automata pass."""
        self._run_automata_pass()

    def step_automata_3(self):
        """Step 5: Third automata pass."""
        self._run_automata_pass()

    def step_find_regions(self):
        """Step 6: Flood fill to find connected floor regions."""
        w, h = self.MAP_SIZE

        # Reset region data
        self.hmap_regions.fill(0.0)
        self.region_ids = []

        # Track visited cells
        visited = [[False] * w for _ in range(h)]
        region_id = 0

        # Region colors (for visualization) - alpha=128 for overlay
        region_colors = [
            mcrfpy.Color(200, 80, 80, 128),
            mcrfpy.Color(80, 200, 80, 128),
            mcrfpy.Color(80, 80, 200, 128),
            mcrfpy.Color(200, 200, 80, 128),
            mcrfpy.Color(200, 80, 200, 128),
            mcrfpy.Color(80, 200, 200, 128),
            mcrfpy.Color(180, 120, 60, 128),
            mcrfpy.Color(120, 60, 180, 128),
        ]

        # Find all floor regions
        for start_y in range(h):
            for start_x in range(w):
                if visited[start_y][start_x]:
                    continue
                if self.hmap_binary[start_x, start_y] > 0.5:
                    # Wall cell
                    visited[start_y][start_x] = True
                    continue

                # Flood fill this region
                region_id += 1
                region_size = 0
                stack = [(start_x, start_y)]

                while stack:
                    x, y = stack.pop()
                    if visited[y][x]:
                        continue
                    if self.hmap_binary[x, y] > 0.5:
                        continue

                    visited[y][x] = True
                    self.hmap_regions[x, y] = region_id
                    region_size += 1

                    # Add neighbors
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < w and 0 <= ny < h and not visited[ny][nx]:
                            stack.append((nx, ny))

                self.region_ids.append((region_id, region_size))

        # Sort by size descending
        self.region_ids.sort(key=lambda x: x[1], reverse=True)
        if self.region_ids:
            self.largest_region_id = self.region_ids[0][0]

        # Visualize regions (alpha=128 for overlay)
        regions_layer = self.get_layer("regions")
        for y in range(h):
            for x in range(w):
                rid = int(self.hmap_regions[x, y])
                if rid > 0:
                    color = region_colors[(rid - 1) % len(region_colors)]
                    regions_layer.set((x, y), color)
                else:
                    regions_layer.set((x, y), mcrfpy.Color(30, 30, 35, 128))

        # Show region count
        print(f"Found {len(self.region_ids)} regions")

    def step_keep_largest(self):
        """Step 7: Keep only the largest connected region."""
        if not self.region_ids:
            return

        w, h = self.MAP_SIZE

        # Fill all non-largest regions with wall
        for y in range(h):
            for x in range(w):
                rid = int(self.hmap_regions[x, y])
                if rid == 0 or rid != self.largest_region_id:
                    self.hmap_binary[x, y] = 1.0  # Make wall
                # else: keep as floor

        # Visualize final result
        final = self.get_layer("final")
        wall = mcrfpy.Color(45, 40, 38)
        floor = mcrfpy.Color(160, 150, 130)
        self._apply_colors_to_layer(final, self.hmap_binary, wall, floor)

        # Also update regions visualization (alpha=128 for overlay)
        regions_layer = self.get_layer("regions")
        for y in range(h):
            for x in range(w):
                if self.hmap_binary[x, y] > 0.5:
                    regions_layer.set((x, y), mcrfpy.Color(30, 30, 35, 128))
                else:
                    regions_layer.set((x, y), mcrfpy.Color(80, 200, 80, 128))


def main():
    """Run the cave demo standalone."""
    demo = CaveDemo()
    demo.activate()


if __name__ == "__main__":
    main()
