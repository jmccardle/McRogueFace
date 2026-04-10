# McRogueFace Python API Consistency Audit

**Date**: 2026-04-09
**Version**: 0.2.6-prerelease
**Purpose**: Catalog the full public API surface, identify inconsistencies and issues before 1.0 API freeze.

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Module-Level API](#module-level-api)
3. [Core Value Types](#core-value-types)
4. [UI Drawable Types](#ui-drawable-types)
5. [Grid System](#grid-system)
6. [Entity System](#entity-system)
7. [Collections](#collections)
8. [Audio Types](#audio-types)
9. [Procedural Generation](#procedural-generation)
10. [Pathfinding](#pathfinding)
11. [Shader System](#shader-system)
12. [Tiled/LDtk Import](#tiledldtk-import)
13. [3D/Experimental Types](#3dexperimental-types)
14. [Enums](#enums)
15. [Findings: Naming Inconsistencies](#findings-naming-inconsistencies)
16. [Findings: Missing Functionality](#findings-missing-functionality)
17. [Findings: Deprecations to Resolve](#findings-deprecations-to-resolve)
18. [Findings: Documentation Gaps](#findings-documentation-gaps)
19. [Recommendations](#recommendations)

---

## Executive Summary

The McRogueFace Python API exposes **44 exported types**, **14 internal types**, **10 enums**, **13 module-level functions**, **7 module-level properties**, and **5 singleton instances** through the `mcrfpy` module.

Overall, the API is remarkably consistent. Properties and methods use snake_case throughout the type system. The major inconsistencies are concentrated in a few areas:

1. **4 module-level functions use camelCase** (`setScale`, `findAll`, `getMetrics`, `setDevConsole`)
2. **Terse/placeholder docstrings** on 5 core types (Vector, Font, Texture, GridPoint, GridPointState)
3. **Deprecated property aliases** still exposed (`sprite_number`)
4. **Color property naming split**: some types use `fill_color`/`outline_color`, others use `color`
5. **Redundant position aliases** on Entity (`grid_pos` vs `cell_pos` for the same data)

---

## Module-Level API

### Functions (`mcrfpy.*`)

| Function | Signature | Notes |
|----------|-----------|-------|
| `step` | `(dt: float = None) -> float` | Advance simulation (headless mode) |
| `exit` | `() -> None` | Shutdown engine |
| `find` | `(name: str, scene: str = None) -> Drawable \| None` | Find UI element by name |
| `lock` | `() -> _LockContext` | Thread-safe UI update context manager |
| `bresenham` | `(start, end, *, include_start=True, include_end=True) -> list[tuple]` | Line algorithm |
| `start_benchmark` | `() -> None` | Begin benchmark capture |
| `end_benchmark` | `() -> str` | End benchmark, return filename |
| `log_benchmark` | `(message: str) -> None` | Add benchmark annotation |
| `_sync_storage` | `() -> None` | WASM persistent storage flush |
| **`setScale`** | `(multiplier: float) -> None` | **CAMELCASE - deprecated** |
| **`findAll`** | `(pattern: str, scene: str = None) -> list` | **CAMELCASE** |
| **`getMetrics`** | `() -> dict` | **CAMELCASE** |
| **`setDevConsole`** | `(enabled: bool) -> None` | **CAMELCASE** |

### Properties (`mcrfpy.*`)

| Property | Type | Writable | Notes |
|----------|------|----------|-------|
| `current_scene` | `Scene \| None` | Yes | Active scene |
| `scenes` | `dict[str, Scene]` | No | All registered scenes |
| `timers` | `list[Timer]` | No | Active timers |
| `animations` | `list[Animation]` | No | Active animations |
| `default_transition` | `Transition` | Yes | Scene transition effect |
| `default_transition_duration` | `float` | Yes | Transition duration |
| `save_dir` | `str` | No | Platform-specific save path |

### Singletons

| Name | Type | Notes |
|------|------|-------|
| `keyboard` | `Keyboard` | Modifier key state |
| `mouse` | `Mouse` | Position and button state |
| `window` | `Window` | Window properties |
| `default_font` | `Font` | JetBrains Mono |
| `default_texture` | `Texture` | Kenney Tiny Dungeon (16x16) |

### Constants

| Name | Type | Value |
|------|------|-------|
| `__version__` | `str` | Build version string |
| `default_fov` | `FOV` | `FOV.BASIC` |

### Submodules

| Name | Contents |
|------|----------|
| `automation` | Screenshot, click simulation, testing utilities |

---

## Core Value Types

### `Color`

```
Color(r: int = 0, g: int = 0, b: int = 0, a: int = 255)
```

| Properties | Type | R/W |
|-----------|------|-----|
| `r`, `g`, `b`, `a` | int (0-255) | R/W |

| Methods | Signature |
|---------|-----------|
| `from_hex` | `(cls, hex_string: str) -> Color` (classmethod) |
| `to_hex` | `() -> str` |
| `lerp` | `(other: Color, t: float) -> Color` |

Protocols: `__repr__`, `__hash__`

### `Vector`

```
Vector(x: float = 0, y: float = 0)
```

| Properties | Type | R/W |
|-----------|------|-----|
| `x`, `y` | float | R/W |
| `int` | tuple[int, int] | R |

| Methods | Signature |
|---------|-----------|
| `magnitude` | `() -> float` |
| `magnitude_squared` | `() -> float` |
| `normalize` | `() -> Vector` |
| `dot` | `(other: Vector) -> float` |
| `distance_to` | `(other: Vector) -> float` |
| `angle` | `() -> float` |
| `copy` | `() -> Vector` |
| `floor` | `() -> Vector` |

Protocols: `__repr__`, `__hash__`, `__eq__`/`__ne__`, arithmetic (`+`, `-`, `*`, `/`, `-x`, `abs`), sequence (`len`, `[0]`/`[1]`)

### `Font`

```
Font(filename: str)
```

| Properties | Type | R/W |
|-----------|------|-----|
| `family` | str | R |
| `source` | str | R |

Methods: None
Protocols: `__repr__`

### `Texture`

```
Texture(filename: str, sprite_width: int, sprite_height: int)
```

| Properties | Type | R/W |
|-----------|------|-----|
| `sprite_width`, `sprite_height` | int | R |
| `sheet_width`, `sheet_height` | int | R |
| `sprite_count` | int | R |
| `source` | str | R |

| Methods | Signature |
|---------|-----------|
| `from_bytes` | `(cls, data, w, h, sprite_w, sprite_h, name=...) -> Texture` (classmethod) |
| `composite` | `(cls, layers, sprite_w, sprite_h, name=...) -> Texture` (classmethod) |
| `hsl_shift` | `(hue_shift, sat_shift=0, lit_shift=0) -> Texture` |

Protocols: `__repr__`, `__hash__`

---

## UI Drawable Types

### Base: `Drawable` (abstract)

Cannot be instantiated directly.

| Properties | Type | R/W | Notes |
|-----------|------|-----|-------|
| `on_click` | callable | R/W | `(pos, button, action)` |
| `z_index` | int | R/W | Render order |
| `visible` | bool | R/W | |
| `opacity` | float | R/W | 0.0-1.0 |
| `name` | str | R/W | |
| `pos` | Vector | R/W | |
| `parent` | Drawable | R | |
| `align` | Alignment | R/W | |
| `margin`, `horiz_margin`, `vert_margin` | float | R/W | |
| `shader` | Shader | R/W | |
| `uniforms` | UniformCollection | R | |
| `rotation` | float | R/W | |
| `origin` | Vector | R/W | |

| Methods | Signature |
|---------|-----------|
| `move` | `(dx, dy)` or `(delta)` |
| `resize` | `(w, h)` or `(size)` |
| `animate` | `(property, target, duration, easing, ...)` |

### `Frame`

```
Frame(pos=None, size=None, **kwargs)
```

Additional properties beyond Drawable:

| Properties | Type | R/W |
|-----------|------|-----|
| `x`, `y`, `w`, `h` | float | R/W |
| `fill_color` | Color | R/W |
| `outline_color` | Color | R/W |
| `outline` | float | R/W |
| `children` | UICollection | R |
| `clip_children` | bool | R/W |
| `cache_subtree` | bool | R/W |
| `grid_pos`, `grid_size` | Vector | R/W |

### `Caption`

```
Caption(pos=None, font=None, text='', **kwargs)
```

Additional properties beyond Drawable:

| Properties | Type | R/W |
|-----------|------|-----|
| `x`, `y` | float | R/W |
| `w`, `h` | float | R (computed) |
| `size` | Vector | R (computed) |
| `text` | str | R/W |
| `font_size` | float | R/W |
| `fill_color` | Color | R/W |
| `outline_color` | Color | R/W |
| `outline` | float | R/W |

### `Sprite`

```
Sprite(pos=None, texture=None, sprite_index=0, **kwargs)
```

Additional properties beyond Drawable:

| Properties | Type | R/W | Notes |
|-----------|------|-----|-------|
| `x`, `y` | float | R/W | |
| `w`, `h` | float | R (computed) | |
| `scale` | float | R/W | Uniform scale |
| `scale_x`, `scale_y` | float | R/W | Per-axis scale |
| `sprite_index` | int | R/W | |
| `sprite_number` | int | R/W | **DEPRECATED alias** |
| `texture` | Texture | R/W | |

### `Line`

```
Line(start=None, end=None, thickness=1.0, color=None, **kwargs)
```

| Properties | Type | R/W | Notes |
|-----------|------|-----|-------|
| `start` | Vector | R/W | |
| `end` | Vector | R/W | |
| `color` | Color | R/W | **Not `fill_color`** |
| `thickness` | float | R/W | |

### `Circle`

```
Circle(radius=0, center=None, fill_color=None, outline_color=None, outline=0, **kwargs)
```

| Properties | Type | R/W |
|-----------|------|-----|
| `radius` | float | R/W |
| `center` | Vector | R/W |
| `fill_color` | Color | R/W |
| `outline_color` | Color | R/W |
| `outline` | float | R/W |

### `Arc`

```
Arc(center=None, radius=0, start_angle=0, end_angle=90, color=None, thickness=1, **kwargs)
```

| Properties | Type | R/W | Notes |
|-----------|------|-----|-------|
| `center` | Vector | R/W | |
| `radius` | float | R/W | |
| `start_angle`, `end_angle` | float | R/W | Degrees |
| `color` | Color | R/W | **Not `fill_color`** |
| `thickness` | float | R/W | |

---

## Grid System

### `Grid` (also available as `GridView`)

```
Grid(grid_size=None, pos=None, size=None, texture=None, **kwargs)
```

| Properties | Type | R/W | Notes |
|-----------|------|-----|-------|
| `grid_size`, `grid_w`, `grid_h` | tuple/int | R | |
| `x`, `y`, `w`, `h` | float | R/W | |
| `pos`, `position` | Vector | R/W | `position` is redundant alias |
| `center` | Vector | R/W | Camera center (pixels) |
| `center_x`, `center_y` | float | R/W | |
| `zoom` | float | R/W | |
| `camera_rotation` | float | R/W | |
| `fill_color` | Color | R/W | |
| `texture` | Texture | R | |
| `entities` | EntityCollection | R | |
| `children` | UICollection | R | |
| `layers` | tuple | R | |
| `perspective`, `perspective_enabled` | various | R/W | |
| `fov`, `fov_radius` | various | R/W | |
| `on_cell_enter`, `on_cell_exit`, `on_cell_click` | callable | R/W | |
| `hovered_cell` | tuple | R | |
| `grid_data` | _GridData | R/W | Internal grid reference |

| Methods | Signature |
|---------|-----------|
| `at` | `(x, y)` or `(pos)` -> GridPoint |
| `compute_fov` | `(pos, radius, light_walls, algorithm)` |
| `is_in_fov` | `(pos) -> bool` |
| `find_path` | `(start, end, diagonal_cost, collide) -> AStarPath` |
| `get_dijkstra_map` | `(root, diagonal_cost, collide) -> DijkstraMap` |
| `clear_dijkstra_maps` | `()` |
| `add_layer` | `(layer)` |
| `remove_layer` | `(name_or_layer)` |
| `layer` | `(name) -> ColorLayer \| TileLayer` |
| `entities_in_radius` | `(pos, radius) -> list` |
| `center_camera` | `(pos)` -- tile coordinates |
| `apply_threshold` | `(source, range, walkable, transparent)` |
| `apply_ranges` | `(source, ranges)` |
| `step` | `(n, turn_order)` -- turn management |

### `GridPoint` (internal, returned by `Grid.at()`)

| Properties | Type | R/W |
|-----------|------|-----|
| `walkable` | bool | R/W |
| `transparent` | bool | R/W |
| `entities` | list | R |
| `grid_pos` | tuple | R |

Dynamic attributes: named layer data via `__getattr__`/`__setattr__`

### `GridPointState` (internal, returned by entity gridstate)

| Properties | Type | R/W |
|-----------|------|-----|
| `visible` | bool | R/W |
| `discovered` | bool | R/W |
| `point` | GridPoint | R |

### `ColorLayer`

```
ColorLayer(z_index=-1, name=None, grid_size=None)
```

| Properties | Type | R/W |
|-----------|------|-----|
| `z_index` | int | R/W |
| `visible` | bool | R/W |
| `grid_size` | tuple | R |
| `name` | str | R |
| `grid` | Grid | R/W |

| Methods | Signature |
|---------|-----------|
| `at` | `(x, y)` or `(pos) -> Color` |
| `set` | `(pos, color)` |
| `fill` | `(color)` |
| `fill_rect` | `(pos, size, color)` |
| `draw_fov` | `(source, radius, fov, visible, discovered, unknown)` |
| `apply_perspective` | `(entity, visible, discovered, unknown)` |
| `update_perspective` | `()` |
| `clear_perspective` | `()` |
| `apply_threshold` | `(source, range, color)` |
| `apply_gradient` | `(source, range, color_low, color_high)` |
| `apply_ranges` | `(source, ranges)` |

### `TileLayer`

```
TileLayer(z_index=-1, name=None, texture=None, grid_size=None)
```

| Properties | Type | R/W |
|-----------|------|-----|
| `z_index` | int | R/W |
| `visible` | bool | R/W |
| `texture` | Texture | R/W |
| `grid_size` | tuple | R |
| `name` | str | R |
| `grid` | Grid | R/W |

| Methods | Signature |
|---------|-----------|
| `at` | `(x, y)` or `(pos) -> int` |
| `set` | `(pos, index)` |
| `fill` | `(index)` |
| `fill_rect` | `(pos, size, index)` |
| `apply_threshold` | `(source, range, tile)` |
| `apply_ranges` | `(source, ranges)` |

---

## Entity System

### `Entity`

```
Entity(grid_pos=None, texture=None, sprite_index=0, **kwargs)
```

| Properties | Type | R/W | Notes |
|-----------|------|-----|-------|
| `pos`, `x`, `y` | Vector/float | R/W | Pixel position |
| `cell_pos`, `cell_x`, `cell_y` | Vector/int | R/W | Integer cell coords |
| `grid_pos`, `grid_x`, `grid_y` | Vector/int | R/W | **Same as cell_pos** |
| `draw_pos` | Vector | R/W | Fractional tile position |
| `sprite_index` | int | R/W | |
| `sprite_number` | int | R/W | **DEPRECATED alias** |
| `sprite_offset`, `sprite_offset_x`, `sprite_offset_y` | Vector/float | R/W | |
| `grid` | Grid | R/W | |
| `gridstate` | GridPointState | R | |
| `labels` | frozenset | R/W | |
| `step` | callable | R/W | Turn callback |
| `default_behavior` | Behavior | R/W | |
| `behavior_type` | Behavior | R | |
| `turn_order` | int | R/W | |
| `move_speed` | float | R/W | |
| `target_label` | str | R/W | |
| `sight_radius` | int | R/W | |
| `visible`, `opacity`, `name` | various | R/W | |
| `shader`, `uniforms` | various | R/W | |

| Methods | Signature |
|---------|-----------|
| `at` | `(x, y)` or `(pos) -> GridPoint` |
| `index` | `() -> int` |
| `die` | `()` |
| `path_to` | `(x, y)` or `(target) -> AStarPath` |
| `find_path` | `(target, diagonal_cost, collide) -> AStarPath` |
| `update_visibility` | `()` |
| `visible_entities` | `(fov, radius) -> list` |
| `animate` | `(property, target, duration, easing, ...)` |

---

## Collections

### `UICollection` (internal, returned by `Frame.children` / `Scene.children`)

| Methods | Signature |
|---------|-----------|
| `append` | `(element)` |
| `extend` | `(iterable)` |
| `insert` | `(index, element)` |
| `remove` | `(element)` |
| `pop` | `([index]) -> Drawable` |
| `index` | `(element) -> int` |
| `count` | `(element) -> int` |
| `find` | `(name, recursive=False) -> Drawable \| None` |

Protocols: `len`, `[]`, slicing, iteration

### `EntityCollection` (internal, returned by `Grid.entities`)

Same methods as UICollection. Protocols: `len`, `[]`, slicing, iteration.

---

## Audio Types

### `Sound`

```
Sound(source: str | SoundBuffer)
```

| Properties | Type | R/W |
|-----------|------|-----|
| `volume` | float (0-100) | R/W |
| `loop` | bool | R/W |
| `playing` | bool | R |
| `duration` | float | R |
| `source` | str | R |
| `pitch` | float | R/W |
| `buffer` | SoundBuffer | R |

| Methods | Signature |
|---------|-----------|
| `play` | `()` |
| `pause` | `()` |
| `stop` | `()` |
| `play_varied` | `(pitch_range=0.1, volume_range=3.0)` |

### `SoundBuffer`

```
SoundBuffer(filename: str)
```

| Properties | Type | R/W |
|-----------|------|-----|
| `duration` | float | R |
| `sample_count` | int | R |
| `sample_rate` | int | R |
| `channels` | int | R |
| `sfxr_params` | dict | R |

| Methods | Signature | Notes |
|---------|-----------|-------|
| `from_samples` | `(cls, data, channels, sample_rate) -> SoundBuffer` | classmethod |
| `tone` | `(cls, frequency, duration, waveform='sine', ...) -> SoundBuffer` | classmethod |
| `sfxr` | `(cls, preset, seed=None) -> SoundBuffer` | classmethod |
| `concat` | `(cls, buffers) -> SoundBuffer` | classmethod |
| `mix` | `(cls, buffers) -> SoundBuffer` | classmethod |
| `pitch_shift` | `(semitones) -> SoundBuffer` | returns new |
| `low_pass` | `(cutoff) -> SoundBuffer` | returns new |
| `high_pass` | `(cutoff) -> SoundBuffer` | returns new |
| `echo` | `(delay, decay) -> SoundBuffer` | returns new |
| `reverb` | `(room_size) -> SoundBuffer` | returns new |
| `distortion` | `(gain) -> SoundBuffer` | returns new |
| `bit_crush` | `(bits) -> SoundBuffer` | returns new |
| `gain` | `(amount) -> SoundBuffer` | returns new |
| `normalize` | `() -> SoundBuffer` | returns new |
| `reverse` | `() -> SoundBuffer` | returns new |
| `slice` | `(start, end) -> SoundBuffer` | returns new |
| `sfxr_mutate` | `(amount) -> SoundBuffer` | returns new |

### `Music`

```
Music(filename: str)
```

| Properties | Type | R/W |
|-----------|------|-----|
| `volume` | float (0-100) | R/W |
| `loop` | bool | R/W |
| `playing` | bool | R |
| `duration` | float | R |
| `position` | float | R/W |
| `source` | str | R |

| Methods | Signature |
|---------|-----------|
| `play` | `()` |
| `pause` | `()` |
| `stop` | `()` |

---

## Procedural Generation

### `HeightMap`

```
HeightMap(size: tuple[int, int], fill: float = 0.0)
```

| Properties | Type | R/W |
|-----------|------|-----|
| `size` | tuple | R |

46 methods covering: fill/clear, get/set (via `[]`), math operations, noise, erosion, BSP integration, kernel operations, binary operations.

Protocols: `[x, y]` subscript (get/set)

### `DiscreteMap`

```
DiscreteMap(size: tuple[int, int], fill: int = 0, enum: type[IntEnum] = None)
```

| Properties | Type | R/W |
|-----------|------|-----|
| `size` | tuple | R |
| `enum_type` | type | R/W |

22 methods covering: fill/clear, get/set (via `[]`), math, bitwise, statistics, conversion.

Protocols: `[x, y]` subscript (get/set)

### `BSP`

```
BSP(pos: tuple[int, int], size: tuple[int, int])
```

| Properties | Type | R/W |
|-----------|------|-----|
| `bounds`, `pos`, `size` | tuple | R |
| `root` | BSPNode | R |
| `adjacency` | BSPAdjacency | R |

| Methods | Signature |
|---------|-----------|
| `split_once` | `(...)` |
| `split_recursive` | `(...)` |
| `clear` | `()` |
| `leaves` | `() -> list[BSPNode]` |
| `traverse` | `(order) -> BSPIter` |
| `find` | `(pos) -> BSPNode` |
| `get_leaf` | `(index) -> BSPNode` |
| `to_heightmap` | `() -> HeightMap` |

### `NoiseSource`

```
NoiseSource(dimensions=2, algorithm='simplex', hurst=0.5, lacunarity=2.0, seed=None)
```

| Properties | Type | R/W |
|-----------|------|-----|
| `dimensions`, `algorithm`, `hurst`, `lacunarity`, `seed` | various | R |

| Methods | Signature |
|---------|-----------|
| `get` | `(pos) -> float` |
| `fbm` | `(pos, octaves=4) -> float` |
| `turbulence` | `(pos, octaves=4) -> float` |
| `sample` | `(size, world_origin, world_size, mode, octaves) -> HeightMap` |

---

## Pathfinding

### `AStarPath`

| Properties | Type | R/W |
|-----------|------|-----|
| `origin` | tuple | R |
| `destination` | tuple | R |
| `remaining` | int | R |

| Methods | Signature |
|---------|-----------|
| `walk` | `() -> tuple` |
| `peek` | `() -> tuple` |

Protocols: `len`, `bool`, iteration

### `DijkstraMap`

| Properties | Type | R/W |
|-----------|------|-----|
| `root` | tuple | R |

| Methods | Signature |
|---------|-----------|
| `distance` | `(x, y) -> float` |
| `path_from` | `(x, y) -> list` |
| `step_from` | `(x, y) -> tuple` |
| `to_heightmap` | `() -> HeightMap` |

---

## Shader System

### `Shader`

```
Shader(fragment_source: str, dynamic: bool = False)
```

| Properties | Type | R/W |
|-----------|------|-----|
| `dynamic` | bool | R/W |
| `source` | str | R |
| `is_valid` | bool | R |

| Methods | Signature |
|---------|-----------|
| `set_uniform` | `(name: str, value: float \| tuple)` |

### `PropertyBinding`

```
PropertyBinding(target: Drawable, property: str)
```

| Properties | Type | R/W |
|-----------|------|-----|
| `target` | Drawable | R |
| `property` | str | R |
| `value` | float | R |
| `is_valid` | bool | R |

### `CallableBinding`

```
CallableBinding(callable: Callable[[], float])
```

| Properties | Type | R/W |
|-----------|------|-----|
| `callable` | callable | R |
| `value` | float | R |
| `is_valid` | bool | R |

### `UniformCollection` (internal, returned by `drawable.uniforms`)

Dict-like container. Supports `[]`, `del`, `in`, `keys()`, `values()`, `items()`, `clear()`.

---

## Tiled/LDtk Import

### `TileSetFile`

```
TileSetFile(path: str)
```

Properties (all R): `name`, `tile_width`, `tile_height`, `tile_count`, `columns`, `margin`, `spacing`, `image_source`, `properties`, `wang_sets`

Methods: `to_texture()`, `tile_info(id)`, `wang_set(name)`

### `TileMapFile`

```
TileMapFile(path: str)
```

Properties (all R): `width`, `height`, `tile_width`, `tile_height`, `orientation`, `properties`, `tileset_count`, `tile_layer_names`, `object_layer_names`

Methods: `tileset(index)`, `tile_layer_data(name)`, `resolve_gid(gid)`, `object_layer(name)`, `apply_to_tile_layer(layer, name)`

### `WangSet` (factory-created from TileSetFile)

Properties (all R): `name`, `type`, `color_count`, `colors`

Methods: `terrain_enum()`, `resolve(discrete_map)`, `apply(discrete_map, tile_layer)`

### `LdtkProject`

```
LdtkProject(path: str)
```

Properties (all R): `version`, `tileset_names`, `ruleset_names`, `level_names`, `enums`

Methods: `tileset(name)`, `ruleset(name)`, `level(name)`

### `AutoRuleSet` (factory-created from LdtkProject)

Properties (all R): `name`, `grid_size`, `value_count`, `values`, `rule_count`, `group_count`

Methods: `terrain_enum()`, `resolve(discrete_map)`, `apply(discrete_map, tile_layer)`

---

## 3D/Experimental Types

> These are exempt from the 1.0 API freeze per ROADMAP.md.

Viewport3D, Entity3D, EntityCollection3D, Model3D, Billboard, VoxelGrid, VoxelRegion, VoxelPoint, Camera3D (via Viewport3D properties).

---

## Enums

| Enum | Values | Notes |
|------|--------|-------|
| `Key` | 42+ keyboard keys | Legacy string comparison (`Key.ESCAPE == "Escape"`) |
| `InputState` | `PRESSED`, `RELEASED` | Legacy: `"start"`, `"end"` |
| `MouseButton` | `LEFT`, `RIGHT`, `MIDDLE`, `X1`, `X2` | Legacy: `"left"`, `"right"`, `"middle"` |
| `Easing` | 32 easing functions | Linear, Quad, Cubic, etc. |
| `Transition` | Scene transition effects | |
| `Traversal` | BSP traversal orders | |
| `Alignment` | 9 positions + NONE | TOP_LEFT through BOTTOM_RIGHT |
| `Behavior` | 11 entity behaviors | For `grid.step()` turn system |
| `Trigger` | 3 trigger types | Entity step callbacks |
| `FOV` | FOV algorithms | Maps to libtcod |

---

## Findings: Naming Inconsistencies

### F1: Module-level camelCase functions (CRITICAL)

Four module-level functions use camelCase while everything else uses snake_case:

| Current | Should Be | Status |
|---------|-----------|--------|
| `setScale` | `set_scale` | Deprecated anyway (use `Window.resolution`) |
| `findAll` | `find_all` | Active, needs alias |
| `getMetrics` | `get_metrics` | Active, needs alias |
| `setDevConsole` | `set_dev_console` | Active, needs alias |

**Resolution**: Add snake_case aliases. Keep camelCase temporarily for backward compatibility. Remove camelCase in 1.0.

### F2: Color property naming split

Filled shapes (Frame, Caption, Circle) use `fill_color`/`outline_color`. Stroke-only shapes (Line, Arc) use `color`. This is actually semantically correct -- Line and Arc don't have a "fill" concept. **No change needed**, but worth documenting.

### F3: Redundant Entity position aliases

Entity exposes the same cell position data under two names:
- `grid_pos`, `grid_x`, `grid_y`
- `cell_pos`, `cell_x`, `cell_y`

Both exist because `grid_pos` is the constructor parameter name and `cell_pos` is more descriptive. **Recommendation**: Keep both but document `grid_pos` as the canonical name (matches constructor).

### F4: Grid `position` alias

`Grid.position` is a redundant alias for `Grid.pos`. All other types use only `pos`. **Recommendation**: Deprecate `position`, keep `pos`.

### F5: Iterator type naming

- `UICollectionIter` -- has "UI" prefix
- `UIEntityCollectionIter` -- has "UI" prefix
- `EntityCollection3DIter` -- no "UI" prefix

The "UI" prefix is an internal detail leaking into type names. Since these are internal types (not exported), this is cosmetic but worth noting.

---

## Findings: Missing Functionality

### F6: No `__eq__` on Color

`Color` has `__hash__` but no `__eq__`/`__ne__`. Two colors with the same RGBA values may not compare equal. This is a bug.

### F7: No `Music.pitch`

`Sound` has a `pitch` property but `Music` does not, despite SFML supporting it. Minor omission.

### F8: No `Font` methods

`Font` has no methods at all -- not even a way to query available sizes or get text metrics. This limits text layout capabilities.

### F9: GridPoint has no `__init__`

`GridPoint` cannot be constructed from Python (`tp_new = NULL`). This is intentional (it's a view into grid data) but should be clearly documented.

### F10: Animation direct construction deprecated but not marked

The `Animation` class can still be instantiated directly even though `.animate()` on drawables is preferred. No deprecation warning is emitted.

---

## Findings: Deprecations to Resolve

### F11: `sprite_number` on Sprite and Entity

Both types expose `sprite_number` as a deprecated alias for `sprite_index`. This should be removed before 1.0.

### F12: `setScale` module function

Deprecated in favor of `Window.resolution`. Should be removed before 1.0.

### F13: Legacy string enum comparisons

`Key`, `InputState`, `MouseButton` support comparing to legacy string values (e.g., `Key.ESCAPE == "Escape"`, `InputState.PRESSED == "start"`). This backward compatibility layer should be removed before 1.0.

---

## Findings: Documentation Gaps

### F14: Terse docstrings on core types

Several types have placeholder-quality `tp_doc` strings:

| Type | Current tp_doc | Should be |
|------|---------------|-----------|
| `Vector` | `"SFML Vector Object"` | Full constructor docs with args |
| `Font` | `"SFML Font Object"` | Full constructor docs |
| `Texture` | `"SFML Texture Object"` | Full constructor docs |
| `GridPoint` | `"UIGridPoint object"` | Description of purpose and access pattern |
| `GridPointState` | `"UIGridPointState object"` | Description of purpose |

### F15: Missing MCRF_* macro usage

Some types use raw string docstrings for methods instead of MCRF_METHOD macros. This means the documentation pipeline may miss them.

---

## Recommendations

### Before 1.0 (Breaking Changes)

1. **Remove camelCase functions**: `setScale`, `findAll`, `getMetrics`, `setDevConsole`
2. **Remove `sprite_number`** deprecated alias from Sprite and Entity
3. **Remove legacy string enum comparisons** from Key, InputState, MouseButton
4. **Remove `Grid.position`** redundant alias (keep `pos`)
5. **Add `__eq__`/`__ne__` to Color** type

### Immediate (Non-Breaking)

1. **Add snake_case aliases** for the 4 camelCase module functions
2. **Improve docstrings** on Vector, Font, Texture, GridPoint, GridPointState
3. **Document `grid_pos` vs `cell_pos`** -- state that `grid_pos` is canonical

### Future Considerations

1. Add `pitch` to `Music`
2. Add basic text metrics to `Font`
3. Consider deprecation warnings for `Animation()` direct construction
4. Unify iterator type naming (remove "UI" prefix from internal types)

---

## Statistics

| Category | Count |
|----------|-------|
| Exported types | 44 |
| Internal types | 14 |
| Enums | 10 |
| Module functions | 13 |
| Module properties | 7 |
| Singletons | 5 |
| **Total public API surface** | **~93 named items** |
| Naming inconsistencies found | 5 |
| Missing functionality items | 5 |
| Deprecations to resolve | 3 |
| Documentation gaps | 2 |
| **Total findings** | **15** |
