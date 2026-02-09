import mcrfpy
import sys

class ProcgenDemo:
    """Multi-step procedural generation visualization.

    Demonstrates the workflow from the libtcod discussion:
    1. BSP defines room structure
    2. Noise adds organic variation
    3. Boolean mask composition (AND/multiply)
    4. Inversion for floor selection
    5. Smoothing for gradient effects
    """

    MAP_SIZE = (64, 48)
    CELL_SIZE = 14

    # Color palettes
    MASK_RANGES = [
        ((0.0, 0.01), (20, 20, 25)),        # Empty: near-black
        ((0.01, 1.0), (220, 215, 200)),     # Filled: off-white
    ]

    TERRAIN_RANGES = [
        ((0.0, 0.25), ((30, 50, 120), (50, 80, 150))),    # Deep water → water
        ((0.25, 0.35), ((50, 80, 150), (180, 170, 130))), # Water → sand
        ((0.35, 0.55), ((80, 140, 60), (50, 110, 40))),   # Light grass → dark grass
        ((0.55, 0.75), ((50, 110, 40), (120, 100, 80))),  # Grass → rock
        ((0.75, 1.0), ((120, 100, 80), (230, 230, 235))), # Rock → snow
    ]

    DUNGEON_RANGES = [
        ((0.0, 0.1), (40, 35, 30)),                        # Wall: dark stone
        ((0.1, 0.5), ((60, 55, 50), (140, 130, 110))),    # Gradient floor
        ((0.5, 1.0), ((140, 130, 110), (180, 170, 140))), # Lighter floor
    ]

    def __init__(self):
        # HeightMaps
        self.terrain = mcrfpy.HeightMap(self.MAP_SIZE, fill=0.0)
        self.scratchpad = mcrfpy.HeightMap(self.MAP_SIZE, fill=0.0)
        self.bsp = None
        self.noise = mcrfpy.NoiseSource(dimensions=2, algorithm='simplex', seed=42)

        # Scene
        scene = mcrfpy.Scene("procgen_demo")

        # Grid with color layer
        self.grid = mcrfpy.Grid(
            grid_size=self.MAP_SIZE,
            pos=(20, 60),
            size=(self.MAP_SIZE[0] * self.CELL_SIZE,
                  self.MAP_SIZE[1] * self.CELL_SIZE),
            layers={"viz": "color"}
        )
        scene.children.append(self.grid)

        # UI
        self.title = mcrfpy.Caption(text="Procedural Generation Demo",
                                     pos=(20, 15), font_size=24)
        self.label = mcrfpy.Caption(text="Initializing...",
                                     pos=(20, 40), font_size=16)
        scene.children.append(self.title)
        scene.children.append(self.label)

        mcrfpy.current_scene = scene

        # Step schedule
        self.steps = [
            (500*2,   self.step_01_bsp_rooms,     "Step 1: BSP Room Partitioning"),
            (2500*2,  self.step_02_noise,         "Step 2: Generate Noise Field"),
            (4500*2,  self.step_03_threshold,     "Step 3: Threshold to Organic Shapes"),
            (6500*2,  self.step_04_combine,       "Step 4: BSP AND Noise to Cave Walls"),
            (8500*2,  self.step_05_invert,        "Step 5: Invert walls (Floor Regions)"),
            (10500*2, self.step_06_floor_heights, "Step 6: Add Floor Height Variation"),
            (12500*2, self.step_07_smooth,        "Step 7: Smooth for Gradient Floors"),
            (14500*2, self.step_done,             "Complete!"),
        ]
        self.current_step = 0
        self.start_time = None

        self.timer = mcrfpy.Timer("procgen", self.tick, 50)

    def tick(self, timer, runtime):
        if self.start_time is None:
            self.start_time = runtime

        elapsed = runtime - self.start_time

        while (self.current_step < len(self.steps) and
               elapsed >= self.steps[self.current_step][0]):
            _, step_fn, step_label = self.steps[self.current_step]
            self.label.text = step_label
            step_fn()
            self.current_step += 1

        if self.current_step >= len(self.steps):
            timer.stop()

    def apply_colors(self, hmap, ranges):
        """Apply color ranges to grid via GridPoint access."""
        # Since we can't get layer directly, iterate cells
        w, h = self.MAP_SIZE
        for y in range(h):
            for x in range(w):
                val = hmap[x, y]
                color = self._value_to_color(val, ranges)
                self.grid[x, y].viz = color

    def _value_to_color(self, val, ranges):
        """Find color for value in ranges list."""
        for (lo, hi), color_spec in ranges:
            if lo <= val <= hi:
                if isinstance(color_spec[0], tuple):
                    # Gradient: interpolate
                    c1, c2 = color_spec
                    t = (val - lo) / (hi - lo) if hi > lo else 0
                    return tuple(int(c1[i] + t * (c2[i] - c1[i])) for i in range(3))
                else:
                    # Fixed color
                    return color_spec
        return (128, 128, 128)  # Fallback gray

    # =========================================================
    # GENERATION STEPS
    # =========================================================

    def step_01_bsp_rooms(self):
        """Create BSP partition and visualize rooms."""
        self.bsp = mcrfpy.BSP(pos=(1, 1), size=(62, 46))
        self.bsp.split_recursive(depth=4, min_size=(8, 6), seed=42)

        rooms = self.bsp.to_heightmap(self.MAP_SIZE, 'leaves', shrink=1)
        self.scratchpad.copy_from(rooms)
        self.apply_colors(self.scratchpad, self.MASK_RANGES)

    def step_02_noise(self):
        """Generate FBM noise and visualize."""
        self.terrain.fill(0.0)
        self.terrain.add_noise(self.noise, world_size=(12, 12),
                               mode='fbm', octaves=5)
        self.terrain.normalize(0.0, 1.0)
        self.apply_colors(self.terrain, self.TERRAIN_RANGES)

    def step_03_threshold(self):
        """Threshold noise to create organic cave boundaries."""
        cave_mask = self.terrain.threshold_binary((0.45, 1.0), value=1.0)
        self.terrain.copy_from(cave_mask)
        self.apply_colors(self.terrain, self.MASK_RANGES)

    def step_04_combine(self):
        """AND operation: BSP rooms × noise threshold = cave walls."""
        # scratchpad has BSP rooms (1 = inside room)
        # terrain has noise threshold (1 = "solid" area)
        # multiply gives: 1 where both are 1
        combined = mcrfpy.HeightMap(self.MAP_SIZE)
        combined.copy_from(self.scratchpad)
        combined.multiply(self.terrain)
        self.scratchpad.copy_from(combined)
        self.apply_colors(self.scratchpad, self.MASK_RANGES)

    def step_05_invert(self):
        """Invert to get floor regions (0 becomes floor)."""
        # After AND: 1 = wall (inside room AND solid noise)
        # Invert: 0 → 1 (floor), 1 → 0 (wall)
        # But inverse does 1 - x, so 1 becomes 0, 0 becomes 1
        floors = self.scratchpad.inverse()
        # Clamp because inverse can give negative values if > 1
        floors.clamp(0.0, 1.0)
        self.terrain.copy_from(floors)
        self.apply_colors(self.terrain, self.DUNGEON_RANGES)

    def step_06_floor_heights(self):
        """Add height variation to floors using noise."""
        # Create new noise for floor heights
        floor_noise = mcrfpy.NoiseSource(dimensions=2, algorithm='simplex', seed=789)
        height_var = mcrfpy.HeightMap(self.MAP_SIZE, fill=0.0)
        height_var.add_noise(floor_noise, world_size=(20, 20),
                             mode='fbm', octaves=3, scale=0.4)
        height_var.add_constant(0.5)
        height_var.clamp(0.0, 1.0)

        # Mask to floor regions only (terrain has floor mask from step 5)
        height_var.multiply(self.terrain)
        self.terrain.copy_from(height_var)
        self.apply_colors(self.terrain, self.DUNGEON_RANGES)

    def step_07_smooth(self):
        """Apply smoothing for gradient floor effect."""
        self.terrain.smooth(iterations=1)
        self.apply_colors(self.terrain, self.DUNGEON_RANGES)

    def step_done(self):
        """Final step - display completion message."""
        self.label.text = "Complete!"

# Launch
demo = ProcgenDemo()

