# McRogueFace API Reference

*Generated on 2026-04-18 07:28:57*

*This documentation was dynamically generated from the compiled module.*

## Table of Contents

- [Functions](#functions)
- [Classes](#classes)
  - [AStarPath](#astarpath)
  - [Alignment](#alignment)
  - [Animation](#animation)
  - [Arc](#arc)
  - [AutoRuleSet](#autoruleset)
  - [BSP](#bsp)
  - [Behavior](#behavior)
  - [Billboard](#billboard)
  - [CallableBinding](#callablebinding)
  - [Caption](#caption)
  - [Circle](#circle)
  - [Color](#color)
  - [ColorLayer](#colorlayer)
  - [DijkstraMap](#dijkstramap)
  - [DiscreteMap](#discretemap)
  - [Drawable](#drawable)
  - [Easing](#easing)
  - [Entity](#entity)
  - [Entity3D](#entity3d)
  - [EntityCollection3D](#entitycollection3d)
  - [EntityCollection3DIter](#entitycollection3diter)
  - [FOV](#fov)
  - [Font](#font)
  - [Frame](#frame)
  - [Grid](#grid)
  - [GridView](#gridview)
  - [HeightMap](#heightmap)
  - [InputState](#inputstate)
  - [Key](#key)
  - [Keyboard](#keyboard)
  - [LdtkProject](#ldtkproject)
  - [Line](#line)
  - [Model3D](#model3d)
  - [Mouse](#mouse)
  - [MouseButton](#mousebutton)
  - [Music](#music)
  - [NoiseSource](#noisesource)
  - [Perspective](#perspective)
  - [PropertyBinding](#propertybinding)
  - [Scene](#scene)
  - [Shader](#shader)
  - [Sound](#sound)
  - [SoundBuffer](#soundbuffer)
  - [Sprite](#sprite)
  - [Texture](#texture)
  - [TileLayer](#tilelayer)
  - [TileMapFile](#tilemapfile)
  - [TileSetFile](#tilesetfile)
  - [Timer](#timer)
  - [Transition](#transition)
  - [Traversal](#traversal)
  - [Trigger](#trigger)
  - [Vector](#vector)
  - [Viewport3D](#viewport3d)
  - [VoxelGrid](#voxelgrid)
  - [VoxelRegion](#voxelregion)
  - [WangSet](#wangset)
  - [Window](#window)
- [Constants](#constants)

## Functions

### `bresenham(start, end, *, include_start=True, include_end=True) -> list[tuple[int, int]]`

Compute grid cells along a line using Bresenham's algorithm.

Note:

**Arguments:**
- `start`: (x, y) tuple or Vector - starting point
- `end`: (x, y) tuple or Vector - ending point
- `include_start`: Include the starting point in results (default: True)
- `include_end`: Include the ending point in results (default: True)

**Returns:** list[tuple[int, int]]: List of (x, y) grid coordinates along the line Useful for line-of-sight checks, projectile paths, and drawing lines on grids. The algorithm ensures minimal grid traversal between two points.

### `end_benchmark() -> str`

Stop benchmark capture and write data to JSON file.

Note:

**Returns:** str: The filename of the written benchmark data

**Raises:** RuntimeError: If no benchmark is currently running Returns the auto-generated filename (e.g., 'benchmark_12345_20250528_143022.json')

### `exit() -> None`

Cleanly shut down the game engine and exit the application.

Note:

**Returns:** None This immediately closes the window and terminates the program.

### `find(name: str, scene: str = None) -> UIDrawable | None`

Find the first UI element with the specified name.

Note:

**Arguments:**
- `name`: Exact name to search for
- `scene`: Scene to search in (default: current scene)

**Returns:** Frame, Caption, Sprite, Grid, or Entity if found; None otherwise Searches scene UI elements and entities within grids.

### `find_all(pattern: str, scene: str = None) -> list`

Find all UI elements matching a name pattern.

Note:

**Arguments:**
- `pattern`: Name pattern with optional wildcards (* matches any characters)
- `scene`: Scene to search in (default: current scene)

**Returns:** list: All matching UI elements and entities

### `get_metrics() -> dict`

Get current performance metrics.

**Returns:** dict: Performance data with keys: frame_time (last frame duration in seconds), avg_frame_time (average frame time), fps (frames per second), draw_calls (number of draw calls), ui_elements (total UI element count), visible_elements (visible element count), current_frame (frame counter), runtime (total runtime in seconds)

### `lock() -> _LockContext`

Get a context manager for thread-safe UI updates from background threads.

Note:

**Returns:** _LockContext: A context manager that blocks until safe to modify UI Use with `with mcrfpy.lock():` to safely modify UI objects from a background thread. The context manager blocks until the render loop reaches a safe point between frames. Without this, modifying UI from threads may cause visual glitches or crashes.

### `log_benchmark(message: str) -> None`

Add a log message to the current benchmark frame.

Note:

**Arguments:**
- `message`: Text to associate with the current frame

**Returns:** None

**Raises:** RuntimeError: If no benchmark is currently running Messages appear in the 'logs' array of each frame in the output JSON.

### `set_dev_console(enabled: bool) -> None`

Enable or disable the developer console overlay.

Note:

**Arguments:**
- `enabled`: True to enable the console (default), False to disable

**Returns:** None When disabled, the grave/tilde key will not open the console. Use this to ship games without debug features.

### `set_scale(multiplier: float) -> None`

Deprecated: use Window.resolution instead. Scale the game window size.

Note:

**Arguments:**
- `multiplier`: Scale factor (e.g., 2.0 for double size)

**Returns:** None The internal resolution remains 1024x768, but the window is scaled. This is deprecated - use Window.resolution instead.

### `start_benchmark() -> None`

Start capturing benchmark data to a file.

Note:

**Returns:** None

**Raises:** RuntimeError: If a benchmark is already running Benchmark filename is auto-generated from PID and timestamp. Use end_benchmark() to stop and get filename.

### `step(dt: float = None) -> float`

Advance simulation time (headless mode only).

Note:

**Arguments:**
- `dt`: Time to advance in seconds. If None, advances to the next scheduled event (timer/animation).

**Returns:** float: Actual time advanced in seconds. Returns 0.0 in windowed mode. In windowed mode, this is a no-op and returns 0.0. Use this for deterministic simulation control in headless/testing scenarios.

## Classes

### AStarPath

A computed A* path result, consumed step by step.

Created by Grid.find_path(). Cannot be instantiated directly.

Use walk() to get and consume each step, or iterate directly.
Use peek() to see the next step without consuming it.
Use bool(path) or len(path) to check if steps remain.

Properties:
    origin (Vector): Starting position (read-only)
    destination (Vector): Ending position (read-only)
    remaining (int): Steps remaining (read-only)

Example:
    path = grid.find_path(start, end)
    if path:
        while path:
            next_pos = path.walk()
            entity.pos = next_pos

**Properties:**
- `destination` *(read-only)*: Ending position of the path (Vector, read-only).
- `origin` *(read-only)*: Starting position of the path (Vector, read-only).
- `remaining` *(read-only)*: Number of steps remaining in the path (int, read-only).

**Methods:**

#### `peek() -> Vector`

See next step without consuming it.

**Returns:** Next position as Vector.

**Raises:** IndexError: If path is exhausted.

#### `walk() -> Vector`

Get and consume next step in the path.

**Returns:** Next position as Vector.

**Raises:** IndexError: If path is exhausted.

### Alignment

*Inherits from: IntEnum*

Alignment enum for positioning UI elements relative to parent bounds.

Values:
    TOP_LEFT, TOP_CENTER, TOP_RIGHT
    CENTER_LEFT, CENTER, CENTER_RIGHT
    BOTTOM_LEFT, BOTTOM_CENTER, BOTTOM_RIGHT

Margin Validation Rules:
    Margins define distance from parent edge when aligned.

    - CENTER: No margins allowed (raises ValueError if margin != 0)
    - TOP_CENTER, BOTTOM_CENTER: Only vert_margin applies (horiz_margin raises ValueError)
    - CENTER_LEFT, CENTER_RIGHT: Only horiz_margin applies (vert_margin raises ValueError)
    - Corner alignments (TOP_LEFT, etc.): All margins valid

Properties:
    align: Alignment value or None to disable
    margin: General margin for all applicable edges
    horiz_margin: Override for horizontal edge (0 = use general margin)
    vert_margin: Override for vertical edge (0 = use general margin)

Example:
    # Center a panel in the scene
    panel = Frame(size=(200, 100), align=Alignment.CENTER)
    scene.children.append(panel)

    # Place button in bottom-right with 10px margin
    button = Frame(size=(80, 30), align=Alignment.BOTTOM_RIGHT, margin=10)
    panel.children.append(button)

**Properties:**
- `denominator`: the denominator of a rational number in lowest terms
- `imag`: the imaginary part of a complex number
- `numerator`: the numerator of a rational number in lowest terms
- `real`: the real part of a complex number

**Methods:**

#### `as_integer_ratio(...)`

Return a pair of integers, whose ratio is equal to the original int.
The ratio is in lowest terms and has a positive denominator.
>>> (10).as_integer_ratio()
(10, 1)
>>> (-10).as_integer_ratio()
(-10, 1)
>>> (0).as_integer_ratio()
(0, 1)

#### `bit_count(...)`

Number of ones in the binary representation of the absolute value of self.
Also known as the population count.
>>> bin(13)
'0b1101'
>>> (13).bit_count()
3

#### `bit_length(...)`

Number of bits necessary to represent self in binary.
>>> bin(37)
'0b100101'
>>> (37).bit_length()
6

#### `conjugate(...)`

Returns self, the complex conjugate of any int.

#### `from_bytes(...)`

Return the integer represented by the given array of bytes.
  bytes
    Holds the array of bytes to convert.  The argument must either
    support the buffer protocol or be an iterable object producing bytes.
    Bytes and bytearray are examples of built-in objects that support the
    buffer protocol.
  byteorder
    The byte order used to represent the integer.  If byteorder is 'big',
    the most significant byte is at the beginning of the byte array.  If
    byteorder is 'little', the most significant byte is at the end of the
    byte array.  To request the native byte order of the host system, use
    sys.byteorder as the byte order value.  Default is to use 'big'.
  signed
    Indicates whether two's complement is used to represent the integer.

#### `is_integer(...)`

Returns True. Exists for duck type compatibility with float.is_integer.

#### `to_bytes(...)`

Return an array of bytes representing an integer.
  length
    Length of bytes object to use.  An OverflowError is raised if the
    integer is not representable with the given number of bytes.  Default
    is length 1.
  byteorder
    The byte order used to represent the integer.  If byteorder is 'big',
    the most significant byte is at the beginning of the byte array.  If
    byteorder is 'little', the most significant byte is at the end of the
    byte array.  To request the native byte order of the host system, use
    sys.byteorder as the byte order value.  Default is to use 'big'.
  signed
    Determines whether two's complement is used to represent the integer.
    If signed is False and a negative integer is given, an OverflowError
    is raised.

### Animation

Animation(property: str, target: Any, duration: float, easing: str = 'linear', delta: bool = False, loop: bool = False, callback: Callable = None)

Create an animation that interpolates a property value over time.

Args:
    property: Property name to animate. Valid properties depend on target type:
        - Position/Size: 'x', 'y', 'w', 'h', 'pos', 'size'
        - Appearance: 'fill_color', 'outline_color', 'outline', 'opacity'
        - Sprite: 'sprite_index', 'scale'
        - Grid: 'center', 'zoom'
        - Caption: 'text'
        - Sub-properties: 'fill_color.r', 'fill_color.g', 'fill_color.b', 'fill_color.a'
    target: Target value for the animation. Type depends on property:
        - float: For numeric properties (x, y, w, h, scale, opacity, zoom)
        - int: For integer properties (sprite_index)
        - tuple (r, g, b[, a]): For color properties
        - tuple (x, y): For vector properties (pos, size, center)
        - list[int]: For sprite animation sequences
        - str: For text animation
    duration: Animation duration in seconds.
    easing: Easing function name. Options:
        - 'linear' (default)
        - 'easeIn', 'easeOut', 'easeInOut'
        - 'easeInQuad', 'easeOutQuad', 'easeInOutQuad'
        - 'easeInCubic', 'easeOutCubic', 'easeInOutCubic'
        - 'easeInQuart', 'easeOutQuart', 'easeInOutQuart'
        - 'easeInSine', 'easeOutSine', 'easeInOutSine'
        - 'easeInExpo', 'easeOutExpo', 'easeInOutExpo'
        - 'easeInCirc', 'easeOutCirc', 'easeInOutCirc'
        - 'easeInElastic', 'easeOutElastic', 'easeInOutElastic'
        - 'easeInBack', 'easeOutBack', 'easeInOutBack'
        - 'easeInBounce', 'easeOutBounce', 'easeInOutBounce'
    delta: If True, target is relative to start value (additive). Default False.
    loop: If True, animation repeats from start when it reaches the end. Default False.
    callback: Function(target, property, value) called when animation completes.
        Not called for looping animations (since they never complete).

Example:
    # Move a frame from current position to x=500 over 2 seconds
    anim = mcrfpy.Animation('x', 500.0, 2.0, 'easeInOut')
    anim.start(my_frame)

    # Looping sprite animation
    walk = mcrfpy.Animation('sprite_index', [0,1,2,3,2,1], 0.6, loop=True)
    walk.start(my_sprite)


**Properties:**
- `duration` *(read-only)*: Animation duration in seconds (float, read-only). Total time for the animation to complete.
- `elapsed` *(read-only)*: Elapsed time in seconds (float, read-only). Time since the animation started.
- `is_complete` *(read-only)*: Whether animation is complete (bool, read-only). True when elapsed >= duration or complete() was called.
- `is_delta` *(read-only)*: Whether animation uses delta mode (bool, read-only). In delta mode, the target value is added to the starting value.
- `is_looping` *(read-only)*: Whether animation loops (bool, read-only). Looping animations repeat from the start when they reach the end.
- `property` *(read-only)*: Target property name (str, read-only). The property being animated (e.g., 'pos', 'opacity', 'sprite_index').

**Methods:**

#### `complete() -> None`

Complete the animation immediately by jumping to the final value.

Note:

**Returns:** None Sets elapsed = duration and applies target value immediately. Completion callback will be called if set.

#### `get_current_value() -> Any`

Get the current interpolated value of the animation.

Note:

**Returns:** Any: Current value (type depends on property: float, int, Color tuple, Vector tuple, or str) Return type matches the target property type. For sprite_index returns int, for pos returns (x, y), for fill_color returns (r, g, b, a).

#### `hasValidTarget() -> bool`

Check if the animation still has a valid target.

Note:

**Returns:** bool: True if the target still exists, False if it was destroyed Animations automatically clean up when targets are destroyed. Use this to check if manual cleanup is needed.

#### `start(target: UIDrawable, conflict_mode: str = 'replace') -> None`

Start the animation on a target UI element.

Note:

**Arguments:**
- `target`: The UI element to animate (Frame, Caption, Sprite, Grid, or Entity)
- `conflict_mode`: How to handle conflicts if property is already animating: 'replace' (default) - complete existing animation and start new one; 'queue' - wait for existing animation to complete; 'error' - raise RuntimeError if property is busy

**Returns:** None

**Raises:** RuntimeError: When conflict_mode='error' and property is already animating The animation will automatically stop if the target is destroyed.

#### `stop() -> None`

Stop the animation without completing it.

Note:

**Returns:** None Unlike complete(), this does NOT apply the final value and does NOT trigger the callback. The animation is simply cancelled and will be removed from the AnimationManager.

#### `update(delta_time: float) -> bool`

Update the animation by the given time delta.

Note:

**Arguments:**
- `delta_time`: Time elapsed since last update in seconds

**Returns:** bool: True if animation is still running, False if complete Typically called by AnimationManager automatically. Manual calls only needed for custom animation control.

### Arc

*Inherits from: Drawable*

Arc(center=None, radius=0, start_angle=0, end_angle=90, color=None, thickness=1, **kwargs)

An arc UI element for drawing curved line segments.

Args:
    center (tuple, optional): Center position as (x, y). Default: (0, 0)
    radius (float, optional): Arc radius in pixels. Default: 0
    start_angle (float, optional): Starting angle in degrees. Default: 0
    end_angle (float, optional): Ending angle in degrees. Default: 90
    color (Color, optional): Arc color. Default: White
    thickness (float, optional): Line thickness. Default: 1.0

Keyword Args:
    on_click (callable): Click handler. Default: None
    visible (bool): Visibility state. Default: True
    opacity (float): Opacity (0.0-1.0). Default: 1.0
    z_index (int): Rendering order. Default: 0
    name (str): Element name for finding. Default: None
    align (Alignment): Alignment relative to parent. Default: None
    margin (float): Margin from parent edge when aligned. Default: 0
    horiz_margin (float): Horizontal margin override. Default: 0 (use margin)
    vert_margin (float): Vertical margin override. Default: 0 (use margin)

Attributes:
    center (Vector): Center position
    radius (float): Arc radius
    start_angle (float): Starting angle in degrees
    end_angle (float): Ending angle in degrees
    color (Color): Arc color
    thickness (float): Line thickness
    visible (bool): Visibility state
    opacity (float): Opacity value
    z_index (int): Rendering order
    name (str): Element name
    align (Alignment): Alignment relative to parent (or None)
    margin (float): General margin for alignment
    horiz_margin (float): Horizontal margin override
    vert_margin (float): Vertical margin override


**Properties:**
- `align`: Alignment relative to parent bounds (Alignment enum or None). When set, position is automatically calculated when parent is assigned or resized. Set to None to disable alignment and use manual positioning.
- `bounds`: Bounding box as (pos, size) tuple of Vectors. Returns (Vector(x, y), Vector(width, height)).
- `center`: Center position of the arc
- `color`: Arc color
- `end_angle`: Ending angle in degrees
- `global_bounds`: Bounding box as (pos, size) tuple of Vectors in screen coordinates. Returns (Vector(x, y), Vector(width, height)).
- `global_position` *(read-only)*: Global screen position (read-only). Calculates absolute position by walking up the parent chain.
- `grid_pos`: Position in grid tile coordinates (only when parent is Grid)
- `grid_size`: Size in grid tile coordinates (only when parent is Grid)
- `horiz_margin`: Horizontal margin override (float, 0 = use general margin). Invalid for vertically-centered alignments (TOP_CENTER, BOTTOM_CENTER, CENTER).
- `hovered` *(read-only)*: Whether mouse is currently over this element (read-only). Updated automatically by the engine during mouse movement.
- `margin`: General margin from edge when aligned (float). Applied to both horizontal and vertical edges unless overridden. Invalid for CENTER alignment (raises ValueError).
- `name`: Name for finding this element.
- `on_click`: Callable executed when arc is clicked. Function receives (pos: Vector, button: str, action: str).
- `on_enter`: Callback for mouse enter events. Called with (pos: Vector, button: str, action: str) when mouse enters this element's bounds.
- `on_exit`: Callback for mouse exit events. Called with (pos: Vector, button: str, action: str) when mouse leaves this element's bounds.
- `on_move`: Callback for mouse movement within bounds. Called with (pos: Vector, button: str, action: str) for each mouse movement while inside. Performance note: Called frequently during movement - keep handlers fast.
- `opacity`: Opacity level (0.0 = transparent, 1.0 = opaque). Automatically clamped to valid range [0.0, 1.0].
- `origin`: Transform origin as Vector (pivot point for rotation). Default (0,0) is top-left; set to (w/2, h/2) to rotate around center.
- `parent`: Parent drawable. Get: Returns the parent Frame/Grid if nested, or None if at scene level. Set: Assign a Frame/Grid to reparent, or None to remove from parent.
- `pos`: Position as a Vector (same as center).
- `radius`: Arc radius in pixels
- `rotate_with_camera`: Whether to rotate visually with parent Grid's camera_rotation (bool). False (default): stay screen-aligned. True: tilt with camera. Only affects children of UIGrid; ignored for other parents.
- `rotation`: Rotation angle in degrees (clockwise around origin). Animatable property.
- `start_angle`: Starting angle in degrees
- `thickness`: Line thickness
- `vert_margin`: Vertical margin override (float, 0 = use general margin). Invalid for horizontally-centered alignments (CENTER_LEFT, CENTER_RIGHT, CENTER).
- `visible`: Whether the object is visible (bool). Invisible objects are not rendered or clickable.
- `z_index`: Z-order for rendering (lower values rendered first).

**Methods:**

#### `animate(property: str, target: Any, duration: float, easing=None, delta=False, loop=False, callback=None, conflict_mode='replace') -> Animation`

Create and start an animation on this drawable's property.

Note:

**Arguments:**
- `property`: Name of the property to animate (e.g., 'x', 'fill_color', 'opacity')
- `target`: Target value - type depends on property (float, tuple for color/vector, etc.)
- `duration`: Animation duration in seconds
- `easing`: Easing function: Easing enum value, string name, or None for linear
- `delta`: If True, target is relative to current value; if False, target is absolute
- `loop`: If True, animation repeats from start when it reaches the end (default False)
- `callback`: Optional callable invoked when animation completes (not called for looping animations)
- `conflict_mode`: 'replace' (default), 'queue', or 'error' if property already animating

**Returns:** Animation object for monitoring progress

**Raises:** ValueError: If property name is not valid for this drawable type This is a convenience method that creates an Animation, starts it, and adds it to the AnimationManager.

#### `move(dx, dy) or (delta) -> None`

Move the element by a relative offset.

Note:

**Arguments:**
- `dx`: Horizontal offset in pixels (or use delta)
- `dy`: Vertical offset in pixels (or use delta)
- `delta`: Offset as tuple, list, or Vector: (dx, dy)

#### `realign() -> None`

Reapply alignment relative to parent, useful for responsive layouts.

Note:
    Call this to recalculate position after parent changes size. For elements with align=None, this has no effect.

#### `resize(width, height) or (size) -> None`

Resize the element to new dimensions.

Note:

**Arguments:**
- `width`: New width in pixels (or use size)
- `height`: New height in pixels (or use size)
- `size`: Size as tuple, list, or Vector: (width, height)

### AutoRuleSet

AutoRuleSet - LDtk auto-tile rule set for pattern-based terrain rendering.

AutoRuleSets are obtained from LdtkProject.ruleset().
They map IntGrid terrain values to sprite tiles using LDtk's
pattern-matching auto-rule system.

Properties:
    name (str, read-only): Rule set name (layer identifier).
    grid_size (int, read-only): Cell size in pixels.
    value_count (int, read-only): Number of IntGrid values.
    values (list, read-only): List of value dicts.
    rule_count (int, read-only): Total rules across all groups.
    group_count (int, read-only): Number of rule groups.

Example:
    rs = project.ruleset('Walls')
    Terrain = rs.terrain_enum()
    rs.apply(discrete_map, tile_layer, seed=42)


**Properties:**
- `grid_size` *(read-only)*: Cell size in pixels (int, read-only).
- `group_count` *(read-only)*: Number of rule groups (int, read-only).
- `name` *(read-only)*: Rule set name / layer identifier (str, read-only).
- `rule_count` *(read-only)*: Total number of rules across all groups (int, read-only).
- `value_count` *(read-only)*: Number of IntGrid terrain values (int, read-only).
- `values` *(read-only)*: List of IntGrid value dicts with value and name (read-only).

**Methods:**

#### `apply(discrete_map: DiscreteMap, tile_layer: TileLayer, seed: int = 0) -> None`

Resolve auto-rules and write tile indices directly into a TileLayer.

**Arguments:**
- `discrete_map`: A DiscreteMap with IntGrid values
- `tile_layer`: Target TileLayer to write resolved tiles into
- `seed`: Random seed for deterministic results (default: 0)

#### `resolve(discrete_map: DiscreteMap, seed: int = 0) -> list[int]`

Resolve IntGrid data to tile indices using LDtk auto-rules.

**Arguments:**
- `discrete_map`: A DiscreteMap with IntGrid values matching this rule set
- `seed`: Random seed for deterministic tile selection and probability (default: 0)

**Returns:** List of tile IDs (one per cell). -1 means no matching rule.

#### `terrain_enum() -> IntEnum`

Generate a Python IntEnum from this rule set's IntGrid values.

**Returns:** IntEnum class with NONE=0 and one member per IntGrid value (UPPER_SNAKE_CASE).

### BSP

BSP(pos: tuple[int, int], size: tuple[int, int])

Binary Space Partitioning tree for procedural dungeon generation.

BSP recursively divides a rectangular region into smaller sub-regions, creating a tree structure perfect for generating dungeon rooms and corridors.

Args:
    pos: (x, y) - Top-left position of the root region.
    size: (w, h) - Width and height of the root region.

Properties:
    pos (tuple[int, int]): Read-only. Top-left position (x, y).
    size (tuple[int, int]): Read-only. Dimensions (width, height).
    bounds ((pos), (size)): Read-only. Combined position and size.
    root (BSPNode): Read-only. Reference to the root node.

Iteration:
    for leaf in bsp:  # Iterates over leaf nodes (rooms)
    len(bsp)          # Returns number of leaf nodes

Example:
    bsp = mcrfpy.BSP(pos=(0, 0), size=(80, 50))
    bsp.split_recursive(depth=4, min_size=(8, 8))
    for leaf in bsp:
        print(f'Room at {leaf.pos}, size {leaf.size}')


**Properties:**
- `adjacency` *(read-only)*: Leaf adjacency graph. adjacency[i] returns tuple of neighbor indices. Read-only.
- `bounds` *(read-only)*: Root node bounds as ((x, y), (w, h)). Read-only.
- `pos` *(read-only)*: Top-left position (x, y). Read-only.
- `root` *(read-only)*: Reference to the root BSPNode. Read-only.
- `size` *(read-only)*: Dimensions (width, height). Read-only.

**Methods:**

#### `clear() -> BSP`

Remove all children, keeping only the root node with original bounds. WARNING: Invalidates all existing BSPNode references from this tree.

**Returns:** BSP: self, for method chaining

#### `find(pos: tuple[int, int]) -> BSPNode | None`

Find the smallest (deepest) node containing the position.

**Arguments:**
- `pos`: Position as (x, y) tuple, list, or Vector

**Returns:** BSPNode if found, None if position is outside bounds

#### `get_leaf(index: int) -> BSPNode`

Get a leaf node by its index (0 to len(bsp)-1). This is useful when working with adjacency data, which returns leaf indices.

**Arguments:**
- `index`: Leaf index (0 to len(bsp)-1). Negative indices supported.

**Returns:** BSPNode at the specified index

**Raises:** IndexError: If index is out of range

#### `leaves() -> Iterator[BSPNode]`

Iterate all leaf nodes (the actual rooms). Same as iterating the BSP directly.

**Returns:** Iterator yielding BSPNode objects

#### `split_once(horizontal: bool, position: int) -> BSP`

Split the root node once at the specified position. horizontal=True creates a horizontal divider, producing top/bottom rooms. horizontal=False creates a vertical divider, producing left/right rooms.

**Arguments:**
- `horizontal`: True for horizontal divider (top/bottom), False for vertical (left/right)
- `position`: Split coordinate (y for horizontal, x for vertical)

**Returns:** BSP: self, for method chaining

#### `split_recursive(depth: int, min_size: tuple[int, int], max_ratio: float = 1.5, seed: int = None) -> BSP`

Recursively split to the specified depth. WARNING: Invalidates all existing BSPNode references from this tree.

**Arguments:**
- `depth`: Maximum recursion depth (1-16). Creates up to 2^depth leaves.
- `min_size`: Minimum (width, height) for a node to be split.
- `max_ratio`: Maximum aspect ratio before forcing split direction. Default: 1.5.
- `seed`: Random seed. None for random.

**Returns:** BSP: self, for method chaining

#### `to_heightmap(size: tuple[int, int] = None, select: str = 'leaves', shrink: int = 0, value: float = 1.0) -> HeightMap`

Convert BSP node selection to a HeightMap.

**Arguments:**
- `size`: Output size (width, height). Default: bounds size.
- `select`: 'leaves', 'all', or 'internal'. Default: 'leaves'.
- `shrink`: Pixels to shrink from each node's bounds. Default: 0.
- `value`: Value inside selected regions. Default: 1.0.

**Returns:** HeightMap with selected regions filled

#### `traverse(order: Traversal = Traversal.LEVEL_ORDER) -> Iterator[BSPNode]`

Iterate all nodes in the specified order.

Note:

**Arguments:**
- `order`: Traversal order from Traversal enum. Default: LEVEL_ORDER.

**Returns:** Iterator yielding BSPNode objects Orders: PRE_ORDER, IN_ORDER, POST_ORDER, LEVEL_ORDER, INVERTED_LEVEL_ORDER

### Behavior

*Inherits from: IntEnum*

Enum representing entity behavior types for grid.step() turn management.

Values:
    IDLE: No action each turn
    CUSTOM: Calls step callback only, no built-in movement
    NOISE4: Random movement in 4 cardinal directions
    NOISE8: Random movement in 8 directions (incl. diagonals)
    PATH: Follow a precomputed path to completion
    WAYPOINT: Path through a sequence of waypoints in order
    PATROL: Patrol waypoints back and forth (reversing at ends)
    LOOP: Loop through waypoints cyclically
    SLEEP: Wait for N turns, then trigger DONE
    SEEK: Move toward target using Dijkstra map
    FLEE: Move away from target using Dijkstra map


**Properties:**
- `denominator`: the denominator of a rational number in lowest terms
- `imag`: the imaginary part of a complex number
- `numerator`: the numerator of a rational number in lowest terms
- `real`: the real part of a complex number

**Methods:**

#### `as_integer_ratio(...)`

Return a pair of integers, whose ratio is equal to the original int.
The ratio is in lowest terms and has a positive denominator.
>>> (10).as_integer_ratio()
(10, 1)
>>> (-10).as_integer_ratio()
(-10, 1)
>>> (0).as_integer_ratio()
(0, 1)

#### `bit_count(...)`

Number of ones in the binary representation of the absolute value of self.
Also known as the population count.
>>> bin(13)
'0b1101'
>>> (13).bit_count()
3

#### `bit_length(...)`

Number of bits necessary to represent self in binary.
>>> bin(37)
'0b100101'
>>> (37).bit_length()
6

#### `conjugate(...)`

Returns self, the complex conjugate of any int.

#### `from_bytes(...)`

Return the integer represented by the given array of bytes.
  bytes
    Holds the array of bytes to convert.  The argument must either
    support the buffer protocol or be an iterable object producing bytes.
    Bytes and bytearray are examples of built-in objects that support the
    buffer protocol.
  byteorder
    The byte order used to represent the integer.  If byteorder is 'big',
    the most significant byte is at the beginning of the byte array.  If
    byteorder is 'little', the most significant byte is at the end of the
    byte array.  To request the native byte order of the host system, use
    sys.byteorder as the byte order value.  Default is to use 'big'.
  signed
    Indicates whether two's complement is used to represent the integer.

#### `is_integer(...)`

Returns True. Exists for duck type compatibility with float.is_integer.

#### `to_bytes(...)`

Return an array of bytes representing an integer.
  length
    Length of bytes object to use.  An OverflowError is raised if the
    integer is not representable with the given number of bytes.  Default
    is length 1.
  byteorder
    The byte order used to represent the integer.  If byteorder is 'big',
    the most significant byte is at the beginning of the byte array.  If
    byteorder is 'little', the most significant byte is at the end of the
    byte array.  To request the native byte order of the host system, use
    sys.byteorder as the byte order value.  Default is to use 'big'.
  signed
    Determines whether two's complement is used to represent the integer.
    If signed is False and a negative integer is given, an OverflowError
    is raised.

### Billboard

Billboard(texture=None, sprite_index=0, pos=(0,0,0), scale=1.0, facing='camera_y')

A camera-facing 3D sprite for trees, items, particles, etc.

Args:
    texture (Texture, optional): Sprite sheet texture. Default: None
    sprite_index (int): Index into sprite sheet. Default: 0
    pos (tuple): World position (x, y, z). Default: (0, 0, 0)
    scale (float): Uniform scale factor. Default: 1.0
    facing (str): Facing mode - 'camera', 'camera_y', or 'fixed'. Default: 'camera_y'

Properties:
    texture (Texture): Sprite sheet texture
    sprite_index (int): Index into sprite sheet
    pos (tuple): World position (x, y, z)
    scale (float): Uniform scale factor
    facing (str): Facing mode - 'camera', 'camera_y', or 'fixed'
    theta (float): Horizontal rotation for 'fixed' mode (radians)
    phi (float): Vertical tilt for 'fixed' mode (radians)
    opacity (float): Opacity 0.0 (transparent) to 1.0 (opaque)
    visible (bool): Visibility state

**Properties:**
- `facing`: Facing mode: 'camera', 'camera_y', or 'fixed' (str)
- `opacity`: Opacity from 0.0 (transparent) to 1.0 (opaque) (float)
- `phi`: Vertical tilt for 'fixed' mode in radians (float)
- `pos`: World position as (x, y, z) tuple
- `scale`: Uniform scale factor (float)
- `sprite_index`: Index into sprite sheet (int)
- `texture`: Sprite sheet texture (Texture or None)
- `theta`: Horizontal rotation for 'fixed' mode in radians (float)
- `visible`: Visibility state (bool)

**Methods:**

### CallableBinding

CallableBinding(callable: Callable[[], float])

A binding that calls a Python function to get its value.

Args:
    callable: A function that takes no arguments and returns a float

The callable is invoked every frame when the shader is rendered.
Keep the callable lightweight to avoid performance issues.

Example:
    player_health = 100
    frame.uniforms['health_pct'] = mcrfpy.CallableBinding(
        lambda: player_health / 100.0
    )


**Properties:**
- `callable` *(read-only)*: The Python callable (read-only).
- `is_valid` *(read-only)*: True if the callable is still valid (bool, read-only).
- `value` *(read-only)*: Current value from calling the callable (float, read-only). Returns None on error.

**Methods:**

### Caption

*Inherits from: Drawable*

Caption(pos=None, font=None, text='', **kwargs)

A text display UI element with customizable font and styling.

Args:
    pos (tuple, optional): Position as (x, y) tuple. Default: (0, 0)
    font (Font, optional): Font object for text rendering. Default: engine default font
    text (str, optional): The text content to display. Default: ''

Keyword Args:
    fill_color (Color): Text fill color. Default: (255, 255, 255, 255)
    outline_color (Color): Text outline color. Default: (0, 0, 0, 255)
    outline (float): Text outline thickness. Default: 0
    font_size (float): Font size in points. Default: 16
    click (callable): Click event handler. Default: None
    visible (bool): Visibility state. Default: True
    opacity (float): Opacity (0.0-1.0). Default: 1.0
    z_index (int): Rendering order. Default: 0
    name (str): Element name for finding. Default: None
    x (float): X position override. Default: 0
    y (float): Y position override. Default: 0
    align (Alignment): Alignment relative to parent. Default: None
    margin (float): Margin from parent edge when aligned. Default: 0
    horiz_margin (float): Horizontal margin override. Default: 0 (use margin)
    vert_margin (float): Vertical margin override. Default: 0 (use margin)

Attributes:
    text (str): The displayed text content
    x, y (float): Position in pixels
    pos (Vector): Position as a Vector object
    font (Font): Font used for rendering
    font_size (float): Font size in points
    fill_color, outline_color (Color): Text appearance
    outline (float): Outline thickness
    click (callable): Click event handler
    visible (bool): Visibility state
    opacity (float): Opacity value
    z_index (int): Rendering order
    name (str): Element name
    w, h (float): Read-only computed size based on text and font
    align (Alignment): Alignment relative to parent (or None)
    margin (float): General margin for alignment
    horiz_margin (float): Horizontal margin override
    vert_margin (float): Vertical margin override

**Properties:**
- `align`: Alignment relative to parent bounds (Alignment enum or None). When set, position is automatically calculated when parent is assigned or resized. Set to None to disable alignment and use manual positioning.
- `bounds`: Bounding box as (pos, size) tuple of Vectors. Returns (Vector(x, y), Vector(width, height)).
- `fill_color`: Fill color of the text. Returns a copy; modifying components requires reassignment. For animation, use 'fill_color.r', 'fill_color.g', etc.
- `font_size`: Font size (integer) in points
- `global_bounds`: Bounding box as (pos, size) tuple of Vectors in screen coordinates. Returns (Vector(x, y), Vector(width, height)).
- `global_position` *(read-only)*: Global screen position (read-only). Calculates absolute position by walking up the parent chain.
- `grid_pos`: Position in grid tile coordinates (only when parent is Grid)
- `grid_size`: Size in grid tile coordinates (only when parent is Grid)
- `h` *(read-only)*: Text height in pixels (read-only)
- `horiz_margin`: Horizontal margin override (float, 0 = use general margin). Invalid for vertically-centered alignments (TOP_CENTER, BOTTOM_CENTER, CENTER).
- `hovered` *(read-only)*: Whether mouse is currently over this element (read-only). Updated automatically by the engine during mouse movement.
- `margin`: General margin from edge when aligned (float). Applied to both horizontal and vertical edges unless overridden. Invalid for CENTER alignment (raises ValueError).
- `name`: Name for finding elements
- `on_click`: Callable executed when object is clicked. Function receives (pos: Vector, button: str, action: str).
- `on_enter`: Callback for mouse enter events. Called with (pos: Vector, button: str, action: str) when mouse enters this element's bounds.
- `on_exit`: Callback for mouse exit events. Called with (pos: Vector, button: str, action: str) when mouse leaves this element's bounds.
- `on_move`: Callback for mouse movement within bounds. Called with (pos: Vector, button: str, action: str) for each mouse movement while inside. Performance note: Called frequently during movement - keep handlers fast.
- `opacity`: Opacity level (0.0 = transparent, 1.0 = opaque). Automatically clamped to valid range [0.0, 1.0].
- `origin`: Transform origin as Vector (pivot point for rotation). Default (0,0) is top-left; set to (w/2, h/2) to rotate around center.
- `outline`: Thickness of the border
- `outline_color`: Outline color of the text. Returns a copy; modifying components requires reassignment. For animation, use 'outline_color.r', 'outline_color.g', etc.
- `parent`: Parent drawable. Get: Returns the parent Frame/Grid if nested, or None if at scene level. Set: Assign a Frame/Grid to reparent, or None to remove from parent.
- `pos`: (x, y) vector
- `rotate_with_camera`: Whether to rotate visually with parent Grid's camera_rotation (bool). False (default): stay screen-aligned. True: tilt with camera. Only affects children of UIGrid; ignored for other parents.
- `rotation`: Rotation angle in degrees (clockwise around origin). Animatable property.
- `shader`: Shader for GPU visual effects (Shader or None). When set, the drawable is rendered through the shader program. Set to None to disable shader effects.
- `size` *(read-only)*: Text dimensions as Vector (read-only)
- `text`: The text displayed
- `uniforms` *(read-only)*: Collection of shader uniforms (read-only access to collection). Set uniforms via dict-like syntax: drawable.uniforms['name'] = value. Supports float, vec2/3/4 tuples, PropertyBinding, and CallableBinding.
- `vert_margin`: Vertical margin override (float, 0 = use general margin). Invalid for horizontally-centered alignments (CENTER_LEFT, CENTER_RIGHT, CENTER).
- `visible`: Whether the object is visible (bool). Invisible objects are not rendered or clickable.
- `w` *(read-only)*: Text width in pixels (read-only)
- `x`: X coordinate of top-left corner
- `y`: Y coordinate of top-left corner
- `z_index`: Z-order for rendering (lower values rendered first). Automatically triggers scene resort when changed.

**Methods:**

#### `animate(property: str, target: Any, duration: float, easing=None, delta=False, loop=False, callback=None, conflict_mode='replace') -> Animation`

Create and start an animation on this drawable's property.

Note:

**Arguments:**
- `property`: Name of the property to animate (e.g., 'x', 'fill_color', 'opacity')
- `target`: Target value - type depends on property (float, tuple for color/vector, etc.)
- `duration`: Animation duration in seconds
- `easing`: Easing function: Easing enum value, string name, or None for linear
- `delta`: If True, target is relative to current value; if False, target is absolute
- `loop`: If True, animation repeats from start when it reaches the end (default False)
- `callback`: Optional callable invoked when animation completes (not called for looping animations)
- `conflict_mode`: 'replace' (default), 'queue', or 'error' if property already animating

**Returns:** Animation object for monitoring progress

**Raises:** ValueError: If property name is not valid for this drawable type This is a convenience method that creates an Animation, starts it, and adds it to the AnimationManager.

#### `move(dx, dy) or (delta) -> None`

Move the element by a relative offset.

Note:

**Arguments:**
- `dx`: Horizontal offset in pixels (or use delta)
- `dy`: Vertical offset in pixels (or use delta)
- `delta`: Offset as tuple, list, or Vector: (dx, dy)

#### `realign() -> None`

Reapply alignment relative to parent, useful for responsive layouts.

Note:
    Call this to recalculate position after parent changes size. For elements with align=None, this has no effect.

#### `resize(width, height) or (size) -> None`

Resize the element to new dimensions.

Note:

**Arguments:**
- `width`: New width in pixels (or use size)
- `height`: New height in pixels (or use size)
- `size`: Size as tuple, list, or Vector: (width, height)

### Circle

*Inherits from: Drawable*

Circle(radius=0, center=None, fill_color=None, outline_color=None, outline=0, **kwargs)

A circle UI element for drawing filled or outlined circles.

Args:
    radius (float, optional): Circle radius in pixels. Default: 0
    center (tuple, optional): Center position as (x, y). Default: (0, 0)
    fill_color (Color, optional): Fill color. Default: White
    outline_color (Color, optional): Outline color. Default: Transparent
    outline (float, optional): Outline thickness. Default: 0 (no outline)

Keyword Args:
    on_click (callable): Click handler. Default: None
    visible (bool): Visibility state. Default: True
    opacity (float): Opacity (0.0-1.0). Default: 1.0
    z_index (int): Rendering order. Default: 0
    name (str): Element name for finding. Default: None
    align (Alignment): Alignment relative to parent. Default: None
    margin (float): Margin from parent edge when aligned. Default: 0
    horiz_margin (float): Horizontal margin override. Default: 0 (use margin)
    vert_margin (float): Vertical margin override. Default: 0 (use margin)

Attributes:
    radius (float): Circle radius
    center (Vector): Center position
    fill_color (Color): Fill color
    outline_color (Color): Outline color
    outline (float): Outline thickness
    visible (bool): Visibility state
    opacity (float): Opacity value
    z_index (int): Rendering order
    name (str): Element name
    align (Alignment): Alignment relative to parent (or None)
    margin (float): General margin for alignment
    horiz_margin (float): Horizontal margin override
    vert_margin (float): Vertical margin override


**Properties:**
- `align`: Alignment relative to parent bounds (Alignment enum or None). When set, position is automatically calculated when parent is assigned or resized. Set to None to disable alignment and use manual positioning.
- `bounds`: Bounding box as (pos, size) tuple of Vectors. Returns (Vector(x, y), Vector(width, height)).
- `center`: Center position of the circle
- `fill_color`: Fill color of the circle
- `global_bounds`: Bounding box as (pos, size) tuple of Vectors in screen coordinates. Returns (Vector(x, y), Vector(width, height)).
- `global_position` *(read-only)*: Global screen position (read-only). Calculates absolute position by walking up the parent chain.
- `grid_pos`: Position in grid tile coordinates (only when parent is Grid)
- `grid_size`: Size in grid tile coordinates (only when parent is Grid)
- `horiz_margin`: Horizontal margin override (float, 0 = use general margin). Invalid for vertically-centered alignments (TOP_CENTER, BOTTOM_CENTER, CENTER).
- `hovered` *(read-only)*: Whether mouse is currently over this element (read-only). Updated automatically by the engine during mouse movement.
- `margin`: General margin from edge when aligned (float). Applied to both horizontal and vertical edges unless overridden. Invalid for CENTER alignment (raises ValueError).
- `name`: Name for finding this element.
- `on_click`: Callable executed when circle is clicked. Function receives (pos: Vector, button: str, action: str).
- `on_enter`: Callback for mouse enter events. Called with (pos: Vector, button: str, action: str) when mouse enters this element's bounds.
- `on_exit`: Callback for mouse exit events. Called with (pos: Vector, button: str, action: str) when mouse leaves this element's bounds.
- `on_move`: Callback for mouse movement within bounds. Called with (pos: Vector, button: str, action: str) for each mouse movement while inside. Performance note: Called frequently during movement - keep handlers fast.
- `opacity`: Opacity level (0.0 = transparent, 1.0 = opaque). Automatically clamped to valid range [0.0, 1.0].
- `origin`: Transform origin as Vector (pivot point for rotation). Default (0,0) is top-left; set to (w/2, h/2) to rotate around center.
- `outline`: Outline thickness (0 for no outline)
- `outline_color`: Outline color of the circle
- `parent`: Parent drawable. Get: Returns the parent Frame/Grid if nested, or None if at scene level. Set: Assign a Frame/Grid to reparent, or None to remove from parent.
- `pos`: Position as a Vector (same as center).
- `radius`: Circle radius in pixels
- `rotate_with_camera`: Whether to rotate visually with parent Grid's camera_rotation (bool). False (default): stay screen-aligned. True: tilt with camera. Only affects children of UIGrid; ignored for other parents.
- `rotation`: Rotation angle in degrees (clockwise around origin). Animatable property.
- `vert_margin`: Vertical margin override (float, 0 = use general margin). Invalid for horizontally-centered alignments (CENTER_LEFT, CENTER_RIGHT, CENTER).
- `visible`: Whether the object is visible (bool). Invisible objects are not rendered or clickable.
- `z_index`: Z-order for rendering (lower values rendered first).

**Methods:**

#### `animate(property: str, target: Any, duration: float, easing=None, delta=False, loop=False, callback=None, conflict_mode='replace') -> Animation`

Create and start an animation on this drawable's property.

Note:

**Arguments:**
- `property`: Name of the property to animate (e.g., 'x', 'fill_color', 'opacity')
- `target`: Target value - type depends on property (float, tuple for color/vector, etc.)
- `duration`: Animation duration in seconds
- `easing`: Easing function: Easing enum value, string name, or None for linear
- `delta`: If True, target is relative to current value; if False, target is absolute
- `loop`: If True, animation repeats from start when it reaches the end (default False)
- `callback`: Optional callable invoked when animation completes (not called for looping animations)
- `conflict_mode`: 'replace' (default), 'queue', or 'error' if property already animating

**Returns:** Animation object for monitoring progress

**Raises:** ValueError: If property name is not valid for this drawable type This is a convenience method that creates an Animation, starts it, and adds it to the AnimationManager.

#### `move(dx, dy) or (delta) -> None`

Move the element by a relative offset.

Note:

**Arguments:**
- `dx`: Horizontal offset in pixels (or use delta)
- `dy`: Vertical offset in pixels (or use delta)
- `delta`: Offset as tuple, list, or Vector: (dx, dy)

#### `realign() -> None`

Reapply alignment relative to parent, useful for responsive layouts.

Note:
    Call this to recalculate position after parent changes size. For elements with align=None, this has no effect.

#### `resize(width, height) or (size) -> None`

Resize the element to new dimensions.

Note:

**Arguments:**
- `width`: New width in pixels (or use size)
- `height`: New height in pixels (or use size)
- `size`: Size as tuple, list, or Vector: (width, height)

### Color

Color(r: int = 0, g: int = 0, b: int = 0, a: int = 255)

RGBA color representation.

Args:
    r: Red component (0-255)
    g: Green component (0-255)
    b: Blue component (0-255)
    a: Alpha component (0-255, default 255 = opaque)

Note:
    When accessing colors from UI elements (e.g., frame.fill_color),
    you receive a COPY of the color. Modifying it doesn't affect the
    original. To change a component:

        # This does NOT work:
        frame.fill_color.r = 255  # Modifies a temporary copy

        # Do this instead:
        c = frame.fill_color
        c.r = 255
        frame.fill_color = c

        # Or use Animation for sub-properties:
        anim = mcrfpy.Animation('fill_color.r', 255, 0.5, 'linear')
        anim.start(frame)


**Properties:**
- `a`: Alpha component (0-255, where 0=transparent, 255=opaque). Automatically clamped to valid range.
- `b`: Blue component (0-255). Automatically clamped to valid range.
- `g`: Green component (0-255). Automatically clamped to valid range.
- `r`: Red component (0-255). Automatically clamped to valid range.

**Methods:**

#### `from_hex(hex_string: str) -> Color`

Create a Color from a hexadecimal string.

Note:

**Arguments:**
- `hex_string`: Hex color string (e.g., '#FF0000', 'FF0000', '#AABBCCDD' for RGBA)

**Returns:** Color: New Color object with values from hex string

**Raises:** ValueError: If hex string is not 6 or 8 characters (RGB or RGBA) This is a class method. Call as Color.from_hex('#FF0000')

#### `lerp(other: Color, t: float) -> Color`

Linearly interpolate between this color and another.

Note:

**Arguments:**
- `other`: The target Color to interpolate towards
- `t`: Interpolation factor (0.0 = this color, 1.0 = other color). Automatically clamped to [0.0, 1.0]

**Returns:** Color: New Color representing the interpolated value All components (r, g, b, a) are interpolated independently

#### `to_hex() -> str`

Convert this Color to a hexadecimal string.

Note:

**Returns:** str: Hex string in format '#RRGGBB' or '#RRGGBBAA' (if alpha < 255) Alpha component is only included if not fully opaque (< 255)

### ColorLayer

ColorLayer(z_index=-1, name=None, grid_size=None)

A grid layer that stores RGBA colors per cell for background/overlay effects.

ColorLayers can be created standalone and attached to a Grid via add_layer()
or passed to the Grid constructor's layers parameter. Layers with size (0, 0)
automatically resize to match the Grid when attached.

Args:
    z_index (int): Render order relative to entities. Negative values render
        below entities (as backgrounds), positive values render above entities
        (as overlays). Default: -1 (background)
    name (str): Layer name for Grid.layer(name) lookup. Default: None
    grid_size (tuple): Dimensions as (width, height). If None or (0, 0), the
        layer will auto-resize when attached to a Grid. Default: None

Attributes:
    z_index (int): Layer z-order relative to entities (read/write)
    name (str): Layer name for lookup (read-only)
    visible (bool): Whether layer is rendered (read/write)
    grid_size (tuple): Layer dimensions as (width, height) (read-only)
    grid (Grid): Parent Grid or None. Setting manages layer association.

Methods:
    at(x, y) -> Color: Get the color at cell position (x, y)
    set(x, y, color): Set the color at cell position (x, y)
    fill(color): Fill the entire layer with a single color
    fill_rect(x, y, w, h, color): Fill a rectangular region with a color
    draw_fov(...): Draw FOV-based visibility colors
    apply_perspective(entity, ...): Bind layer to entity for automatic FOV updates

Example:
    fog = mcrfpy.ColorLayer(z_index=-1, name='fog')
    grid = mcrfpy.Grid(grid_size=(20, 15), layers=[fog])
    fog.fill(mcrfpy.Color(40, 40, 40))  # Dark gray background
    grid.layer('fog').set(5, 5, mcrfpy.Color(255, 0, 0, 128))

**Properties:**
- `grid`: Parent Grid or None. Setting manages layer association and handles lazy allocation.
- `grid_size`: Layer dimensions as (width, height) tuple.
- `name` *(read-only)*: Layer name (str, read-only). Used for Grid.layer(name) lookup.
- `visible`: Whether the layer is rendered.
- `z_index`: Layer z-order. Negative values render below entities.

**Methods:**

#### `apply_gradient(source, range, color_low, color_high) -> ColorLayer`

Interpolate between colors based on HeightMap value within range.

Note:

**Arguments:**
- `color_low`: Color at range minimum
- `color_high`: Color at range maximum

**Returns:** self for method chaining Uses the original HeightMap value for interpolation, not binary. This allows smooth color transitions within a value range.

#### `apply_perspective(entity, visible=None, discovered=None, unknown=None)`

Bind this layer to an entity for automatic FOV updates.

#### `apply_ranges(source, ranges) -> ColorLayer`

Apply multiple color assignments in a single pass.

Note:

**Returns:** self for method chaining Later ranges override earlier ones if overlapping. Cells not matching any range are left unchanged.

#### `apply_threshold(source, range, color) -> ColorLayer`

Set fixed color for cells where HeightMap value is within range.

**Arguments:**
- `color`: Color or (r, g, b[, a]) tuple to set for cells in range

**Returns:** self for method chaining

#### `at(pos) -> Color`

at(x, y) -> Color
Get the color at cell position.

**Arguments:**
- `pos`: Position as (x, y) tuple, list, or Vector

#### `clear_perspective()`

Remove the perspective binding from this layer.

#### `draw_fov(source, radius=None, fov=None, visible=None, discovered=None, unknown=None)`

Paint cells based on field-of-view visibility from source position.

Note: Layer must be attached to a grid for FOV calculation.

#### `fill(color)`

Fill the entire layer with the specified color.

#### `fill_rect(pos, size, color)`

Fill a rectangular region with a color.

**Arguments:**
- `color`: Color object or (r, g, b[, a]) tuple

#### `set(pos, color)`

Set the color at cell position.

**Arguments:**
- `pos`: Position as (x, y) tuple, list, or Vector
- `color`: Color object or (r, g, b[, a]) tuple

#### `update_perspective()`

Redraw FOV based on the bound entity's current position.
Call this after the entity moves to update the visibility layer.

### DijkstraMap

A Dijkstra distance map from a fixed root position.

Created by Grid.get_dijkstra_map(). Cannot be instantiated directly.

Grid caches these maps - multiple requests for the same root return
the same map. Call Grid.clear_dijkstra_maps() after changing grid
walkability to invalidate the cache.

Properties:
    root (Vector): Root position (read-only)

Methods:
    distance(pos) -> float | None: Get distance to root
    path_from(pos) -> AStarPath: Get full path to root
    step_from(pos) -> Vector | None: Get single step toward root

Example:
    dijkstra = grid.get_dijkstra_map(player.pos)
    for enemy in enemies:
        dist = dijkstra.distance(enemy.pos)
        if dist and dist < 10:
            step = dijkstra.step_from(enemy.pos)
            if step:
                enemy.pos = step

**Properties:**
- `root` *(read-only)*: Root position that distances are measured from (Vector, read-only).

**Methods:**

#### `distance(pos) -> float | None`

Get distance from position to root.

**Arguments:**
- `pos`: Position as Vector, Entity, or (x, y) tuple.

**Returns:** Float distance, or None if position is unreachable.

#### `path_from(pos) -> AStarPath`

Get full path from position to root.

**Arguments:**
- `pos`: Starting position as Vector, Entity, or (x, y) tuple.

**Returns:** AStarPath from pos toward root.

#### `step_from(pos) -> Vector | None`

Get single step from position toward root.

**Arguments:**
- `pos`: Current position as Vector, Entity, or (x, y) tuple.

**Returns:** Next position as Vector, or None if at root or unreachable.

#### `to_heightmap(size=None, unreachable=-1.0) -> HeightMap`

Convert distance field to a HeightMap.
Each cell's height equals its pathfinding distance from the root.
Useful for visualization, procedural terrain, or influence mapping.

**Arguments:**
- `size`: Optional (width, height) tuple. Defaults to dijkstra dimensions.
- `unreachable`: Value for cells that cannot reach root (default -1.0).

**Returns:** HeightMap with distance values as heights.

### DiscreteMap

DiscreteMap(size: tuple[int, int], fill: int = 0, enum: type[IntEnum] = None)

A 2D grid of uint8 values (0-255) for discrete/categorical data.

DiscreteMap provides memory-efficient storage for terrain types, region IDs,
walkability masks, and other categorical data. Uses 4x less memory than HeightMap
for the same dimensions.

Args:
    size: (width, height) dimensions. Immutable after creation.
    fill: Initial value for all cells (0-255). Default 0.
    enum: Optional IntEnum class for value interpretation.

Example:
    from enum import IntEnum
    class Terrain(IntEnum):
        WATER = 0
        GRASS = 1
        MOUNTAIN = 2

    dmap = mcrfpy.DiscreteMap((100, 100), fill=0, enum=Terrain)
    dmap.fill(Terrain.GRASS, pos=(10, 10), size=(20, 20))
    print(dmap[15, 15])  # Terrain.GRASS


**Properties:**
- `enum_type`: Optional IntEnum class for value interpretation.
- `size` *(read-only)*: Dimensions (width, height) of the map. Read-only.

**Methods:**

#### `add(other: DiscreteMap | int, *, pos=None, source_pos=None, size=None) -> DiscreteMap`

Add values from another map or a scalar, with saturation to 0-255.

**Arguments:**
- `other`: DiscreteMap to add, or int scalar to add to all cells
- `pos`: Destination start (x, y) in self (default: (0, 0))
- `source_pos`: Source start (x, y) in other (default: (0, 0))
- `size`: Region (width, height) (default: max overlapping area)

**Returns:** DiscreteMap: self, for method chaining

#### `bitwise_and(other: DiscreteMap, *, pos=None, source_pos=None, size=None) -> DiscreteMap`

Bitwise AND with another DiscreteMap.

**Arguments:**
- `other`: DiscreteMap for AND operation
- `pos`: Destination start (x, y) in self (default: (0, 0))
- `source_pos`: Source start (x, y) in other (default: (0, 0))
- `size`: Region (width, height) (default: max overlapping area)

**Returns:** DiscreteMap: self, for method chaining

#### `bitwise_or(other: DiscreteMap, *, pos=None, source_pos=None, size=None) -> DiscreteMap`

Bitwise OR with another DiscreteMap.

**Arguments:**
- `other`: DiscreteMap for OR operation
- `pos`: Destination start (x, y) in self (default: (0, 0))
- `source_pos`: Source start (x, y) in other (default: (0, 0))
- `size`: Region (width, height) (default: max overlapping area)

**Returns:** DiscreteMap: self, for method chaining

#### `bitwise_xor(other: DiscreteMap, *, pos=None, source_pos=None, size=None) -> DiscreteMap`

Bitwise XOR with another DiscreteMap.

**Arguments:**
- `other`: DiscreteMap for XOR operation
- `pos`: Destination start (x, y) in self (default: (0, 0))
- `source_pos`: Source start (x, y) in other (default: (0, 0))
- `size`: Region (width, height) (default: max overlapping area)

**Returns:** DiscreteMap: self, for method chaining

#### `bool(condition: int | set | callable) -> DiscreteMap`

Create binary mask from condition. Returns NEW DiscreteMap.

**Arguments:**
- `condition`: int: match that value; set: match any in set; callable: predicate

**Returns:** DiscreteMap: new map with 1 where condition true, 0 elsewhere

#### `clear() -> DiscreteMap`

Set all cells to 0. Equivalent to fill(0).

**Returns:** DiscreteMap: self, for method chaining

#### `copy_from(other: DiscreteMap, *, pos=None, source_pos=None, size=None) -> DiscreteMap`

Copy values from another DiscreteMap into the specified region.

**Arguments:**
- `other`: DiscreteMap to copy from
- `pos`: Destination start (x, y) in self (default: (0, 0))
- `source_pos`: Source start (x, y) in other (default: (0, 0))
- `size`: Region (width, height) (default: max overlapping area)

**Returns:** DiscreteMap: self, for method chaining

#### `count(value: int) -> int`

Count cells with the specified value.

**Arguments:**
- `value`: Value to count (0-255)

**Returns:** int: Number of cells with that value

#### `count_range(min_val: int, max_val: int) -> int`

Count cells with values in the specified range (inclusive).

**Arguments:**
- `min_val`: Minimum value (inclusive)
- `max_val`: Maximum value (inclusive)

**Returns:** int: Number of cells in range

#### `fill(value: int, *, pos=None, size=None) -> DiscreteMap`

Set cells in region to the specified value.

**Arguments:**
- `value`: The value to set (0-255, or IntEnum member)
- `pos`: Region start (x, y) in destination (default: (0, 0))
- `size`: Region (width, height) to fill (default: remaining space)

**Returns:** DiscreteMap: self, for method chaining

#### `from_bytes(data: bytes, size: tuple[int, int], *, enum: type = None) -> DiscreteMap`

Create a DiscreteMap from raw byte data.

**Arguments:**
- `data`: Raw cell data (one byte per cell, row-major)
- `size`: (width, height) dimensions
- `enum`: Optional IntEnum class for value interpretation

**Returns:** DiscreteMap: new map initialized from data

**Raises:** ValueError: Data length does not match width * height

#### `from_heightmap(hmap: HeightMap, mapping: list[tuple[tuple[float,float], int]], *, enum=None) -> DiscreteMap`

Create DiscreteMap from HeightMap using range-to-value mapping.

**Arguments:**
- `hmap`: HeightMap to convert
- `mapping`: List of ((min, max), value) tuples
- `enum`: Optional IntEnum class for value interpretation

**Returns:** DiscreteMap: new map with mapped values

#### `get(x, y) or (pos) -> int | Enum`

Get the value at integer coordinates.

**Returns:** int or enum member if enum_type is set

**Raises:** IndexError: Position is out of bounds

#### `histogram() -> dict[int, int]`

Get a histogram of value counts.

**Returns:** dict: {value: count} for all values present in the map

#### `invert() -> DiscreteMap`

Return NEW DiscreteMap with (255 - value) for each cell.

**Returns:** DiscreteMap: new inverted map (original unchanged)

#### `mask() -> memoryview`

Get raw uint8_t data as memoryview for libtcod compatibility.

**Returns:** memoryview: Direct access to internal buffer (read/write)

#### `max(other: DiscreteMap, *, pos=None, source_pos=None, size=None) -> DiscreteMap`

Set each cell to the maximum of this and another DiscreteMap.

**Arguments:**
- `other`: DiscreteMap to compare with
- `pos`: Destination start (x, y) in self (default: (0, 0))
- `source_pos`: Source start (x, y) in other (default: (0, 0))
- `size`: Region (width, height) (default: max overlapping area)

**Returns:** DiscreteMap: self, for method chaining

#### `min(other: DiscreteMap, *, pos=None, source_pos=None, size=None) -> DiscreteMap`

Set each cell to the minimum of this and another DiscreteMap.

**Arguments:**
- `other`: DiscreteMap to compare with
- `pos`: Destination start (x, y) in self (default: (0, 0))
- `source_pos`: Source start (x, y) in other (default: (0, 0))
- `size`: Region (width, height) (default: max overlapping area)

**Returns:** DiscreteMap: self, for method chaining

#### `min_max() -> tuple[int, int]`

Get the minimum and maximum values in the map.

**Returns:** tuple[int, int]: (min_value, max_value)

#### `multiply(factor: float, *, pos=None, size=None) -> DiscreteMap`

Multiply values by a scalar factor, with saturation to 0-255.

**Arguments:**
- `factor`: Multiplier for each cell
- `pos`: Region start (x, y) (default: (0, 0))
- `size`: Region (width, height) (default: entire map)

**Returns:** DiscreteMap: self, for method chaining

#### `set(x: int, y: int, value: int) -> None`

Set the value at integer coordinates.

**Arguments:**
- `x`: X coordinate
- `y`: Y coordinate
- `value`: Value to set (0-255, or IntEnum member)

**Raises:** IndexError: Position is out of bounds ValueError: Value out of range 0-255

#### `subtract(other: DiscreteMap | int, *, pos=None, source_pos=None, size=None) -> DiscreteMap`

Subtract values from another map or a scalar, with saturation to 0-255.

**Arguments:**
- `other`: DiscreteMap to subtract, or int scalar
- `pos`: Destination start (x, y) in self (default: (0, 0))
- `source_pos`: Source start (x, y) in other (default: (0, 0))
- `size`: Region (width, height) (default: max overlapping area)

**Returns:** DiscreteMap: self, for method chaining

#### `to_bytes() -> bytes`

Serialize map data to bytes (row-major, one byte per cell).

**Returns:** bytes: Raw cell data, length = width * height

#### `to_heightmap(mapping: dict[int, float] = None) -> HeightMap`

Convert to HeightMap, optionally mapping values to floats.

**Arguments:**
- `mapping`: Optional {int: float} mapping (default: direct cast)

**Returns:** HeightMap: new heightmap with converted values

### Drawable

Base class for all drawable UI elements

**Properties:**
- `on_click`: Callable executed when object is clicked. Function receives (pos: Vector, button: str, action: str).
- `opacity`: Opacity level (0.0 = transparent, 1.0 = opaque). Automatically clamped to valid range [0.0, 1.0].
- `visible`: Whether the object is visible (bool). Invisible objects are not rendered or clickable.
- `z_index`: Z-order for rendering (lower values rendered first). Automatically triggers scene resort when changed.

**Methods:**

#### `move(dx, dy) or (delta) -> None`

Move the element by a relative offset.

Note:

**Arguments:**
- `dx`: Horizontal offset in pixels (or use delta)
- `dy`: Vertical offset in pixels (or use delta)
- `delta`: Offset as tuple, list, or Vector: (dx, dy)

#### `resize(width, height) or (size) -> None`

Resize the element to new dimensions.

Note:

**Arguments:**
- `width`: New width in pixels (or use size)
- `height`: New height in pixels (or use size)
- `size`: Size as tuple, list, or Vector: (width, height)

### Easing

*Inherits from: IntEnum*

**Properties:**
- `denominator`: the denominator of a rational number in lowest terms
- `imag`: the imaginary part of a complex number
- `numerator`: the numerator of a rational number in lowest terms
- `real`: the real part of a complex number

**Methods:**

#### `as_integer_ratio(...)`

Return a pair of integers, whose ratio is equal to the original int.
The ratio is in lowest terms and has a positive denominator.
>>> (10).as_integer_ratio()
(10, 1)
>>> (-10).as_integer_ratio()
(-10, 1)
>>> (0).as_integer_ratio()
(0, 1)

#### `bit_count(...)`

Number of ones in the binary representation of the absolute value of self.
Also known as the population count.
>>> bin(13)
'0b1101'
>>> (13).bit_count()
3

#### `bit_length(...)`

Number of bits necessary to represent self in binary.
>>> bin(37)
'0b100101'
>>> (37).bit_length()
6

#### `conjugate(...)`

Returns self, the complex conjugate of any int.

#### `from_bytes(...)`

Return the integer represented by the given array of bytes.
  bytes
    Holds the array of bytes to convert.  The argument must either
    support the buffer protocol or be an iterable object producing bytes.
    Bytes and bytearray are examples of built-in objects that support the
    buffer protocol.
  byteorder
    The byte order used to represent the integer.  If byteorder is 'big',
    the most significant byte is at the beginning of the byte array.  If
    byteorder is 'little', the most significant byte is at the end of the
    byte array.  To request the native byte order of the host system, use
    sys.byteorder as the byte order value.  Default is to use 'big'.
  signed
    Indicates whether two's complement is used to represent the integer.

#### `is_integer(...)`

Returns True. Exists for duck type compatibility with float.is_integer.

#### `to_bytes(...)`

Return an array of bytes representing an integer.
  length
    Length of bytes object to use.  An OverflowError is raised if the
    integer is not representable with the given number of bytes.  Default
    is length 1.
  byteorder
    The byte order used to represent the integer.  If byteorder is 'big',
    the most significant byte is at the beginning of the byte array.  If
    byteorder is 'little', the most significant byte is at the end of the
    byte array.  To request the native byte order of the host system, use
    sys.byteorder as the byte order value.  Default is to use 'big'.
  signed
    Determines whether two's complement is used to represent the integer.
    If signed is False and a negative integer is given, an OverflowError
    is raised.

### Entity

Entity(grid_pos=None, texture=None, sprite_index=0, **kwargs)

A game entity that exists on a grid with sprite rendering.

Args:
    grid_pos (tuple, optional): Grid position as (x, y) tuple. Default: (0, 0)
    texture (Texture, optional): Texture object for sprite. Default: default texture
    sprite_index (int, optional): Index into texture atlas. Default: 0

Keyword Args:
    grid (Grid): Grid to attach entity to. Default: None
    visible (bool): Visibility state. Default: True
    opacity (float): Opacity (0.0-1.0). Default: 1.0
    name (str): Element name for finding. Default: None
    x (float): X grid position override (tile coords). Default: 0
    y (float): Y grid position override (tile coords). Default: 0
    sprite_offset (tuple): Pixel offset for oversized sprites. Default: (0, 0)
    sprite_grid (list): Per-tile sprite indices for composite entities. Default: None

Attributes:
    pos (Vector): Pixel position relative to grid (requires grid attachment)
    x, y (float): Pixel position components (requires grid attachment)
    grid_pos (Vector): Integer tile coordinates (logical game position)
    grid_x, grid_y (int): Integer tile coordinate components
    draw_pos (Vector): Fractional tile position for smooth animation
    perspective_map (DiscreteMap | None): 3-state per-entity FOV memory
    sprite_index (int): Current sprite index
    visible (bool): Visibility state
    opacity (float): Opacity value
    name (str): Element name
    sprite_offset (Vector): Pixel offset for oversized sprites
    sprite_offset_x (float): X component of sprite offset
    sprite_offset_y (float): Y component of sprite offset

**Properties:**
- `behavior_type` *(read-only)*: Current behavior type (int, read-only). Use set_behavior() to change.
- `cell_pos`: Integer logical cell position (Vector). Decoupled from draw_pos. Determines which cell this entity logically occupies for collision, pathfinding, etc.
- `cell_x`: Integer X cell coordinate.
- `cell_y`: Integer Y cell coordinate.
- `default_behavior`: Default behavior type (int, maps to Behavior enum). Entity reverts to this after DONE trigger. Default: 0 (IDLE).
- `draw_pos`: Fractional tile position for rendering (Vector). Use for smooth animation between grid cells.
- `grid`: Grid this entity belongs to. Get: Returns the Grid or None. Set: Assign a Grid to move entity, or None to remove from grid.
- `grid_pos`: Grid position as integer cell coordinates (Vector). Alias for cell_pos.
- `grid_x`: Grid X position as integer cell coordinate. Alias for cell_x.
- `grid_y`: Grid Y position as integer cell coordinate. Alias for cell_y.
- `labels`: Set of string labels for collision/targeting (frozenset). Assign any iterable of strings to replace all labels.
- `move_speed`: Animation duration for behavior movement in seconds (float). 0 = instant. Default: 0.15.
- `name`: Name for finding elements
- `opacity`: Opacity (0.0 = transparent, 1.0 = opaque)
- `perspective_map`: Per-entity FOV memory (DiscreteMap, read-write). 3-state values per cell: 0 = unknown (never seen), 1 = discovered (seen before, not currently visible), 2 = visible (in current FOV). Use mcrfpy.Perspective enum for clarity. Lazy-allocated on first access once the entity has a grid; returns None otherwise. The returned DiscreteMap is a live reference -- mutations are visible to subsequent updateVisibility() calls. Assigning a DiscreteMap replaces the entity's memory; the new map's size must match the grid's size or ValueError is raised. Assign None to clear (will be lazy-reallocated on next access).
- `pos`: Pixel position relative to grid (Vector). Computed as draw_pos * tile_size. Requires entity to be attached to a grid.
- `shader`: Shader for GPU visual effects (Shader or None). When set, the entity is rendered through the shader program. Set to None to disable shader effects.
- `sight_radius`: FOV radius for TARGET trigger (int). Default: 10.
- `sprite_grid`: Per-tile sprite indices for composite multi-tile entities (list of lists or None). Row-major, dimensions must match tile_width x tile_height. Use -1 for empty tiles. When set, each tile renders its own sprite index instead of the single entity sprite.
- `sprite_index`: Sprite index on the texture on the display
- `sprite_offset`: Pixel offset for oversized sprites (Vector). Applied pre-zoom during grid rendering.
- `sprite_offset_x`: X component of sprite pixel offset.
- `sprite_offset_y`: Y component of sprite pixel offset.
- `step`: Step callback for grid.step() turn management. Called with (trigger, data) when behavior triggers fire. Set to None to clear.
- `target_label`: Label to search for with TARGET trigger (str or None). Default: None.
- `tile_height`: Entity height in tiles (int). Must be >= 1. Default 1.
- `tile_size`: Entity size in tiles as (width, height) Vector. Default (1, 1).
- `tile_width`: Entity width in tiles (int). Must be >= 1. Default 1.
- `turn_order`: Turn order for grid.step() (int). 0 = skip, higher values go later. Default: 1.
- `uniforms` *(read-only)*: Collection of shader uniforms (read-only access to collection). Set uniforms via dict-like syntax: entity.uniforms['name'] = value. Supports float, vec2/3/4 tuples, PropertyBinding, and CallableBinding.
- `visible`: Visibility flag
- `x`: Pixel X position relative to grid. Requires entity to be attached to a grid.
- `y`: Pixel Y position relative to grid. Requires entity to be attached to a grid.

**Methods:**

#### `add_label(label: str) -> None`

Add a label to this entity. Idempotent (adding same label twice is safe).

#### `animate(property: str, target: Any, duration: float, easing=None, delta=False, loop=False, callback=None, conflict_mode='replace') -> Animation`

Create and start an animation on this entity's property.

Note:

**Arguments:**
- `property`: Name of the property to animate: 'draw_x', 'draw_y' (tile coords), 'sprite_scale', 'sprite_index'
- `target`: Target value - float, int, or list of int (for sprite frame sequences)
- `duration`: Animation duration in seconds
- `easing`: Easing function: Easing enum value, string name, or None for linear
- `delta`: If True, target is relative to current value; if False, target is absolute
- `loop`: If True, animation repeats from start when it reaches the end (default False)
- `callback`: Optional callable invoked when animation completes (not called for looping animations)
- `conflict_mode`: 'replace' (default), 'queue', or 'error' if property already animating

**Returns:** Animation object for monitoring progress

**Raises:** ValueError: If property name is not valid for Entity (draw_x, draw_y, sprite_scale, sprite_index) Use 'draw_x'/'draw_y' to animate tile coordinates for smooth movement between grid cells. Use list target with loop=True for repeating sprite frame animations.

#### `at(x, y) or at(pos) -> GridPoint | None`

Return the GridPoint at (x, y) if currently VISIBLE to this entity's
perspective_map, otherwise None. Equivalent to:
    grid.at(x, y) if perspective_map[x, y] == Perspective.VISIBLE else None
To inspect discovered-but-not-visible cells, read entity.perspective_map[x, y]
directly and use grid.at(x, y) for cell data.

**Arguments:**
- `pos`: Grid coordinates as tuple, list, or Vector

#### `die(...)`

Remove this entity from its grid.
Warning: Do not call during iteration over grid.entities.
Modifying the collection during iteration raises RuntimeError.

#### `find_path(target, diagonal_cost=1.41, collide=None) -> AStarPath | None`

Find a path from this entity to the target position.

**Arguments:**
- `target`: Target as Vector, Entity, or (x, y) tuple.
- `diagonal_cost`: Cost of diagonal movement (default 1.41).
- `collide`: Label string. Entities with this label block pathfinding.

**Returns:** AStarPath object, or None if no path exists.

#### `has_label(label: str) -> bool`

Check if this entity has the given label.

#### `index(...)`

Return the index of this entity in its grid's entity collection

#### `move(dx, dy) or (delta) -> None`

Move the element by a relative offset.

Note:

**Arguments:**
- `dx`: Horizontal offset in pixels (or use delta)
- `dy`: Vertical offset in pixels (or use delta)
- `delta`: Offset as tuple, list, or Vector: (dx, dy)

#### `path_to(x, y) or path_to(target) -> list`

Find a path to the target position using Dijkstra pathfinding.

**Arguments:**
- `target`: Target coordinates as tuple, list, or Vector

**Returns:** List of (x, y) tuples representing the path.

#### `remove_label(label: str) -> None`

Remove a label from this entity. No-op if label not present.

#### `resize(width, height) or (size) -> None`

Resize the element to new dimensions.

Note:

**Arguments:**
- `width`: New width in pixels (or use size)
- `height`: New height in pixels (or use size)
- `size`: Size as tuple, list, or Vector: (width, height)

#### `set_behavior(type, waypoints=None, turns=0, path=None) -> None`

Configure this entity's behavior for grid.step() turn management.

#### `update_visibility() -> None`

Update entity's visibility state based on current FOV.
Recomputes which cells are visible from the entity's position and updates
the entity's perspective_map (see entity.perspective_map and mcrfpy.Perspective).
This is called automatically when the entity moves if it has a grid with
perspective set.

#### `visible_entities(fov=None, radius=None) -> list[Entity]`

Get list of other entities visible from this entity's position.

**Returns:** List of Entity objects that are within field of view. Computes FOV from this entity's position and returns all other entities whose positions fall within the visible area.

### Entity3D

Entity3D(pos=None, **kwargs)

A 3D game entity that exists on a Viewport3D's navigation grid.

Args:
    pos (tuple, optional): Grid position as (x, z). Default: (0, 0)

Keyword Args:
    viewport (Viewport3D): Viewport to attach entity to. Default: None
    rotation (float): Y-axis rotation in degrees. Default: 0
    scale (float or tuple): Scale factor. Default: 1.0
    visible (bool): Visibility state. Default: True
    color (Color): Entity color. Default: orange

Attributes:
    pos (tuple): Grid position (x, z) - setting triggers movement
    grid_pos (tuple): Same as pos (read-only)
    world_pos (tuple): Current world coordinates (x, y, z) (read-only)
    rotation (float): Y-axis rotation in degrees
    scale (float): Uniform scale factor
    visible (bool): Visibility state
    color (Color): Entity render color
    viewport (Viewport3D): Owning viewport (read-only)

**Properties:**
- `anim_clip`: Current animation clip name. Set to play an animation.
- `anim_frame` *(read-only)*: Current animation frame number (read-only, approximate at 30fps).
- `anim_loop`: Whether animation loops when it reaches the end.
- `anim_paused`: Whether animation playback is paused.
- `anim_speed`: Animation playback speed multiplier. 1.0 = normal speed.
- `anim_time`: Current time position in animation (seconds).
- `auto_animate`: Enable auto-play of walk/idle clips based on movement.
- `color`: Entity render color.
- `grid_pos`: Grid position (x, z). Same as pos.
- `idle_clip`: Animation clip to play when entity is stationary.
- `is_moving` *(read-only)*: Whether entity is currently moving (read-only).
- `model`: 3D model (Model3D). If None, uses placeholder cube.
- `name`: Entity name (str). Used for find() lookup.
- `on_anim_complete`: Callback(entity, clip_name) when non-looping animation ends.
- `pos`: Grid position (x, z). Setting triggers smooth movement.
- `rotation`: Y-axis rotation in degrees.
- `scale`: Uniform scale factor. Can also set as (x, y, z) tuple.
- `viewport` *(read-only)*: Owning Viewport3D (read-only).
- `visible`: Visibility state.
- `walk_clip`: Animation clip to play when entity is moving.
- `world_pos` *(read-only)*: Current world position (x, y, z) (read-only). Includes animation interpolation.

**Methods:**

#### `animate(property, target, duration, easing=None, delta=False, callback=None, conflict_mode=None)`

Animate a property over time.

**Arguments:**
- `property`: Property name (x, y, z, rotation, scale, etc.)
- `target`: Target value (float or int)
- `duration`: Animation duration in seconds
- `easing`: Easing function (Easing enum or None for linear)
- `delta`: If True, target is relative to current value
- `callback`: Called with (target, property, value) when complete
- `conflict_mode`: 'replace', 'queue', or 'error'

#### `at(x, z) -> dict`

Get visibility state for a cell from this entity's perspective.
Returns dict with 'visible' and 'discovered' boolean keys.

#### `clear_path()`

Clear the movement queue and stop at current position.

#### `follow_path(path)`

Queue path positions for smooth movement.

**Arguments:**
- `path`: List of (x, z) tuples (as returned by path_to())

#### `path_to(x, z) or path_to(pos=(x, z)) -> list`

Compute A* path to target position.
Returns list of (x, z) tuples, or empty list if no path exists.

#### `teleport(x, z) or teleport(pos=(x, z))`

Instantly move to target position without animation.

#### `update_visibility()`

Recompute field of view from current position.

### EntityCollection3D

Collection of Entity3D objects belonging to a Viewport3D.

Supports list-like operations: indexing, iteration, append, remove.

Example:
    viewport.entities.append(entity)
    for entity in viewport.entities:
        print(entity.pos)

**Methods:**

#### `append(entity)`

Add an Entity3D to the collection.

#### `clear()`

Remove all entities from the collection.

#### `extend(iterable)`

Add all Entity3D objects from iterable to the collection.

#### `find(name) -> Entity3D or None`

Find an Entity3D by name. Returns None if not found.

#### `pop(index=-1) -> Entity3D`

Remove and return Entity3D at index (default: last).

#### `remove(entity)`

Remove an Entity3D from the collection.

### EntityCollection3DIter

Iterator for EntityCollection3D

**Methods:**

### FOV

*Inherits from: IntEnum*

**Properties:**
- `denominator`: the denominator of a rational number in lowest terms
- `imag`: the imaginary part of a complex number
- `numerator`: the numerator of a rational number in lowest terms
- `real`: the real part of a complex number

**Methods:**

#### `as_integer_ratio(...)`

Return a pair of integers, whose ratio is equal to the original int.
The ratio is in lowest terms and has a positive denominator.
>>> (10).as_integer_ratio()
(10, 1)
>>> (-10).as_integer_ratio()
(-10, 1)
>>> (0).as_integer_ratio()
(0, 1)

#### `bit_count(...)`

Number of ones in the binary representation of the absolute value of self.
Also known as the population count.
>>> bin(13)
'0b1101'
>>> (13).bit_count()
3

#### `bit_length(...)`

Number of bits necessary to represent self in binary.
>>> bin(37)
'0b100101'
>>> (37).bit_length()
6

#### `conjugate(...)`

Returns self, the complex conjugate of any int.

#### `from_bytes(...)`

Return the integer represented by the given array of bytes.
  bytes
    Holds the array of bytes to convert.  The argument must either
    support the buffer protocol or be an iterable object producing bytes.
    Bytes and bytearray are examples of built-in objects that support the
    buffer protocol.
  byteorder
    The byte order used to represent the integer.  If byteorder is 'big',
    the most significant byte is at the beginning of the byte array.  If
    byteorder is 'little', the most significant byte is at the end of the
    byte array.  To request the native byte order of the host system, use
    sys.byteorder as the byte order value.  Default is to use 'big'.
  signed
    Indicates whether two's complement is used to represent the integer.

#### `is_integer(...)`

Returns True. Exists for duck type compatibility with float.is_integer.

#### `to_bytes(...)`

Return an array of bytes representing an integer.
  length
    Length of bytes object to use.  An OverflowError is raised if the
    integer is not representable with the given number of bytes.  Default
    is length 1.
  byteorder
    The byte order used to represent the integer.  If byteorder is 'big',
    the most significant byte is at the beginning of the byte array.  If
    byteorder is 'little', the most significant byte is at the end of the
    byte array.  To request the native byte order of the host system, use
    sys.byteorder as the byte order value.  Default is to use 'big'.
  signed
    Determines whether two's complement is used to represent the integer.
    If signed is False and a negative integer is given, an OverflowError
    is raised.

### Font

Font(filename: str)

A font resource for rendering text in Caption elements.

Args:
    filename: Path to a TrueType (.ttf) or OpenType (.otf) font file.

Properties:
    family (str, read-only): Font family name from metadata.
    source (str, read-only): File path used to load this font.


**Properties:**
- `family` *(read-only)*: Font family name (str, read-only). Retrieved from font metadata.
- `source` *(read-only)*: Source filename path (str, read-only). The path used to load this font.

**Methods:**

### Frame

*Inherits from: Drawable*

Frame(pos=None, size=None, **kwargs)

A rectangular frame UI element that can contain other drawable elements.

Args:
    pos (tuple, optional): Position as (x, y) tuple. Default: (0, 0)
    size (tuple, optional): Size as (width, height) tuple. Default: (0, 0)

Keyword Args:
    fill_color (Color): Background fill color. Default: (0, 0, 0, 128)
    outline_color (Color): Border outline color. Default: (255, 255, 255, 255)
    outline (float): Border outline thickness. Default: 0
    click (callable): Click event handler. Default: None
    children (list): Initial list of child drawable elements. Default: None
    visible (bool): Visibility state. Default: True
    opacity (float): Opacity (0.0-1.0). Default: 1.0
    z_index (int): Rendering order. Default: 0
    name (str): Element name for finding. Default: None
    x (float): X position override. Default: 0
    y (float): Y position override. Default: 0
    w (float): Width override. Default: 0
    h (float): Height override. Default: 0
    clip_children (bool): Whether to clip children to frame bounds. Default: False
    cache_subtree (bool): Cache rendering to texture for performance. Default: False
    align (Alignment): Alignment relative to parent. Default: None (manual positioning)
    margin (float): Margin from parent edge when aligned. Default: 0
    horiz_margin (float): Horizontal margin override. Default: 0 (use margin)
    vert_margin (float): Vertical margin override. Default: 0 (use margin)

Attributes:
    x, y (float): Position in pixels
    w, h (float): Size in pixels
    pos (Vector): Position as a Vector object
    fill_color, outline_color (Color): Visual appearance
    outline (float): Border thickness
    click (callable): Click event handler
    children (list): Collection of child drawable elements
    visible (bool): Visibility state
    opacity (float): Opacity value
    z_index (int): Rendering order
    name (str): Element name
    clip_children (bool): Whether to clip children to frame bounds
    cache_subtree (bool): Cache subtree rendering to texture
    align (Alignment): Alignment relative to parent (or None)
    margin (float): General margin for alignment
    horiz_margin (float): Horizontal margin override
    vert_margin (float): Vertical margin override

**Properties:**
- `align`: Alignment relative to parent bounds (Alignment enum or None). When set, position is automatically calculated when parent is assigned or resized. Set to None to disable alignment and use manual positioning.
- `bounds`: Bounding box as (pos, size) tuple of Vectors. Returns (Vector(x, y), Vector(width, height)).
- `cache_subtree`: #144: Cache subtree rendering to texture for performance
- `children`: UICollection of objects on top of this one
- `clip_children`: Whether to clip children to frame bounds
- `fill_color`: Fill color of the rectangle. Returns a copy; modifying components requires reassignment. For animation, use 'fill_color.r', 'fill_color.g', etc.
- `global_bounds`: Bounding box as (pos, size) tuple of Vectors in screen coordinates. Returns (Vector(x, y), Vector(width, height)).
- `global_position` *(read-only)*: Global screen position (read-only). Calculates absolute position by walking up the parent chain.
- `grid_pos`: Position in grid tile coordinates (only when parent is Grid)
- `grid_size`: Size in grid tile coordinates (only when parent is Grid)
- `h`: height of the rectangle
- `horiz_margin`: Horizontal margin override (float, 0 = use general margin). Invalid for vertically-centered alignments (TOP_CENTER, BOTTOM_CENTER, CENTER).
- `hovered` *(read-only)*: Whether mouse is currently over this element (read-only). Updated automatically by the engine during mouse movement.
- `margin`: General margin from edge when aligned (float). Applied to both horizontal and vertical edges unless overridden. Invalid for CENTER alignment (raises ValueError).
- `name`: Name for finding elements
- `on_click`: Callable executed when object is clicked. Function receives (pos: Vector, button: str, action: str).
- `on_enter`: Callback for mouse enter events. Called with (pos: Vector, button: str, action: str) when mouse enters this element's bounds.
- `on_exit`: Callback for mouse exit events. Called with (pos: Vector, button: str, action: str) when mouse leaves this element's bounds.
- `on_move`: Callback for mouse movement within bounds. Called with (pos: Vector, button: str, action: str) for each mouse movement while inside. Performance note: Called frequently during movement - keep handlers fast.
- `opacity`: Opacity level (0.0 = transparent, 1.0 = opaque). Automatically clamped to valid range [0.0, 1.0].
- `origin`: Transform origin as Vector (pivot point for rotation). Default (0,0) is top-left; set to (w/2, h/2) to rotate around center.
- `outline`: Thickness of the border
- `outline_color`: Outline color of the rectangle. Returns a copy; modifying components requires reassignment. For animation, use 'outline_color.r', 'outline_color.g', etc.
- `parent`: Parent drawable. Get: Returns the parent Frame/Grid if nested, or None if at scene level. Set: Assign a Frame/Grid to reparent, or None to remove from parent.
- `pos`: Position as a Vector
- `rotate_with_camera`: Whether to rotate visually with parent Grid's camera_rotation (bool). False (default): stay screen-aligned. True: tilt with camera. Only affects children of UIGrid; ignored for other parents.
- `rotation`: Rotation angle in degrees (clockwise around origin). Animatable property.
- `shader`: Shader for GPU visual effects (Shader or None). When set, the drawable is rendered through the shader program. Set to None to disable shader effects.
- `uniforms` *(read-only)*: Collection of shader uniforms (read-only access to collection). Set uniforms via dict-like syntax: drawable.uniforms['name'] = value. Supports float, vec2/3/4 tuples, PropertyBinding, and CallableBinding.
- `vert_margin`: Vertical margin override (float, 0 = use general margin). Invalid for horizontally-centered alignments (CENTER_LEFT, CENTER_RIGHT, CENTER).
- `visible`: Whether the object is visible (bool). Invisible objects are not rendered or clickable.
- `w`: width of the rectangle
- `x`: X coordinate of top-left corner
- `y`: Y coordinate of top-left corner
- `z_index`: Z-order for rendering (lower values rendered first). Automatically triggers scene resort when changed.

**Methods:**

#### `animate(property: str, target: Any, duration: float, easing=None, delta=False, loop=False, callback=None, conflict_mode='replace') -> Animation`

Create and start an animation on this drawable's property.

Note:

**Arguments:**
- `property`: Name of the property to animate (e.g., 'x', 'fill_color', 'opacity')
- `target`: Target value - type depends on property (float, tuple for color/vector, etc.)
- `duration`: Animation duration in seconds
- `easing`: Easing function: Easing enum value, string name, or None for linear
- `delta`: If True, target is relative to current value; if False, target is absolute
- `loop`: If True, animation repeats from start when it reaches the end (default False)
- `callback`: Optional callable invoked when animation completes (not called for looping animations)
- `conflict_mode`: 'replace' (default), 'queue', or 'error' if property already animating

**Returns:** Animation object for monitoring progress

**Raises:** ValueError: If property name is not valid for this drawable type This is a convenience method that creates an Animation, starts it, and adds it to the AnimationManager.

#### `move(dx, dy) or (delta) -> None`

Move the element by a relative offset.

Note:

**Arguments:**
- `dx`: Horizontal offset in pixels (or use delta)
- `dy`: Vertical offset in pixels (or use delta)
- `delta`: Offset as tuple, list, or Vector: (dx, dy)

#### `realign() -> None`

Reapply alignment relative to parent, useful for responsive layouts.

Note:
    Call this to recalculate position after parent changes size. For elements with align=None, this has no effect.

#### `resize(width, height) or (size) -> None`

Resize the element to new dimensions.

Note:

**Arguments:**
- `width`: New width in pixels (or use size)
- `height`: New height in pixels (or use size)
- `size`: Size as tuple, list, or Vector: (width, height)

### Grid

*Inherits from: Drawable*

Grid(grid_size=None, pos=None, size=None, texture=None, **kwargs)

A grid-based UI element for tile-based rendering and entity management.
Creates and owns grid data (cells, entities, layers) with an integrated
rendering view (camera, zoom, perspective).

Can also be constructed as a view of existing grid data:
    Grid(grid=existing_grid, pos=..., size=...)

Args:
    grid_size (tuple): Grid dimensions as (grid_w, grid_h). Default: (2, 2)
    pos (tuple): Position as (x, y). Default: (0, 0)
    size (tuple): Size as (w, h). Default: auto-calculated
    texture (Texture): Tile texture atlas. Default: default texture

Keyword Args:
    grid (Grid): Existing Grid to view (creates view of shared data).
    fill_color (Color): Background fill color.
    on_click (callable): Click event handler.
    center_x, center_y (float): Camera center coordinates.
    zoom (float): Zoom level. Default: 1.0
    visible (bool): Visibility. Default: True
    opacity (float): Opacity (0.0-1.0). Default: 1.0
    z_index (int): Rendering order. Default: 0
    name (str): Element name.
    layers (list): List of ColorLayer/TileLayer objects.


**Properties:**
- `align`: Alignment relative to parent bounds (Alignment enum or None). When set, position is automatically calculated when parent is assigned or resized. Set to None to disable alignment and use manual positioning.
- `bounds`: Bounding box as (pos, size) tuple of Vectors. Returns (Vector(x, y), Vector(width, height)).
- `camera_rotation`: Rotation of grid contents around camera center (degrees).
- `center`: Camera center point in pixel coordinates.
- `center_x`: center of the view X-coordinate
- `center_y`: center of the view Y-coordinate
- `fill_color`: Background fill color.
- `global_bounds`: Bounding box as (pos, size) tuple of Vectors in screen coordinates. Returns (Vector(x, y), Vector(width, height)).
- `global_position` *(read-only)*: Global screen position (read-only). Calculates absolute position by walking up the parent chain.
- `grid_data`: The underlying grid data object (for multi-view scenarios).
- `h`: visible widget height
- `horiz_margin`: Horizontal margin override (float, 0 = use general margin). Invalid for vertically-centered alignments (TOP_CENTER, BOTTOM_CENTER, CENTER).
- `hovered` *(read-only)*: Whether mouse is currently over this element (read-only). Updated automatically by the engine during mouse movement.
- `margin`: General margin from edge when aligned (float). Applied to both horizontal and vertical edges unless overridden. Invalid for CENTER alignment (raises ValueError).
- `name`: Name for finding elements
- `on_click`: Callable executed when object is clicked.
- `on_enter`: Callback for mouse enter events. Called with (pos: Vector, button: str, action: str) when mouse enters this element's bounds.
- `on_exit`: Callback for mouse exit events. Called with (pos: Vector, button: str, action: str) when mouse leaves this element's bounds.
- `on_move`: Callback for mouse movement within bounds. Called with (pos: Vector, button: str, action: str) for each mouse movement while inside. Performance note: Called frequently during movement - keep handlers fast.
- `opacity`: Opacity level (0.0 = transparent, 1.0 = opaque). Automatically clamped to valid range [0.0, 1.0].
- `origin`: Transform origin as Vector (pivot point for rotation). Default (0,0) is top-left; set to (w/2, h/2) to rotate around center.
- `parent`: Parent drawable. Get: Returns the parent Frame/Grid if nested, or None if at scene level. Set: Assign a Frame/Grid to reparent, or None to remove from parent.
- `pos`: Position of the grid as Vector
- `rotate_with_camera`: Whether to rotate visually with parent Grid's camera_rotation (bool). False (default): stay screen-aligned. True: tilt with camera. Only affects children of UIGrid; ignored for other parents.
- `rotation`: Rotation angle in degrees (clockwise around origin). Animatable property.
- `shader`: Shader for GPU visual effects (Shader or None). When set, the drawable is rendered through the shader program. Set to None to disable shader effects.
- `texture` *(read-only)*: Texture used for tile rendering (read-only).
- `uniforms` *(read-only)*: Collection of shader uniforms (read-only access to collection). Set uniforms via dict-like syntax: drawable.uniforms['name'] = value. Supports float, vec2/3/4 tuples, PropertyBinding, and CallableBinding.
- `vert_margin`: Vertical margin override (float, 0 = use general margin). Invalid for horizontally-centered alignments (CENTER_LEFT, CENTER_RIGHT, CENTER).
- `visible`: Whether the object is visible (bool). Invisible objects are not rendered or clickable.
- `w`: visible widget width
- `x`: top-left corner X-coordinate
- `y`: top-left corner Y-coordinate
- `z_index`: Z-order for rendering (lower values rendered first).
- `zoom`: Zoom level for rendering.

**Methods:**

#### `animate(property: str, target: Any, duration: float, easing=None, delta=False, loop=False, callback=None, conflict_mode='replace') -> Animation`

Create and start an animation on this drawable's property.

Note:

**Arguments:**
- `property`: Name of the property to animate (e.g., 'x', 'fill_color', 'opacity')
- `target`: Target value - type depends on property (float, tuple for color/vector, etc.)
- `duration`: Animation duration in seconds
- `easing`: Easing function: Easing enum value, string name, or None for linear
- `delta`: If True, target is relative to current value; if False, target is absolute
- `loop`: If True, animation repeats from start when it reaches the end (default False)
- `callback`: Optional callable invoked when animation completes (not called for looping animations)
- `conflict_mode`: 'replace' (default), 'queue', or 'error' if property already animating

**Returns:** Animation object for monitoring progress

**Raises:** ValueError: If property name is not valid for this drawable type This is a convenience method that creates an Animation, starts it, and adds it to the AnimationManager.

#### `move(dx, dy) or (delta) -> None`

Move the element by a relative offset.

Note:

**Arguments:**
- `dx`: Horizontal offset in pixels (or use delta)
- `dy`: Vertical offset in pixels (or use delta)
- `delta`: Offset as tuple, list, or Vector: (dx, dy)

#### `realign() -> None`

Reapply alignment relative to parent, useful for responsive layouts.

Note:
    Call this to recalculate position after parent changes size. For elements with align=None, this has no effect.

#### `resize(width, height) or (size) -> None`

Resize the element to new dimensions.

Note:

**Arguments:**
- `width`: New width in pixels (or use size)
- `height`: New height in pixels (or use size)
- `size`: Size as tuple, list, or Vector: (width, height)

### GridView

*Inherits from: Drawable*

Grid(grid_size=None, pos=None, size=None, texture=None, **kwargs)

A grid-based UI element for tile-based rendering and entity management.
Creates and owns grid data (cells, entities, layers) with an integrated
rendering view (camera, zoom, perspective).

Can also be constructed as a view of existing grid data:
    Grid(grid=existing_grid, pos=..., size=...)

Args:
    grid_size (tuple): Grid dimensions as (grid_w, grid_h). Default: (2, 2)
    pos (tuple): Position as (x, y). Default: (0, 0)
    size (tuple): Size as (w, h). Default: auto-calculated
    texture (Texture): Tile texture atlas. Default: default texture

Keyword Args:
    grid (Grid): Existing Grid to view (creates view of shared data).
    fill_color (Color): Background fill color.
    on_click (callable): Click event handler.
    center_x, center_y (float): Camera center coordinates.
    zoom (float): Zoom level. Default: 1.0
    visible (bool): Visibility. Default: True
    opacity (float): Opacity (0.0-1.0). Default: 1.0
    z_index (int): Rendering order. Default: 0
    name (str): Element name.
    layers (list): List of ColorLayer/TileLayer objects.


**Properties:**
- `align`: Alignment relative to parent bounds (Alignment enum or None). When set, position is automatically calculated when parent is assigned or resized. Set to None to disable alignment and use manual positioning.
- `bounds`: Bounding box as (pos, size) tuple of Vectors. Returns (Vector(x, y), Vector(width, height)).
- `camera_rotation`: Rotation of grid contents around camera center (degrees).
- `center`: Camera center point in pixel coordinates.
- `center_x`: center of the view X-coordinate
- `center_y`: center of the view Y-coordinate
- `fill_color`: Background fill color.
- `global_bounds`: Bounding box as (pos, size) tuple of Vectors in screen coordinates. Returns (Vector(x, y), Vector(width, height)).
- `global_position` *(read-only)*: Global screen position (read-only). Calculates absolute position by walking up the parent chain.
- `grid_data`: The underlying grid data object (for multi-view scenarios).
- `h`: visible widget height
- `horiz_margin`: Horizontal margin override (float, 0 = use general margin). Invalid for vertically-centered alignments (TOP_CENTER, BOTTOM_CENTER, CENTER).
- `hovered` *(read-only)*: Whether mouse is currently over this element (read-only). Updated automatically by the engine during mouse movement.
- `margin`: General margin from edge when aligned (float). Applied to both horizontal and vertical edges unless overridden. Invalid for CENTER alignment (raises ValueError).
- `name`: Name for finding elements
- `on_click`: Callable executed when object is clicked.
- `on_enter`: Callback for mouse enter events. Called with (pos: Vector, button: str, action: str) when mouse enters this element's bounds.
- `on_exit`: Callback for mouse exit events. Called with (pos: Vector, button: str, action: str) when mouse leaves this element's bounds.
- `on_move`: Callback for mouse movement within bounds. Called with (pos: Vector, button: str, action: str) for each mouse movement while inside. Performance note: Called frequently during movement - keep handlers fast.
- `opacity`: Opacity level (0.0 = transparent, 1.0 = opaque). Automatically clamped to valid range [0.0, 1.0].
- `origin`: Transform origin as Vector (pivot point for rotation). Default (0,0) is top-left; set to (w/2, h/2) to rotate around center.
- `parent`: Parent drawable. Get: Returns the parent Frame/Grid if nested, or None if at scene level. Set: Assign a Frame/Grid to reparent, or None to remove from parent.
- `pos`: Position of the grid as Vector
- `rotate_with_camera`: Whether to rotate visually with parent Grid's camera_rotation (bool). False (default): stay screen-aligned. True: tilt with camera. Only affects children of UIGrid; ignored for other parents.
- `rotation`: Rotation angle in degrees (clockwise around origin). Animatable property.
- `shader`: Shader for GPU visual effects (Shader or None). When set, the drawable is rendered through the shader program. Set to None to disable shader effects.
- `texture` *(read-only)*: Texture used for tile rendering (read-only).
- `uniforms` *(read-only)*: Collection of shader uniforms (read-only access to collection). Set uniforms via dict-like syntax: drawable.uniforms['name'] = value. Supports float, vec2/3/4 tuples, PropertyBinding, and CallableBinding.
- `vert_margin`: Vertical margin override (float, 0 = use general margin). Invalid for horizontally-centered alignments (CENTER_LEFT, CENTER_RIGHT, CENTER).
- `visible`: Whether the object is visible (bool). Invisible objects are not rendered or clickable.
- `w`: visible widget width
- `x`: top-left corner X-coordinate
- `y`: top-left corner Y-coordinate
- `z_index`: Z-order for rendering (lower values rendered first).
- `zoom`: Zoom level for rendering.

**Methods:**

#### `animate(property: str, target: Any, duration: float, easing=None, delta=False, loop=False, callback=None, conflict_mode='replace') -> Animation`

Create and start an animation on this drawable's property.

Note:

**Arguments:**
- `property`: Name of the property to animate (e.g., 'x', 'fill_color', 'opacity')
- `target`: Target value - type depends on property (float, tuple for color/vector, etc.)
- `duration`: Animation duration in seconds
- `easing`: Easing function: Easing enum value, string name, or None for linear
- `delta`: If True, target is relative to current value; if False, target is absolute
- `loop`: If True, animation repeats from start when it reaches the end (default False)
- `callback`: Optional callable invoked when animation completes (not called for looping animations)
- `conflict_mode`: 'replace' (default), 'queue', or 'error' if property already animating

**Returns:** Animation object for monitoring progress

**Raises:** ValueError: If property name is not valid for this drawable type This is a convenience method that creates an Animation, starts it, and adds it to the AnimationManager.

#### `move(dx, dy) or (delta) -> None`

Move the element by a relative offset.

Note:

**Arguments:**
- `dx`: Horizontal offset in pixels (or use delta)
- `dy`: Vertical offset in pixels (or use delta)
- `delta`: Offset as tuple, list, or Vector: (dx, dy)

#### `realign() -> None`

Reapply alignment relative to parent, useful for responsive layouts.

Note:
    Call this to recalculate position after parent changes size. For elements with align=None, this has no effect.

#### `resize(width, height) or (size) -> None`

Resize the element to new dimensions.

Note:

**Arguments:**
- `width`: New width in pixels (or use size)
- `height`: New height in pixels (or use size)
- `size`: Size as tuple, list, or Vector: (width, height)

### HeightMap

HeightMap(size: tuple[int, int], fill: float = 0.0)

A 2D grid of float values for procedural generation.

HeightMap is the universal canvas for procedural generation. It stores float values that can be manipulated, combined, and applied to Grid and Layer objects.

Args:
    size: (width, height) dimensions of the heightmap. Immutable after creation.
    fill: Initial value for all cells. Default 0.0.

Example:
    hmap = mcrfpy.HeightMap((100, 100))
    hmap.fill(0.5).scale(2.0).clamp(0.0, 1.0)
    value = hmap[5, 5]  # Subscript shorthand for get()


**Properties:**
- `size` *(read-only)*: Dimensions (width, height) of the heightmap. Read-only.

**Methods:**

#### `add(other: HeightMap, *, pos=None, source_pos=None, size=None) -> HeightMap`

Add another heightmap's values to this one in the specified region.

**Arguments:**
- `other`: HeightMap to add values from
- `pos`: Destination start (x, y) in self (default: (0, 0))
- `source_pos`: Source start (x, y) in other (default: (0, 0))
- `size`: Region (width, height) (default: max overlapping area)

**Returns:** HeightMap: self, for method chaining

#### `add_bsp(bsp: BSP, *, pos=None, select: str = 'leaves', nodes: list = None, shrink: int = 0, value: float = 1.0) -> HeightMap`

Add BSP node regions to heightmap. More efficient than creating intermediate HeightMap.

**Arguments:**
- `bsp`: BSP tree to sample from
- `pos`: Where BSP origin maps to in HeightMap (default: origin-relative like to_heightmap)
- `select`: 'leaves', 'all', or 'internal' (default: 'leaves')
- `nodes`: Override: specific BSPNodes only (default: None)
- `shrink`: Pixels to shrink from node bounds (default: 0)
- `value`: Value to add inside regions (default: 1.0)

**Returns:** HeightMap: self, for method chaining

#### `add_constant(value: float, *, pos=None, size=None) -> HeightMap`

Add a constant value to cells in region.

**Arguments:**
- `value`: The value to add to each cell
- `pos`: Region start (x, y) in destination (default: (0, 0))
- `size`: Region (width, height) (default: remaining space)

**Returns:** HeightMap: self, for method chaining

#### `add_hill(center, radius: float, height: float) -> HeightMap`

Add a smooth hill at the specified position.

**Arguments:**
- `center`: Center position as (x, y) tuple, list, or Vector
- `radius`: Radius of the hill in cells
- `height`: Height of the hill peak

**Returns:** HeightMap: self, for method chaining

#### `add_noise(source: NoiseSource, world_origin: tuple = (0.0, 0.0), world_size: tuple = None, mode: str = 'fbm', octaves: int = 4, scale: float = 1.0) -> HeightMap`

Sample noise and add to current values. More efficient than creating intermediate HeightMap.

**Arguments:**
- `source`: 2D NoiseSource to sample from
- `world_origin`: World coordinates of top-left (default: (0, 0))
- `world_size`: World area to sample (default: HeightMap size)
- `mode`: 'flat', 'fbm', or 'turbulence' (default: 'fbm')
- `octaves`: Octaves for fbm/turbulence (default: 4)
- `scale`: Multiplier for sampled values (default: 1.0)

**Returns:** HeightMap: self, for method chaining

#### `add_voronoi(num_points: int, coefficients: tuple = (1.0, -0.5), seed: int = None) -> HeightMap`

Add Voronoi-based terrain features.

**Arguments:**
- `num_points`: Number of Voronoi seed points
- `coefficients`: Coefficients for distance calculations (default: (1.0, -0.5))
- `seed`: Random seed (None for random)

**Returns:** HeightMap: self, for method chaining

#### `clamp(min: float = 0.0, max: float = 1.0, *, pos=None, size=None) -> HeightMap`

Clamp values in region to the specified range.

**Arguments:**
- `min`: Minimum value (default 0.0)
- `max`: Maximum value (default 1.0)
- `pos`: Region start (x, y) in destination (default: (0, 0))
- `size`: Region (width, height) (default: remaining space)

**Returns:** HeightMap: self, for method chaining

#### `clear() -> HeightMap`

Set all cells to 0.0. Equivalent to fill(0.0).

**Returns:** HeightMap: self, for method chaining

#### `copy_from(other: HeightMap, *, pos=None, source_pos=None, size=None) -> HeightMap`

Copy values from another heightmap into the specified region.

**Arguments:**
- `other`: HeightMap to copy from
- `pos`: Destination start (x, y) in self (default: (0, 0))
- `source_pos`: Source start (x, y) in other (default: (0, 0))
- `size`: Region (width, height) (default: max overlapping area)

**Returns:** HeightMap: self, for method chaining

#### `count_in_range(range: tuple[float, float]) -> int`

Count cells with values in the specified range (inclusive).

**Arguments:**
- `range`: Value range as (min, max) tuple or list

**Returns:** int: Number of cells with values in range

**Raises:** ValueError: min > max

#### `dig_bezier(points: tuple, start_radius: float, end_radius: float, start_height: float, end_height: float) -> HeightMap`

Construct a canal along a cubic Bezier curve with specified heights.

Note:

**Arguments:**
- `points`: Four control points as ((x0,y0), (x1,y1), (x2,y2), (x3,y3))
- `start_radius`: Radius at start of path
- `end_radius`: Radius at end of path
- `start_height`: Target height at start of path
- `end_height`: Target height at end of path

**Returns:** HeightMap: self, for method chaining Only lowers cells; cells below target height are unchanged

#### `dig_hill(center, radius: float, target_height: float) -> HeightMap`

Construct a pit or crater with the specified center height.

Note:

**Arguments:**
- `center`: Center position as (x, y) tuple, list, or Vector
- `radius`: Radius of the crater in cells
- `target_height`: Height at the center of the pit

**Returns:** HeightMap: self, for method chaining Only lowers cells; cells below target_height are unchanged

#### `fill(value: float, *, pos=None, size=None) -> HeightMap`

Set cells in region to the specified value.

**Arguments:**
- `value`: The value to set
- `pos`: Region start (x, y) in destination (default: (0, 0))
- `size`: Region (width, height) to fill (default: remaining space)

**Returns:** HeightMap: self, for method chaining

#### `get(x, y) or (pos) -> float`

Get the height value at integer coordinates.

**Returns:** float: Height value at that position

**Raises:** IndexError: Position is out of bounds

#### `get_interpolated(x, y) or (pos) -> float`

Get interpolated height value at non-integer coordinates.

**Returns:** float: Bilinearly interpolated height value

#### `get_normal(x, y, water_level=0.0) or (pos, water_level=0.0) -> tuple[float, float, float]`

Get the normal vector at given coordinates for lighting calculations.

**Arguments:**
- `water_level`: Water level below which terrain is considered flat (default 0.0)

**Returns:** tuple[float, float, float]: Normal vector (nx, ny, nz)

#### `get_slope(x, y) or (pos) -> float`

Get the slope at integer coordinates, from 0 (flat) to pi/2 (vertical).

**Returns:** float: Slope angle in radians (0 to pi/2)

**Raises:** IndexError: Position is out of bounds

#### `inverse() -> HeightMap`

Return NEW HeightMap with (1.0 - value) for each cell.

**Returns:** HeightMap: New inverted HeightMap (original is unchanged)

#### `lerp(other: HeightMap, t: float, *, pos=None, source_pos=None, size=None) -> HeightMap`

Linear interpolation between this and another heightmap in the specified region.

**Arguments:**
- `other`: HeightMap to interpolate towards
- `t`: Interpolation factor (0.0 = this, 1.0 = other)
- `pos`: Destination start (x, y) in self (default: (0, 0))
- `source_pos`: Source start (x, y) in other (default: (0, 0))
- `size`: Region (width, height) (default: max overlapping area)

**Returns:** HeightMap: self, for method chaining

#### `max(other: HeightMap, *, pos=None, source_pos=None, size=None) -> HeightMap`

Set each cell in region to the maximum of this and another heightmap.

**Arguments:**
- `other`: HeightMap to compare with
- `pos`: Destination start (x, y) in self (default: (0, 0))
- `source_pos`: Source start (x, y) in other (default: (0, 0))
- `size`: Region (width, height) (default: max overlapping area)

**Returns:** HeightMap: self, for method chaining

#### `mid_point_displacement(roughness: float = 0.5, seed: int = None) -> HeightMap`

Generate terrain using midpoint displacement algorithm (diamond-square).

Note:

**Arguments:**
- `roughness`: Controls terrain roughness (0.0-1.0, default 0.5)
- `seed`: Random seed (None for random)

**Returns:** HeightMap: self, for method chaining Works best with power-of-2+1 dimensions (e.g., 65x65, 129x129)

#### `min(other: HeightMap, *, pos=None, source_pos=None, size=None) -> HeightMap`

Set each cell in region to the minimum of this and another heightmap.

**Arguments:**
- `other`: HeightMap to compare with
- `pos`: Destination start (x, y) in self (default: (0, 0))
- `source_pos`: Source start (x, y) in other (default: (0, 0))
- `size`: Region (width, height) (default: max overlapping area)

**Returns:** HeightMap: self, for method chaining

#### `min_max() -> tuple[float, float]`

Get the minimum and maximum height values in the map.

**Returns:** tuple[float, float]: (min_value, max_value)

#### `multiply(other: HeightMap, *, pos=None, source_pos=None, size=None) -> HeightMap`

Multiply this heightmap by another in the specified region (useful for masking).

**Arguments:**
- `other`: HeightMap to multiply by
- `pos`: Destination start (x, y) in self (default: (0, 0))
- `source_pos`: Source start (x, y) in other (default: (0, 0))
- `size`: Region (width, height) (default: max overlapping area)

**Returns:** HeightMap: self, for method chaining

#### `multiply_bsp(bsp: BSP, *, pos=None, select: str = 'leaves', nodes: list = None, shrink: int = 0, value: float = 1.0) -> HeightMap`

Multiply by BSP regions. Effectively masks the heightmap to node interiors.

**Arguments:**
- `bsp`: BSP tree to sample from
- `pos`: Where BSP origin maps to in HeightMap (default: origin-relative like to_heightmap)
- `select`: 'leaves', 'all', or 'internal' (default: 'leaves')
- `nodes`: Override: specific BSPNodes only (default: None)
- `shrink`: Pixels to shrink from node bounds (default: 0)
- `value`: Value to multiply inside regions (default: 1.0)

**Returns:** HeightMap: self, for method chaining

#### `multiply_noise(source: NoiseSource, world_origin: tuple = (0.0, 0.0), world_size: tuple = None, mode: str = 'fbm', octaves: int = 4, scale: float = 1.0) -> HeightMap`

Sample noise and multiply with current values. Useful for applying noise-based masks.

**Arguments:**
- `source`: 2D NoiseSource to sample from
- `world_origin`: World coordinates of top-left (default: (0, 0))
- `world_size`: World area to sample (default: HeightMap size)
- `mode`: 'flat', 'fbm', or 'turbulence' (default: 'fbm')
- `octaves`: Octaves for fbm/turbulence (default: 4)
- `scale`: Multiplier for sampled values (default: 1.0)

**Returns:** HeightMap: self, for method chaining

#### `normalize(min: float = 0.0, max: float = 1.0, *, pos=None, size=None) -> HeightMap`

Linearly rescale values in region. Current min becomes new min, current max becomes new max.

**Arguments:**
- `min`: Target minimum value (default 0.0)
- `max`: Target maximum value (default 1.0)
- `pos`: Region start (x, y) in destination (default: (0, 0))
- `size`: Region (width, height) (default: remaining space)

**Returns:** HeightMap: self, for method chaining

#### `rain_erosion(drops: int, erosion: float = 0.1, sedimentation: float = 0.05, seed: int = None) -> HeightMap`

Simulate rain erosion on the terrain.

**Arguments:**
- `drops`: Number of rain drops to simulate
- `erosion`: Erosion coefficient (default 0.1)
- `sedimentation`: Sedimentation coefficient (default 0.05)
- `seed`: Random seed (None for random)

**Returns:** HeightMap: self, for method chaining

#### `scale(factor: float, *, pos=None, size=None) -> HeightMap`

Multiply cells in region by a factor.

**Arguments:**
- `factor`: The multiplier for each cell
- `pos`: Region start (x, y) in destination (default: (0, 0))
- `size`: Region (width, height) (default: remaining space)

**Returns:** HeightMap: self, for method chaining

#### `smooth(iterations: int = 1) -> HeightMap`

Smooth the heightmap by averaging neighboring cells.

**Arguments:**
- `iterations`: Number of smoothing passes (default 1)

**Returns:** HeightMap: self, for method chaining

#### `sparse_kernel(weights: dict[tuple[int, int], float]) -> HeightMap`

Apply sparse convolution kernel, returning a NEW HeightMap with results.

**Arguments:**
- `weights`: Dict mapping (dx, dy) offsets to weight values

**Returns:** HeightMap: new heightmap with convolution result

#### `sparse_kernel_from(source: HeightMap, weights: dict[tuple[int, int], float]) -> None`

Apply sparse convolution from source heightmap into self (for reusing destination buffers).

**Arguments:**
- `source`: Source HeightMap to convolve from
- `weights`: Dict mapping (dx, dy) offsets to weight values

**Returns:** None

#### `subtract(other: HeightMap, *, pos=None, source_pos=None, size=None) -> HeightMap`

Subtract another heightmap's values from this one in the specified region.

**Arguments:**
- `other`: HeightMap to subtract values from
- `pos`: Destination start (x, y) in self (default: (0, 0))
- `source_pos`: Source start (x, y) in other (default: (0, 0))
- `size`: Region (width, height) (default: max overlapping area)

**Returns:** HeightMap: self, for method chaining

#### `threshold(range: tuple[float, float]) -> HeightMap`

Return NEW HeightMap with original values where in range, 0.0 elsewhere.

**Arguments:**
- `range`: Value range as (min, max) tuple or list, inclusive

**Returns:** HeightMap: New HeightMap (original is unchanged)

**Raises:** ValueError: min > max

#### `threshold_binary(range: tuple[float, float], value: float = 1.0) -> HeightMap`

Return NEW HeightMap with uniform value where in range, 0.0 elsewhere.

**Arguments:**
- `range`: Value range as (min, max) tuple or list, inclusive
- `value`: Value to set for cells in range (default 1.0)

**Returns:** HeightMap: New HeightMap (original is unchanged)

**Raises:** ValueError: min > max

### InputState

*Inherits from: IntEnum*

Enum representing input event states (pressed/released).

Values:
    PRESSED: Key or button was pressed
    RELEASED: Key or button was released


**Properties:**
- `denominator`: the denominator of a rational number in lowest terms
- `imag`: the imaginary part of a complex number
- `numerator`: the numerator of a rational number in lowest terms
- `real`: the real part of a complex number

**Methods:**

#### `as_integer_ratio(...)`

Return a pair of integers, whose ratio is equal to the original int.
The ratio is in lowest terms and has a positive denominator.
>>> (10).as_integer_ratio()
(10, 1)
>>> (-10).as_integer_ratio()
(-10, 1)
>>> (0).as_integer_ratio()
(0, 1)

#### `bit_count(...)`

Number of ones in the binary representation of the absolute value of self.
Also known as the population count.
>>> bin(13)
'0b1101'
>>> (13).bit_count()
3

#### `bit_length(...)`

Number of bits necessary to represent self in binary.
>>> bin(37)
'0b100101'
>>> (37).bit_length()
6

#### `conjugate(...)`

Returns self, the complex conjugate of any int.

#### `from_bytes(...)`

Return the integer represented by the given array of bytes.
  bytes
    Holds the array of bytes to convert.  The argument must either
    support the buffer protocol or be an iterable object producing bytes.
    Bytes and bytearray are examples of built-in objects that support the
    buffer protocol.
  byteorder
    The byte order used to represent the integer.  If byteorder is 'big',
    the most significant byte is at the beginning of the byte array.  If
    byteorder is 'little', the most significant byte is at the end of the
    byte array.  To request the native byte order of the host system, use
    sys.byteorder as the byte order value.  Default is to use 'big'.
  signed
    Indicates whether two's complement is used to represent the integer.

#### `is_integer(...)`

Returns True. Exists for duck type compatibility with float.is_integer.

#### `to_bytes(...)`

Return an array of bytes representing an integer.
  length
    Length of bytes object to use.  An OverflowError is raised if the
    integer is not representable with the given number of bytes.  Default
    is length 1.
  byteorder
    The byte order used to represent the integer.  If byteorder is 'big',
    the most significant byte is at the beginning of the byte array.  If
    byteorder is 'little', the most significant byte is at the end of the
    byte array.  To request the native byte order of the host system, use
    sys.byteorder as the byte order value.  Default is to use 'big'.
  signed
    Determines whether two's complement is used to represent the integer.
    If signed is False and a negative integer is given, an OverflowError
    is raised.

### Key

*Inherits from: IntEnum*

Enum representing keyboard keys.

Values map to SFML's sf::Keyboard::Key enum.

Categories:
    Letters: A-Z
    Numbers: NUM_0 through NUM_9 (top row)
    Numpad: NUMPAD_0 through NUMPAD_9
    Function: F1 through F15
    Modifiers: LEFT_SHIFT, RIGHT_SHIFT, LEFT_CONTROL, etc.
    Navigation: LEFT, RIGHT, UP, DOWN, HOME, END, PAGE_UP, PAGE_DOWN
    Editing: ENTER, BACKSPACE, DELETE, INSERT, TAB, SPACE
    Symbols: COMMA, PERIOD, SLASH, SEMICOLON, etc.


**Properties:**
- `denominator`: the denominator of a rational number in lowest terms
- `imag`: the imaginary part of a complex number
- `numerator`: the numerator of a rational number in lowest terms
- `real`: the real part of a complex number

**Methods:**

#### `as_integer_ratio(...)`

Return a pair of integers, whose ratio is equal to the original int.
The ratio is in lowest terms and has a positive denominator.
>>> (10).as_integer_ratio()
(10, 1)
>>> (-10).as_integer_ratio()
(-10, 1)
>>> (0).as_integer_ratio()
(0, 1)

#### `bit_count(...)`

Number of ones in the binary representation of the absolute value of self.
Also known as the population count.
>>> bin(13)
'0b1101'
>>> (13).bit_count()
3

#### `bit_length(...)`

Number of bits necessary to represent self in binary.
>>> bin(37)
'0b100101'
>>> (37).bit_length()
6

#### `conjugate(...)`

Returns self, the complex conjugate of any int.

#### `from_bytes(...)`

Return the integer represented by the given array of bytes.
  bytes
    Holds the array of bytes to convert.  The argument must either
    support the buffer protocol or be an iterable object producing bytes.
    Bytes and bytearray are examples of built-in objects that support the
    buffer protocol.
  byteorder
    The byte order used to represent the integer.  If byteorder is 'big',
    the most significant byte is at the beginning of the byte array.  If
    byteorder is 'little', the most significant byte is at the end of the
    byte array.  To request the native byte order of the host system, use
    sys.byteorder as the byte order value.  Default is to use 'big'.
  signed
    Indicates whether two's complement is used to represent the integer.

#### `is_integer(...)`

Returns True. Exists for duck type compatibility with float.is_integer.

#### `to_bytes(...)`

Return an array of bytes representing an integer.
  length
    Length of bytes object to use.  An OverflowError is raised if the
    integer is not representable with the given number of bytes.  Default
    is length 1.
  byteorder
    The byte order used to represent the integer.  If byteorder is 'big',
    the most significant byte is at the beginning of the byte array.  If
    byteorder is 'little', the most significant byte is at the end of the
    byte array.  To request the native byte order of the host system, use
    sys.byteorder as the byte order value.  Default is to use 'big'.
  signed
    Determines whether two's complement is used to represent the integer.
    If signed is False and a negative integer is given, an OverflowError
    is raised.

### Keyboard

Keyboard state singleton for checking modifier keys

**Properties:**
- `alt` *(read-only)*: True if either Alt key is currently pressed (read-only).
- `ctrl` *(read-only)*: True if either Control key is currently pressed (read-only).
- `shift` *(read-only)*: True if either Shift key is currently pressed (read-only).
- `system` *(read-only)*: True if either System key (Win/Cmd) is currently pressed (read-only).

**Methods:**

### LdtkProject

LdtkProject(path: str)

Load an LDtk project file (.ldtk).

Parses the project and provides access to tilesets, auto-rule sets,
levels, and enum definitions.

Args:
    path: Path to the .ldtk project file.

Properties:
    version (str, read-only): LDtk JSON format version.
    tileset_names (list[str], read-only): Names of all tilesets.
    ruleset_names (list[str], read-only): Names of all rule sets.
    level_names (list[str], read-only): Names of all levels.
    enums (dict, read-only): Enum definitions from the project.

Example:
    proj = mcrfpy.LdtkProject('dungeon.ldtk')
    ts = proj.tileset('Dungeon_Tiles')
    rs = proj.ruleset('Walls')
    level = proj.level('Level_0')


**Properties:**
- `enums` *(read-only)*: Enum definitions from the project as a list of dicts (read-only).
- `level_names` *(read-only)*: List of level identifier names (list[str], read-only).
- `ruleset_names` *(read-only)*: List of rule set / layer names (list[str], read-only).
- `tileset_names` *(read-only)*: List of tileset identifier names (list[str], read-only).
- `version` *(read-only)*: LDtk JSON format version string (str, read-only).

**Methods:**

#### `level(name: str) -> dict`

Get level data by name.

**Arguments:**
- `name`: Level identifier from the LDtk project

**Returns:** Dict with name, dimensions, world position, and layer data.

**Raises:** KeyError: If no level with the given name exists

#### `ruleset(name: str) -> AutoRuleSet`

Get an auto-rule set by layer name.

**Arguments:**
- `name`: Layer identifier from the LDtk project

**Returns:** An AutoRuleSet for resolving IntGrid data to sprite tiles.

**Raises:** KeyError: If no ruleset with the given name exists

#### `tileset(name: str) -> TileSetFile`

Get a tileset by name.

**Arguments:**
- `name`: Tileset identifier from the LDtk project

**Returns:** A TileSetFile object for texture creation and tile metadata.

**Raises:** KeyError: If no tileset with the given name exists

### Line

*Inherits from: Drawable*

Line(start=None, end=None, thickness=1.0, color=None, **kwargs)

A line UI element for drawing straight lines between two points.

Args:
    start (tuple, optional): Starting point as (x, y). Default: (0, 0)
    end (tuple, optional): Ending point as (x, y). Default: (0, 0)
    thickness (float, optional): Line thickness in pixels. Default: 1.0
    color (Color, optional): Line color. Default: White

Keyword Args:
    on_click (callable): Click handler. Default: None
    visible (bool): Visibility state. Default: True
    opacity (float): Opacity (0.0-1.0). Default: 1.0
    z_index (int): Rendering order. Default: 0
    name (str): Element name for finding. Default: None
    align (Alignment): Alignment relative to parent. Default: None
    margin (float): Margin from parent edge when aligned. Default: 0
    horiz_margin (float): Horizontal margin override. Default: 0 (use margin)
    vert_margin (float): Vertical margin override. Default: 0 (use margin)

Attributes:
    start (Vector): Starting point
    end (Vector): Ending point
    thickness (float): Line thickness
    color (Color): Line color
    visible (bool): Visibility state
    opacity (float): Opacity value
    z_index (int): Rendering order
    name (str): Element name
    align (Alignment): Alignment relative to parent (or None)
    margin (float): General margin for alignment
    horiz_margin (float): Horizontal margin override
    vert_margin (float): Vertical margin override


**Properties:**
- `align`: Alignment relative to parent bounds (Alignment enum or None). When set, position is automatically calculated when parent is assigned or resized. Set to None to disable alignment and use manual positioning.
- `bounds`: Bounding box as (pos, size) tuple of Vectors. Returns (Vector(x, y), Vector(width, height)).
- `color`: Line color as a Color object.
- `end`: Ending point of the line as a Vector.
- `global_bounds`: Bounding box as (pos, size) tuple of Vectors in screen coordinates. Returns (Vector(x, y), Vector(width, height)).
- `global_position` *(read-only)*: Global screen position (read-only). Calculates absolute position by walking up the parent chain.
- `grid_pos`: Position in grid tile coordinates (only when parent is Grid)
- `grid_size`: Size in grid tile coordinates (only when parent is Grid)
- `horiz_margin`: Horizontal margin override (float, 0 = use general margin). Invalid for vertically-centered alignments (TOP_CENTER, BOTTOM_CENTER, CENTER).
- `hovered` *(read-only)*: Whether mouse is currently over this element (read-only). Updated automatically by the engine during mouse movement.
- `margin`: General margin from edge when aligned (float). Applied to both horizontal and vertical edges unless overridden. Invalid for CENTER alignment (raises ValueError).
- `name`: Name for finding this element.
- `on_click`: Callable executed when line is clicked. Function receives (pos: Vector, button: str, action: str).
- `on_enter`: Callback for mouse enter events. Called with (pos: Vector, button: str, action: str) when mouse enters this element's bounds.
- `on_exit`: Callback for mouse exit events. Called with (pos: Vector, button: str, action: str) when mouse leaves this element's bounds.
- `on_move`: Callback for mouse movement within bounds. Called with (pos: Vector, button: str, action: str) for each mouse movement while inside. Performance note: Called frequently during movement - keep handlers fast.
- `opacity`: Opacity level (0.0 = transparent, 1.0 = opaque). Automatically clamped to valid range [0.0, 1.0].
- `origin`: Transform origin as Vector (pivot point for rotation). Default (0,0) is top-left; set to (w/2, h/2) to rotate around center.
- `parent`: Parent drawable. Get: Returns the parent Frame/Grid if nested, or None if at scene level. Set: Assign a Frame/Grid to reparent, or None to remove from parent.
- `pos`: Position as a Vector (midpoint of line).
- `rotate_with_camera`: Whether to rotate visually with parent Grid's camera_rotation (bool). False (default): stay screen-aligned. True: tilt with camera. Only affects children of UIGrid; ignored for other parents.
- `rotation`: Rotation angle in degrees (clockwise around origin). Animatable property.
- `start`: Starting point of the line as a Vector.
- `thickness`: Line thickness in pixels.
- `vert_margin`: Vertical margin override (float, 0 = use general margin). Invalid for horizontally-centered alignments (CENTER_LEFT, CENTER_RIGHT, CENTER).
- `visible`: Whether the object is visible (bool). Invisible objects are not rendered or clickable.
- `z_index`: Z-order for rendering (lower values rendered first).

**Methods:**

#### `animate(property: str, target: Any, duration: float, easing=None, delta=False, loop=False, callback=None, conflict_mode='replace') -> Animation`

Create and start an animation on this drawable's property.

Note:

**Arguments:**
- `property`: Name of the property to animate (e.g., 'x', 'fill_color', 'opacity')
- `target`: Target value - type depends on property (float, tuple for color/vector, etc.)
- `duration`: Animation duration in seconds
- `easing`: Easing function: Easing enum value, string name, or None for linear
- `delta`: If True, target is relative to current value; if False, target is absolute
- `loop`: If True, animation repeats from start when it reaches the end (default False)
- `callback`: Optional callable invoked when animation completes (not called for looping animations)
- `conflict_mode`: 'replace' (default), 'queue', or 'error' if property already animating

**Returns:** Animation object for monitoring progress

**Raises:** ValueError: If property name is not valid for this drawable type This is a convenience method that creates an Animation, starts it, and adds it to the AnimationManager.

#### `move(dx, dy) or (delta) -> None`

Move the element by a relative offset.

Note:

**Arguments:**
- `dx`: Horizontal offset in pixels (or use delta)
- `dy`: Vertical offset in pixels (or use delta)
- `delta`: Offset as tuple, list, or Vector: (dx, dy)

#### `realign() -> None`

Reapply alignment relative to parent, useful for responsive layouts.

Note:
    Call this to recalculate position after parent changes size. For elements with align=None, this has no effect.

#### `resize(width, height) or (size) -> None`

Resize the element to new dimensions.

Note:

**Arguments:**
- `width`: New width in pixels (or use size)
- `height`: New height in pixels (or use size)
- `size`: Size as tuple, list, or Vector: (width, height)

### Model3D

Model3D(path=None)

A 3D model resource that can be rendered by Entity3D.

Args:
    path (str, optional): Path to .glb file to load. If None, creates empty model.

Class Methods:
    cube(size=1.0) -> Model3D: Create a unit cube
    plane(width=1.0, depth=1.0, segments=1) -> Model3D: Create a flat plane
    sphere(radius=0.5, segments=16, rings=12) -> Model3D: Create a UV sphere

Properties:
    name (str, read-only): Model name
    vertex_count (int, read-only): Total vertices across all meshes
    triangle_count (int, read-only): Total triangles across all meshes
    has_skeleton (bool, read-only): Whether model has skeletal animation data
    bounds (tuple, read-only): AABB as ((min_x, min_y, min_z), (max_x, max_y, max_z))
    mesh_count (int, read-only): Number of submeshes
    bone_count (int, read-only): Number of bones in skeleton
    animation_clips (list, read-only): List of animation clip names

**Properties:**
- `animation_clips` *(read-only)*: List of animation clip names (read-only)
- `bone_count` *(read-only)*: Number of bones in skeleton (read-only)
- `bounds` *(read-only)*: AABB as ((min_x, min_y, min_z), (max_x, max_y, max_z)) (read-only)
- `has_skeleton` *(read-only)*: Whether model has skeletal animation data (read-only)
- `mesh_count` *(read-only)*: Number of submeshes (read-only)
- `name` *(read-only)*: Model name (read-only)
- `triangle_count` *(read-only)*: Total triangle count across all meshes (read-only)
- `vertex_count` *(read-only)*: Total vertex count across all meshes (read-only)

**Methods:**

#### `cube(size=1.0) -> Model3D`

Create a unit cube centered at origin.

#### `plane(width=1.0, depth=1.0, segments=1) -> Model3D`

Create a flat plane.

#### `sphere(radius=0.5, segments=16, rings=12) -> Model3D`

Create a UV sphere.

### Mouse

Mouse state singleton for reading button/position state and controlling cursor visibility

**Properties:**
- `grabbed`: Whether the mouse cursor is confined to the window (default: False).
- `left` *(read-only)*: True if left mouse button is currently pressed (read-only).
- `middle` *(read-only)*: True if middle mouse button is currently pressed (read-only).
- `pos` *(read-only)*: Current mouse position as Vector (read-only).
- `right` *(read-only)*: True if right mouse button is currently pressed (read-only).
- `visible`: Whether the mouse cursor is visible (default: True).
- `x` *(read-only)*: Current mouse X position in window coordinates (read-only).
- `y` *(read-only)*: Current mouse Y position in window coordinates (read-only).

**Methods:**

### MouseButton

*Inherits from: IntEnum*

Enum representing mouse buttons and scroll wheel.

Values:
    LEFT: Left mouse button
    RIGHT: Right mouse button
    MIDDLE: Middle mouse button / scroll wheel click
    X1: Extra mouse button 1
    X2: Extra mouse button 2
    SCROLL_UP: Scroll wheel up
    SCROLL_DOWN: Scroll wheel down


**Properties:**
- `denominator`: the denominator of a rational number in lowest terms
- `imag`: the imaginary part of a complex number
- `numerator`: the numerator of a rational number in lowest terms
- `real`: the real part of a complex number

**Methods:**

#### `as_integer_ratio(...)`

Return a pair of integers, whose ratio is equal to the original int.
The ratio is in lowest terms and has a positive denominator.
>>> (10).as_integer_ratio()
(10, 1)
>>> (-10).as_integer_ratio()
(-10, 1)
>>> (0).as_integer_ratio()
(0, 1)

#### `bit_count(...)`

Number of ones in the binary representation of the absolute value of self.
Also known as the population count.
>>> bin(13)
'0b1101'
>>> (13).bit_count()
3

#### `bit_length(...)`

Number of bits necessary to represent self in binary.
>>> bin(37)
'0b100101'
>>> (37).bit_length()
6

#### `conjugate(...)`

Returns self, the complex conjugate of any int.

#### `from_bytes(...)`

Return the integer represented by the given array of bytes.
  bytes
    Holds the array of bytes to convert.  The argument must either
    support the buffer protocol or be an iterable object producing bytes.
    Bytes and bytearray are examples of built-in objects that support the
    buffer protocol.
  byteorder
    The byte order used to represent the integer.  If byteorder is 'big',
    the most significant byte is at the beginning of the byte array.  If
    byteorder is 'little', the most significant byte is at the end of the
    byte array.  To request the native byte order of the host system, use
    sys.byteorder as the byte order value.  Default is to use 'big'.
  signed
    Indicates whether two's complement is used to represent the integer.

#### `is_integer(...)`

Returns True. Exists for duck type compatibility with float.is_integer.

#### `to_bytes(...)`

Return an array of bytes representing an integer.
  length
    Length of bytes object to use.  An OverflowError is raised if the
    integer is not representable with the given number of bytes.  Default
    is length 1.
  byteorder
    The byte order used to represent the integer.  If byteorder is 'big',
    the most significant byte is at the beginning of the byte array.  If
    byteorder is 'little', the most significant byte is at the end of the
    byte array.  To request the native byte order of the host system, use
    sys.byteorder as the byte order value.  Default is to use 'big'.
  signed
    Determines whether two's complement is used to represent the integer.
    If signed is False and a negative integer is given, an OverflowError
    is raised.

### Music

Streaming music object for longer audio tracks

**Properties:**
- `duration` *(read-only)*: Total duration of the music in seconds (read-only).
- `loop`: Whether the music loops when it reaches the end.
- `playing` *(read-only)*: True if the music is currently playing (read-only).
- `position`: Current playback position in seconds. Can be set to seek.
- `source` *(read-only)*: Filename path used to load this music (read-only).
- `volume`: Volume level from 0 (silent) to 100 (full volume).

**Methods:**

#### `pause() -> None`

Pause the music. Use play() to resume from the paused position.

#### `play() -> None`

Start or resume playing the music.

#### `stop() -> None`

Stop playing and reset to the beginning.

### NoiseSource

NoiseSource(dimensions: int = 2, algorithm: str = 'simplex', hurst: float = 0.5, lacunarity: float = 2.0, seed: int = None)

A configured noise generator for procedural generation.

NoiseSource wraps libtcod's noise generator, providing coherent noise values that can be used for terrain generation, textures, and other procedural content. The same coordinates always produce the same value (deterministic).

Args:
    dimensions: Number of input dimensions (1-4). Default: 2.
    algorithm: Noise algorithm - 'simplex', 'perlin', or 'wavelet'. Default: 'simplex'.
    hurst: Fractal Hurst exponent for fbm/turbulence (0.0-1.0). Default: 0.5.
    lacunarity: Frequency multiplier between octaves. Default: 2.0.
    seed: Random seed for reproducibility. None for random seed.

Properties:
    dimensions (int): Read-only. Number of input dimensions.
    algorithm (str): Read-only. Noise algorithm name.
    hurst (float): Read-only. Hurst exponent.
    lacunarity (float): Read-only. Lacunarity value.
    seed (int): Read-only. Seed used (even if originally None).

Example:
    noise = mcrfpy.NoiseSource(dimensions=2, algorithm='simplex', seed=42)
    value = noise.get((10.5, 20.3))  # Returns -1.0 to 1.0
    fbm_val = noise.fbm((10.5, 20.3), octaves=6)


**Properties:**
- `algorithm` *(read-only)*: Noise algorithm name ('simplex', 'perlin', or 'wavelet'). Read-only.
- `dimensions` *(read-only)*: Number of input dimensions (1-4). Read-only.
- `hurst` *(read-only)*: Hurst exponent for fbm/turbulence. Read-only.
- `lacunarity` *(read-only)*: Frequency multiplier between octaves. Read-only.
- `seed` *(read-only)*: Random seed used (even if originally None). Read-only.

**Methods:**

#### `fbm(pos: tuple[float, ...], octaves: int = 4) -> float`

Get fractal brownian motion value at coordinates.

**Arguments:**
- `pos`: Position tuple with length matching dimensions
- `octaves`: Number of noise octaves to combine (default: 4)

**Returns:** float: FBM noise value in range [-1.0, 1.0]

**Raises:** ValueError: Position tuple length doesn't match dimensions

#### `get(pos: tuple[float, ...]) -> float`

Get flat noise value at coordinates.

**Arguments:**
- `pos`: Position tuple with length matching dimensions

**Returns:** float: Noise value in range [-1.0, 1.0]

**Raises:** ValueError: Position tuple length doesn't match dimensions

#### `sample(size: tuple[int, int], world_origin: tuple[float, float] = (0.0, 0.0), world_size: tuple[float, float] = None, mode: str = 'fbm', octaves: int = 4) -> HeightMap`

Sample noise into a HeightMap for batch processing.

Note:

**Arguments:**
- `size`: Output dimensions in cells as (width, height)
- `world_origin`: World coordinates of top-left corner (default: (0, 0))
- `world_size`: World area to sample (default: same as size)
- `mode`: Sampling mode: 'flat', 'fbm', or 'turbulence' (default: 'fbm')
- `octaves`: Octaves for fbm/turbulence modes (default: 4)

**Returns:** HeightMap: New HeightMap filled with sampled noise values Requires dimensions=2. Values are in range [-1.0, 1.0].

#### `turbulence(pos: tuple[float, ...], octaves: int = 4) -> float`

Get turbulence (absolute fbm) value at coordinates.

**Arguments:**
- `pos`: Position tuple with length matching dimensions
- `octaves`: Number of noise octaves to combine (default: 4)

**Returns:** float: Turbulence noise value in range [-1.0, 1.0]

**Raises:** ValueError: Position tuple length doesn't match dimensions

### Perspective

*Inherits from: IntEnum*

Enum representing an entity's knowledge of a cell.

Values:
    UNKNOWN: Never seen (perspective_map value 0)
    DISCOVERED: Seen before but not currently visible (value 1)
    VISIBLE: In current FOV (value 2)


**Properties:**
- `denominator`: the denominator of a rational number in lowest terms
- `imag`: the imaginary part of a complex number
- `numerator`: the numerator of a rational number in lowest terms
- `real`: the real part of a complex number

**Methods:**

#### `as_integer_ratio(...)`

Return a pair of integers, whose ratio is equal to the original int.
The ratio is in lowest terms and has a positive denominator.
>>> (10).as_integer_ratio()
(10, 1)
>>> (-10).as_integer_ratio()
(-10, 1)
>>> (0).as_integer_ratio()
(0, 1)

#### `bit_count(...)`

Number of ones in the binary representation of the absolute value of self.
Also known as the population count.
>>> bin(13)
'0b1101'
>>> (13).bit_count()
3

#### `bit_length(...)`

Number of bits necessary to represent self in binary.
>>> bin(37)
'0b100101'
>>> (37).bit_length()
6

#### `conjugate(...)`

Returns self, the complex conjugate of any int.

#### `from_bytes(...)`

Return the integer represented by the given array of bytes.
  bytes
    Holds the array of bytes to convert.  The argument must either
    support the buffer protocol or be an iterable object producing bytes.
    Bytes and bytearray are examples of built-in objects that support the
    buffer protocol.
  byteorder
    The byte order used to represent the integer.  If byteorder is 'big',
    the most significant byte is at the beginning of the byte array.  If
    byteorder is 'little', the most significant byte is at the end of the
    byte array.  To request the native byte order of the host system, use
    sys.byteorder as the byte order value.  Default is to use 'big'.
  signed
    Indicates whether two's complement is used to represent the integer.

#### `is_integer(...)`

Returns True. Exists for duck type compatibility with float.is_integer.

#### `to_bytes(...)`

Return an array of bytes representing an integer.
  length
    Length of bytes object to use.  An OverflowError is raised if the
    integer is not representable with the given number of bytes.  Default
    is length 1.
  byteorder
    The byte order used to represent the integer.  If byteorder is 'big',
    the most significant byte is at the beginning of the byte array.  If
    byteorder is 'little', the most significant byte is at the end of the
    byte array.  To request the native byte order of the host system, use
    sys.byteorder as the byte order value.  Default is to use 'big'.
  signed
    Determines whether two's complement is used to represent the integer.
    If signed is False and a negative integer is given, an OverflowError
    is raised.

### PropertyBinding

PropertyBinding(target: UIDrawable, property: str)

A binding that reads a property value from a UI drawable.

Args:
    target: The drawable to read the property from
    property: Name of the property to read (e.g., 'x', 'opacity')

Use this to create dynamic shader uniforms that follow a drawable's
properties. The binding automatically handles cases where the target
is destroyed.

Example:
    other_frame = mcrfpy.Frame(pos=(100, 100))
    frame.uniforms['offset_x'] = mcrfpy.PropertyBinding(other_frame, 'x')


**Properties:**
- `is_valid` *(read-only)*: True if the binding target still exists and property is valid (bool, read-only).
- `property` *(read-only)*: The property name being read (str, read-only).
- `target` *(read-only)*: The drawable this binding reads from (read-only).
- `value` *(read-only)*: Current value of the binding (float, read-only). Returns None if invalid.

**Methods:**

### Scene

Scene(name: str)

Object-oriented scene management with lifecycle callbacks.

This is the recommended approach for scene management, replacing module-level
functions like createScene(), setScene(), and sceneUI(). Key advantage: you can
set on_key handlers on ANY scene, not just the currently active one.

Args:
    name: Unique identifier for this scene. Used for scene transitions.

Properties:
    name (str, read-only): Scene's unique identifier.
    active (bool, read-only): Whether this scene is currently displayed.
    children (UICollection, read-only): UI elements in this scene. Modify to add/remove elements.
    on_key (callable): Keyboard handler. Set on ANY scene, regardless of which is active!
    pos (Vector): Position offset for all UI elements.
    visible (bool): Whether the scene renders.
    opacity (float): Scene transparency (0.0-1.0).

Lifecycle Callbacks (override in subclass):
    on_enter(): Called when scene becomes active via activate().
    on_exit(): Called when scene is deactivated (another scene activates).
    on_key(key: str, action: str): Called for keyboard events (subclass method).
    update(dt: float): Called every frame with delta time in seconds.
    on_resize(new_size: Vector): Called when window is resized.

Example:
    # Basic usage (replacing module functions):
    scene = mcrfpy.Scene('main_menu')
    scene.children.append(mcrfpy.Caption(text='Welcome', pos=(100, 100)))
    scene.on_key = lambda key, action: print(f'Key: {key}')
    scene.activate()  # Switch to this scene

    # Subclassing for lifecycle:
    class GameScene(mcrfpy.Scene):
        def on_enter(self):
            print('Game started!')
        def update(self, dt):
            self.player.move(dt)


**Properties:**
- `active` *(read-only)*: Whether this scene is currently active (bool, read-only). Only one scene can be active at a time.
- `children` *(read-only)*: UI element collection for this scene (UICollection, read-only). Use to add, remove, or iterate over UI elements. Changes are reflected immediately.
- `name` *(read-only)*: Scene name (str, read-only). Unique identifier for this scene.
- `on_key`: Keyboard event handler (callable or None). Function receives (key: Key, action: InputState) for keyboard events. Set to None to remove the handler.
- `opacity`: Scene opacity (0.0-1.0). Applied to all UI elements during rendering.
- `pos`: Scene position offset (Vector). Applied to all UI elements during rendering.
- `registered` *(read-only)*: Whether this scene is registered with the game engine (bool, read-only). Unregistered scenes still exist but won't receive lifecycle callbacks.
- `visible`: Scene visibility (bool). If False, scene is not rendered.

**Methods:**

#### `activate(transition: Transition = None, duration: float = None) -> None`

Make this the active scene with optional transition effect.

Note:

**Arguments:**
- `transition`: Transition type (mcrfpy.Transition enum). Defaults to mcrfpy.default_transition
- `duration`: Transition duration in seconds. Defaults to mcrfpy.default_transition_duration

**Returns:** None Deactivates the current scene and activates this one. Lifecycle callbacks (on_exit, on_enter) are triggered.

#### `realign() -> None`

Recalculate alignment for all children with alignment set.

Note:
    Call this after window resize or when game_resolution changes. For responsive layouts, connect this to on_resize callback.

#### `register() -> None`

Register this scene with the game engine.

Note:
    Makes the scene available for activation and receives lifecycle callbacks. If another scene with the same name exists, it will be unregistered first. Called automatically by activate() if needed.

#### `unregister() -> None`

Unregister this scene from the game engine.

Note:
    Removes the scene from the engine's registry but keeps the Python object alive. The scene's UI elements and state are preserved. Call register() to re-add it. Useful for temporary scenes or scene pooling.

### Shader

Shader(fragment_source: str, dynamic: bool = False)

A GPU shader program for visual effects.

Args:
    fragment_source: GLSL fragment shader source code
    dynamic: If True, shader uses time-varying effects and will
             invalidate parent caches each frame

Shaders enable GPU-accelerated visual effects like glow, distortion,
color manipulation, and more. Assign to drawable.shader to apply.

Engine-provided uniforms (automatically available):
    - float time: Seconds since engine start
    - float delta_time: Seconds since last frame
    - vec2 resolution: Texture size in pixels
    - vec2 mouse: Mouse position in window coordinates

Example:
    shader = mcrfpy.Shader('''
        uniform sampler2D texture;
        uniform float time;
        void main() {
            vec2 uv = gl_TexCoord[0].xy;
            vec4 color = texture2D(texture, uv);
            color.rgb *= 0.5 + 0.5 * sin(time);
            gl_FragColor = color;
        }
    ''', dynamic=True)
    frame.shader = shader


**Properties:**
- `dynamic`: Whether this shader uses time-varying effects (bool). Dynamic shaders invalidate parent caches each frame.
- `is_valid` *(read-only)*: True if the shader compiled successfully (bool, read-only).
- `source` *(read-only)*: The GLSL fragment shader source code (str, read-only).

**Methods:**

#### `set_uniform(name: str, value: float|tuple) -> None`

Set a custom uniform value on this shader.

Note:

**Arguments:**
- `name`: Uniform variable name in the shader
- `value`: Float, vec2 (2-tuple), vec3 (3-tuple), or vec4 (4-tuple)

**Raises:** ValueError: If uniform type cannot be determined Engine uniforms (time, resolution, etc.) are set automatically

### Sound

Sound(source)

Sound effect object for short audio clips.

Args:
    source: Filename string or SoundBuffer object.

Properties:
    volume (float): Volume 0-100.
    loop (bool): Whether to loop.
    playing (bool, read-only): True if playing.
    duration (float, read-only): Duration in seconds.
    source (str, read-only): Source filename.
    pitch (float): Playback pitch (1.0 = normal).
    buffer (SoundBuffer, read-only): The SoundBuffer, if created from one.


**Properties:**
- `buffer` *(read-only)*: The SoundBuffer if created from one, else None (read-only).
- `duration` *(read-only)*: Total duration of the sound in seconds (read-only).
- `loop`: Whether the sound loops when it reaches the end.
- `pitch`: Playback pitch multiplier (1.0 = normal, >1 = higher, <1 = lower).
- `playing` *(read-only)*: True if the sound is currently playing (read-only).
- `source` *(read-only)*: Filename path used to load this sound (read-only).
- `volume`: Volume level from 0 (silent) to 100 (full volume).

**Methods:**

#### `pause() -> None`

Pause the sound. Use play() to resume from the paused position.

#### `play() -> None`

Start or resume playing the sound.

#### `play_varied(pitch_range: float = 0.1, volume_range: float = 3.0) -> None`

Play with randomized pitch and volume for natural variation.

**Arguments:**
- `pitch_range`: Random pitch offset range (default 0.1)
- `volume_range`: Random volume offset range (default 3.0)

#### `stop() -> None`

Stop playing and reset to the beginning.

### SoundBuffer

SoundBuffer(filename: str)
SoundBuffer.from_samples(data: bytes, channels: int, sample_rate: int)
SoundBuffer.tone(frequency: float, duration: float, waveform: str = 'sine', ...)
SoundBuffer.sfxr(preset: str, seed: int = None)

Audio sample buffer for procedural audio generation and effects.

Holds PCM sample data that can be created from files, raw samples,
tone synthesis, or sfxr presets. Effect methods return new SoundBuffer
instances (copy-modify pattern).

Properties:
    duration (float, read-only): Duration in seconds.
    sample_count (int, read-only): Total number of samples.
    sample_rate (int, read-only): Samples per second (e.g. 44100).
    channels (int, read-only): Number of audio channels.
    sfxr_params (dict or None, read-only): sfxr parameters if sfxr-generated.


**Properties:**
- `channels` *(read-only)*: Number of audio channels (read-only).
- `duration` *(read-only)*: Total duration in seconds (read-only).
- `sample_count` *(read-only)*: Total number of samples (read-only).
- `sample_rate` *(read-only)*: Sample rate in Hz (read-only).
- `sfxr_params` *(read-only)*: Dict of sfxr parameters if sfxr-generated, else None (read-only).

**Methods:**

#### `bit_crush(bits: int, rate_divisor: int) -> SoundBuffer`

Reduce bit depth and sample rate for lo-fi effect.

#### `concat(buffers: list[SoundBuffer], overlap: float = 0.0) -> SoundBuffer`

Concatenate multiple SoundBuffers with optional crossfade overlap.

**Arguments:**
- `buffers`: List of SoundBuffer objects to concatenate
- `overlap`: Crossfade overlap duration in seconds

#### `distortion(drive: float) -> SoundBuffer`

Apply tanh soft clipping distortion.

#### `echo(delay_ms: float, feedback: float, wet: float) -> SoundBuffer`

Apply echo effect with delay, feedback, and wet/dry mix.

#### `from_samples(data: bytes, channels: int, sample_rate: int) -> SoundBuffer`

Create a SoundBuffer from raw int16 PCM sample data.

**Arguments:**
- `data`: Raw PCM data as bytes (int16 little-endian)
- `channels`: Number of audio channels (1=mono, 2=stereo)
- `sample_rate`: Sample rate in Hz (e.g. 44100)

#### `gain(factor: float) -> SoundBuffer`

Multiply all samples by a scalar factor. Use for volume/amplitude control before mixing.

**Arguments:**
- `factor`: Amplitude multiplier (0.5 = half volume, 2.0 = double). Clamps to int16 range.

#### `high_pass(cutoff_hz: float) -> SoundBuffer`

Apply single-pole IIR high-pass filter.

#### `low_pass(cutoff_hz: float) -> SoundBuffer`

Apply single-pole IIR low-pass filter.

#### `mix(buffers: list[SoundBuffer]) -> SoundBuffer`

Mix multiple SoundBuffers together (additive, clamped).

**Arguments:**
- `buffers`: List of SoundBuffer objects to mix

#### `normalize() -> SoundBuffer`

Scale samples to 95%% of int16 max.

#### `pitch_shift(factor: float) -> SoundBuffer`

Resample to shift pitch. factor>1 = higher+shorter.

#### `reverb(room_size: float, damping: float, wet: float) -> SoundBuffer`

Apply simplified Freeverb-style reverb.

#### `reverse() -> SoundBuffer`

Reverse the sample order.

#### `sfxr(preset: str = None, seed: int = None, **params) -> SoundBuffer`

Generate retro sound effects using sfxr synthesis.

**Arguments:**
- `preset`: One of: coin, laser, explosion, powerup, hurt, jump, blip
- `seed`: Random seed for deterministic generation

**Returns:** SoundBuffer with sfxr_params set for later mutation

#### `sfxr_mutate(amount: float = 0.05, seed: int = None) -> SoundBuffer`

Jitter sfxr params and re-synthesize. Only works on sfxr-generated buffers.

#### `slice(start: float, end: float) -> SoundBuffer`

Extract a time range in seconds.

#### `tone(frequency: float, duration: float, waveform: str = 'sine', ...) -> SoundBuffer`

Generate a tone with optional ADSR envelope.

**Arguments:**
- `frequency`: Frequency in Hz
- `duration`: Duration in seconds
- `waveform`: One of: sine, square, saw, triangle, noise
- `attack`: ADSR attack time in seconds (default 0.01)
- `decay`: ADSR decay time in seconds (default 0.0)
- `sustain`: ADSR sustain level 0.0-1.0 (default 1.0)
- `release`: ADSR release time in seconds (default 0.01)

### Sprite

*Inherits from: Drawable*

Sprite(pos=None, texture=None, sprite_index=0, **kwargs)

A sprite UI element that displays a texture or portion of a texture atlas.

Args:
    pos (tuple, optional): Position as (x, y) tuple. Default: (0, 0)
    texture (Texture, optional): Texture object to display. Default: default texture
    sprite_index (int, optional): Index into texture atlas. Default: 0

Keyword Args:
    scale (float): Uniform scale factor. Default: 1.0
    scale_x (float): Horizontal scale factor. Default: 1.0
    scale_y (float): Vertical scale factor. Default: 1.0
    click (callable): Click event handler. Default: None
    visible (bool): Visibility state. Default: True
    opacity (float): Opacity (0.0-1.0). Default: 1.0
    z_index (int): Rendering order. Default: 0
    name (str): Element name for finding. Default: None
    x (float): X position override. Default: 0
    y (float): Y position override. Default: 0
    align (Alignment): Alignment relative to parent. Default: None
    margin (float): Margin from parent edge when aligned. Default: 0
    horiz_margin (float): Horizontal margin override. Default: 0 (use margin)
    vert_margin (float): Vertical margin override. Default: 0 (use margin)

Attributes:
    x, y (float): Position in pixels
    pos (Vector): Position as a Vector object
    texture (Texture): The texture being displayed
    sprite_index (int): Current sprite index in texture atlas
    scale (float): Uniform scale factor
    scale_x, scale_y (float): Individual scale factors
    click (callable): Click event handler
    visible (bool): Visibility state
    opacity (float): Opacity value
    z_index (int): Rendering order
    name (str): Element name
    w, h (float): Read-only computed size based on texture and scale
    align (Alignment): Alignment relative to parent (or None)
    margin (float): General margin for alignment
    horiz_margin (float): Horizontal margin override
    vert_margin (float): Vertical margin override

**Properties:**
- `align`: Alignment relative to parent bounds (Alignment enum or None). When set, position is automatically calculated when parent is assigned or resized. Set to None to disable alignment and use manual positioning.
- `bounds`: Bounding box as (pos, size) tuple of Vectors. Returns (Vector(x, y), Vector(width, height)).
- `global_bounds`: Bounding box as (pos, size) tuple of Vectors in screen coordinates. Returns (Vector(x, y), Vector(width, height)).
- `global_position` *(read-only)*: Global screen position (read-only). Calculates absolute position by walking up the parent chain.
- `grid_pos`: Position in grid tile coordinates (only when parent is Grid)
- `grid_size`: Size in grid tile coordinates (only when parent is Grid)
- `horiz_margin`: Horizontal margin override (float, 0 = use general margin). Invalid for vertically-centered alignments (TOP_CENTER, BOTTOM_CENTER, CENTER).
- `hovered` *(read-only)*: Whether mouse is currently over this element (read-only). Updated automatically by the engine during mouse movement.
- `margin`: General margin from edge when aligned (float). Applied to both horizontal and vertical edges unless overridden. Invalid for CENTER alignment (raises ValueError).
- `name`: Name for finding elements
- `on_click`: Callable executed when object is clicked. Function receives (pos: Vector, button: str, action: str).
- `on_enter`: Callback for mouse enter events. Called with (pos: Vector, button: str, action: str) when mouse enters this element's bounds.
- `on_exit`: Callback for mouse exit events. Called with (pos: Vector, button: str, action: str) when mouse leaves this element's bounds.
- `on_move`: Callback for mouse movement within bounds. Called with (pos: Vector, button: str, action: str) for each mouse movement while inside. Performance note: Called frequently during movement - keep handlers fast.
- `opacity`: Opacity level (0.0 = transparent, 1.0 = opaque). Automatically clamped to valid range [0.0, 1.0].
- `origin`: Transform origin as Vector (pivot point for rotation). Default (0,0) is top-left; set to (w/2, h/2) to rotate around center.
- `parent`: Parent drawable. Get: Returns the parent Frame/Grid if nested, or None if at scene level. Set: Assign a Frame/Grid to reparent, or None to remove from parent.
- `pos`: Position as a Vector
- `rotate_with_camera`: Whether to rotate visually with parent Grid's camera_rotation (bool). False (default): stay screen-aligned. True: tilt with camera. Only affects children of UIGrid; ignored for other parents.
- `rotation`: Rotation angle in degrees (clockwise around origin). Animatable property.
- `scale`: Uniform size factor
- `scale_x`: Horizontal scale factor
- `scale_y`: Vertical scale factor
- `shader`: Shader for GPU visual effects (Shader or None). When set, the drawable is rendered through the shader program. Set to None to disable shader effects.
- `sprite_index`: Which sprite on the texture is shown
- `texture`: Texture object
- `uniforms` *(read-only)*: Collection of shader uniforms (read-only access to collection). Set uniforms via dict-like syntax: drawable.uniforms['name'] = value. Supports float, vec2/3/4 tuples, PropertyBinding, and CallableBinding.
- `vert_margin`: Vertical margin override (float, 0 = use general margin). Invalid for horizontally-centered alignments (CENTER_LEFT, CENTER_RIGHT, CENTER).
- `visible`: Whether the object is visible (bool). Invisible objects are not rendered or clickable.
- `x`: X coordinate of top-left corner
- `y`: Y coordinate of top-left corner
- `z_index`: Z-order for rendering (lower values rendered first). Automatically triggers scene resort when changed.

**Methods:**

#### `animate(property: str, target: Any, duration: float, easing=None, delta=False, loop=False, callback=None, conflict_mode='replace') -> Animation`

Create and start an animation on this drawable's property.

Note:

**Arguments:**
- `property`: Name of the property to animate (e.g., 'x', 'fill_color', 'opacity')
- `target`: Target value - type depends on property (float, tuple for color/vector, etc.)
- `duration`: Animation duration in seconds
- `easing`: Easing function: Easing enum value, string name, or None for linear
- `delta`: If True, target is relative to current value; if False, target is absolute
- `loop`: If True, animation repeats from start when it reaches the end (default False)
- `callback`: Optional callable invoked when animation completes (not called for looping animations)
- `conflict_mode`: 'replace' (default), 'queue', or 'error' if property already animating

**Returns:** Animation object for monitoring progress

**Raises:** ValueError: If property name is not valid for this drawable type This is a convenience method that creates an Animation, starts it, and adds it to the AnimationManager.

#### `move(dx, dy) or (delta) -> None`

Move the element by a relative offset.

Note:

**Arguments:**
- `dx`: Horizontal offset in pixels (or use delta)
- `dy`: Vertical offset in pixels (or use delta)
- `delta`: Offset as tuple, list, or Vector: (dx, dy)

#### `realign() -> None`

Reapply alignment relative to parent, useful for responsive layouts.

Note:
    Call this to recalculate position after parent changes size. For elements with align=None, this has no effect.

#### `resize(width, height) or (size) -> None`

Resize the element to new dimensions.

Note:

**Arguments:**
- `width`: New width in pixels (or use size)
- `height`: New height in pixels (or use size)
- `size`: Size as tuple, list, or Vector: (width, height)

### Texture

Texture(filename: str, sprite_width: int = 0, sprite_height: int = 0, display_size: tuple = None, display_origin: tuple = None)

A texture atlas for sprites and tiles.

Args:
    filename: Path to an image file (PNG, BMP, etc.).
    sprite_width: Width of each sprite cell in pixels (0 = full image).
    sprite_height: Height of each sprite cell in pixels (0 = full image).
    display_size: Optional (w, h) actual content size within each cell.
    display_origin: Optional (x, y) content offset within each cell.

Properties:
    sprite_width, sprite_height (int, read-only): Cell dimensions.
    sheet_width, sheet_height (int, read-only): Grid dimensions in cells.
    sprite_count (int, read-only): Total number of sprite cells.
    source (str, read-only): File path used to load this texture.
    display_width, display_height (int, read-only): Content size within cells.
    display_offset_x, display_offset_y (int, read-only): Content offset within cells.


**Properties:**
- `display_height` *(read-only)*: Display height of sprite content within each cell (int, read-only). Defaults to sprite_height.
- `display_offset_x` *(read-only)*: X offset of sprite content within each cell (int, read-only). Default 0.
- `display_offset_y` *(read-only)*: Y offset of sprite content within each cell (int, read-only). Default 0.
- `display_width` *(read-only)*: Display width of sprite content within each cell (int, read-only). Defaults to sprite_width.
- `sheet_height` *(read-only)*: Number of sprite rows in the texture sheet (int, read-only). Calculated as texture_height / sprite_height.
- `sheet_width` *(read-only)*: Number of sprite columns in the texture sheet (int, read-only). Calculated as texture_width / sprite_width.
- `source` *(read-only)*: Source filename path (str, read-only). The path used to load this texture.
- `sprite_count` *(read-only)*: Total number of sprites in the texture sheet (int, read-only). Equals sheet_width * sheet_height.
- `sprite_height` *(read-only)*: Height of each sprite in pixels (int, read-only). Specified during texture initialization.
- `sprite_width` *(read-only)*: Width of each sprite in pixels (int, read-only). Specified during texture initialization.

**Methods:**

#### `composite(layers: list[Texture], sprite_width: int, sprite_height: int, name: str = '<composite>') -> Texture`

Alpha-composite multiple texture layers into a single texture.

Note:

**Arguments:**
- `layers`: List of Texture objects, composited bottom-to-top
- `sprite_width`: Width of each sprite cell in the result
- `sprite_height`: Height of each sprite cell in the result
- `name`: Optional name for the composite texture

**Returns:** Texture: New texture with all layers composited

**Raises:** ValueError: If layers have different dimensions or list is empty This is a class method. Uses Porter-Duff 'over' alpha compositing.

#### `from_bytes(data: bytes, width: int, height: int, sprite_width: int, sprite_height: int, name: str = '<generated>') -> Texture`

Create a Texture from raw RGBA pixel data.

Note:

**Arguments:**
- `data`: Raw RGBA bytes (length must equal width * height * 4)
- `width`: Image width in pixels
- `height`: Image height in pixels
- `sprite_width`: Width of each sprite cell
- `sprite_height`: Height of each sprite cell
- `name`: Optional name for the texture (default: '<generated>')

**Returns:** Texture: New texture containing the pixel data

**Raises:** ValueError: If data length does not match width * height * 4 This is a class method. Useful for procedurally generated textures.

#### `hsl_shift(hue_shift: float, sat_shift: float = 0.0, lit_shift: float = 0.0) -> Texture`

Create a new texture with HSL color adjustments applied.

Note:

**Arguments:**
- `hue_shift`: Hue rotation in degrees [0.0, 360.0)
- `sat_shift`: Saturation adjustment [-1.0, 1.0] (default 0.0)
- `lit_shift`: Lightness adjustment [-1.0, 1.0] (default 0.0)

**Returns:** Texture: New texture with color-shifted pixels Preserves alpha channel. Skips fully transparent pixels.

### TileLayer

TileLayer(z_index=-1, name=None, texture=None, grid_size=None)

A grid layer that stores sprite indices per cell for tile-based rendering.

TileLayers can be created standalone and attached to a Grid via add_layer()
or passed to the Grid constructor's layers parameter. Layers with size (0, 0)
automatically resize to match the Grid when attached.

Args:
    z_index (int): Render order relative to entities. Negative values render
        below entities (as backgrounds), positive values render above entities
        (as overlays). Default: -1 (background)
    name (str): Layer name for Grid.layer(name) lookup. Default: None
    texture (Texture): Sprite atlas containing tile images. The texture's
        sprite_size determines individual tile dimensions. Required for
        rendering; can be set after creation. Default: None
    grid_size (tuple): Dimensions as (width, height). If None or (0, 0), the
        layer will auto-resize when attached to a Grid. Default: None

Attributes:
    z_index (int): Layer z-order relative to entities (read/write)
    name (str): Layer name for lookup (read-only)
    visible (bool): Whether layer is rendered (read/write)
    texture (Texture): Sprite atlas for tile images (read/write)
    grid_size (tuple): Layer dimensions as (width, height) (read-only)
    grid (Grid): Parent Grid or None. Setting manages layer association.

Methods:
    at(x, y) -> int: Get the tile index at cell position (x, y)
    set(x, y, index): Set the tile index at cell position (x, y)
    fill(index): Fill the entire layer with a single tile index
    fill_rect(x, y, w, h, index): Fill a rectangular region with a tile index

Tile Index Values:
    -1: No tile (transparent/empty cell)
    0+: Index into the texture's sprite atlas (row-major order)

Example:
    terrain = mcrfpy.TileLayer(z_index=-2, name='terrain', texture=tileset)
    grid = mcrfpy.Grid(grid_size=(20, 15), layers=[terrain])
    terrain.fill(0)  # Fill with tile index 0
    grid.layer('terrain').set(5, 5, 42)  # Place tile 42 at (5, 5)

**Properties:**
- `grid`: Parent Grid or None. Setting manages layer association and handles lazy allocation.
- `grid_size`: Layer dimensions as (width, height) tuple.
- `name` *(read-only)*: Layer name (str, read-only). Used for Grid.layer(name) lookup.
- `texture`: Texture atlas for tile sprites.
- `visible`: Whether the layer is rendered.
- `z_index`: Layer z-order. Negative values render below entities.

**Methods:**

#### `apply_ranges(source, ranges) -> TileLayer`

Apply multiple tile assignments in a single pass.

Note:

**Returns:** self for method chaining Later ranges override earlier ones if overlapping. Cells not matching any range are left unchanged.

#### `apply_threshold(source, range, tile) -> TileLayer`

Set tile index for cells where HeightMap value is within range.

**Returns:** self for method chaining

#### `at(pos) -> int`

at(x, y) -> int
Get the tile index at cell position. Returns -1 if no tile.

**Arguments:**
- `pos`: Position as (x, y) tuple, list, or Vector

#### `fill(index)`

Fill the entire layer with the specified tile index.

#### `fill_rect(pos, size, index)`

Fill a rectangular region with a tile index.

#### `set(pos, index)`

Set the tile index at cell position. Use -1 for no tile.

**Arguments:**
- `pos`: Position as (x, y) tuple, list, or Vector
- `index`: Tile index (-1 for no tile)

### TileMapFile

TileMapFile(path: str)

Load a Tiled map file (.tmx or .tmj).

Parses the map and its referenced tilesets, providing access to tile layers,
object layers, and GID resolution.

Args:
    path: Path to the .tmx or .tmj map file.

Properties:
    width (int, read-only): Map width in tiles.
    height (int, read-only): Map height in tiles.
    tile_width (int, read-only): Tile width in pixels.
    tile_height (int, read-only): Tile height in pixels.
    orientation (str, read-only): Map orientation (e.g. 'orthogonal').
    properties (dict, read-only): Custom map properties.
    tileset_count (int, read-only): Number of referenced tilesets.
    tile_layer_names (list, read-only): Names of tile layers.
    object_layer_names (list, read-only): Names of object layers.

Example:
    tm = mcrfpy.TileMapFile('map.tmx')
    data = tm.tile_layer_data('Ground')
    tm.apply_to_tile_layer(my_tile_layer, 'Ground')


**Properties:**
- `height` *(read-only)*: Map height in tiles (int, read-only).
- `object_layer_names` *(read-only)*: List of object layer names (read-only).
- `orientation` *(read-only)*: Map orientation, e.g. 'orthogonal' (str, read-only).
- `properties` *(read-only)*: Custom map properties as a dict (read-only).
- `tile_height` *(read-only)*: Tile height in pixels (int, read-only).
- `tile_layer_names` *(read-only)*: List of tile layer names (read-only).
- `tile_width` *(read-only)*: Tile width in pixels (int, read-only).
- `tileset_count` *(read-only)*: Number of referenced tilesets (int, read-only).
- `width` *(read-only)*: Map width in tiles (int, read-only).

**Methods:**

#### `apply_to_tile_layer(tile_layer: TileLayer, layer_name: str, tileset_index: int = 0) -> None`

Resolve GIDs and write sprite indices into a TileLayer.

**Arguments:**
- `tile_layer`: Target TileLayer to write into
- `layer_name`: Name of the tile layer in this map
- `tileset_index`: Which tileset to resolve GIDs against (default 0)

#### `object_layer(name: str) -> list[dict]`

Get objects from an object layer as Python dicts.

**Arguments:**
- `name`: Name of the object layer

**Returns:** List of dicts with object properties (id, name, x, y, width, height, etc.).

**Raises:** KeyError: If no object layer with that name exists

#### `resolve_gid(gid: int) -> tuple[int, int]`

Resolve a global tile ID to tileset index and local tile ID.

**Arguments:**
- `gid`: Global tile ID from tile_layer_data()

**Returns:** Tuple of (tileset_index, local_tile_id). (-1, -1) for empty/invalid.

#### `tile_layer_data(name: str) -> list[int]`

Get raw global GID data for a tile layer.

**Arguments:**
- `name`: Name of the tile layer

**Returns:** Flat list of global GIDs (0 = empty tile).

**Raises:** KeyError: If no tile layer with that name exists

#### `tileset(index: int) -> tuple[int, TileSetFile]`

Get a referenced tileset by index.

**Arguments:**
- `index`: Tileset index (0-based)

**Returns:** Tuple of (firstgid, TileSetFile).

### TileSetFile

TileSetFile(path: str)

Load a Tiled tileset file (.tsx or .tsj).

Parses the tileset and provides access to tile metadata, properties,
Wang sets, and texture creation.

Args:
    path: Path to the .tsx or .tsj tileset file.

Properties:
    name (str, read-only): Tileset name.
    tile_width (int, read-only): Width of each tile in pixels.
    tile_height (int, read-only): Height of each tile in pixels.
    tile_count (int, read-only): Total number of tiles.
    columns (int, read-only): Number of columns in the tileset image.
    image_source (str, read-only): Resolved path to the tileset image.
    properties (dict, read-only): Custom properties from the tileset.
    wang_sets (list, read-only): List of WangSet objects.

Example:
    ts = mcrfpy.TileSetFile('tileset.tsx')
    texture = ts.to_texture()
    print(f'{ts.name}: {ts.tile_count} tiles')


**Properties:**
- `columns` *(read-only)*: Number of columns in tileset image (int, read-only).
- `image_source` *(read-only)*: Resolved path to the tileset image file (str, read-only).
- `margin` *(read-only)*: Margin around tiles in pixels (int, read-only).
- `name` *(read-only)*: Tileset name (str, read-only).
- `properties` *(read-only)*: Custom tileset properties as a dict (read-only).
- `spacing` *(read-only)*: Spacing between tiles in pixels (int, read-only).
- `tile_count` *(read-only)*: Total number of tiles (int, read-only).
- `tile_height` *(read-only)*: Height of each tile in pixels (int, read-only).
- `tile_width` *(read-only)*: Width of each tile in pixels (int, read-only).
- `wang_sets` *(read-only)*: List of WangSet objects from this tileset (read-only).

**Methods:**

#### `tile_info(tile_id: int) -> dict | None`

Get metadata for a specific tile.

**Arguments:**
- `tile_id`: Local tile ID (0-based)

**Returns:** Dict with 'properties' and 'animation' keys, or None if no metadata.

#### `to_texture() -> Texture`

Create a Texture from the tileset image.

**Returns:** A Texture object for use with TileLayer.

#### `wang_set(name: str) -> WangSet`

Look up a WangSet by name.

**Arguments:**
- `name`: Name of the Wang set

**Returns:** The WangSet object.

**Raises:** KeyError: If no WangSet with that name exists

### Timer

Timer(name, callback, interval, once=False, start=True)

Create a timer that calls a function at regular intervals.

Args:
    name (str): Unique identifier for the timer
    callback (callable): Function to call - receives (timer, runtime) args
    interval (int): Time between calls in milliseconds
    once (bool): If True, timer stops after first call. Default: False
    start (bool): If True, timer starts immediately. Default: True

Attributes:
    interval (int): Time between calls in milliseconds
    remaining (int): Time until next call in milliseconds (read-only)
    paused (bool): Whether timer is paused (read-only)
    stopped (bool): Whether timer is stopped (read-only)
    active (bool): Running state (read-write). Set True to start, False to pause
    callback (callable): The callback function (preserved when stopped)
    once (bool): Whether timer stops after firing once

Methods:
    start(): Start the timer, adding to engine tick loop
    stop(): Stop the timer (removes from engine, preserves callback)
    pause(): Pause the timer, preserving time remaining
    resume(): Resume a paused timer
    restart(): Reset timer and ensure it's running

Example:
    def on_timer(timer, runtime):
        print(f'Timer {timer} fired at {runtime}ms')
        if runtime > 5000:
            timer.stop()  # Stop but can restart later
    
    timer = mcrfpy.Timer('my_timer', on_timer, 1000)
    timer.pause()  # Pause timer
    timer.resume() # Resume timer
    timer.stop()   # Stop completely
    timer.start()  # Restart from beginning

**Properties:**
- `active`: Running state (bool, read-write). True if running (not paused, not stopped). Set True to start/resume, False to pause.
- `callback`: The callback function (callable). Preserved when stopped, allowing timer restart.
- `interval`: Timer interval in milliseconds (int). Must be positive. Can be changed while timer is running.
- `name` *(read-only)*: Timer name (str, read-only). Unique identifier for this timer.
- `once`: Whether the timer stops after firing once (bool). One-shot timers can be restarted.
- `paused` *(read-only)*: Whether the timer is paused (bool, read-only). Paused timers preserve their remaining time.
- `remaining` *(read-only)*: Time remaining until next trigger in milliseconds (int, read-only). Full interval when stopped.
- `stopped` *(read-only)*: Whether the timer is stopped (bool, read-only). Stopped timers are not in the engine tick loop but preserve their callback.

**Methods:**

#### `pause() -> None`

Pause the timer, preserving the time remaining until next trigger.

Note:

**Returns:** None The timer can be resumed later with resume(). Time spent paused does not count toward the interval.

#### `restart() -> None`

Restart the timer from the beginning and ensure it's running.

Note:

**Returns:** None Resets progress and adds timer to engine if stopped. Equivalent to stop() followed by start().

#### `resume() -> None`

Resume a paused timer from where it left off.

Note:

**Returns:** None Has no effect if the timer is not paused. Timer will fire after the remaining time elapses.

#### `start() -> None`

Start the timer, adding it to the engine tick loop.

Note:

**Returns:** None Resets progress and begins counting toward the next fire. If another timer has this name, it will be stopped.

#### `stop() -> None`

Stop the timer and remove it from the engine tick loop.

Note:

**Returns:** None The callback is preserved, so the timer can be restarted with start() or restart().

### Transition

*Inherits from: IntEnum*

**Properties:**
- `denominator`: the denominator of a rational number in lowest terms
- `imag`: the imaginary part of a complex number
- `numerator`: the numerator of a rational number in lowest terms
- `real`: the real part of a complex number

**Methods:**

#### `as_integer_ratio(...)`

Return a pair of integers, whose ratio is equal to the original int.
The ratio is in lowest terms and has a positive denominator.
>>> (10).as_integer_ratio()
(10, 1)
>>> (-10).as_integer_ratio()
(-10, 1)
>>> (0).as_integer_ratio()
(0, 1)

#### `bit_count(...)`

Number of ones in the binary representation of the absolute value of self.
Also known as the population count.
>>> bin(13)
'0b1101'
>>> (13).bit_count()
3

#### `bit_length(...)`

Number of bits necessary to represent self in binary.
>>> bin(37)
'0b100101'
>>> (37).bit_length()
6

#### `conjugate(...)`

Returns self, the complex conjugate of any int.

#### `from_bytes(...)`

Return the integer represented by the given array of bytes.
  bytes
    Holds the array of bytes to convert.  The argument must either
    support the buffer protocol or be an iterable object producing bytes.
    Bytes and bytearray are examples of built-in objects that support the
    buffer protocol.
  byteorder
    The byte order used to represent the integer.  If byteorder is 'big',
    the most significant byte is at the beginning of the byte array.  If
    byteorder is 'little', the most significant byte is at the end of the
    byte array.  To request the native byte order of the host system, use
    sys.byteorder as the byte order value.  Default is to use 'big'.
  signed
    Indicates whether two's complement is used to represent the integer.

#### `is_integer(...)`

Returns True. Exists for duck type compatibility with float.is_integer.

#### `to_bytes(...)`

Return an array of bytes representing an integer.
  length
    Length of bytes object to use.  An OverflowError is raised if the
    integer is not representable with the given number of bytes.  Default
    is length 1.
  byteorder
    The byte order used to represent the integer.  If byteorder is 'big',
    the most significant byte is at the beginning of the byte array.  If
    byteorder is 'little', the most significant byte is at the end of the
    byte array.  To request the native byte order of the host system, use
    sys.byteorder as the byte order value.  Default is to use 'big'.
  signed
    Determines whether two's complement is used to represent the integer.
    If signed is False and a negative integer is given, an OverflowError
    is raised.

### Traversal

*Inherits from: IntEnum*

**Properties:**
- `denominator`: the denominator of a rational number in lowest terms
- `imag`: the imaginary part of a complex number
- `numerator`: the numerator of a rational number in lowest terms
- `real`: the real part of a complex number

**Methods:**

#### `as_integer_ratio(...)`

Return a pair of integers, whose ratio is equal to the original int.
The ratio is in lowest terms and has a positive denominator.
>>> (10).as_integer_ratio()
(10, 1)
>>> (-10).as_integer_ratio()
(-10, 1)
>>> (0).as_integer_ratio()
(0, 1)

#### `bit_count(...)`

Number of ones in the binary representation of the absolute value of self.
Also known as the population count.
>>> bin(13)
'0b1101'
>>> (13).bit_count()
3

#### `bit_length(...)`

Number of bits necessary to represent self in binary.
>>> bin(37)
'0b100101'
>>> (37).bit_length()
6

#### `conjugate(...)`

Returns self, the complex conjugate of any int.

#### `from_bytes(...)`

Return the integer represented by the given array of bytes.
  bytes
    Holds the array of bytes to convert.  The argument must either
    support the buffer protocol or be an iterable object producing bytes.
    Bytes and bytearray are examples of built-in objects that support the
    buffer protocol.
  byteorder
    The byte order used to represent the integer.  If byteorder is 'big',
    the most significant byte is at the beginning of the byte array.  If
    byteorder is 'little', the most significant byte is at the end of the
    byte array.  To request the native byte order of the host system, use
    sys.byteorder as the byte order value.  Default is to use 'big'.
  signed
    Indicates whether two's complement is used to represent the integer.

#### `is_integer(...)`

Returns True. Exists for duck type compatibility with float.is_integer.

#### `to_bytes(...)`

Return an array of bytes representing an integer.
  length
    Length of bytes object to use.  An OverflowError is raised if the
    integer is not representable with the given number of bytes.  Default
    is length 1.
  byteorder
    The byte order used to represent the integer.  If byteorder is 'big',
    the most significant byte is at the beginning of the byte array.  If
    byteorder is 'little', the most significant byte is at the end of the
    byte array.  To request the native byte order of the host system, use
    sys.byteorder as the byte order value.  Default is to use 'big'.
  signed
    Determines whether two's complement is used to represent the integer.
    If signed is False and a negative integer is given, an OverflowError
    is raised.

### Trigger

*Inherits from: IntEnum*

Enum representing trigger types passed to entity step() callbacks.

Values:
    DONE: Behavior completed (path exhausted, sleep finished, etc.)
    BLOCKED: Movement blocked by wall or collision
    TARGET: Target entity spotted in FOV


**Properties:**
- `denominator`: the denominator of a rational number in lowest terms
- `imag`: the imaginary part of a complex number
- `numerator`: the numerator of a rational number in lowest terms
- `real`: the real part of a complex number

**Methods:**

#### `as_integer_ratio(...)`

Return a pair of integers, whose ratio is equal to the original int.
The ratio is in lowest terms and has a positive denominator.
>>> (10).as_integer_ratio()
(10, 1)
>>> (-10).as_integer_ratio()
(-10, 1)
>>> (0).as_integer_ratio()
(0, 1)

#### `bit_count(...)`

Number of ones in the binary representation of the absolute value of self.
Also known as the population count.
>>> bin(13)
'0b1101'
>>> (13).bit_count()
3

#### `bit_length(...)`

Number of bits necessary to represent self in binary.
>>> bin(37)
'0b100101'
>>> (37).bit_length()
6

#### `conjugate(...)`

Returns self, the complex conjugate of any int.

#### `from_bytes(...)`

Return the integer represented by the given array of bytes.
  bytes
    Holds the array of bytes to convert.  The argument must either
    support the buffer protocol or be an iterable object producing bytes.
    Bytes and bytearray are examples of built-in objects that support the
    buffer protocol.
  byteorder
    The byte order used to represent the integer.  If byteorder is 'big',
    the most significant byte is at the beginning of the byte array.  If
    byteorder is 'little', the most significant byte is at the end of the
    byte array.  To request the native byte order of the host system, use
    sys.byteorder as the byte order value.  Default is to use 'big'.
  signed
    Indicates whether two's complement is used to represent the integer.

#### `is_integer(...)`

Returns True. Exists for duck type compatibility with float.is_integer.

#### `to_bytes(...)`

Return an array of bytes representing an integer.
  length
    Length of bytes object to use.  An OverflowError is raised if the
    integer is not representable with the given number of bytes.  Default
    is length 1.
  byteorder
    The byte order used to represent the integer.  If byteorder is 'big',
    the most significant byte is at the beginning of the byte array.  If
    byteorder is 'little', the most significant byte is at the end of the
    byte array.  To request the native byte order of the host system, use
    sys.byteorder as the byte order value.  Default is to use 'big'.
  signed
    Determines whether two's complement is used to represent the integer.
    If signed is False and a negative integer is given, an OverflowError
    is raised.

### Vector

Vector(x: float = 0, y: float = 0)

2D vector for positions, sizes, and directions.

Args:
    x: X component.
    y: Y component.

Supports arithmetic (+, -, *, /), abs(), len() == 2,
indexing ([0] for x, [1] for y), hashing, and equality.

Properties:
    x (float): X component.
    y (float): Y component.
    int (tuple[int, int], read-only): Integer floor of (x, y).


**Properties:**
- `int` *(read-only)*: Integer tuple (floor of x and y) for use as dict keys. Read-only.
- `x`: X coordinate of the vector (float)
- `y`: Y coordinate of the vector (float)

**Methods:**

#### `angle() -> float`

Get the angle of this vector in radians.

**Returns:** float: Angle in radians from positive x-axis

#### `copy() -> Vector`

Create a copy of this vector.

**Returns:** Vector: New Vector object with same x and y values

#### `distance_to(other: Vector) -> float`

Calculate the distance to another vector.

**Arguments:**
- `other`: The other vector

**Returns:** float: Distance between the two vectors

#### `dot(other: Vector) -> float`

Calculate the dot product with another vector.

**Arguments:**
- `other`: The other vector

**Returns:** float: Dot product of the two vectors

#### `floor() -> Vector`

Return a new vector with floored (integer) coordinates.

Note:

**Returns:** Vector: New Vector with floor(x) and floor(y) Useful for grid-based positioning. For a hashable tuple, use the .int property instead.

#### `magnitude() -> float`

Calculate the length/magnitude of this vector.

**Returns:** float: The magnitude of the vector

#### `magnitude_squared() -> float`

Calculate the squared magnitude of this vector.

Note:

**Returns:** float: The squared magnitude (faster than magnitude()) Use this for comparisons to avoid expensive square root calculation.

#### `normalize() -> Vector`

Return a unit vector in the same direction.

Note:

**Returns:** Vector: New normalized vector with magnitude 1.0 For zero vectors (magnitude 0.0), returns a zero vector rather than raising an exception

### Viewport3D

*Inherits from: Drawable*

Viewport3D(pos=None, size=None, **kwargs)

A 3D rendering viewport that displays a 3D scene as a UI element.

Args:
    pos (tuple, optional): Position as (x, y) tuple. Default: (0, 0)
    size (tuple, optional): Display size as (width, height). Default: (320, 240)

Keyword Args:
    render_resolution (tuple): Internal render resolution (width, height). Default: (320, 240)
    fov (float): Camera field of view in degrees. Default: 60
    camera_pos (tuple): Camera position (x, y, z). Default: (0, 0, 5)
    camera_target (tuple): Camera look-at point (x, y, z). Default: (0, 0, 0)
    bg_color (Color): Background clear color. Default: (25, 25, 50)
    enable_vertex_snap (bool): PS1-style vertex snapping. Default: True
    enable_affine (bool): PS1-style affine texture mapping. Default: True
    enable_dither (bool): PS1-style color dithering. Default: True
    enable_fog (bool): Distance fog. Default: True
    fog_color (Color): Fog color. Default: (128, 128, 153)
    fog_near (float): Fog start distance. Default: 10
    fog_far (float): Fog end distance. Default: 100


**Properties:**
- `bg_color`: Background clear color.
- `bounds`: Bounding box as (pos, size) tuple of Vectors. Returns (Vector(x, y), Vector(width, height)).
- `camera_pos`: Camera position as (x, y, z) tuple.
- `camera_target`: Camera look-at target as (x, y, z) tuple.
- `cell_size`: World units per navigation grid cell.
- `enable_affine`: Enable PS1-style affine texture mapping (warped textures).
- `enable_dither`: Enable PS1-style color dithering.
- `enable_fog`: Enable distance fog.
- `enable_vertex_snap`: Enable PS1-style vertex snapping (jittery vertices).
- `entities` *(read-only)*: Collection of Entity3D objects (read-only). Use append/remove to modify.
- `fog_color`: Fog color.
- `fog_far`: Fog end distance.
- `fog_near`: Fog start distance.
- `fov`: Camera field of view in degrees.
- `global_bounds`: Bounding box as (pos, size) tuple of Vectors in screen coordinates. Returns (Vector(x, y), Vector(width, height)).
- `global_position` *(read-only)*: Global screen position (read-only). Calculates absolute position by walking up the parent chain.
- `grid_size`: Navigation grid dimensions as (width, depth) tuple.
- `h`: Display height in pixels.
- `hovered` *(read-only)*: Whether mouse is currently over this element (read-only). Updated automatically by the engine during mouse movement.
- `on_click`: Callable executed when object is clicked. Function receives (pos: Vector, button: str, action: str).
- `on_enter`: Callback for mouse enter events. Called with (pos: Vector, button: str, action: str) when mouse enters this element's bounds.
- `on_exit`: Callback for mouse exit events. Called with (pos: Vector, button: str, action: str) when mouse leaves this element's bounds.
- `on_move`: Callback for mouse movement within bounds. Called with (pos: Vector, button: str, action: str) for each mouse movement while inside. Performance note: Called frequently during movement - keep handlers fast.
- `opacity`: Opacity level (0.0 = transparent, 1.0 = opaque). Automatically clamped to valid range [0.0, 1.0].
- `parent`: Parent drawable. Get: Returns the parent Frame/Grid if nested, or None if at scene level. Set: Assign a Frame/Grid to reparent, or None to remove from parent.
- `pos`: Position as Vector (x, y).
- `render_resolution`: Internal render resolution (width, height). Lower values for PS1 effect.
- `visible`: Whether the object is visible (bool). Invisible objects are not rendered or clickable.
- `w`: Display width in pixels.
- `x`: X position in pixels.
- `y`: Y position in pixels.
- `z_index`: Z-order for rendering (lower values rendered first). Automatically triggers scene resort when changed.

**Methods:**

#### `add_billboard(billboard)`

Add a Billboard to the viewport.

**Arguments:**
- `billboard`: Billboard object to add

#### `add_layer(name, z_index=0) -> dict`

Add a new mesh layer to the viewport.

**Arguments:**
- `name`: Unique identifier for the layer
- `z_index`: Render order (lower = rendered first)

#### `add_mesh(layer_name, model, pos, rotation=0, scale=1.0) -> int`

Add a Model3D instance to a layer at the specified position.

**Arguments:**
- `layer_name`: Name of layer to add mesh to (created if needed)
- `model`: Model3D object to place
- `pos`: World position as (x, y, z) tuple
- `rotation`: Y-axis rotation in degrees
- `scale`: Uniform scale factor

**Returns:** Index of the mesh instance

#### `add_voxel_layer(voxel_grid, z_index=0)`

Add a VoxelGrid as a renderable layer.

**Arguments:**
- `voxel_grid`: VoxelGrid object to render
- `z_index`: Render order (lower = rendered first)

#### `animate(property: str, target: Any, duration: float, easing=None, delta=False, loop=False, callback=None, conflict_mode='replace') -> Animation`

Create and start an animation on this drawable's property.

Note:

**Arguments:**
- `property`: Name of the property to animate (e.g., 'x', 'fill_color', 'opacity')
- `target`: Target value - type depends on property (float, tuple for color/vector, etc.)
- `duration`: Animation duration in seconds
- `easing`: Easing function: Easing enum value, string name, or None for linear
- `delta`: If True, target is relative to current value; if False, target is absolute
- `loop`: If True, animation repeats from start when it reaches the end (default False)
- `callback`: Optional callable invoked when animation completes (not called for looping animations)
- `conflict_mode`: 'replace' (default), 'queue', or 'error' if property already animating

**Returns:** Animation object for monitoring progress

**Raises:** ValueError: If property name is not valid for this drawable type This is a convenience method that creates an Animation, starts it, and adds it to the AnimationManager.

#### `apply_heightmap(heightmap, y_scale=1.0)`

Set cell heights from HeightMap.

**Arguments:**
- `heightmap`: HeightMap object
- `y_scale`: Vertical scale factor

#### `apply_terrain_colors(layer_name, r_map, g_map, b_map)`

Apply per-vertex colors to terrain from RGB HeightMaps.

**Arguments:**
- `layer_name`: Name of terrain layer to colorize
- `r_map`: HeightMap for red channel (0-1 values)
- `g_map`: HeightMap for green channel (0-1 values)
- `b_map`: HeightMap for blue channel (0-1 values)

#### `apply_threshold(heightmap, min_height, max_height, walkable=True)`

Set cell walkability based on height thresholds.

**Arguments:**
- `heightmap`: HeightMap object
- `min_height`: Minimum height (0-1)
- `max_height`: Maximum height (0-1)
- `walkable`: Walkability value for cells in range

#### `at(x, z) -> VoxelPoint`

Get VoxelPoint at grid coordinates.

**Arguments:**
- `x`: X coordinate in grid
- `z`: Z coordinate in grid

**Returns:** VoxelPoint object for the cell

#### `billboard_count() -> int`

Get the number of billboards.

**Returns:** Number of billboards in the viewport

#### `build_terrain(layer_name, heightmap, y_scale=1.0, cell_size=1.0) -> int`

Build terrain mesh from HeightMap on specified layer.

**Arguments:**
- `layer_name`: Name of layer to build terrain on (created if doesn't exist)
- `heightmap`: HeightMap object with height data
- `y_scale`: Vertical exaggeration factor
- `cell_size`: World-space size of each grid cell

**Returns:** Number of vertices in the generated mesh

#### `clear_billboards()`

Remove all billboards from the viewport.

#### `clear_meshes(layer_name)`

Clear all mesh instances from a layer.

**Arguments:**
- `layer_name`: Name of layer to clear

#### `clear_voxel_nav_region(voxel_grid)`

Clear navigation cells in a voxel grid's footprint.
Resets walkability, transparency, height, and cost to defaults
for all nav cells corresponding to the voxel grid's XZ extent.

**Arguments:**
- `voxel_grid`: VoxelGrid whose nav region to clear

#### `compute_fov(origin, radius=10) -> list`

Compute field of view from a position.

**Arguments:**
- `origin`: Origin point as (x, z) tuple
- `radius`: FOV radius

**Returns:** List of visible (x, z) positions

#### `find_path(start, end) -> list`

Find A* path between two points.

**Arguments:**
- `start`: Starting point as (x, z) tuple
- `end`: End point as (x, z) tuple

**Returns:** List of (x, z) tuples forming the path, or empty list if no path

#### `follow(entity, distance=10, height=5, smoothing=1.0)`

Position camera to follow an entity.

**Arguments:**
- `entity`: Entity3D to follow
- `distance`: Distance behind entity
- `height`: Camera height above entity
- `smoothing`: Interpolation factor (0-1). 1 = instant, lower = smoother

#### `get_billboard(index) -> Billboard`

Get a Billboard by index.

**Arguments:**
- `index`: Index of the billboard

**Returns:** Billboard object

#### `get_layer(name) -> dict or None`

Get a layer by name.

#### `is_in_fov(x, z) -> bool`

Check if a cell is in the current FOV (after compute_fov).

**Arguments:**
- `x`: X coordinate
- `z`: Z coordinate

**Returns:** True if the cell is visible

#### `layer_count() -> int`

Get the number of mesh layers.

#### `move(dx, dy) or (delta) -> None`

Move the element by a relative offset.

Note:

**Arguments:**
- `dx`: Horizontal offset in pixels (or use delta)
- `dy`: Vertical offset in pixels (or use delta)
- `delta`: Offset as tuple, list, or Vector: (dx, dy)

#### `orbit_camera(angle=0, distance=10, height=5)`

Position camera to orbit around origin.

**Arguments:**
- `angle`: Orbit angle in radians
- `distance`: Distance from origin
- `height`: Camera height above XZ plane

#### `place_blocking(grid_pos, footprint, walkable=False, transparent=False)`

Mark grid cells as blocking for pathfinding and FOV.

**Arguments:**
- `grid_pos`: Top-left grid position as (x, z) tuple
- `footprint`: Size in cells as (width, depth) tuple
- `walkable`: Whether cells should be walkable (default: False)
- `transparent`: Whether cells should be transparent (default: False)

#### `project_all_voxels_to_nav(headroom=2)`

Project all voxel layers to the navigation grid.
Resets navigation grid and projects each voxel layer in z_index order.
Later layers (higher z_index) overwrite earlier ones.

**Arguments:**
- `headroom`: Required air voxels above floor for walkability (default: 2)

#### `project_voxel_to_nav(voxel_grid, headroom=2)`

Project a VoxelGrid to the navigation grid.
Scans each column of the voxel grid and updates corresponding
navigation cells with walkability, transparency, height, and cost.

**Arguments:**
- `voxel_grid`: VoxelGrid to project
- `headroom`: Required air voxels above floor for walkability (default: 2)

#### `realign() -> None`

Reapply alignment relative to parent, useful for responsive layouts.

Note:
    Call this to recalculate position after parent changes size. For elements with align=None, this has no effect.

#### `remove_billboard(billboard)`

Remove a Billboard from the viewport.

**Arguments:**
- `billboard`: Billboard object to remove

#### `remove_layer(name) -> bool`

Remove a layer by name. Returns True if found and removed.

#### `remove_voxel_layer(voxel_grid) -> bool`

Remove a VoxelGrid layer from the viewport.

**Arguments:**
- `voxel_grid`: VoxelGrid object to remove

**Returns:** True if the layer was found and removed

#### `resize(width, height) or (size) -> None`

Resize the element to new dimensions.

Note:

**Arguments:**
- `width`: New width in pixels (or use size)
- `height`: New height in pixels (or use size)
- `size`: Size as tuple, list, or Vector: (width, height)

#### `screen_to_world(x, y, y_plane=0.0) -> tuple or None`

Convert screen coordinates to world position via ray casting.

**Arguments:**
- `x`: Screen X coordinate relative to viewport
- `y`: Screen Y coordinate relative to viewport
- `y_plane`: Y value of horizontal plane to intersect (default: 0.0)

**Returns:** (x, y, z) world position tuple, or None if no intersection with the plane

#### `set_grid_size(width, depth)`

Initialize navigation grid with specified dimensions.

**Arguments:**
- `width`: Grid width (X axis)
- `depth`: Grid depth (Z axis)

#### `set_slope_cost(max_slope=0.5, cost_multiplier=1.0)`

Calculate slope costs and mark steep cells unwalkable.

**Arguments:**
- `max_slope`: Maximum height difference before marking unwalkable
- `cost_multiplier`: Cost increase per unit slope

#### `voxel_layer_count() -> int`

Get the number of voxel layers.

**Returns:** Number of voxel layers in the viewport

### VoxelGrid

VoxelGrid(size: tuple[int, int, int], cell_size: float = 1.0)

A dense 3D grid of voxel material IDs with a material palette.

VoxelGrids provide volumetric storage for 3D structures like buildings,
caves, and dungeon walls. Each cell stores a uint8 material ID (0-255),
where 0 is always air.

Args:
    size: (width, height, depth) dimensions. Immutable after creation.
    cell_size: World units per voxel. Default 1.0.

Properties:
    size (tuple, read-only): Grid dimensions as (width, height, depth)
    width, height, depth (int, read-only): Individual dimensions
    cell_size (float, read-only): World units per voxel
    offset (tuple): World-space position (x, y, z)
    rotation (float): Y-axis rotation in degrees
    material_count (int, read-only): Number of defined materials

Example:
    voxels = mcrfpy.VoxelGrid(size=(16, 8, 16), cell_size=1.0)
    stone = voxels.add_material('stone', color=mcrfpy.Color(128, 128, 128))
    voxels.set(5, 0, 5, stone)
    assert voxels.get(5, 0, 5) == stone
    print(f'Non-air voxels: {voxels.count_non_air()}')

**Properties:**
- `cell_size` *(read-only)*: World units per voxel. Read-only.
- `depth` *(read-only)*: Grid depth (Z dimension). Read-only.
- `greedy_meshing`: Enable greedy meshing optimization (reduces vertex count for uniform regions).
- `height` *(read-only)*: Grid height (Y dimension). Read-only.
- `material_count` *(read-only)*: Number of materials in the palette. Read-only.
- `offset`: World-space position (x, y, z) of the grid origin.
- `rotation`: Y-axis rotation in degrees.
- `size` *(read-only)*: Dimensions (width, height, depth) of the grid. Read-only.
- `vertex_count` *(read-only)*: Number of vertices after mesh generation. Read-only.
- `visible`: Show or hide this voxel grid in rendering.
- `width` *(read-only)*: Grid width (X dimension). Read-only.

**Methods:**

#### `add_material(name, color=Color(255,255,255), sprite_index=-1, transparent=False, path_cost=1.0) -> int`

Add a new material to the palette. Returns the material ID (1-indexed).
Material 0 is always air (implicit, never stored in palette).
Maximum 255 materials can be added.

#### `clear() -> None`

Clear the grid (fill with air, material 0).

#### `copy_region(min_coord, max_coord) -> VoxelRegion`

Copy a rectangular region to a VoxelRegion prefab.

**Arguments:**
- `min_coord`: (x0, y0, z0) - minimum corner (inclusive)
- `max_coord`: (x1, y1, z1) - maximum corner (inclusive)

**Returns:** VoxelRegion object that can be pasted elsewhere.

#### `count_material(material) -> int`

Count the number of voxels with the specified material ID.

#### `count_non_air() -> int`

Count the number of non-air voxels in the grid.

#### `fill(material) -> None`

Fill the entire grid with the specified material ID.

#### `fill_box(min_coord, max_coord, material) -> None`

Fill a rectangular region with the specified material.

**Arguments:**
- `min_coord`: (x0, y0, z0) - minimum corner (inclusive)
- `max_coord`: (x1, y1, z1) - maximum corner (inclusive)
- `material`: material ID (0-255)

#### `fill_box_hollow(min_coord, max_coord, material, thickness=1) -> None`

Create a hollow rectangular room (walls only, hollow inside).

**Arguments:**
- `min_coord`: (x0, y0, z0) - minimum corner (inclusive)
- `max_coord`: (x1, y1, z1) - maximum corner (inclusive)
- `material`: material ID for walls (0-255)
- `thickness`: wall thickness in voxels (default 1)

#### `fill_cylinder(base_pos, radius, height, material) -> None`

Fill a vertical cylinder (Y-axis aligned).

**Arguments:**
- `base_pos`: (cx, cy, cz) - base center position
- `radius`: cylinder radius in voxels
- `height`: cylinder height in voxels
- `material`: material ID (0-255)

#### `fill_noise(min_coord, max_coord, material, threshold=0.5, scale=0.1, seed=0) -> None`

Fill region with 3D noise-based pattern (caves, clouds).

**Arguments:**
- `min_coord`: (x0, y0, z0) - minimum corner
- `max_coord`: (x1, y1, z1) - maximum corner
- `material`: material ID for solid areas
- `threshold`: noise threshold (0-1, higher = more solid)
- `scale`: noise scale (smaller = larger features)
- `seed`: random seed (0 for default)

#### `fill_sphere(center, radius, material) -> None`

Fill a spherical region.

**Arguments:**
- `center`: (cx, cy, cz) - sphere center coordinates
- `radius`: sphere radius in voxels
- `material`: material ID (0-255, use 0 to carve)

#### `from_bytes(data) -> bool`

Load voxel data from a bytes object.

Note: This replaces the current grid data entirely.

**Arguments:**
- `data`: bytes object containing serialized grid data

**Returns:** True on success, False on failure.

#### `get(x, y, z) -> int`

Get the material ID at integer coordinates.
Returns 0 (air) for out-of-bounds coordinates.

#### `get_material(id) -> dict`

Get material properties by ID.
Returns dict with keys: name, color, sprite_index, transparent, path_cost.
ID 0 returns the implicit air material.

#### `load(path) -> bool`

Load voxel data from a binary file.

Note: This replaces the current grid data entirely, including

**Arguments:**
- `path`: File path to load from

**Returns:** True on success, False on failure. dimensions and material palette.

#### `paste_region(region, position, skip_air=True) -> None`

Paste a VoxelRegion prefab at the specified position.

**Arguments:**
- `region`: VoxelRegion from copy_region()
- `position`: (x, y, z) - paste destination
- `skip_air`: if True, air voxels don't overwrite (default True)

#### `project_column(x, z, headroom=2) -> dict`

Project a single column to navigation info.
Scans the column from top to bottom, finding the topmost floor
(solid voxel with air above) and checking for adequate headroom.

**Arguments:**
- `x`: X coordinate in voxel grid
- `z`: Z coordinate in voxel grid
- `headroom`: Required air voxels above floor (default 2)

**Returns:** dict with keys: height (float): World Y of floor surface walkable (bool): True if floor found with adequate headroom transparent (bool): True if no opaque voxels in column path_cost (float): Floor material's path cost

#### `rebuild_mesh() -> None`

Force immediate mesh rebuild for rendering.

#### `save(path) -> bool`

Save the voxel grid to a binary file.

**Arguments:**
- `path`: File path to save to (.mcvg extension recommended)

**Returns:** True on success, False on failure. The file format includes grid dimensions, cell size, material palette, and RLE-compressed voxel data.

#### `set(x, y, z, material) -> None`

Set the material ID at integer coordinates.
Out-of-bounds coordinates are silently ignored.

#### `to_bytes() -> bytes`

Serialize the voxel grid to a bytes object.

**Returns:** bytes object containing the serialized grid data. Useful for network transmission or custom storage.

### VoxelRegion

VoxelRegion - Portable voxel data for copy/paste operations.

Created by VoxelGrid.copy_region(), used with paste_region().
Cannot be instantiated directly.

Properties:
    size (tuple, read-only): Dimensions as (width, height, depth)
    width, height, depth (int, read-only): Individual dimensions

**Properties:**
- `depth` *(read-only)*: Region depth. Read-only.
- `height` *(read-only)*: Region height. Read-only.
- `size` *(read-only)*: Dimensions (width, height, depth) of the region. Read-only.
- `width` *(read-only)*: Region width. Read-only.

**Methods:**

### WangSet

WangSet - Wang terrain auto-tile set from a Tiled tileset.

WangSets are obtained from TileSetFile.wang_sets or TileSetFile.wang_set().
They map abstract terrain types to concrete sprite indices using Tiled's
Wang tile algorithm.

Properties:
    name (str, read-only): Wang set name.
    type (str, read-only): 'corner', 'edge', or 'mixed'.
    color_count (int, read-only): Number of terrain colors.
    colors (list, read-only): List of color dicts.

Example:
    ws = tileset.wang_set('overworld')
    Terrain = ws.terrain_enum()
    tiles = ws.resolve(discrete_map)


**Properties:**
- `color_count` *(read-only)*: Number of terrain colors (int, read-only).
- `colors` *(read-only)*: List of color dicts with name, index, tile_id, probability (read-only).
- `name` *(read-only)*: Wang set name (str, read-only).
- `type` *(read-only)*: Wang set type: 'corner', 'edge', or 'mixed' (str, read-only).

**Methods:**

#### `apply(discrete_map: DiscreteMap, tile_layer: TileLayer) -> None`

Resolve terrain and write tile indices directly into a TileLayer.

**Arguments:**
- `discrete_map`: A DiscreteMap with terrain IDs
- `tile_layer`: Target TileLayer to write resolved tiles into

#### `resolve(discrete_map: DiscreteMap) -> list[int]`

Resolve terrain data to tile indices using Wang tile rules.

**Arguments:**
- `discrete_map`: A DiscreteMap with terrain IDs matching this WangSet's colors

**Returns:** List of tile IDs (one per cell). -1 means no matching Wang tile.

#### `terrain_enum() -> IntEnum`

Generate a Python IntEnum from this WangSet's terrain colors.

**Returns:** IntEnum class with NONE=0 and one member per color (UPPER_SNAKE_CASE).

### Window

Window singleton for accessing and modifying the game window properties

**Properties:**
- `framerate_limit`: Frame rate limit in FPS (int, 0 for unlimited). Caps maximum frame rate.
- `fullscreen`: Window fullscreen state (bool). Setting this recreates the window.
- `game_resolution`: Fixed game resolution as (width, height) tuple. Enables resolution-independent rendering with scaling.
- `resolution`: Window resolution as (width, height) tuple. Setting this recreates the window.
- `scaling_mode`: Viewport scaling mode (str): 'center' (no scaling), 'stretch' (fill window), or 'fit' (maintain aspect ratio).
- `title`: Window title string (str). Displayed in the window title bar.
- `visible`: Window visibility state (bool). Hidden windows still process events.
- `vsync`: Vertical sync enabled state (bool). Prevents screen tearing but may limit framerate.

**Methods:**

#### `center() -> None`

Center the window on the screen.

Note:

**Returns:** None Only works in windowed mode. Has no effect when fullscreen or in headless mode.

#### `get() -> Window`

Get the Window singleton instance.

Note:

**Returns:** Window: The global window object This is a class method. Call as Window.get(). There is only one window instance per application.

#### `screenshot(filename: str = None) -> bytes | None`

Take a screenshot of the current window contents.

Note:

**Arguments:**
- `filename`: Optional path to save screenshot. If omitted, returns raw RGBA bytes.

**Returns:** bytes | None: Raw RGBA pixel data if no filename given, otherwise None after saving Screenshot is taken at the actual window resolution. Use after render loop update for current frame.

## Constants

