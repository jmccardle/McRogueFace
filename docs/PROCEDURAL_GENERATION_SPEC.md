# McRogueFace Procedural Generation System Specification

**Version:** 1.0 Draft
**Date:** 2026-01-11
**Status:** Design Complete, Pending Implementation

## Overview

This specification defines the procedural generation system for McRogueFace, exposing libtcod's noise, BSP, and heightmap capabilities through a Pythonic interface optimized for batch operations on Grid and Layer objects.

### Design Philosophy

1. **HeightMap as Universal Canvas**: All procedural data flows through HeightMap objects. Noise and BSP structures generate data *onto* HeightMaps, and Grids/Layers consume data *from* HeightMaps.

2. **Data Stays in C++**: Python defines rules and configuration; C++ executes batch operations. Map data (potentially 1M+ cells) never crosses the Python/C++ boundary during generation.

3. **Composability**: HeightMaps can be combined (add, multiply, lerp), allowing complex terrain from simple building blocks.

4. **Vector-Based Coordinates**: All positions use `(x, y)` tuples. Regions use `((x, y), (w, h))` for bounds or `((x1, y1), (x2, y2))` for world regions.

5. **Mutation with Chaining**: Operations mutate in place and return `self` for method chaining. Threshold operations return new HeightMaps to preserve originals.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           SOURCES                                   │
│                                                                     │
│  NoiseSource                           BSP                          │
│  (infinite function,                   (structural partition,       │
│   stateless)                            tree of nodes)              │
│         │                                    │                      │
│         │ .sample()                          │ .to_heightmap()      │
│         ▼                                    ▼                      │
│  ┌─────────────┐                      ┌─────────────┐              │
│  │ NoiseSample │                      │   BSPMap    │              │
│  │ (HeightMap) │                      │ (HeightMap) │              │
│  └──────┬──────┘                      └──────┬──────┘              │
│         │    ▲                               │    ▲                 │
│         │    │ .add_noise()                  │    │ .add_bsp()      │
│         │    │ .multiply_noise()             │    │ .multiply_bsp() │
│         ▼    │                               ▼    │                 │
│         └────┴───────────┬───────────────────┴────┘                 │
│                          ▼                                          │
│                ┌─────────────────┐                                  │
│                │    HeightMap    │                                  │
│                │  (2D float[])   │                                  │
│                │                 │                                  │
│                │ Operations:     │                                  │
│                │ • add/multiply  │                                  │
│                │ • hills/erosion │                                  │
│                │ • threshold     │                                  │
│                │ • normalize     │                                  │
│                └────────┬────────┘                                  │
│                         │                                           │
│          ┌──────────────┼──────────────┐                           │
│          ▼              ▼              ▼                            │
│   ┌───────────┐  ┌───────────┐  ┌───────────┐                      │
│   │   Grid    │  │ TileLayer │  │ColorLayer │                      │
│   │           │  │           │  │           │                      │
│   │ walkable  │  │ tile_index│  │ color     │                      │
│   │transparent│  │           │  │ gradient  │                      │
│   └───────────┘  └───────────┘  └───────────┘                      │
│                       TARGETS                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Class Reference

### mcrfpy.HeightMap

The universal canvas for procedural generation. A 2D grid of float values that can be generated, manipulated, combined, and applied to game objects.

#### Constructor

