# McRogueFace API Reference

*Generated on 2025-12-29 14:24:58*

*This documentation was dynamically generated from the compiled module.*

## Table of Contents

- [Functions](#functions)
- [Classes](#classes)
  - [Animation](#animation)
  - [Arc](#arc)
  - [Caption](#caption)
  - [Circle](#circle)
  - [Color](#color)
  - [ColorLayer](#colorlayer)
  - [Drawable](#drawable)
  - [Entity](#entity)
  - [EntityCollection](#entitycollection)
  - [FOV](#fov)
  - [Font](#font)
  - [Frame](#frame)
  - [Grid](#grid)
  - [GridPoint](#gridpoint)
  - [GridPointState](#gridpointstate)
  - [Line](#line)
  - [Scene](#scene)
  - [Sprite](#sprite)
  - [Texture](#texture)
  - [TileLayer](#tilelayer)
  - [Timer](#timer)
  - [UICollection](#uicollection)
  - [UICollectionIter](#uicollectioniter)
  - [UIEntityCollectionIter](#uientitycollectioniter)
  - [Vector](#vector)
  - [Window](#window)
- [Constants](#constants)

## Functions

### `createScene(name: str) -> None`

Create a new empty scene.

Note:

**Arguments:**
- `name`: Unique name for the new scene

**Returns:** None

**Raises:** ValueError: If a scene with this name already exists The scene is created but not made active. Use setScene() to switch to it.

### `createSoundBuffer(filename: str) -> int`

Load a sound effect from a file and return its buffer ID.

**Arguments:**
- `filename`: Path to the sound file (WAV, OGG, FLAC)

**Returns:** int: Buffer ID for use with playSound()

**Raises:** RuntimeError: If the file cannot be loaded

### `currentScene() -> str`

Get the name of the currently active scene.

**Returns:** str: Name of the current scene

### `delTimer(name: str) -> None`

Stop and remove a timer.

Note:

**Arguments:**
- `name`: Timer identifier to remove

**Returns:** None No error is raised if the timer doesn't exist.

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

### `getMusicVolume() -> int`

Get the current music volume level.

**Returns:** int: Current volume (0-100)

### `getSoundVolume() -> int`

Get the current sound effects volume level.

**Returns:** int: Current volume (0-100)

### `keypressScene(handler: callable) -> None`

Set the keyboard event handler for the current scene.

Note:

**Arguments:**
- `handler`: Callable that receives (key_name: str, is_pressed: bool)

**Returns:** None

### `loadMusic(filename: str) -> None`

Load and immediately play background music from a file.

Note:

**Arguments:**
- `filename`: Path to the music file (WAV, OGG, FLAC)

**Returns:** None Only one music track can play at a time. Loading new music stops the current track.

### `log_benchmark(message: str) -> None`

Add a log message to the current benchmark frame.

Note:

**Arguments:**
- `message`: Text to associate with the current frame

**Returns:** None

**Raises:** RuntimeError: If no benchmark is currently running Messages appear in the 'logs' array of each frame in the output JSON.

### `playSound(buffer_id: int) -> None`

Play a sound effect using a previously loaded buffer.

**Arguments:**
- `buffer_id`: Sound buffer ID returned by createSoundBuffer()

**Returns:** None

**Raises:** RuntimeError: If the buffer ID is invalid

### `sceneUI(scene: str = None) -> list`

Get all UI elements for a scene.

**Arguments:**
- `scene`: Scene name. If None, uses current scene

**Returns:** list: All UI elements (Frame, Caption, Sprite, Grid) in the scene

**Raises:** KeyError: If the specified scene doesn't exist

### `setDevConsole(enabled: bool) -> None`

Enable or disable the developer console overlay.

Note:

**Arguments:**
- `enabled`: True to enable the console (default), False to disable

**Returns:** None When disabled, the grave/tilde key will not open the console. Use this to ship games without debug features.

### `setMusicVolume(volume: int) -> None`

Set the global music volume.

**Arguments:**
- `volume`: Volume level from 0 (silent) to 100 (full volume)

**Returns:** None

### `setScale(multiplier: float) -> None`

Scale the game window size.

Note:

**Arguments:**
- `multiplier`: Scale factor (e.g., 2.0 for double size)

**Returns:** None The internal resolution remains 1024x768, but the window is scaled. This is deprecated - use Window.resolution instead.

### `setScene(scene: str, transition: str = None, duration: float = 0.0) -> None`

Switch to a different scene with optional transition effect.

**Arguments:**
- `scene`: Name of the scene to switch to
- `transition`: Transition type ('fade', 'slide_left', 'slide_right', 'slide_up', 'slide_down')
- `duration`: Transition duration in seconds (default: 0.0 for instant)

**Returns:** None

**Raises:** KeyError: If the scene doesn't exist ValueError: If the transition type is invalid

### `setSoundVolume(volume: int) -> None`

Set the global sound effects volume.

**Arguments:**
- `volume`: Volume level from 0 (silent) to 100 (full volume)

**Returns:** None

### `setTimer(name: str, handler: callable, interval: int) -> None`

Create or update a recurring timer.

Note:

**Arguments:**
- `name`: Unique identifier for the timer
- `handler`: Function called with (runtime: float) parameter
- `interval`: Time between calls in milliseconds

**Returns:** None If a timer with this name exists, it will be replaced. The handler receives the total runtime in seconds as its argument.

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

### Animation

Animation object for animating UI properties

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


**Properties:**
- `bounds`: Bounding rectangle (x, y, width, height) in local coordinates.
- `center`: Center position of the arc
- `color`: Arc color
- `end_angle`: Ending angle in degrees
- `global_bounds`: Bounding rectangle (x, y, width, height) in screen coordinates.
- `global_position` *(read-only)*: Global screen position (read-only). Calculates absolute position by walking up the parent chain.
- `hovered` *(read-only)*: Whether mouse is currently over this element (read-only). Updated automatically by the engine during mouse movement.
- `name`: Name for finding this element.
- `on_click`: Callable executed when arc is clicked.
- `on_enter`: Callback for mouse enter events. Called with (x, y, button, action) when mouse enters this element's bounds.
- `on_exit`: Callback for mouse exit events. Called with (x, y, button, action) when mouse leaves this element's bounds.
- `on_move`: Callback for mouse movement within bounds. Called with (x, y, button, action) for each mouse movement while inside. Performance note: Called frequently during movement - keep handlers fast.
- `opacity`: Opacity level (0.0 = transparent, 1.0 = opaque). Automatically clamped to valid range [0.0, 1.0].
- `parent`: Parent drawable. Get: Returns the parent Frame/Grid if nested, or None if at scene level. Set: Assign a Frame/Grid to reparent, or None to remove from parent.
- `pos`: Position as a Vector (same as center).
- `radius`: Arc radius in pixels
- `start_angle`: Starting angle in degrees
- `thickness`: Line thickness
- `visible`: Whether the object is visible (bool). Invisible objects are not rendered or clickable.
- `z_index`: Z-order for rendering (lower values rendered first).

**Methods:**

#### `get_bounds() -> tuple`

Get the bounding rectangle of this drawable element.

Note:

**Returns:** tuple: (x, y, width, height) representing the element's bounds The bounds are in screen coordinates and account for current position and size.

#### `move(dx: float, dy: float) -> None`

Move the element by a relative offset.

Note:

**Arguments:**
- `dx`: Horizontal offset in pixels
- `dy`: Vertical offset in pixels

#### `resize(width: float, height: float) -> None`

Resize the element to new dimensions.

Note:

**Arguments:**
- `width`: New width in pixels
- `height`: New height in pixels

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

**Properties:**
- `bounds`: Bounding rectangle (x, y, width, height) in local coordinates.
- `fill_color`: Fill color of the text
- `font_size`: Font size (integer) in points
- `global_bounds`: Bounding rectangle (x, y, width, height) in screen coordinates.
- `global_position` *(read-only)*: Global screen position (read-only). Calculates absolute position by walking up the parent chain.
- `hovered` *(read-only)*: Whether mouse is currently over this element (read-only). Updated automatically by the engine during mouse movement.
- `name`: Name for finding elements
- `on_click`: Callable executed when object is clicked. Function receives (x, y) coordinates of click.
- `on_enter`: Callback for mouse enter events. Called with (x, y, button, action) when mouse enters this element's bounds.
- `on_exit`: Callback for mouse exit events. Called with (x, y, button, action) when mouse leaves this element's bounds.
- `on_move`: Callback for mouse movement within bounds. Called with (x, y, button, action) for each mouse movement while inside. Performance note: Called frequently during movement - keep handlers fast.
- `opacity`: Opacity level (0.0 = transparent, 1.0 = opaque). Automatically clamped to valid range [0.0, 1.0].
- `outline`: Thickness of the border
- `outline_color`: Outline color of the text
- `parent`: Parent drawable. Get: Returns the parent Frame/Grid if nested, or None if at scene level. Set: Assign a Frame/Grid to reparent, or None to remove from parent.
- `pos`: (x, y) vector
- `text`: The text displayed
- `visible`: Whether the object is visible (bool). Invisible objects are not rendered or clickable.
- `x`: X coordinate of top-left corner
- `y`: Y coordinate of top-left corner
- `z_index`: Z-order for rendering (lower values rendered first). Automatically triggers scene resort when changed.

**Methods:**

#### `get_bounds() -> tuple`

Get the bounding rectangle of this drawable element.

Note:

**Returns:** tuple: (x, y, width, height) representing the element's bounds The bounds are in screen coordinates and account for current position and size.

#### `move(dx: float, dy: float) -> None`

Move the element by a relative offset.

Note:

**Arguments:**
- `dx`: Horizontal offset in pixels
- `dy`: Vertical offset in pixels

#### `resize(width: float, height: float) -> None`

Resize the element to new dimensions.

Note:

**Arguments:**
- `width`: New width in pixels
- `height`: New height in pixels

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


**Properties:**
- `bounds`: Bounding rectangle (x, y, width, height) in local coordinates.
- `center`: Center position of the circle
- `fill_color`: Fill color of the circle
- `global_bounds`: Bounding rectangle (x, y, width, height) in screen coordinates.
- `global_position` *(read-only)*: Global screen position (read-only). Calculates absolute position by walking up the parent chain.
- `hovered` *(read-only)*: Whether mouse is currently over this element (read-only). Updated automatically by the engine during mouse movement.
- `name`: Name for finding this element.
- `on_click`: Callable executed when circle is clicked.
- `on_enter`: Callback for mouse enter events. Called with (x, y, button, action) when mouse enters this element's bounds.
- `on_exit`: Callback for mouse exit events. Called with (x, y, button, action) when mouse leaves this element's bounds.
- `on_move`: Callback for mouse movement within bounds. Called with (x, y, button, action) for each mouse movement while inside. Performance note: Called frequently during movement - keep handlers fast.
- `opacity`: Opacity level (0.0 = transparent, 1.0 = opaque). Automatically clamped to valid range [0.0, 1.0].
- `outline`: Outline thickness (0 for no outline)
- `outline_color`: Outline color of the circle
- `parent`: Parent drawable. Get: Returns the parent Frame/Grid if nested, or None if at scene level. Set: Assign a Frame/Grid to reparent, or None to remove from parent.
- `pos`: Position as a Vector (same as center).
- `radius`: Circle radius in pixels
- `visible`: Whether the object is visible (bool). Invisible objects are not rendered or clickable.
- `z_index`: Z-order for rendering (lower values rendered first).

**Methods:**

#### `get_bounds() -> tuple`

Get the bounding rectangle of this drawable element.

Note:

**Returns:** tuple: (x, y, width, height) representing the element's bounds The bounds are in screen coordinates and account for current position and size.

#### `move(dx: float, dy: float) -> None`

Move the element by a relative offset.

Note:

**Arguments:**
- `dx`: Horizontal offset in pixels
- `dy`: Vertical offset in pixels

#### `resize(width: float, height: float) -> None`

Resize the element to new dimensions.

Note:

**Arguments:**
- `width`: New width in pixels
- `height`: New height in pixels

### Color

SFML Color Object

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

A grid layer that stores RGBA colors per cell.

Args:
    z_index (int): Render order. Negative = below entities. Default: -1
    grid_size (tuple): Dimensions as (width, height). Default: parent grid size

Attributes:
    z_index (int): Layer z-order relative to entities
    visible (bool): Whether layer is rendered
    grid_size (tuple): Layer dimensions (read-only)

Methods:
    at(x, y): Get color at cell position
    set(x, y, color): Set color at cell position
    fill(color): Fill entire layer with color

**Properties:**
- `grid_size`: Layer dimensions as (width, height) tuple.
- `visible`: Whether the layer is rendered.
- `z_index`: Layer z-order. Negative values render below entities.

**Methods:**

#### `apply_perspective(entity, visible=None, discovered=None, unknown=None)`

Bind this layer to an entity for automatic FOV updates.

#### `at(x, y) -> Color`

Get the color at cell position (x, y).

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

#### `set(x, y, color)`

Set the color at cell position (x, y).

#### `update_perspective()`

Redraw FOV based on the bound entity's current position.
Call this after the entity moves to update the visibility layer.

### Drawable

Base class for all drawable UI elements

**Properties:**
- `on_click`: Callable executed when object is clicked. Function receives (x, y) coordinates of click.
- `opacity`: Opacity level (0.0 = transparent, 1.0 = opaque). Automatically clamped to valid range [0.0, 1.0].
- `visible`: Whether the object is visible (bool). Invisible objects are not rendered or clickable.
- `z_index`: Z-order for rendering (lower values rendered first). Automatically triggers scene resort when changed.

**Methods:**

#### `get_bounds() -> tuple`

Get the bounding rectangle of this drawable element.

Note:

**Returns:** tuple: (x, y, width, height) representing the element's bounds The bounds are in screen coordinates and account for current position and size.

#### `move(dx: float, dy: float) -> None`

Move the element by a relative offset.

Note:

**Arguments:**
- `dx`: Horizontal offset in pixels
- `dy`: Vertical offset in pixels

#### `resize(width: float, height: float) -> None`

Resize the element to new dimensions.

Note:

**Arguments:**
- `width`: New width in pixels
- `height`: New height in pixels

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
    x (float): X grid position override. Default: 0
    y (float): Y grid position override. Default: 0

Attributes:
    pos (tuple): Grid position as (x, y) tuple
    x, y (float): Grid position coordinates
    draw_pos (tuple): Pixel position for rendering
    gridstate (GridPointState): Visibility state for grid points
    sprite_index (int): Current sprite index
    visible (bool): Visibility state
    opacity (float): Opacity value
    name (str): Element name

**Properties:**
- `draw_pos`: Entity position (graphically)
- `grid`: Grid this entity belongs to. Get: Returns the Grid or None. Set: Assign a Grid to move entity, or None to remove from grid.
- `gridstate`: Grid point states for the entity
- `name`: Name for finding elements
- `opacity`: Opacity (0.0 = transparent, 1.0 = opaque)
- `pos`: Entity position (integer grid coordinates)
- `sprite_index`: Sprite index on the texture on the display
- `sprite_number`: Sprite index (DEPRECATED: use sprite_index instead)
- `visible`: Visibility flag
- `x`: Entity x position
- `y`: Entity y position

**Methods:**

#### `at(...)`

#### `die(...)`

Remove this entity from its grid

#### `get_bounds() -> tuple`

Get the bounding rectangle of this drawable element.

Note:

**Returns:** tuple: (x, y, width, height) representing the element's bounds The bounds are in screen coordinates and account for current position and size.

#### `index(...)`

Return the index of this entity in its grid's entity collection

#### `move(dx: float, dy: float) -> None`

Move the element by a relative offset.

Note:

**Arguments:**
- `dx`: Horizontal offset in pixels
- `dy`: Vertical offset in pixels

#### `path_to(x: int, y: int) -> bool`

Find and follow path to target position using A* pathfinding.

**Arguments:**
- `x`: Target X coordinate
- `y`: Target Y coordinate

**Returns:** True if a path was found and the entity started moving, False otherwise The entity will automatically move along the path over multiple frames. Call this again to change the target or repath.

#### `resize(width: float, height: float) -> None`

Resize the element to new dimensions.

Note:

**Arguments:**
- `width`: New width in pixels
- `height`: New height in pixels

#### `update_visibility() -> None`

Update entity's visibility state based on current FOV.
Recomputes which cells are visible from the entity's position and updates
the entity's gridstate to track explored areas. This is called automatically
when the entity moves if it has a grid with perspective set.

#### `visible_entities(fov=None, radius=None) -> list[Entity]`

Get list of other entities visible from this entity's position.

**Returns:** List of Entity objects that are within field of view. Computes FOV from this entity's position and returns all other entities whose positions fall within the visible area.

### EntityCollection

Iterable, indexable collection of Entities

**Methods:**

#### `append(entity)`

Add an entity to the end of the collection.

#### `count(entity) -> int`

Count occurrences of entity in the collection.

#### `extend(iterable)`

Add all entities from an iterable to the collection.

#### `find(name) -> entity or list`

Find entities by name.

**Returns:** Single entity if exact match, list if wildcard, None if not found.

#### `index(entity) -> int`

Return index of first occurrence of entity. Raises ValueError if not found.

#### `insert(index, entity)`

Insert entity at index. Like list.insert(), indices past the end append.

#### `pop([index]) -> entity`

Remove and return entity at index (default: last entity).

#### `remove(entity)`

Remove first occurrence of entity. Raises ValueError if not found.

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

**Properties:**
- `bounds`: Bounding rectangle (x, y, width, height) in local coordinates.
- `cache_subtree`: #144: Cache subtree rendering to texture for performance
- `children`: UICollection of objects on top of this one
- `clip_children`: Whether to clip children to frame bounds
- `fill_color`: Fill color of the rectangle
- `global_bounds`: Bounding rectangle (x, y, width, height) in screen coordinates.
- `global_position` *(read-only)*: Global screen position (read-only). Calculates absolute position by walking up the parent chain.
- `h`: height of the rectangle
- `hovered` *(read-only)*: Whether mouse is currently over this element (read-only). Updated automatically by the engine during mouse movement.
- `name`: Name for finding elements
- `on_click`: Callable executed when object is clicked. Function receives (x, y) coordinates of click.
- `on_enter`: Callback for mouse enter events. Called with (x, y, button, action) when mouse enters this element's bounds.
- `on_exit`: Callback for mouse exit events. Called with (x, y, button, action) when mouse leaves this element's bounds.
- `on_move`: Callback for mouse movement within bounds. Called with (x, y, button, action) for each mouse movement while inside. Performance note: Called frequently during movement - keep handlers fast.
- `opacity`: Opacity level (0.0 = transparent, 1.0 = opaque). Automatically clamped to valid range [0.0, 1.0].
- `outline`: Thickness of the border
- `outline_color`: Outline color of the rectangle
- `parent`: Parent drawable. Get: Returns the parent Frame/Grid if nested, or None if at scene level. Set: Assign a Frame/Grid to reparent, or None to remove from parent.
- `pos`: Position as a Vector
- `visible`: Whether the object is visible (bool). Invisible objects are not rendered or clickable.
- `w`: width of the rectangle
- `x`: X coordinate of top-left corner
- `y`: Y coordinate of top-left corner
- `z_index`: Z-order for rendering (lower values rendered first). Automatically triggers scene resort when changed.

**Methods:**

#### `get_bounds() -> tuple`

Get the bounding rectangle of this drawable element.

Note:

**Returns:** tuple: (x, y, width, height) representing the element's bounds The bounds are in screen coordinates and account for current position and size.

#### `move(dx: float, dy: float) -> None`

Move the element by a relative offset.

Note:

**Arguments:**
- `dx`: Horizontal offset in pixels
- `dy`: Vertical offset in pixels

#### `resize(width: float, height: float) -> None`

Resize the element to new dimensions.

Note:

**Arguments:**
- `width`: New width in pixels
- `height`: New height in pixels

### Grid

*Inherits from: Drawable*

Grid(pos=None, size=None, grid_size=None, texture=None, **kwargs)

A grid-based UI element for tile-based rendering and entity management.

Args:
    pos (tuple, optional): Position as (x, y) tuple. Default: (0, 0)
    size (tuple, optional): Size as (width, height) tuple. Default: auto-calculated from grid_size
    grid_size (tuple, optional): Grid dimensions as (grid_x, grid_y) tuple. Default: (2, 2)
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
    grid_x (int): Grid width override. Default: 2
    grid_y (int): Grid height override. Default: 2

Attributes:
    x, y (float): Position in pixels
    w, h (float): Size in pixels
    pos (Vector): Position as a Vector object
    size (tuple): Size as (width, height) tuple
    center (tuple): Center point as (x, y) tuple
    center_x, center_y (float): Center point coordinates
    zoom (float): Zoom level for rendering
    grid_size (tuple): Grid dimensions (width, height) in tiles
    grid_x, grid_y (int): Grid dimensions
    texture (Texture): Tile texture atlas
    fill_color (Color): Background color
    entities (EntityCollection): Collection of entities in the grid
    perspective (int): Entity perspective index
    click (callable): Click event handler
    visible (bool): Visibility state
    opacity (float): Opacity value
    z_index (int): Rendering order
    name (str): Element name

**Properties:**
- `bounds`: Bounding rectangle (x, y, width, height) in local coordinates.
- `center`: Grid coordinate at the center of the Grid's view (pan)
- `center_x`: center of the view X-coordinate
- `center_y`: center of the view Y-coordinate
- `children`: UICollection of UIDrawable children (speech bubbles, effects, overlays)
- `entities`: EntityCollection of entities on this grid
- `fill_color`: Background fill color of the grid
- `fov`: FOV algorithm for this grid (mcrfpy.FOV enum). Used by entity.updateVisibility() and layer methods when fov=None.
- `fov_radius`: Default FOV radius for this grid. Used when radius not specified.
- `global_bounds`: Bounding rectangle (x, y, width, height) in screen coordinates.
- `global_position` *(read-only)*: Global screen position (read-only). Calculates absolute position by walking up the parent chain.
- `grid_size`: Grid dimensions (grid_x, grid_y)
- `grid_x`: Grid x dimension
- `grid_y`: Grid y dimension
- `h`: visible widget height
- `hovered` *(read-only)*: Whether mouse is currently over this element (read-only). Updated automatically by the engine during mouse movement.
- `hovered_cell`: Currently hovered cell as (x, y) tuple, or None if not hovering.
- `layers`: List of grid layers (ColorLayer, TileLayer) sorted by z_index
- `name`: Name for finding elements
- `on_cell_click`: Callback when a grid cell is clicked. Called with (cell_x, cell_y).
- `on_cell_enter`: Callback when mouse enters a grid cell. Called with (cell_x, cell_y).
- `on_cell_exit`: Callback when mouse exits a grid cell. Called with (cell_x, cell_y).
- `on_click`: Callable executed when object is clicked. Function receives (x, y) coordinates of click.
- `on_enter`: Callback for mouse enter events. Called with (x, y, button, action) when mouse enters this element's bounds.
- `on_exit`: Callback for mouse exit events. Called with (x, y, button, action) when mouse leaves this element's bounds.
- `on_move`: Callback for mouse movement within bounds. Called with (x, y, button, action) for each mouse movement while inside. Performance note: Called frequently during movement - keep handlers fast.
- `opacity`: Opacity level (0.0 = transparent, 1.0 = opaque). Automatically clamped to valid range [0.0, 1.0].
- `parent`: Parent drawable. Get: Returns the parent Frame/Grid if nested, or None if at scene level. Set: Assign a Frame/Grid to reparent, or None to remove from parent.
- `perspective`: Entity whose perspective to use for FOV rendering (None for omniscient view). Setting an entity automatically enables perspective mode.
- `perspective_enabled`: Whether to use perspective-based FOV rendering. When True with no valid entity, all cells appear undiscovered.
- `pos`: Position of the grid as Vector
- `position`: Position of the grid (x, y)
- `size`: Size of the grid (width, height)
- `texture`: Texture of the grid
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

#### `at(...)`

#### `compute_astar_path(x1: int, y1: int, x2: int, y2: int, diagonal_cost: float = 1.41) -> List[Tuple[int, int]]`

Compute A* path between two points.

**Arguments:**
- `x1`: Starting X coordinate
- `y1`: Starting Y coordinate
- `x2`: Target X coordinate
- `y2`: Target Y coordinate
- `diagonal_cost`: Cost of diagonal movement (default: 1.41)

**Returns:** List of (x, y) tuples representing the path, empty list if no path exists Alternative A* implementation. Prefer find_path() for consistency.

#### `compute_dijkstra(root_x: int, root_y: int, diagonal_cost: float = 1.41) -> None`

Compute Dijkstra map from root position.

**Arguments:**
- `root_x`: X coordinate of the root/target
- `root_y`: Y coordinate of the root/target
- `diagonal_cost`: Cost of diagonal movement (default: 1.41)

#### `compute_fov(x: int, y: int, radius: int = 0, light_walls: bool = True, algorithm: int = FOV_BASIC) -> None`

Compute field of view from a position.

**Arguments:**
- `x`: X coordinate of the viewer
- `y`: Y coordinate of the viewer
- `radius`: Maximum view distance (0 = unlimited)
- `light_walls`: Whether walls are lit when visible
- `algorithm`: FOV algorithm to use (FOV_BASIC, FOV_DIAMOND, FOV_SHADOW, FOV_PERMISSIVE_0-8)

#### `entities_in_radius(x: float, y: float, radius: float) -> list[Entity]`

Query entities within radius using spatial hash (O(k) where k = nearby entities).

**Arguments:**
- `x`: Center X coordinate
- `y`: Center Y coordinate
- `radius`: Search radius

**Returns:** List of Entity objects within the radius.

#### `find_path(x1: int, y1: int, x2: int, y2: int, diagonal_cost: float = 1.41) -> List[Tuple[int, int]]`

Find A* path between two points.

**Arguments:**
- `x1`: Starting X coordinate
- `y1`: Starting Y coordinate
- `x2`: Target X coordinate
- `y2`: Target Y coordinate
- `diagonal_cost`: Cost of diagonal movement (default: 1.41)

**Returns:** List of (x, y) tuples representing the path, empty list if no path exists Uses A* algorithm with walkability from grid cells.

#### `get_bounds() -> tuple`

Get the bounding rectangle of this drawable element.

Note:

**Returns:** tuple: (x, y, width, height) representing the element's bounds The bounds are in screen coordinates and account for current position and size.

#### `get_dijkstra_distance(x: int, y: int) -> Optional[float]`

Get distance from Dijkstra root to position.

**Arguments:**
- `x`: X coordinate to query
- `y`: Y coordinate to query

**Returns:** Distance as float, or None if position is unreachable or invalid Must call compute_dijkstra() first.

#### `get_dijkstra_path(x: int, y: int) -> List[Tuple[int, int]]`

Get path from position to Dijkstra root.

**Arguments:**
- `x`: Starting X coordinate
- `y`: Starting Y coordinate

**Returns:** List of (x, y) tuples representing path to root, empty if unreachable Must call compute_dijkstra() first. Path includes start but not root position.

#### `is_in_fov(x: int, y: int) -> bool`

Check if a cell is in the field of view.

**Arguments:**
- `x`: X coordinate to check
- `y`: Y coordinate to check

**Returns:** True if the cell is visible, False otherwise Must call compute_fov() first to calculate visibility.

#### `layer(z_index: int) -> ColorLayer | TileLayer | None`

Get a layer by its z_index.

**Arguments:**
- `z_index`: The z_index of the layer to find.

**Returns:** The layer with the specified z_index, or None if not found.

#### `move(dx: float, dy: float) -> None`

Move the element by a relative offset.

Note:

**Arguments:**
- `dx`: Horizontal offset in pixels
- `dy`: Vertical offset in pixels

#### `remove_layer(layer: ColorLayer | TileLayer) -> None`

Remove a layer from the grid.

**Arguments:**
- `layer`: The layer to remove.

#### `resize(width: float, height: float) -> None`

Resize the element to new dimensions.

Note:

**Arguments:**
- `width`: New width in pixels
- `height`: New height in pixels

### GridPoint

UIGridPoint object

**Properties:**
- `entities` *(read-only)*: List of entities at this grid cell (read-only)
- `transparent`: Is the GridPoint transparent
- `walkable`: Is the GridPoint walkable

**Methods:**

### GridPointState

UIGridPointState object

**Properties:**
- `discovered`: Has the GridPointState been discovered
- `point`: GridPoint at this position (None if not discovered)
- `visible`: Is the GridPointState visible

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

Attributes:
    start (Vector): Starting point
    end (Vector): Ending point
    thickness (float): Line thickness
    color (Color): Line color
    visible (bool): Visibility state
    opacity (float): Opacity value
    z_index (int): Rendering order
    name (str): Element name


**Properties:**
- `bounds`: Bounding rectangle (x, y, width, height) in local coordinates.
- `color`: Line color as a Color object.
- `end`: Ending point of the line as a Vector.
- `global_bounds`: Bounding rectangle (x, y, width, height) in screen coordinates.
- `global_position` *(read-only)*: Global screen position (read-only). Calculates absolute position by walking up the parent chain.
- `hovered` *(read-only)*: Whether mouse is currently over this element (read-only). Updated automatically by the engine during mouse movement.
- `name`: Name for finding this element.
- `on_click`: Callable executed when line is clicked.
- `on_enter`: Callback for mouse enter events. Called with (x, y, button, action) when mouse enters this element's bounds.
- `on_exit`: Callback for mouse exit events. Called with (x, y, button, action) when mouse leaves this element's bounds.
- `on_move`: Callback for mouse movement within bounds. Called with (x, y, button, action) for each mouse movement while inside. Performance note: Called frequently during movement - keep handlers fast.
- `opacity`: Opacity level (0.0 = transparent, 1.0 = opaque). Automatically clamped to valid range [0.0, 1.0].
- `parent`: Parent drawable. Get: Returns the parent Frame/Grid if nested, or None if at scene level. Set: Assign a Frame/Grid to reparent, or None to remove from parent.
- `pos`: Position as a Vector (midpoint of line).
- `start`: Starting point of the line as a Vector.
- `thickness`: Line thickness in pixels.
- `visible`: Whether the object is visible (bool). Invisible objects are not rendered or clickable.
- `z_index`: Z-order for rendering (lower values rendered first).

**Methods:**

#### `get_bounds() -> tuple`

Get the bounding rectangle of this drawable element.

Note:

**Returns:** tuple: (x, y, width, height) representing the element's bounds The bounds are in screen coordinates and account for current position and size.

#### `move(dx: float, dy: float) -> None`

Move the element by a relative offset.

Note:

**Arguments:**
- `dx`: Horizontal offset in pixels
- `dy`: Vertical offset in pixels

#### `resize(width: float, height: float) -> None`

Resize the element to new dimensions.

Note:

**Arguments:**
- `width`: New width in pixels
- `height`: New height in pixels

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
    on_keypress(key: str, action: str): Called for keyboard events. Alternative to on_key property.
    update(dt: float): Called every frame with delta time in seconds.
    on_resize(width: int, height: int): Called when window is resized.

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

#### `activate() -> None`

Make this the active scene.

Note:

**Returns:** None Deactivates the current scene and activates this one. Scene transitions and lifecycle callbacks are triggered.

#### `register_keyboard(callback: callable) -> None`

Register a keyboard event handler function.

Note:

**Arguments:**
- `callback`: Function that receives (key: str, pressed: bool) when keyboard events occur

**Returns:** None Alternative to setting on_key property. Handler is called for both key press and release events.

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

**Properties:**
- `bounds`: Bounding rectangle (x, y, width, height) in local coordinates.
- `global_bounds`: Bounding rectangle (x, y, width, height) in screen coordinates.
- `global_position` *(read-only)*: Global screen position (read-only). Calculates absolute position by walking up the parent chain.
- `hovered` *(read-only)*: Whether mouse is currently over this element (read-only). Updated automatically by the engine during mouse movement.
- `name`: Name for finding elements
- `on_click`: Callable executed when object is clicked. Function receives (x, y) coordinates of click.
- `on_enter`: Callback for mouse enter events. Called with (x, y, button, action) when mouse enters this element's bounds.
- `on_exit`: Callback for mouse exit events. Called with (x, y, button, action) when mouse leaves this element's bounds.
- `on_move`: Callback for mouse movement within bounds. Called with (x, y, button, action) for each mouse movement while inside. Performance note: Called frequently during movement - keep handlers fast.
- `opacity`: Opacity level (0.0 = transparent, 1.0 = opaque). Automatically clamped to valid range [0.0, 1.0].
- `parent`: Parent drawable. Get: Returns the parent Frame/Grid if nested, or None if at scene level. Set: Assign a Frame/Grid to reparent, or None to remove from parent.
- `pos`: Position as a Vector
- `scale`: Uniform size factor
- `scale_x`: Horizontal scale factor
- `scale_y`: Vertical scale factor
- `sprite_index`: Which sprite on the texture is shown
- `sprite_number`: Sprite index (DEPRECATED: use sprite_index instead)
- `texture`: Texture object
- `visible`: Whether the object is visible (bool). Invisible objects are not rendered or clickable.
- `x`: X coordinate of top-left corner
- `y`: Y coordinate of top-left corner
- `z_index`: Z-order for rendering (lower values rendered first). Automatically triggers scene resort when changed.

**Methods:**

#### `get_bounds() -> tuple`

Get the bounding rectangle of this drawable element.

Note:

**Returns:** tuple: (x, y, width, height) representing the element's bounds The bounds are in screen coordinates and account for current position and size.

#### `move(dx: float, dy: float) -> None`

Move the element by a relative offset.

Note:

**Arguments:**
- `dx`: Horizontal offset in pixels
- `dy`: Vertical offset in pixels

#### `resize(width: float, height: float) -> None`

Resize the element to new dimensions.

Note:

**Arguments:**
- `width`: New width in pixels
- `height`: New height in pixels

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

A grid layer that stores sprite indices per cell.

Args:
    z_index (int): Render order. Negative = below entities. Default: -1
    texture (Texture): Sprite atlas for tile rendering. Default: None
    grid_size (tuple): Dimensions as (width, height). Default: parent grid size

Attributes:
    z_index (int): Layer z-order relative to entities
    visible (bool): Whether layer is rendered
    texture (Texture): Tile sprite atlas
    grid_size (tuple): Layer dimensions (read-only)

Methods:
    at(x, y): Get tile index at cell position
    set(x, y, index): Set tile index at cell position
    fill(index): Fill entire layer with tile index

**Properties:**
- `grid_size`: Layer dimensions as (width, height) tuple.
- `texture`: Texture atlas for tile sprites.
- `visible`: Whether the layer is rendered.
- `z_index`: Layer z-order. Negative values render below entities.

**Methods:**

#### `at(x, y) -> int`

Get the tile index at cell position (x, y). Returns -1 if no tile.

#### `fill(index)`

Fill the entire layer with the specified tile index.

#### `fill_rect(pos, size, index)`

Fill a rectangular region with a tile index.

#### `set(x, y, index)`

Set the tile index at cell position (x, y). Use -1 for no tile.

### Timer

Timer(name, callback, interval, once=False)

Create a timer that calls a function at regular intervals.

Args:
    name (str): Unique identifier for the timer
    callback (callable): Function to call - receives (timer, runtime) args
    interval (int): Time between calls in milliseconds
    once (bool): If True, timer stops after first call. Default: False

Attributes:
    interval (int): Time between calls in milliseconds
    remaining (int): Time until next call in milliseconds (read-only)
    paused (bool): Whether timer is paused (read-only)
    active (bool): Whether timer is active and not paused (read-only)
    callback (callable): The callback function
    once (bool): Whether timer stops after firing once

Methods:
    pause(): Pause the timer, preserving time remaining
    resume(): Resume a paused timer
    cancel(): Stop and remove the timer
    restart(): Reset timer to start from beginning

Example:
    def on_timer(timer, runtime):
        print(f'Timer {timer} fired at {runtime}ms')
        if runtime > 5000:
            timer.cancel()
    
    timer = mcrfpy.Timer('my_timer', on_timer, 1000)
    timer.pause()  # Pause timer
    timer.resume() # Resume timer
    timer.once = True  # Make it one-shot

**Properties:**
- `active` *(read-only)*: Whether the timer is active and not paused (bool, read-only). False if cancelled or paused.
- `callback`: The callback function to be called when timer fires (callable). Can be changed while timer is running.
- `interval`: Timer interval in milliseconds (int). Must be positive. Can be changed while timer is running.
- `name` *(read-only)*: Timer name (str, read-only). Unique identifier for this timer.
- `once`: Whether the timer stops after firing once (bool). If False, timer repeats indefinitely.
- `paused` *(read-only)*: Whether the timer is paused (bool, read-only). Paused timers preserve their remaining time.
- `remaining` *(read-only)*: Time remaining until next trigger in milliseconds (int, read-only). Preserved when timer is paused.

**Methods:**

#### `cancel() -> None`

Cancel the timer and remove it from the timer system.

Note:

**Returns:** None The timer will no longer fire and cannot be restarted. The callback will not be called again.

#### `pause() -> None`

Pause the timer, preserving the time remaining until next trigger.

Note:

**Returns:** None The timer can be resumed later with resume(). Time spent paused does not count toward the interval.

#### `restart() -> None`

Restart the timer from the beginning.

Note:

**Returns:** None Resets the timer to fire after a full interval from now, regardless of remaining time.

#### `resume() -> None`

Resume a paused timer from where it left off.

Note:

**Returns:** None Has no effect if the timer is not paused. Timer will fire after the remaining time elapses.

### UICollection

Iterable, indexable collection of UI objects

**Methods:**

#### `append(element)`

Add an element to the end of the collection.

#### `count(element) -> int`

Count occurrences of element in the collection.

#### `extend(iterable)`

Add all elements from an iterable to the collection.

#### `find(name, recursive=False) -> element or list`

Find elements by name.

**Returns:** Single element if exact match, list if wildcard, None if not found.

#### `index(element) -> int`

Return index of first occurrence of element. Raises ValueError if not found.

#### `insert(index, element)`

Insert element at index. Like list.insert(), indices past the end append.

Note: If using z_index for sorting, insertion order may not persist after
the next render. Use name-based .find() for stable element access.

#### `pop([index]) -> element`

Remove and return element at index (default: last element).

Note: If using z_index for sorting, indices may shift after render.
Use name-based .find() for stable element access.

#### `remove(element)`

Remove first occurrence of element. Raises ValueError if not found.

### UICollectionIter

Iterator for a collection of UI objects

**Methods:**

### UIEntityCollectionIter

Iterator for a collection of UI objects

**Methods:**

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

