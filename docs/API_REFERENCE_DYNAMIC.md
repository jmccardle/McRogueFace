# McRogueFace API Reference

*Generated on 2026-01-23 20:45:13*

*This documentation was dynamically generated from the compiled module.*

## Table of Contents

- [Functions](#functions)
- [Classes](#classes)
  - [AStarPath](#astarpath)
  - [Alignment](#alignment)
  - [Animation](#animation)
  - [Arc](#arc)
  - [BSP](#bsp)
  - [Caption](#caption)
  - [Circle](#circle)
  - [Color](#color)
  - [ColorLayer](#colorlayer)
  - [DijkstraMap](#dijkstramap)
  - [Drawable](#drawable)
  - [Easing](#easing)
  - [Entity](#entity)
  - [FOV](#fov)
  - [Font](#font)
  - [Frame](#frame)
  - [Grid](#grid)
  - [HeightMap](#heightmap)
  - [InputState](#inputstate)
  - [Key](#key)
  - [Keyboard](#keyboard)
  - [Line](#line)
  - [Mouse](#mouse)
  - [MouseButton](#mousebutton)
  - [Music](#music)
  - [NoiseSource](#noisesource)
  - [Scene](#scene)
  - [Sound](#sound)
  - [Sprite](#sprite)
  - [Texture](#texture)
  - [TileLayer](#tilelayer)
  - [Timer](#timer)
  - [Transition](#transition)
  - [Traversal](#traversal)
  - [Vector](#vector)
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

### `findAll(pattern: str, scene: str = None) -> list`

Find all UI elements matching a name pattern.

Note:

**Arguments:**
- `pattern`: Name pattern with optional wildcards (* matches any characters)
- `scene`: Scene to search in (default: current scene)

**Returns:** list: All matching UI elements and entities

### `getMetrics() -> dict`

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

### `setDevConsole(enabled: bool) -> None`

Enable or disable the developer console overlay.

Note:

**Arguments:**
- `enabled`: True to enable the console (default), False to disable

**Returns:** None When disabled, the grave/tilde key will not open the console. Use this to ship games without debug features.

### `setScale(multiplier: float) -> None`

Scale the game window size.

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

Animation(property: str, target: Any, duration: float, easing: str = 'linear', delta: bool = False, callback: Callable = None)

Create an animation that interpolates a property value over time.

Args:
    property: Property name to animate. Valid properties depend on target type:
        - Position/Size: 'x', 'y', 'w', 'h', 'pos', 'size'
        - Appearance: 'fill_color', 'outline_color', 'outline', 'opacity'
        - Sprite: 'sprite_index', 'sprite_number', 'scale'
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
    callback: Function(animation, target) called when animation completes.

Example:
    # Move a frame from current position to x=500 over 2 seconds
    anim = mcrfpy.Animation('x', 500.0, 2.0, 'easeInOut')
    anim.start(my_frame)

    # Fade out with callback
    def on_done(anim, target):
        print('Animation complete!')
    fade = mcrfpy.Animation('fill_color.a', 0, 1.0, callback=on_done)
    fade.start(my_sprite)

    # Animate through sprite frames
    walk_cycle = mcrfpy.Animation('sprite_index', [0,1,2,3,2,1], 0.5, 'linear')
    walk_cycle.start(my_entity)


**Properties:**
- `duration` *(read-only)*: Animation duration in seconds (float, read-only). Total time for the animation to complete.
- `elapsed` *(read-only)*: Elapsed time in seconds (float, read-only). Time since the animation started.
- `is_complete` *(read-only)*: Whether animation is complete (bool, read-only). True when elapsed >= duration or complete() was called.
- `is_delta` *(read-only)*: Whether animation uses delta mode (bool, read-only). In delta mode, the target value is added to the starting value.
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
- `parent`: Parent drawable. Get: Returns the parent Frame/Grid if nested, or None if at scene level. Set: Assign a Frame/Grid to reparent, or None to remove from parent.
- `pos`: Position as a Vector (same as center).
- `radius`: Arc radius in pixels
- `start_angle`: Starting angle in degrees
- `thickness`: Line thickness
- `vert_margin`: Vertical margin override (float, 0 = use general margin). Invalid for horizontally-centered alignments (CENTER_LEFT, CENTER_RIGHT, CENTER).
- `visible`: Whether the object is visible (bool). Invisible objects are not rendered or clickable.
- `z_index`: Z-order for rendering (lower values rendered first).

**Methods:**

#### `animate(property: str, target: Any, duration: float, easing=None, delta=False, callback=None, conflict_mode='replace') -> Animation`

Create and start an animation on this drawable's property.

Note:

**Arguments:**
- `property`: Name of the property to animate (e.g., 'x', 'fill_color', 'opacity')
- `target`: Target value - type depends on property (float, tuple for color/vector, etc.)
- `duration`: Animation duration in seconds
- `easing`: Easing function: Easing enum value, string name, or None for linear
- `delta`: If True, target is relative to current value; if False, target is absolute
- `callback`: Optional callable invoked when animation completes
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
- `outline`: Thickness of the border
- `outline_color`: Outline color of the text. Returns a copy; modifying components requires reassignment. For animation, use 'outline_color.r', 'outline_color.g', etc.
- `parent`: Parent drawable. Get: Returns the parent Frame/Grid if nested, or None if at scene level. Set: Assign a Frame/Grid to reparent, or None to remove from parent.
- `pos`: (x, y) vector
- `size` *(read-only)*: Text dimensions as Vector (read-only)
- `text`: The text displayed
- `vert_margin`: Vertical margin override (float, 0 = use general margin). Invalid for horizontally-centered alignments (CENTER_LEFT, CENTER_RIGHT, CENTER).
- `visible`: Whether the object is visible (bool). Invisible objects are not rendered or clickable.
- `w` *(read-only)*: Text width in pixels (read-only)
- `x`: X coordinate of top-left corner
- `y`: Y coordinate of top-left corner
- `z_index`: Z-order for rendering (lower values rendered first). Automatically triggers scene resort when changed.

**Methods:**

#### `animate(property: str, target: Any, duration: float, easing=None, delta=False, callback=None, conflict_mode='replace') -> Animation`

Create and start an animation on this drawable's property.

Note:

**Arguments:**
- `property`: Name of the property to animate (e.g., 'x', 'fill_color', 'opacity')
- `target`: Target value - type depends on property (float, tuple for color/vector, etc.)
- `duration`: Animation duration in seconds
- `easing`: Easing function: Easing enum value, string name, or None for linear
- `delta`: If True, target is relative to current value; if False, target is absolute
- `callback`: Optional callable invoked when animation completes
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
- `outline`: Outline thickness (0 for no outline)
- `outline_color`: Outline color of the circle
- `parent`: Parent drawable. Get: Returns the parent Frame/Grid if nested, or None if at scene level. Set: Assign a Frame/Grid to reparent, or None to remove from parent.
- `pos`: Position as a Vector (same as center).
- `radius`: Circle radius in pixels
- `vert_margin`: Vertical margin override (float, 0 = use general margin). Invalid for horizontally-centered alignments (CENTER_LEFT, CENTER_RIGHT, CENTER).
- `visible`: Whether the object is visible (bool). Invisible objects are not rendered or clickable.
- `z_index`: Z-order for rendering (lower values rendered first).

**Methods:**

#### `animate(property: str, target: Any, duration: float, easing=None, delta=False, callback=None, conflict_mode='replace') -> Animation`

Create and start an animation on this drawable's property.

Note:

**Arguments:**
- `property`: Name of the property to animate (e.g., 'x', 'fill_color', 'opacity')
- `target`: Target value - type depends on property (float, tuple for color/vector, etc.)
- `duration`: Animation duration in seconds
- `easing`: Easing function: Easing enum value, string name, or None for linear
- `delta`: If True, target is relative to current value; if False, target is absolute
- `callback`: Optional callable invoked when animation completes
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

ColorLayer(z_index=-1, grid_size=None)

A grid layer that stores RGBA colors per cell for background/overlay effects.

ColorLayers are typically created via Grid.add_layer('color', ...) rather than
instantiated directly. When attached to a Grid, the layer inherits rendering
parameters and can participate in FOV (field of view) calculations.

Args:
    z_index (int): Render order relative to entities. Negative values render
        below entities (as backgrounds), positive values render above entities
        (as overlays). Default: -1 (background)
    grid_size (tuple): Dimensions as (width, height). If None, the layer will
        inherit the parent Grid's dimensions when attached. Default: None

Attributes:
    z_index (int): Layer z-order relative to entities (read/write)
    visible (bool): Whether layer is rendered (read/write)
    grid_size (tuple): Layer dimensions as (width, height) (read-only)

Methods:
    at(x, y) -> Color: Get the color at cell position (x, y)
    set(x, y, color): Set the color at cell position (x, y)
    fill(color): Fill the entire layer with a single color
    fill_rect(x, y, w, h, color): Fill a rectangular region with a color
    draw_fov(...): Draw FOV-based visibility colors
    apply_perspective(entity, ...): Bind layer to entity for automatic FOV updates

Example:
    grid = mcrfpy.Grid(grid_size=(20, 15), texture=my_texture,
                       pos=(50, 50), size=(640, 480))
    layer = grid.add_layer('color', z_index=-1)
    layer.fill(mcrfpy.Color(40, 40, 40))  # Dark gray background
    layer.set(5, 5, mcrfpy.Color(255, 0, 0, 128))  # Semi-transparent red cell

**Properties:**
- `grid_size`: Layer dimensions as (width, height) tuple.
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

Attributes:
    pos (Vector): Pixel position relative to grid (requires grid attachment)
    x, y (float): Pixel position components (requires grid attachment)
    grid_pos (Vector): Integer tile coordinates (logical game position)
    grid_x, grid_y (int): Integer tile coordinate components
    draw_pos (Vector): Fractional tile position for smooth animation
    gridstate (GridPointState): Visibility state for grid points
    sprite_index (int): Current sprite index
    visible (bool): Visibility state
    opacity (float): Opacity value
    name (str): Element name

**Properties:**
- `draw_pos`: Fractional tile position for rendering (Vector). Use for smooth animation between grid cells.
- `grid`: Grid this entity belongs to. Get: Returns the Grid or None. Set: Assign a Grid to move entity, or None to remove from grid.
- `grid_pos`: Grid position as integer tile coordinates (Vector). The logical cell this entity occupies.
- `grid_x`: Grid X position as integer tile coordinate.
- `grid_y`: Grid Y position as integer tile coordinate.
- `gridstate`: Grid point states for the entity
- `name`: Name for finding elements
- `opacity`: Opacity (0.0 = transparent, 1.0 = opaque)
- `pos`: Pixel position relative to grid (Vector). Computed as draw_pos * tile_size. Requires entity to be attached to a grid.
- `sprite_index`: Sprite index on the texture on the display
- `sprite_number`: Sprite index (DEPRECATED: use sprite_index instead)
- `visible`: Visibility flag
- `x`: Pixel X position relative to grid. Requires entity to be attached to a grid.
- `y`: Pixel Y position relative to grid. Requires entity to be attached to a grid.

**Methods:**

#### `animate(property: str, target: Any, duration: float, easing=None, delta=False, callback=None, conflict_mode='replace') -> Animation`

Create and start an animation on this entity's property.

Note:

**Arguments:**
- `property`: Name of the property to animate: 'draw_x', 'draw_y' (tile coords), 'sprite_scale', 'sprite_index'
- `target`: Target value - float or int depending on property
- `duration`: Animation duration in seconds
- `easing`: Easing function: Easing enum value, string name, or None for linear
- `delta`: If True, target is relative to current value; if False, target is absolute
- `callback`: Optional callable invoked when animation completes
- `conflict_mode`: 'replace' (default), 'queue', or 'error' if property already animating

**Returns:** Animation object for monitoring progress

**Raises:** ValueError: If property name is not valid for Entity (draw_x, draw_y, sprite_scale, sprite_index) Use 'draw_x'/'draw_y' to animate tile coordinates for smooth movement between grid cells.

#### `at(x, y) or at(pos) -> GridPointState`

Get the grid point state at the specified position.

**Arguments:**
- `pos`: Grid coordinates as tuple, list, or Vector

**Returns:** GridPointState for the entity's view of that grid cell.

#### `die(...)`

Remove this entity from its grid

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

#### `resize(width, height) or (size) -> None`

Resize the element to new dimensions.

Note:

**Arguments:**
- `width`: New width in pixels (or use size)
- `height`: New height in pixels (or use size)
- `size`: Size as tuple, list, or Vector: (width, height)

#### `update_visibility() -> None`

Update entity's visibility state based on current FOV.
Recomputes which cells are visible from the entity's position and updates
the entity's gridstate to track explored areas. This is called automatically
when the entity moves if it has a grid with perspective set.

#### `visible_entities(fov=None, radius=None) -> list[Entity]`

Get list of other entities visible from this entity's position.

**Returns:** List of Entity objects that are within field of view. Computes FOV from this entity's position and returns all other entities whose positions fall within the visible area.

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

SFML Font Object

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
- `outline`: Thickness of the border
- `outline_color`: Outline color of the rectangle. Returns a copy; modifying components requires reassignment. For animation, use 'outline_color.r', 'outline_color.g', etc.
- `parent`: Parent drawable. Get: Returns the parent Frame/Grid if nested, or None if at scene level. Set: Assign a Frame/Grid to reparent, or None to remove from parent.
- `pos`: Position as a Vector
- `vert_margin`: Vertical margin override (float, 0 = use general margin). Invalid for horizontally-centered alignments (CENTER_LEFT, CENTER_RIGHT, CENTER).
- `visible`: Whether the object is visible (bool). Invisible objects are not rendered or clickable.
- `w`: width of the rectangle
- `x`: X coordinate of top-left corner
- `y`: Y coordinate of top-left corner
- `z_index`: Z-order for rendering (lower values rendered first). Automatically triggers scene resort when changed.

**Methods:**

#### `animate(property: str, target: Any, duration: float, easing=None, delta=False, callback=None, conflict_mode='replace') -> Animation`

Create and start an animation on this drawable's property.

Note:

**Arguments:**
- `property`: Name of the property to animate (e.g., 'x', 'fill_color', 'opacity')
- `target`: Target value - type depends on property (float, tuple for color/vector, etc.)
- `duration`: Animation duration in seconds
- `easing`: Easing function: Easing enum value, string name, or None for linear
- `delta`: If True, target is relative to current value; if False, target is absolute
- `callback`: Optional callable invoked when animation completes
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

Grid(pos=None, size=None, grid_size=None, texture=None, **kwargs)

A grid-based UI element for tile-based rendering and entity management.

Args:
    pos (tuple, optional): Position as (x, y) tuple. Default: (0, 0)
    size (tuple, optional): Size as (width, height) tuple. Default: auto-calculated from grid_size
    grid_size (tuple, optional): Grid dimensions as (grid_w, grid_h) tuple. Default: (2, 2)
    texture (Texture, optional): Texture containing tile sprites. Default: default texture

Keyword Args:
    fill_color (Color): Background fill color. Default: None
    click (callable): Click event handler. Default: None
    center_x (float): X coordinate of center point. Default: 0
    center_y (float): Y coordinate of center point. Default: 0
    zoom (float): Zoom level for rendering. Default: 1.0
    perspective (int): Entity perspective index (-1 for omniscient). Default: -1
    visible (bool): Visibility state. Default: True
    opacity (float): Opacity (0.0-1.0). Default: 1.0
    z_index (int): Rendering order. Default: 0
    name (str): Element name for finding. Default: None
    x (float): X position override. Default: 0
    y (float): Y position override. Default: 0
    w (float): Width override. Default: auto-calculated
    h (float): Height override. Default: auto-calculated
    grid_w (int): Grid width override. Default: 2
    grid_h (int): Grid height override. Default: 2
    align (Alignment): Alignment relative to parent. Default: None
    margin (float): Margin from parent edge when aligned. Default: 0
    horiz_margin (float): Horizontal margin override. Default: 0 (use margin)
    vert_margin (float): Vertical margin override. Default: 0 (use margin)

Attributes:
    x, y (float): Position in pixels
    w, h (float): Size in pixels
    pos (Vector): Position as a Vector object
    size (Vector): Size as (width, height) Vector
    center (Vector): Center point as (x, y) Vector
    center_x, center_y (float): Center point coordinates
    zoom (float): Zoom level for rendering
    grid_size (Vector): Grid dimensions (width, height) in tiles
    grid_w, grid_h (int): Grid dimensions
    texture (Texture): Tile texture atlas
    fill_color (Color): Background color
    entities (EntityCollection): Collection of entities in the grid
    perspective (int): Entity perspective index
    click (callable): Click event handler
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
- `center`: Grid coordinate at the center of the Grid's view (pan)
- `center_x`: center of the view X-coordinate
- `center_y`: center of the view Y-coordinate
- `children`: UICollection of UIDrawable children (speech bubbles, effects, overlays)
- `entities`: EntityCollection of entities on this grid
- `fill_color`: Background fill color of the grid. Returns a copy; modifying components requires reassignment. For animation, use 'fill_color.r', 'fill_color.g', etc.
- `fov`: FOV algorithm for this grid (mcrfpy.FOV enum). Used by entity.updateVisibility() and layer methods when fov=None.
- `fov_radius`: Default FOV radius for this grid. Used when radius not specified.
- `global_bounds`: Bounding box as (pos, size) tuple of Vectors in screen coordinates. Returns (Vector(x, y), Vector(width, height)).
- `global_position` *(read-only)*: Global screen position (read-only). Calculates absolute position by walking up the parent chain.
- `grid_h`: Grid height in cells
- `grid_pos`: Position in parent grid's tile coordinates (only when parent is Grid)
- `grid_size`: Grid dimensions (grid_w, grid_h)
- `grid_w`: Grid width in cells
- `h`: visible widget height
- `horiz_margin`: Horizontal margin override (float, 0 = use general margin). Invalid for vertically-centered alignments (TOP_CENTER, BOTTOM_CENTER, CENTER).
- `hovered` *(read-only)*: Whether mouse is currently over this element (read-only). Updated automatically by the engine during mouse movement.
- `hovered_cell`: Currently hovered cell as (x, y) tuple, or None if not hovering.
- `layers`: List of grid layers (ColorLayer, TileLayer) sorted by z_index
- `margin`: General margin from edge when aligned (float). Applied to both horizontal and vertical edges unless overridden. Invalid for CENTER alignment (raises ValueError).
- `name`: Name for finding elements
- `on_cell_click`: Callback when a grid cell is clicked. Called with (cell_pos: Vector).
- `on_cell_enter`: Callback when mouse enters a grid cell. Called with (cell_pos: Vector).
- `on_cell_exit`: Callback when mouse exits a grid cell. Called with (cell_pos: Vector).
- `on_click`: Callable executed when object is clicked. Function receives (pos: Vector, button: str, action: str).
- `on_enter`: Callback for mouse enter events. Called with (pos: Vector, button: str, action: str) when mouse enters this element's bounds.
- `on_exit`: Callback for mouse exit events. Called with (pos: Vector, button: str, action: str) when mouse leaves this element's bounds.
- `on_move`: Callback for mouse movement within bounds. Called with (pos: Vector, button: str, action: str) for each mouse movement while inside. Performance note: Called frequently during movement - keep handlers fast.
- `opacity`: Opacity level (0.0 = transparent, 1.0 = opaque). Automatically clamped to valid range [0.0, 1.0].
- `parent`: Parent drawable. Get: Returns the parent Frame/Grid if nested, or None if at scene level. Set: Assign a Frame/Grid to reparent, or None to remove from parent.
- `perspective`: Entity whose perspective to use for FOV rendering (None for omniscient view). Setting an entity automatically enables perspective mode.
- `perspective_enabled`: Whether to use perspective-based FOV rendering. When True with no valid entity, all cells appear undiscovered.
- `pos`: Position of the grid as Vector
- `position`: Position of the grid (x, y)
- `size`: Size of the grid as Vector (width, height)
- `texture`: Texture of the grid
- `vert_margin`: Vertical margin override (float, 0 = use general margin). Invalid for horizontally-centered alignments (CENTER_LEFT, CENTER_RIGHT, CENTER).
- `visible`: Whether the object is visible (bool). Invisible objects are not rendered or clickable.
- `w`: visible widget width
- `x`: top-left corner X-coordinate
- `y`: top-left corner Y-coordinate
- `z_index`: Z-order for rendering (lower values rendered first). Automatically triggers scene resort when changed.
- `zoom`: zoom factor for displaying the Grid

**Methods:**

#### `add_layer(type: str, z_index: int = -1, texture: Texture = None) -> ColorLayer | TileLayer`

Add a new layer to the grid.

**Arguments:**
- `type`: Layer type ('color' or 'tile')
- `z_index`: Render order. Negative = below entities, >= 0 = above entities. Default: -1
- `texture`: Texture for tile layers. Required for 'tile' type.

**Returns:** The created ColorLayer or TileLayer object.

#### `animate(property: str, target: Any, duration: float, easing=None, delta=False, callback=None, conflict_mode='replace') -> Animation`

Create and start an animation on this drawable's property.

Note:

**Arguments:**
- `property`: Name of the property to animate (e.g., 'x', 'fill_color', 'opacity')
- `target`: Target value - type depends on property (float, tuple for color/vector, etc.)
- `duration`: Animation duration in seconds
- `easing`: Easing function: Easing enum value, string name, or None for linear
- `delta`: If True, target is relative to current value; if False, target is absolute
- `callback`: Optional callable invoked when animation completes
- `conflict_mode`: 'replace' (default), 'queue', or 'error' if property already animating

**Returns:** Animation object for monitoring progress

**Raises:** ValueError: If property name is not valid for this drawable type This is a convenience method that creates an Animation, starts it, and adds it to the AnimationManager.

#### `apply_ranges(source: HeightMap, ranges: list) -> Grid`

Apply multiple thresholds in a single pass.

**Arguments:**
- `source`: HeightMap with values to check. Must match grid size.
- `ranges`: List of (range_tuple, properties_dict) tuples.
- `range_tuple`: (min, max) value range
- `properties_dict`: {'walkable': bool, 'transparent': bool}

**Returns:** Grid: self, for method chaining.

#### `apply_threshold(source: HeightMap, range: tuple, walkable: bool = None, transparent: bool = None) -> Grid`

Apply walkable/transparent properties where heightmap values are in range.

**Arguments:**
- `source`: HeightMap with values to check. Must match grid size.
- `range`: Tuple of (min, max) - cells with values in this range are affected.
- `walkable`: If not None, set walkable to this value for cells in range.
- `transparent`: If not None, set transparent to this value for cells in range.

**Returns:** Grid: self, for method chaining.

**Raises:** ValueError: If HeightMap size doesn't match grid size.

#### `at(...)`

#### `center_camera(pos: tuple = None) -> None`

Center the camera on a tile coordinate.

**Arguments:**
- `pos`: Optional (tile_x, tile_y) tuple. If None, centers on grid's middle tile.

#### `clear_dijkstra_maps() -> None`

Clear all cached Dijkstra maps.
Call this after modifying grid cell walkability to ensure pathfinding
uses updated walkability data.

#### `compute_fov(pos, radius: int = 0, light_walls: bool = True, algorithm: int = FOV_BASIC) -> None`

Compute field of view from a position.

**Arguments:**
- `pos`: Position as (x, y) tuple, list, or Vector
- `radius`: Maximum view distance (0 = unlimited)
- `light_walls`: Whether walls are lit when visible
- `algorithm`: FOV algorithm to use (FOV_BASIC, FOV_DIAMOND, FOV_SHADOW, FOV_PERMISSIVE_0-8)

#### `entities_in_radius(pos: tuple|Vector, radius: float) -> list[Entity]`

Query entities within radius using spatial hash (O(k) where k = nearby entities).

**Arguments:**
- `pos`: Center position as (x, y) tuple, Vector, or other 2-element sequence
- `radius`: Search radius

**Returns:** List of Entity objects within the radius.

#### `find_path(start, end, diagonal_cost: float = 1.41) -> AStarPath | None`

Compute A* path between two points.

**Arguments:**
- `start`: Starting position as Vector, Entity, or (x, y) tuple
- `end`: Target position as Vector, Entity, or (x, y) tuple
- `diagonal_cost`: Cost of diagonal movement (default: 1.41)

**Returns:** AStarPath object if path exists, None otherwise. The returned AStarPath can be iterated or walked step-by-step.

#### `get_dijkstra_map(root, diagonal_cost: float = 1.41) -> DijkstraMap`

Get or create a Dijkstra distance map for a root position.

**Arguments:**
- `root`: Root position as Vector, Entity, or (x, y) tuple
- `diagonal_cost`: Cost of diagonal movement (default: 1.41)

**Returns:** DijkstraMap object for querying distances and paths. Grid caches DijkstraMaps by root position. Multiple requests for the same root return the same cached map. Call clear_dijkstra_maps() after changing grid walkability to invalidate the cache.

#### `is_in_fov(pos) -> bool`

Check if a cell is in the field of view.

**Arguments:**
- `pos`: Position as (x, y) tuple, list, or Vector

**Returns:** True if the cell is visible, False otherwise Must call compute_fov() first to calculate visibility.

#### `layer(z_index: int) -> ColorLayer | TileLayer | None`

Get a layer by its z_index.

**Arguments:**
- `z_index`: The z_index of the layer to find.

**Returns:** The layer with the specified z_index, or None if not found.

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

#### `remove_layer(layer: ColorLayer | TileLayer) -> None`

Remove a layer from the grid.

**Arguments:**
- `layer`: The layer to remove.

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
    PRESSED: Key or button was pressed (legacy: 'start')
    RELEASED: Key or button was released (legacy: 'end')

These enum values compare equal to their legacy string equivalents
for backwards compatibility:
    InputState.PRESSED == 'start'  # True
    InputState.RELEASED == 'end'   # True


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

These enum values compare equal to their legacy string equivalents
for backwards compatibility:
    Key.ESCAPE == 'Escape'  # True
    Key.LEFT_SHIFT == 'LShift'  # True


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
- `parent`: Parent drawable. Get: Returns the parent Frame/Grid if nested, or None if at scene level. Set: Assign a Frame/Grid to reparent, or None to remove from parent.
- `pos`: Position as a Vector (midpoint of line).
- `start`: Starting point of the line as a Vector.
- `thickness`: Line thickness in pixels.
- `vert_margin`: Vertical margin override (float, 0 = use general margin). Invalid for horizontally-centered alignments (CENTER_LEFT, CENTER_RIGHT, CENTER).
- `visible`: Whether the object is visible (bool). Invisible objects are not rendered or clickable.
- `z_index`: Z-order for rendering (lower values rendered first).

**Methods:**

#### `animate(property: str, target: Any, duration: float, easing=None, delta=False, callback=None, conflict_mode='replace') -> Animation`

Create and start an animation on this drawable's property.

Note:

**Arguments:**
- `property`: Name of the property to animate (e.g., 'x', 'fill_color', 'opacity')
- `target`: Target value - type depends on property (float, tuple for color/vector, etc.)
- `duration`: Animation duration in seconds
- `easing`: Easing function: Easing enum value, string name, or None for linear
- `delta`: If True, target is relative to current value; if False, target is absolute
- `callback`: Optional callable invoked when animation completes
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

Enum representing mouse buttons.

Values:
    LEFT: Left mouse button (legacy: 'left')
    RIGHT: Right mouse button (legacy: 'right')
    MIDDLE: Middle mouse button / scroll wheel click (legacy: 'middle')
    X1: Extra mouse button 1 (legacy: 'x1')
    X2: Extra mouse button 2 (legacy: 'x2')

These enum values compare equal to their legacy string equivalents
for backwards compatibility:
    MouseButton.LEFT == 'left'  # True
    MouseButton.RIGHT == 'right'  # True


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
- `on_key`: Keyboard event handler (callable or None). Function receives (key: str, action: str) for keyboard events. Set to None to remove the handler.
- `opacity`: Scene opacity (0.0-1.0). Applied to all UI elements during rendering.
- `pos`: Scene position offset (Vector). Applied to all UI elements during rendering.
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

### Sound

Sound effect object for short audio clips

**Properties:**
- `duration` *(read-only)*: Total duration of the sound in seconds (read-only).
- `loop`: Whether the sound loops when it reaches the end.
- `playing` *(read-only)*: True if the sound is currently playing (read-only).
- `source` *(read-only)*: Filename path used to load this sound (read-only).
- `volume`: Volume level from 0 (silent) to 100 (full volume).

**Methods:**

#### `pause() -> None`

Pause the sound. Use play() to resume from the paused position.

#### `play() -> None`

Start or resume playing the sound.

#### `stop() -> None`

Stop playing and reset to the beginning.

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
- `parent`: Parent drawable. Get: Returns the parent Frame/Grid if nested, or None if at scene level. Set: Assign a Frame/Grid to reparent, or None to remove from parent.
- `pos`: Position as a Vector
- `scale`: Uniform size factor
- `scale_x`: Horizontal scale factor
- `scale_y`: Vertical scale factor
- `sprite_index`: Which sprite on the texture is shown
- `sprite_number`: Sprite index (DEPRECATED: use sprite_index instead)
- `texture`: Texture object
- `vert_margin`: Vertical margin override (float, 0 = use general margin). Invalid for horizontally-centered alignments (CENTER_LEFT, CENTER_RIGHT, CENTER).
- `visible`: Whether the object is visible (bool). Invisible objects are not rendered or clickable.
- `x`: X coordinate of top-left corner
- `y`: Y coordinate of top-left corner
- `z_index`: Z-order for rendering (lower values rendered first). Automatically triggers scene resort when changed.

**Methods:**

#### `animate(property: str, target: Any, duration: float, easing=None, delta=False, callback=None, conflict_mode='replace') -> Animation`

Create and start an animation on this drawable's property.

Note:

**Arguments:**
- `property`: Name of the property to animate (e.g., 'x', 'fill_color', 'opacity')
- `target`: Target value - type depends on property (float, tuple for color/vector, etc.)
- `duration`: Animation duration in seconds
- `easing`: Easing function: Easing enum value, string name, or None for linear
- `delta`: If True, target is relative to current value; if False, target is absolute
- `callback`: Optional callable invoked when animation completes
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

SFML Texture Object

**Properties:**
- `sheet_height` *(read-only)*: Number of sprite rows in the texture sheet (int, read-only). Calculated as texture_height / sprite_height.
- `sheet_width` *(read-only)*: Number of sprite columns in the texture sheet (int, read-only). Calculated as texture_width / sprite_width.
- `source` *(read-only)*: Source filename path (str, read-only). The path used to load this texture.
- `sprite_count` *(read-only)*: Total number of sprites in the texture sheet (int, read-only). Equals sheet_width * sheet_height.
- `sprite_height` *(read-only)*: Height of each sprite in pixels (int, read-only). Specified during texture initialization.
- `sprite_width` *(read-only)*: Width of each sprite in pixels (int, read-only). Specified during texture initialization.

**Methods:**

### TileLayer

TileLayer(z_index=-1, texture=None, grid_size=None)

A grid layer that stores sprite indices per cell for tile-based rendering.

TileLayers are typically created via Grid.add_layer('tile', ...) rather than
instantiated directly. Each cell stores an integer index into the layer's
sprite atlas texture. An index of -1 means no tile (transparent/empty).

Args:
    z_index (int): Render order relative to entities. Negative values render
        below entities (as backgrounds), positive values render above entities
        (as overlays). Default: -1 (background)
    texture (Texture): Sprite atlas containing tile images. The texture's
        sprite_size determines individual tile dimensions. Required for
        rendering; can be set after creation. Default: None
    grid_size (tuple): Dimensions as (width, height). If None, the layer will
        inherit the parent Grid's dimensions when attached. Default: None

Attributes:
    z_index (int): Layer z-order relative to entities (read/write)
    visible (bool): Whether layer is rendered (read/write)
    texture (Texture): Sprite atlas for tile images (read/write)
    grid_size (tuple): Layer dimensions as (width, height) (read-only)

Methods:
    at(x, y) -> int: Get the tile index at cell position (x, y)
    set(x, y, index): Set the tile index at cell position (x, y)
    fill(index): Fill the entire layer with a single tile index
    fill_rect(x, y, w, h, index): Fill a rectangular region with a tile index

Tile Index Values:
    -1: No tile (transparent/empty cell)
    0+: Index into the texture's sprite atlas (row-major order)

Example:
    grid = mcrfpy.Grid(grid_size=(20, 15), texture=my_texture,
                       pos=(50, 50), size=(640, 480))
    layer = grid.add_layer('tile', z_index=1, texture=overlay_texture)
    layer.fill(-1)  # Clear layer (all transparent)
    layer.set(5, 5, 42)  # Place tile index 42 at position (5, 5)
    layer.fill_rect(0, 0, 20, 1, 10)  # Top row filled with tile 10

**Properties:**
- `grid_size`: Layer dimensions as (width, height) tuple.
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

### Vector

SFML Vector Object

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