```python
HeightMap(size: tuple[int, int], fill: float = 0.0)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `size` | `(int, int)` | Width and height in cells. Immutable after creation. |
| `fill` | `float` | Initial value for all cells. Default 0.0. |

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `size` | `(int, int)` | Read-only. Width and height of the heightmap. |

#### Scalar Operations

All scalar operations mutate in place and return `self` for chaining.

```python
def fill(self, value: float) -> HeightMap
```
Set all cells to `value`.

```python
def clear(self) -> HeightMap
```
Set all cells to 0.0. Equivalent to `fill(0.0)`.

```python
def add_constant(self, value: float) -> HeightMap
```
Add `value` to every cell.

```python
def scale(self, factor: float) -> HeightMap
```
Multiply every cell by `factor`.

```python
def clamp(self, min: float = 0.0, max: float = 1.0) -> HeightMap
```
Clamp all values to the range [min, max].

```python
def normalize(self, min: float = 0.0, max: float = 1.0) -> HeightMap
```
Linearly rescale values so the current minimum becomes `min` and current maximum becomes `max`.

#### HeightMap Combination

All combination operations mutate in place and return `self`. The `other` HeightMap must have the same size.

```python
def add(self, other: HeightMap) -> HeightMap
```
Add `other` to this heightmap cell-by-cell.

```python
def subtract(self, other: HeightMap) -> HeightMap
```
Subtract `other` from this heightmap cell-by-cell.

```python
def multiply(self, other: HeightMap) -> HeightMap
```
Multiply this heightmap by `other` cell-by-cell. Useful for masking.

```python
def lerp(self, other: HeightMap, t: float) -> HeightMap
```
Linear interpolation: `self = self + (other - self) * t`.

```python
def copy_from(self, other: HeightMap) -> HeightMap
```
Copy all values from `other` into this heightmap.

```python
def max(self, other: HeightMap) -> HeightMap
```
Per-cell maximum of this and `other`.

```python
def min(self, other: HeightMap) -> HeightMap
```
Per-cell minimum of this and `other`.

#### Direct Source Sampling

These methods sample from sources directly onto the heightmap without intermediate allocation.

```python
def add_noise(self,
              source: NoiseSource,
              world_region: tuple = None,
              mode: str = "fbm",
              octaves: int = 4,
              scale: float = 1.0) -> HeightMap
```
Sample noise and add to current values.

| Parameter | Type | Description |
|-----------|------|-------------|
| `source` | `NoiseSource` | The noise generator to sample from. |
| `world_region` | `((x1,y1), (x2,y2))` | World coordinates to sample. Default: `((0,0), size)`. |
| `mode` | `str` | `"flat"`, `"fbm"`, or `"turbulence"`. Default: `"fbm"`. |
| `octaves` | `int` | Octaves for fbm/turbulence. Default: 4. |
| `scale` | `float` | Multiplier for sampled values. Default: 1.0. |

```python
def multiply_noise(self, source: NoiseSource, **kwargs) -> HeightMap
```
Sample noise and multiply with current values. Same parameters as `add_noise`.

```python
def add_bsp(self,
            bsp: BSP,
            select: str = "leaves",
            nodes: list[BSPNode] = None,
            shrink: int = 0,
            value: float = 1.0) -> HeightMap
```
Add BSP node regions to heightmap.

| Parameter | Type | Description |
|-----------|------|-------------|
| `bsp` | `BSP` | The BSP tree to sample from. |
| `select` | `str` | `"leaves"`, `"all"`, or `"internal"`. Default: `"leaves"`. |
| `nodes` | `list[BSPNode]` | Override: specific nodes only. Default: None (use select). |
| `shrink` | `int` | Pixels to shrink from node bounds. Default: 0. |
| `value` | `float` | Value to add inside selected regions. Default: 1.0. |

```python
def multiply_bsp(self, bsp: BSP, **kwargs) -> HeightMap
```
Multiply by BSP regions. Same parameters as `add_bsp`.

#### Terrain Generation

These methods implement libtcod heightmap generation algorithms.

```python
def add_hill(self, center: tuple[int, int], radius: float, height: float) -> HeightMap
```
Add a hill (half-spheroid) at the specified position.

```python
def dig_hill(self, center: tuple[int, int], radius: float, depth: float) -> HeightMap
```
Dig a depression. Takes minimum of current value and hill shape (for carving rivers, pits).

```python
def add_voronoi(self,
                num_points: int,
                coefficients: tuple[float, ...] = (1.0, -0.5),
                seed: int = None) -> HeightMap
```
Add Voronoi diagram values. Coefficients weight distance to Nth-closest point.

```python
def mid_point_displacement(self,
                           roughness: float = 0.5,
                           seed: int = None) -> HeightMap
```
Generate fractal terrain using diamond-square algorithm. Roughness should be 0.4-0.6.

```python
def rain_erosion(self,
                 drops: int,
                 erosion: float = 0.1,
                 sedimentation: float = 0.05,
                 seed: int = None) -> HeightMap
