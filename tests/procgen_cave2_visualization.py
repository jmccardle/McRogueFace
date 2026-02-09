import mcrfpy

class ProcgenDemo:
    """Multi-step procedural generation: terrain with embedded caves."""

    MAP_SIZE = (64, 48)
    CELL_SIZE = 14

    # Terrain colors (outside caves)
    TERRAIN_RANGES = [
        ((0.0, 0.15), ((30, 50, 120), (50, 80, 150))),     # Water
        ((0.51, 0.25), ((50, 80, 150), (180, 170, 130))),  # Beach
        ((0.25, 0.55), ((80, 140, 60), (50, 110, 40))),    # Grass
        ((0.55, 0.75), ((50, 110, 40), (120, 100, 80))),   # Rock
        ((0.75, 1.0), ((120, 100, 80), (200, 195, 190))),  # Mountain
    ]

    # Cave interior colors
    CAVE_RANGES = [
        ((0.0, 0.15), (35, 30, 28)),                        # Wall (dark)
        ((0.15, 0.5), ((50, 45, 42), (100, 90, 80))),      # Floor gradient
        ((0.5, 1.0), ((100, 90, 80), (140, 125, 105))),    # Lighter floor
    ]

    # Mask visualization
    MASK_RANGES = [
        ((0.0, 0.01), (20, 20, 25)),
        ((0.01, 1.0), (220, 215, 200)),
    ]

    def __init__(self):
        # HeightMaps
        self.terrain = mcrfpy.HeightMap(self.MAP_SIZE, fill=0.0)
        self.cave_selection = mcrfpy.HeightMap(self.MAP_SIZE, fill=0.0)
        self.cave_interior = mcrfpy.HeightMap(self.MAP_SIZE, fill=0.0)
        self.scratchpad = mcrfpy.HeightMap(self.MAP_SIZE, fill=0.0)

        self.bsp = None
        self.terrain_noise = mcrfpy.NoiseSource(dimensions=2, algorithm='simplex', seed=44)
        self.cave_noise = mcrfpy.NoiseSource(dimensions=2, algorithm='simplex', seed=900)

        # Scene setup
        scene = mcrfpy.Scene("procgen_demo")

        self.grid = mcrfpy.Grid(
            grid_size=self.MAP_SIZE,
            pos=(0,0),
            size=(1024, 768),
            layers={"viz": "color"}
        )
        scene.children.append(self.grid)

        self.title = mcrfpy.Caption(text="Terrain + Cave Procgen",
                                     pos=(20, 15), font_size=24)
        self.label = mcrfpy.Caption(text="", pos=(20, 45), font_size=16)
        scene.children.append(self.title)
        scene.children.append(self.label)

        mcrfpy.current_scene = scene

        # Steps with longer pauses for complex operations
        self.steps = [
            (500,   self.step_01_terrain,           "1: Generate terrain elevation"),
            (4000,  self.step_02_bsp_all,           "2: BSP partition (all leaves)"),
            (5000,  self.step_03_bsp_subset,        "3: Select cave-worthy BSP nodes"),
            (7000,  self.step_04_terrain_mask,      "4: Exclude low terrain (water/canyon)"),
            (9000,  self.step_05_valid_caves,       "5: Valid cave regions (BSP && high terrain)"),
            (11000, self.step_06_cave_noise,        "6: Organic cave walls (noise threshold)"),
            (13000, self.step_07_apply_to_selection,"7: Walls within selection only"),
            (15000, self.step_08_invert_floors,     "8: Invert -> cave floors"),
            (17000, self.step_09_floor_heights,     "9: Add floor height variation"),
            (19000, self.step_10_smooth,            "10: Smooth floor gradients"),
            (21000, self.step_11_composite,         "11: Composite: terrain + caves"),
            (23000, self.step_done,                 "Complete!"),
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
        w, h = self.MAP_SIZE
        for y in range(h):
            for x in range(w):
                val = hmap[x, y]
                color = self._value_to_color(val, ranges)
                self.grid[x, y].viz = color

    def _value_to_color(self, val, ranges):
        for (lo, hi), color_spec in ranges:
            if lo <= val <= hi:
                if isinstance(color_spec[0], tuple):
                    c1, c2 = color_spec
                    t = (val - lo) / (hi - lo) if hi > lo else 0
                    return tuple(int(c1[i] + t * (c2[i] - c1[i])) for i in range(3))
                else:
                    return color_spec
        return (128, 128, 128)

    # =========================================================
    # STEP 1: BASE TERRAIN
    # =========================================================

    def step_01_terrain(self):
        """Generate the base terrain with elevation."""
        self.terrain.fill(0.0)
        self.terrain.add_noise(self.terrain_noise,
                               world_size=(10, 10),
                               mode='fbm', octaves=5)
        self.terrain.normalize(0.0, 1.0)
        self.apply_colors(self.terrain, self.TERRAIN_RANGES)

    # =========================================================
    # STEPS 2-5: CAVE SELECTION (where caves can exist)
    # =========================================================

    def step_02_bsp_all(self):
        """Show all BSP leaves (potential cave locations)."""
        self.bsp = mcrfpy.BSP(pos=(2, 2), size=(60, 44))
        self.bsp.split_recursive(depth=4, min_size=(8, 6), seed=66)

        all_rooms = self.bsp.to_heightmap(self.MAP_SIZE, 'leaves', shrink=1)
        self.apply_colors(all_rooms, self.MASK_RANGES)

    def step_03_bsp_subset(self):
        """Select only SOME BSP leaves for caves."""
        self.cave_selection.fill(0.0)

        # Selection criteria: only leaves whose center is in
        # higher terrain AND not too close to edges
        w, h = self.MAP_SIZE
        for leaf in self.bsp.leaves():
            cx, cy = leaf.center()

            # Skip if center is out of bounds
            if not (0 <= cx < w and 0 <= cy < h):
                continue

            terrain_height = self.terrain[cx, cy]

            # Criteria:
            # - Terrain height > 0.4 (above water/beach)
            # - Not too close to map edges
            # - Some randomness based on position
            edge_margin = 8
            in_center = (edge_margin < cx < w - edge_margin and
                         edge_margin < cy < h - edge_margin)

            # Pseudo-random selection based on leaf position
            pseudo_rand = ((cx * 7 + cy * 13) % 10) / 10.0

            if terrain_height > 0.45 and in_center and pseudo_rand > 0.3:
                # Fill this leaf into selection
                lx, ly = leaf.pos
                lw, lh = leaf.size
                for y in range(ly, ly + lh):
                    for x in range(lx, lx + lw):
                        if 0 <= x < w and 0 <= y < h:
                            self.cave_selection[x, y] = 1.0

        self.apply_colors(self.cave_selection, self.MASK_RANGES)

    def step_04_terrain_mask(self):
        """Create mask of terrain high enough for caves."""
        # Threshold: only where terrain > 0.35 (above water/beach)
        high_terrain = self.terrain.threshold_binary((0.35, 1.0), value=1.0)
        self.scratchpad.copy_from(high_terrain)
        self.apply_colors(self.scratchpad, self.MASK_RANGES)

    def step_05_valid_caves(self):
        """AND: selected BSP nodes × high terrain = valid cave regions."""
        # cave_selection has our chosen BSP leaves
        # scratchpad has the "high enough" terrain mask
        self.cave_selection.multiply(self.scratchpad)
        self.apply_colors(self.cave_selection, self.MASK_RANGES)

    # =========================================================
    # STEPS 6-10: CAVE INTERIOR (detail within selection)
    # =========================================================

    def step_06_cave_noise(self):
        """Generate organic noise for cave wall shapes."""
        self.cave_interior.fill(0.0)
        self.cave_interior.add_noise(self.cave_noise,
                                      world_size=(15, 15),
                                      mode='fbm', octaves=4)
        self.cave_interior.normalize(0.0, 1.0)

        # Threshold to binary: 1 = solid (wall), 0 = open
        walls = self.cave_interior.threshold_binary((0.42, 1.0), value=1.0)
        self.cave_interior.copy_from(walls)
        self.apply_colors(self.cave_interior, self.MASK_RANGES)

    def step_07_apply_to_selection(self):
        """Walls only within the valid cave selection."""
        # cave_interior has organic wall pattern
        # cave_selection has valid cave regions
        # AND them: walls only where both are 1
        self.cave_interior.multiply(self.cave_selection)
        self.apply_colors(self.cave_interior, self.MASK_RANGES)

    def step_08_invert_floors(self):
        """Invert to get floor regions within caves."""
        # cave_interior: 1 = wall, 0 = not-wall
        # We want floors where selection=1 AND wall=0
        # floors = selection AND (NOT walls)

        walls_inverted = self.cave_interior.inverse()
        walls_inverted.clamp(0.0, 1.0)

        # AND with selection to get floors only in cave areas
        floors = mcrfpy.HeightMap(self.MAP_SIZE)
        floors.copy_from(self.cave_selection)
        floors.multiply(walls_inverted)

        self.cave_interior.copy_from(floors)
        self.apply_colors(self.cave_interior, self.MASK_RANGES)

    def step_09_floor_heights(self):
        """Add height variation to cave floors."""
        floor_noise = mcrfpy.NoiseSource(dimensions=2, algorithm='simplex', seed=456)

        heights = mcrfpy.HeightMap(self.MAP_SIZE, fill=0.0)
        heights.add_noise(floor_noise, world_size=(25, 25),
                          mode='fbm', octaves=3, scale=0.5)
        heights.add_constant(0.5)
        heights.clamp(0.2, 1.0)  # Keep floors visible (not too dark)

        # Mask to floor regions
        heights.multiply(self.cave_interior)
        self.cave_interior.copy_from(heights)
        self.apply_colors(self.cave_interior, self.CAVE_RANGES)

    def step_10_smooth(self):
        """Smooth the floor heights for gradients."""
        self.cave_interior.smooth(iterations=1)
        self.apply_colors(self.cave_interior, self.CAVE_RANGES)

    # =========================================================
    # STEP 11: COMPOSITE
    # =========================================================

    def step_11_composite(self):
        """Composite: terrain outside caves + cave interior inside."""
        w, h = self.MAP_SIZE

        for y in range(h):
            for x in range(w):
                cave_val = self.cave_interior[x, y]
                terrain_val = self.terrain[x, y]

                if cave_val > 0.01:
                    # Inside cave: use cave colors
                    color = self._value_to_color(cave_val, self.CAVE_RANGES)
                else:
                    # Outside cave: use terrain colors
                    color = self._value_to_color(terrain_val, self.TERRAIN_RANGES)

                self.grid[x, y].viz = color

    def step_done(self):
        self.label.text = "Mixed procgen terrain"

# Launch
demo = ProcgenDemo()

