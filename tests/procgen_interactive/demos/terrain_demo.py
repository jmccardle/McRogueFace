"""Terrain Generation Demo - Multi-layer Elevation

Demonstrates terrain generation with:
1. Generate base elevation with simplex FBM
2. Normalize to 0-1 range
3. Apply water level (flatten below threshold)
4. Add mountain enhancement (boost peaks)
5. Optional erosion simulation
6. Apply terrain color ranges (biomes)
"""

import mcrfpy
from typing import List
from ..core.demo_base import ProcgenDemoBase, StepDef, LayerDef
from ..core.parameter import Parameter


class TerrainDemo(ProcgenDemoBase):
    """Interactive multi-layer terrain generation demo."""

    name = "Terrain"
    description = "Multi-layer elevation with noise and biome coloring"
    MAP_SIZE = (256, 256)

    # Terrain color ranges (elevation -> color gradient)
    TERRAIN_COLORS = [
        (0.00, 0.15, (30, 50, 120), (50, 80, 150)),     # Deep water -> Shallow water
        (0.15, 0.22, (50, 80, 150), (180, 170, 130)),   # Shallow water -> Beach
        (0.22, 0.35, (180, 170, 130), (80, 140, 60)),   # Beach -> Grass low
        (0.35, 0.55, (80, 140, 60), (50, 110, 40)),     # Grass low -> Grass high
        (0.55, 0.70, (50, 110, 40), (100, 90, 70)),     # Grass high -> Rock low
        (0.70, 0.85, (100, 90, 70), (140, 130, 120)),   # Rock low -> Rock high
        (0.85, 1.00, (140, 130, 120), (220, 220, 225)), # Rock high -> Snow
    ]

    def define_steps(self) -> List[StepDef]:
        """Define the generation steps."""
        return [
            StepDef("Generate base elevation", self.step_base_elevation,
                   "Create initial terrain using simplex FBM noise"),
            StepDef("Normalize heights", self.step_normalize,
                   "Normalize elevation values to 0-1 range"),
            StepDef("Apply water level", self.step_water_level,
                   "Flatten terrain below water threshold"),
            StepDef("Enhance mountains", self.step_mountains,
                   "Boost high elevation areas for dramatic peaks"),
            StepDef("Apply erosion", self.step_erosion,
                   "Smooth terrain with erosion simulation"),
            StepDef("Color biomes", self.step_biomes,
                   "Apply biome colors based on elevation"),
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
                description="Noise seed"
            ),
            Parameter(
                name="octaves",
                display="Octaves",
                type="int",
                default=6,
                min_val=1,
                max_val=8,
                step=1,
                affects_step=0,
                description="FBM detail octaves"
            ),
            Parameter(
                name="world_size",
                display="Scale",
                type="float",
                default=8.0,
                min_val=2.0,
                max_val=20.0,
                step=1.0,
                affects_step=0,
                description="Noise scale (larger = more zoomed out)"
            ),
            Parameter(
                name="water_level",
                display="Water Level",
                type="float",
                default=0.20,
                min_val=0.0,
                max_val=0.40,
                step=0.02,
                affects_step=2,
                description="Sea level threshold"
            ),
            Parameter(
                name="mountain_boost",
                display="Mt. Boost",
                type="float",
                default=0.25,
                min_val=0.0,
                max_val=0.50,
                step=0.05,
                affects_step=3,
                description="Mountain height enhancement"
            ),
            Parameter(
                name="erosion_passes",
                display="Erosion",
                type="int",
                default=2,
                min_val=0,
                max_val=5,
                step=1,
                affects_step=4,
                description="Erosion smoothing passes"
            ),
        ]

    def define_layers(self) -> List[LayerDef]:
        """Define visualization layers."""
        return [
            LayerDef("colored", "Colored Terrain", "color", z_index=-1, visible=True,
                    description="Final terrain with biome colors"),
            LayerDef("elevation", "Elevation", "color", z_index=0, visible=False,
                    description="Grayscale height values"),
            LayerDef("water_mask", "Water Mask", "color", z_index=1, visible=False,
                    description="Binary water regions"),
        ]

    def __init__(self):
        """Initialize terrain demo."""
        super().__init__()

        # Create working heightmaps
        self.hmap_elevation = self.create_heightmap("elevation", 0.0)
        self.hmap_water = self.create_heightmap("water", 0.0)

        # Noise source
        self.noise = None

    def _apply_grayscale(self, layer, hmap, alpha=255):
        """Apply grayscale visualization to layer."""
        w, h = self.MAP_SIZE
        for y in range(h):
            for x in range(w):
                val = hmap[x, y]
                v = int(max(0, min(255, val * 255)))
                layer.set((x, y), mcrfpy.Color(v, v, v, alpha))

    def _apply_terrain_colors(self, layer, hmap, alpha=255):
        """Apply terrain biome colors based on elevation."""
        w, h = self.MAP_SIZE
        for y in range(h):
            for x in range(w):
                val = hmap[x, y]
                color = self._elevation_to_color(val, alpha)
                layer.set((x, y), color)

    def _elevation_to_color(self, val, alpha=255):
        """Convert elevation value to terrain color."""
        for low, high, c1, c2 in self.TERRAIN_COLORS:
            if low <= val <= high:
                # Interpolate between c1 and c2
                t = (val - low) / (high - low) if high > low else 0
                r = int(c1[0] + t * (c2[0] - c1[0]))
                g = int(c1[1] + t * (c2[1] - c1[1]))
                b = int(c1[2] + t * (c2[2] - c1[2]))
                return mcrfpy.Color(r, g, b, alpha)

        # Default for out of range
        return mcrfpy.Color(128, 128, 128)

    # === Step Implementations ===

    def step_base_elevation(self):
        """Step 1: Generate base elevation with FBM noise."""
        seed = self.get_param("seed")
        octaves = self.get_param("octaves")
        world_size = self.get_param("world_size")

        # Create noise source
        self.noise = mcrfpy.NoiseSource(
            dimensions=2,
            algorithm='simplex',
            seed=seed
        )

        # Fill with FBM noise
        self.hmap_elevation.fill(0.0)
        self.hmap_elevation.add_noise(
            self.noise,
            world_size=(world_size, world_size),
            mode='fbm',
            octaves=octaves
        )

        # Show raw noise (elevation layer alpha=128 for overlay)
        elevation_layer = self.get_layer("elevation")
        self._apply_grayscale(elevation_layer, self.hmap_elevation, alpha=128)

        # Also on colored layer (full opacity for final)
        colored_layer = self.get_layer("colored")
        self._apply_grayscale(colored_layer, self.hmap_elevation, alpha=255)

    def step_normalize(self):
        """Step 2: Normalize elevation to 0-1 range."""
        self.hmap_elevation.normalize(0.0, 1.0)

        # Update visualization
        elevation_layer = self.get_layer("elevation")
        self._apply_grayscale(elevation_layer, self.hmap_elevation, alpha=128)

        colored_layer = self.get_layer("colored")
        self._apply_grayscale(colored_layer, self.hmap_elevation, alpha=255)

    def step_water_level(self):
        """Step 3: Flatten terrain below water level."""
        water_level = self.get_param("water_level")
        w, h = self.MAP_SIZE

        # Create water mask
        self.hmap_water.fill(0.0)

        for y in range(h):
            for x in range(w):
                val = self.hmap_elevation[x, y]
                if val < water_level:
                    # Flatten to water level
                    self.hmap_elevation[x, y] = water_level
                    self.hmap_water[x, y] = 1.0

        # Update water mask layer (alpha=128 for overlay)
        water_layer = self.get_layer("water_mask")
        for y in range(h):
            for x in range(w):
                if self.hmap_water[x, y] > 0.5:
                    water_layer.set((x, y), mcrfpy.Color(80, 120, 200, 128))
                else:
                    water_layer.set((x, y), mcrfpy.Color(30, 30, 35, 128))

        # Update other layers
        elevation_layer = self.get_layer("elevation")
        self._apply_grayscale(elevation_layer, self.hmap_elevation, alpha=128)

        colored_layer = self.get_layer("colored")
        self._apply_grayscale(colored_layer, self.hmap_elevation, alpha=255)

    def step_mountains(self):
        """Step 4: Enhance mountain peaks."""
        mountain_boost = self.get_param("mountain_boost")
        w, h = self.MAP_SIZE

        if mountain_boost <= 0:
            return  # Skip if no boost

        for y in range(h):
            for x in range(w):
                val = self.hmap_elevation[x, y]
                # Boost high elevations more than low ones
                # Using a power curve
                if val > 0.5:
                    boost = (val - 0.5) * 2  # 0 to 1 for upper half
                    boost = boost * boost * mountain_boost  # Squared for sharper peaks
                    self.hmap_elevation[x, y] = min(1.0, val + boost)

        # Re-normalize to ensure 0-1 range
        self.hmap_elevation.normalize(0.0, 1.0)

        # Update visualization
        elevation_layer = self.get_layer("elevation")
        self._apply_grayscale(elevation_layer, self.hmap_elevation, alpha=128)

        colored_layer = self.get_layer("colored")
        self._apply_grayscale(colored_layer, self.hmap_elevation, alpha=255)

    def step_erosion(self):
        """Step 5: Apply erosion/smoothing."""
        erosion_passes = self.get_param("erosion_passes")

        if erosion_passes <= 0:
            return  # Skip if no erosion

        for _ in range(erosion_passes):
            self.hmap_elevation.smooth(iterations=1)

        # Update visualization
        elevation_layer = self.get_layer("elevation")
        self._apply_grayscale(elevation_layer, self.hmap_elevation, alpha=128)

        colored_layer = self.get_layer("colored")
        self._apply_grayscale(colored_layer, self.hmap_elevation, alpha=255)

    def step_biomes(self):
        """Step 6: Apply biome colors based on elevation."""
        colored_layer = self.get_layer("colored")
        self._apply_terrain_colors(colored_layer, self.hmap_elevation, alpha=255)


def main():
    """Run the terrain demo standalone."""
    demo = TerrainDemo()
    demo.activate()


if __name__ == "__main__":
    main()