```
Simulate rain erosion. `drops` should be at least `width * height`.

```python
def dig_bezier(self,
               points: tuple[tuple[int, int], ...],
               start_radius: float,
               end_radius: float,
               start_depth: float,
               end_depth: float) -> HeightMap
```
Carve a path along a cubic Bezier curve. Requires exactly 4 control points.

```python
def smooth(self, iterations: int = 1) -> HeightMap
```
Apply smoothing kernel. Each iteration averages cells with neighbors.

#### Threshold Operations

These methods return **new** HeightMap objects, preserving the original.

```python
def threshold(self, range: tuple[float, float]) -> HeightMap
```
Return new HeightMap with original values where in range, 0.0 elsewhere.

```python
def threshold_binary(self,
                     range: tuple[float, float],
                     value: float = 1.0) -> HeightMap
```
Return new HeightMap with `value` where in range, 0.0 elsewhere.

```python
def inverse(self) -> HeightMap
```
Return new HeightMap with `(1.0 - value)` for each cell.

#### Queries

These methods return values to Python for inspection.

```python
def get(self, pos: tuple[int, int]) -> float
```
Get value at integer coordinates.

```python
def get_interpolated(self, pos: tuple[float, float]) -> float
```
Get bilinearly interpolated value at float coordinates.

```python
def get_slope(self, pos: tuple[int, int]) -> float
```
Get slope (0 to π/2) at position.

```python
def get_normal(self, pos: tuple[int, int]) -> tuple[float, float, float]
```
Get normalized surface normal vector at position.

```python
def min_max(self) -> tuple[float, float]
```
Return (minimum_value, maximum_value) across all cells.

```python
def count_in_range(self, range: tuple[float, float]) -> int
```
Count cells with values in the specified range.

---

### mcrfpy.NoiseSource

A configured noise generator function. Stateless and infinite - the same coordinates always produce the same value.

#### Constructor

```python
NoiseSource(dimensions: int = 2,
            algorithm: str = "simplex",
            hurst: float = 0.5,
            lacunarity: float = 2.0,
            seed: int = None)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `dimensions` | `int` | 1-4. Number of input dimensions. Default: 2. |
| `algorithm` | `str` | `"simplex"`, `"perlin"`, or `"wavelet"`. Default: `"simplex"`. |
| `hurst` | `float` | Fractal Hurst exponent for fbm/turbulence. Default: 0.5. |
| `lacunarity` | `float` | Frequency multiplier between octaves. Default: 2.0. |
| `seed` | `int` | Random seed. None for random. |

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `dimensions` | `int` | Read-only. |
| `algorithm` | `str` | Read-only. |
| `hurst` | `float` | Read-only. |
| `lacunarity` | `float` | Read-only. |
| `seed` | `int` | Read-only. |

#### Point Queries

```python
def get(self, pos: tuple[float, ...]) -> float
```
Get flat noise value at coordinates. Tuple length must match dimensions. Returns -1.0 to 1.0.

```python
def fbm(self, pos: tuple[float, ...], octaves: int = 4) -> float
```
Get fractal brownian motion value. Returns -1.0 to 1.0.

```python
def turbulence(self, pos: tuple[float, ...], octaves: int = 4) -> float
```
Get turbulence (absolute fbm) value. Returns -1.0 to 1.0.

#### Batch Sampling

```python
def sample(self,
           size: tuple[int, int],
           world_region: tuple = None,
           mode: str = "fbm",
           octaves: int = 4) -> NoiseSample
```
Create a NoiseSample (HeightMap subclass) by sampling a region.

| Parameter | Type | Description |
|-----------|------|-------------|
| `size` | `(int, int)` | Output dimensions in cells. |
| `world_region` | `((x1,y1), (x2,y2))` | World coordinates to sample. Default: `((0,0), size)`. |
| `mode` | `str` | `"flat"`, `"fbm"`, or `"turbulence"`. Default: `"fbm"`. |
| `octaves` | `int` | Octaves for fbm/turbulence. Default: 4. |

---

### mcrfpy.NoiseSample

A HeightMap created by sampling a NoiseSource. Tracks its origin for convenient adjacent sampling and rescaling.

#### Inheritance

`NoiseSample` extends `HeightMap` - all HeightMap methods are available.

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `source` | `NoiseSource` | Read-only. The generator that created this sample. |
| `world_region` | `((x1,y1), (x2,y2))` | Read-only. World coordinates that were sampled. |
| `mode` | `str` | Read-only. `"flat"`, `"fbm"`, or `"turbulence"`. |
| `octaves` | `int` | Read-only. Octaves used for sampling. |

#### Adjacent Sampling

```python
def next_left(self) -> NoiseSample
def next_right(self) -> NoiseSample
def next_up(self) -> NoiseSample
def next_down(self) -> NoiseSample
```
Sample the adjacent region in the specified direction. Returns a new NoiseSample with the same size, mode, and octaves, but shifted world_region.

#### Rescaling

```python
def resample(self, size: tuple[int, int]) -> NoiseSample
```
Resample the same world_region at a different output resolution. Useful for minimaps (smaller size) or detail views (larger size).

```python
def zoom(self, factor: float) -> NoiseSample
```
Sample a different-sized world region at the same output size.
- `factor > 1.0`: Zoom in (smaller world region, more detail)
- `factor < 1.0`: Zoom out (larger world region, overview)

---

### mcrfpy.BSP

Binary space partition tree for rectangular regions. Useful for dungeon rooms, zones, or any hierarchical spatial organization.

#### Constructor

```python
BSP(bounds: tuple[tuple[int, int], tuple[int, int]])
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `bounds` | `((x, y), (w, h))` | Position and size of the root region. |

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `bounds` | `((x, y), (w, h))` | Read-only. Root node bounds. |
| `root` | `BSPNode` | Read-only. Reference to the root node. |

#### Splitting

```python
def split_once(self, horizontal: bool, position: int) -> BSP
```
Split the root node once. Returns self for chaining.

```python
def split_recursive(self,
                    depth: int,
                    min_size: tuple[int, int],
                    max_ratio: float = 1.5,
                    seed: int = None) -> BSP
```
Recursively split to the specified depth.

| Parameter | Type | Description |
|-----------|------|-------------|
| `depth` | `int` | Maximum recursion depth. Creates up to 2^depth leaves. |
| `min_size` | `(int, int)` | Minimum (width, height) for a node to be split. |
| `max_ratio` | `float` | Maximum aspect ratio before forcing split direction. Default: 1.5. |
| `seed` | `int` | Random seed. None for random. |

```python
def clear(self) -> BSP
```
Remove all children, keeping only the root node with original bounds.

#### Iteration

```python
def leaves(self) -> Iterator[BSPNode]
```
Iterate all leaf nodes (the actual rooms).

```python
def traverse(self, order: Traversal = Traversal.LEVEL_ORDER) -> Iterator[BSPNode]
```
Iterate all nodes in the specified order.

#### Queries

```python
def find(self, pos: tuple[int, int]) -> BSPNode
```
Find the smallest (deepest) node containing the position.

```python
def find_path(self, start: BSPNode, end: BSPNode) -> tuple[BSPNode, ...]
```
Find a sequence of sibling-connected nodes between start and end leaves. Useful for corridor generation.

#### HeightMap Generation

```python
def to_heightmap(self,
                 size: tuple[int, int] = None,
                 select: str = "leaves",
                 nodes: list[BSPNode] = None,
                 shrink: int = 0,
                 value: float = 1.0) -> BSPMap
```
Create a BSPMap (HeightMap subclass) from selected nodes.

| Parameter | Type | Description |
|-----------|------|-------------|
| `size` | `(int, int)` | Output size. Default: bounds size. |
| `select` | `str` | `"leaves"`, `"all"`, or `"internal"`. Default: `"leaves"`. |
| `nodes` | `list[BSPNode]` | Override: specific nodes only. |
| `shrink` | `int` | Pixels to shrink from each node's bounds. Default: 0. |
| `value` | `float` | Value inside selected regions. Default: 1.0. |

---

### mcrfpy.BSPNode

A lightweight reference to a node in a BSP tree. Read-only.

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `bounds` | `((x, y), (w, h))` | Position and size of this node. |
| `level` | `int` | Depth in tree (0 for root). |
| `index` | `int` | Unique index within the tree. |
| `is_leaf` | `bool` | True if this node has no children. |
| `split_horizontal` | `bool \| None` | Split orientation. None if leaf. |
| `split_position` | `int \| None` | Split coordinate. None if leaf. |

#### Navigation

| Property | Type | Description |
|----------|------|-------------|
| `left` | `BSPNode \| None` | Left child, or None if leaf. |
| `right` | `BSPNode \| None` | Right child, or None if leaf. |
| `parent` | `BSPNode \| None` | Parent node, or None if root. |
| `sibling` | `BSPNode \| None` | Other child of parent, or None. |

#### Methods

```python
def contains(self, pos: tuple[int, int]) -> bool
```
Check if position is inside this node's bounds.

```python
def center(self) -> tuple[int, int]
```
Return the center point of this node's bounds.

---

### mcrfpy.BSPMap

A HeightMap created from BSP node selection. Tracks its origin for convenient re-querying.

#### Inheritance

`BSPMap` extends `HeightMap` - all HeightMap methods are available.

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `bsp` | `BSP` | Read-only. The tree that created this map. |
| `nodes` | `tuple[BSPNode, ...]` | Read-only. Nodes represented in this map. |
| `shrink` | `int` | Read-only. Margin applied from bounds. |

#### BSP-Specific Operations

```python
def inverse(self) -> BSPMap
```
Return a new BSPMap with walls instead of rooms (inverts the selection within BSP bounds).

```python
def expand(self, amount: int = 1) -> BSPMap
```
Return a new BSPMap with node bounds grown by amount.

```python
def contract(self, amount: int = 1) -> BSPMap
```
Return a new BSPMap with node bounds shrunk by additional amount.

#### Re-querying

```python
def with_nodes(self, nodes: list[BSPNode]) -> BSPMap
```
Return a new BSPMap with different node selection.

```python
def with_shrink(self, shrink: int) -> BSPMap
```
Return a new BSPMap with different shrink value.

---

### mcrfpy.Traversal

Enumeration for BSP tree traversal orders.

```python
class Traversal(Enum):
    PRE_ORDER = "pre"           # Node, then left, then right
    IN_ORDER = "in"             # Left, then node, then right
    POST_ORDER = "post"         # Left, then right, then node
    LEVEL_ORDER = "level"       # Top to bottom, left to right
    INVERTED_LEVEL_ORDER = "level_inverted"  # Bottom to top, right to left
```

---

## Application to Grid and Layers

### Grid.apply_threshold

```python
def apply_threshold(self,
                    source: HeightMap,
                    range: tuple[float, float],
                    walkable: bool = None,
                    transparent: bool = None) -> Grid
```
Set walkable/transparent properties where source value is in range.

| Parameter | Type | Description |
|-----------|------|-------------|
| `source` | `HeightMap` | Must match grid size. |
| `range` | `(float, float)` | (min, max) inclusive range. |
| `walkable` | `bool \| None` | Set walkable to this value. None = don't change. |
| `transparent` | `bool \| None` | Set transparent to this value. None = don't change. |

### Grid.apply_ranges

```python
def apply_ranges(self,
                 source: HeightMap,
                 ranges: list[tuple]) -> Grid
```
Apply multiple thresholds in a single pass.

```python
# Example
grid.apply_ranges(terrain, [
    ((0.0, 0.3), {"walkable": False, "transparent": True}),   # Water
    ((0.3, 0.8), {"walkable": True, "transparent": True}),    # Land
    ((0.8, 1.0), {"walkable": False, "transparent": False}),  # Mountains
])
```

### TileLayer.apply_threshold

```python
def apply_threshold(self,
                    source: HeightMap,
                    range: tuple[float, float],
                    tile: int) -> TileLayer
```
Set tile index where source value is in range.

### TileLayer.apply_ranges

```python
def apply_ranges(self,
                 source: HeightMap,
                 ranges: list[tuple]) -> TileLayer
```
Apply multiple tile assignments in a single pass.

```python
# Example
tiles.apply_ranges(terrain, [
    ((0.0, 0.2), DEEP_WATER),
    ((0.2, 0.3), SHALLOW_WATER),
    ((0.3, 0.5), SAND),
    ((0.5, 0.7), GRASS),
    ((0.7, 0.85), ROCK),
    ((0.85, 1.0), SNOW),
])
```

### ColorLayer.apply_threshold

```python
def apply_threshold(self,
                    source: HeightMap,
                    range: tuple[float, float],
                    color: tuple[int, ...]) -> ColorLayer
```
Set fixed color where source value is in range. Color is (R, G, B) or (R, G, B, A).

### ColorLayer.apply_gradient

```python
def apply_gradient(self,
                   source: HeightMap,
                   range: tuple[float, float],
                   color_low: tuple[int, ...],
                   color_high: tuple[int, ...]) -> ColorLayer
```
Interpolate between colors based on source value within range.
- At range minimum → color_low
- At range maximum → color_high

### ColorLayer.apply_ranges

```python
def apply_ranges(self,
                 source: HeightMap,
                 ranges: list[tuple]) -> ColorLayer
```
Apply multiple color assignments. Each range maps to either a fixed color or a gradient.

```python
# Example
colors.apply_ranges(terrain, [
    ((0.0, 0.3), (0, 0, 180)),                        # Fixed blue
    ((0.3, 0.7), ((50, 120, 50), (100, 200, 100))),  # Gradient green (tuple of 2)
    ((0.7, 1.0), ((100, 100, 100), (255, 255, 255))), # Gradient gray to white
])
```

---

## Usage Examples

### Example 1: Simple Dungeon

```python
import mcrfpy

# Create BSP dungeon layout
bsp = mcrfpy.BSP(bounds=((0, 0), (80, 50)))
bsp.split_recursive(depth=4, min_size=(6, 6), max_ratio=1.5)

# Generate room mask (1.0 inside rooms, 0.0 in walls)
rooms = bsp.to_heightmap(select="leaves", shrink=1)

# Apply to grid
grid.apply_threshold(rooms, range=(0.5, 1.0), walkable=True, transparent=True)

# Apply floor tiles
tiles.apply_threshold(rooms, range=(0.5, 1.0), tile=FLOOR_TILE)

# Walls are left as default (not in threshold range)
```

### Example 2: Natural Caves

```python
import mcrfpy

# Create noise generator
noise = mcrfpy.NoiseSource(algorithm="simplex", seed=42)

# Sample onto heightmap
cave = noise.sample(
    size=(100, 100),
    world_region=((0, 0), (10, 10)),  # 10x zoom for smooth features
    mode="fbm",
    octaves=4
)
cave.normalize()

# Open areas where noise > 0.45
grid.apply_threshold(cave, range=(0.45, 1.0), walkable=True, transparent=True)
tiles.apply_threshold(cave, range=(0.45, 1.0), tile=CAVE_FLOOR)
tiles.apply_threshold(cave, range=(0.0, 0.45), tile=CAVE_WALL)
```

### Example 3: Overworld with Rivers

```python
import mcrfpy

# Base terrain
terrain = mcrfpy.HeightMap(size=(200, 200))
terrain.mid_point_displacement(roughness=0.5)

# Add hills
terrain.add_hill(center=(50, 80), radius=20, height=0.4)
terrain.add_hill(center=(150, 120), radius=25, height=0.5)

# Carve river
terrain.dig_bezier(
    points=((10, 100), (60, 80), (140, 120), (190, 100)),
    start_radius=2, end_radius=5,
    start_depth=0.5, end_depth=0.5
)

# Erosion for realism
terrain.rain_erosion(drops=8000)
terrain.normalize()

# Apply terrain bands
grid.apply_ranges(terrain, [
    ((0.0, 0.25), {"walkable": False, "transparent": True}),   # Water
    ((0.25, 0.75), {"walkable": True, "transparent": True}),   # Land
    ((0.75, 1.0), {"walkable": False, "transparent": False}),  # Mountains
])

tiles.apply_ranges(terrain, [
    ((0.0, 0.25), WATER_TILE),
    ((0.25, 0.4), SAND_TILE),
    ((0.4, 0.65), GRASS_TILE),
    ((0.65, 0.8), ROCK_TILE),
    ((0.8, 1.0), SNOW_TILE),
])

colors.apply_ranges(terrain, [
    ((0.0, 0.25), ((0, 50, 150), (0, 100, 200))),
    ((0.25, 0.65), ((80, 160, 80), (120, 200, 120))),
    ((0.65, 1.0), ((120, 120, 120), (255, 255, 255))),
])
```

### Example 4: Dungeon with Varied Room Terrain

```python
import mcrfpy

# Create dungeon structure
bsp = mcrfpy.BSP(bounds=((0, 0), (100, 100)))
bsp.split_recursive(depth=5, min_size=(8, 8))

# Room mask
rooms = bsp.to_heightmap(select="leaves", shrink=1)

# Create terrain variation
noise = mcrfpy.NoiseSource(seed=123)
terrain = mcrfpy.HeightMap(size=(100, 100))
terrain.add_noise(noise, mode="fbm", octaves=4)
terrain.normalize()

# Mask terrain to rooms only
terrain.multiply(rooms)

# Apply varied floor tiles within rooms
tiles.apply_threshold(rooms, range=(0.5, 1.0), tile=STONE_FLOOR)  # Base floor
tiles.apply_threshold(terrain, range=(0.3, 0.5), tile=MOSSY_FLOOR)
tiles.apply_threshold(terrain, range=(0.5, 0.7), tile=CRACKED_FLOOR)

# Walkability from rooms mask
grid.apply_threshold(rooms, range=(0.5, 1.0), walkable=True, transparent=True)
```

### Example 5: Infinite World with Chunks

```python
import mcrfpy

# Persistent world generator
WORLD_SEED = 12345
world_noise = mcrfpy.NoiseSource(seed=WORLD_SEED)

CHUNK_SIZE = 64

def generate_chunk(chunk_x: int, chunk_y: int) -> mcrfpy.NoiseSample:
    """Generate terrain for a world chunk."""
    return world_noise.sample(
        size=(CHUNK_SIZE, CHUNK_SIZE),
        world_region=(
            (chunk_x * CHUNK_SIZE, chunk_y * CHUNK_SIZE),
            ((chunk_x + 1) * CHUNK_SIZE, (chunk_y + 1) * CHUNK_SIZE)
        ),
        mode="fbm",
        octaves=6
    )

# Generate current chunk
current_chunk = generate_chunk(0, 0)

# When player moves right, get adjacent chunk
next_chunk = current_chunk.next_right()

# Generate minimap of large area
minimap = world_noise.sample(
    size=(100, 100),
    world_region=((0, 0), (1000, 1000)),
    mode="fbm",
    octaves=3
)
```

### Example 6: Biome Blending

```python
import mcrfpy

# Multiple noise layers
elevation_noise = mcrfpy.NoiseSource(seed=1)
moisture_noise = mcrfpy.NoiseSource(seed=2)

# Sample both
elevation = mcrfpy.HeightMap(size=(200, 200))
elevation.add_noise(elevation_noise, mode="fbm", octaves=6)
elevation.normalize()

moisture = mcrfpy.HeightMap(size=(200, 200))
moisture.add_noise(moisture_noise, mode="fbm", octaves=4)
moisture.normalize()

# Desert: low moisture AND medium elevation
desert_mask = moisture.threshold((0.0, 0.3))
desert_mask.multiply(elevation.threshold((0.2, 0.6)))

# Forest: high moisture AND low elevation
forest_mask = moisture.threshold((0.6, 1.0))
forest_mask.multiply(elevation.threshold((0.1, 0.5)))

# Swamp: high moisture AND very low elevation
swamp_mask = moisture.threshold((0.7, 1.0))
swamp_mask.multiply(elevation.threshold((0.0, 0.2)))

# Apply biome tiles (later biomes override earlier)
tiles.apply_threshold(elevation, range=(0.0, 1.0), tile=GRASS_TILE)  # Default
tiles.apply_threshold(desert_mask, range=(0.5, 1.0), tile=SAND_TILE)
tiles.apply_threshold(forest_mask, range=(0.5, 1.0), tile=TREE_TILE)
tiles.apply_threshold(swamp_mask, range=(0.5, 1.0), tile=SWAMP_TILE)
```

---

## Implementation Notes

### Size Matching

All HeightMap operations between two heightmaps require matching sizes. The `apply_*` methods on Grid/Layer also require the source HeightMap to match the Grid's `grid_size`.

```python
# This will raise ValueError
small = mcrfpy.HeightMap(size=(50, 50))
large = mcrfpy.HeightMap(size=(100, 100))
large.add(small)  # Error: size mismatch
```

### Value Ranges

- NoiseSource outputs: -1.0 to 1.0
- HeightMap after `normalize()`: 0.0 to 1.0 (by default)
- Threshold operations: work on any float range

Recommendation: Always `normalize()` before applying to Grid/Layer for predictable threshold behavior.

### Performance Considerations

For grids up to 1000×1000 (1M cells):

| Operation | Approximate Cost |
|-----------|------------------|
| HeightMap creation | O(n) |
| add/multiply/scale | O(n), parallelizable |
| add_noise | O(n × octaves), parallelizable |
| mid_point_displacement | O(n log n) |
| rain_erosion | O(drops) |
| apply_ranges | O(n × num_ranges), single pass |

All operations execute entirely in C++ with no Python callbacks.

---

## Future Considerations

The following features are explicitly **out of scope** for the initial implementation but should not be precluded by the design:

1. **Serialization**: Saving/loading HeightMaps to disk for pre-generated worlds.

2. **Region Operations**: Applying operations to sub-regions when HeightMap sizes don't match.

3. **Corridor Generation**: Built-in BSP corridor creation (currently user code using `find_path` and `dig_bezier` or manual fills).

4. **Custom Kernels**: User-defined kernel transforms beyond simple smoothing.

---

## Appendix: libtcod Function Mapping

| libtcod Function | McRogueFace Equivalent |
|------------------|------------------------|
| `TCOD_noise_new` | `NoiseSource()` |
| `TCOD_noise_get` | `NoiseSource.get()` |
| `TCOD_noise_get_fbm` | `NoiseSource.fbm()` |
| `TCOD_noise_get_turbulence` | `NoiseSource.turbulence()` |
| `TCOD_heightmap_new` | `HeightMap()` |
| `TCOD_heightmap_add_hill` | `HeightMap.add_hill()` |
| `TCOD_heightmap_dig_hill` | `HeightMap.dig_hill()` |
| `TCOD_heightmap_rain_erosion` | `HeightMap.rain_erosion()` |
| `TCOD_heightmap_add_voronoi` | `HeightMap.add_voronoi()` |
| `TCOD_heightmap_mid_point_displacement` | `HeightMap.mid_point_displacement()` |
| `TCOD_heightmap_dig_bezier` | `HeightMap.dig_bezier()` |
| `TCOD_heightmap_add_fbm` | `HeightMap.add_noise(..., mode="fbm")` |
| `TCOD_heightmap_scale_fbm` | `HeightMap.multiply_noise(..., mode="fbm")` |
| `TCOD_heightmap_normalize` | `HeightMap.normalize()` |
| `TCOD_heightmap_clamp` | `HeightMap.clamp()` |
| `TCOD_heightmap_add` | `HeightMap.add()` |
| `TCOD_heightmap_multiply` | `HeightMap.multiply()` |
| `TCOD_heightmap_lerp` | `HeightMap.lerp()` |
| `TCOD_bsp_new_with_size` | `BSP()` |
| `TCOD_bsp_split_once` | `BSP.split_once()` |
| `TCOD_bsp_split_recursive` | `BSP.split_recursive()` |
| `TCOD_bsp_traverse_*` | `BSP.traverse(order=...)` |
| `TCOD_bsp_is_leaf` | `BSPNode.is_leaf` |
| `TCOD_bsp_contains` | `BSPNode.contains()` |
| `TCOD_bsp_find_node` | `BSP.find()` |
