# McRogueFace API Reference

## Overview

McRogueFace Python API

Core game engine interface for creating roguelike games with Python.

This module provides:
- Scene management (createScene, setScene, currentScene)
- UI components (Frame, Caption, Sprite, Grid)
- Entity system for game objects
- Audio playback (sound effects and music)
- Timer system for scheduled events
- Input handling
- Performance metrics

Example:
    import mcrfpy
    
    # Create a new scene
    mcrfpy.createScene('game')
    mcrfpy.setScene('game')
    
    # Add UI elements
    frame = mcrfpy.Frame(10, 10, 200, 100)
    caption = mcrfpy.Caption('Hello World', 50, 50)
    mcrfpy.sceneUI().extend([frame, caption])


## Table of Contents

- [Functions](#functions)
  - [Scene Management](#scene-management)
  - [Audio](#audio)
  - [UI Utilities](#ui-utilities)
  - [System](#system)
- [Classes](#classes)
  - [UI Components](#ui-components)
  - [Collections](#collections)
  - [System Types](#system-types)
  - [Other Classes](#other-classes)
- [Automation Module](#automation-module)

## Functions

### Scene Management

### `createScene(name: str) -> None`

Create a new empty scene with the given name.

**Arguments:**
- `name` (*str*): Unique name for the new scene

**Raises:** ValueError: If a scene with this name already exists

**Note:** The scene is created but not made active. Use setScene() to switch to it.

**Example:**
```python
mcrfpy.createScene("game_over")
```

---

### `setScene(scene: str, transition: str = None, duration: float = 0.0) -> None`

Switch to a different scene with optional transition effect.

**Arguments:**
- `scene` (*str*): Name of the scene to switch to
- `transition` (*str*): Transition type: "fade", "slide_left", "slide_right", "slide_up", "slide_down"
- `duration` (*float*): Transition duration in seconds (default: 0.0 for instant)

**Raises:** KeyError: If the scene doesn't exist

**Example:**
```python
mcrfpy.setScene("game", "fade", 0.5)
```

---

### `currentScene() -> str`

Get the name of the currently active scene.

**Returns:** str: Name of the current scene

**Example:**
```python
scene_name = mcrfpy.currentScene()
```

---

### `sceneUI(scene: str = None) -> UICollection`

Get all UI elements for a scene.

**Arguments:**
- `scene` (*str*): Scene name. If None, uses current scene

**Returns:** UICollection: All UI elements in the scene

**Raises:** KeyError: If the specified scene doesn't exist

**Example:**
```python
ui_elements = mcrfpy.sceneUI("game")
```

---

### `keypressScene(handler: callable) -> None`

Set the keyboard event handler for the current scene.

**Arguments:**
- `handler` (*callable*): Function that receives (key_name: str, is_pressed: bool)

**Example:**
```python
def on_key(key, pressed):
    if key == "SPACE" and pressed:
        player.jump()
mcrfpy.keypressScene(on_key)
```

---

### Audio

### `createSoundBuffer(filename: str) -> int`

Load a sound effect from a file and return its buffer ID.

**Arguments:**
- `filename` (*str*): Path to the sound file (WAV, OGG, FLAC)

**Returns:** int: Buffer ID for use with playSound()

**Raises:** RuntimeError: If the file cannot be loaded

**Example:**
```python
jump_sound = mcrfpy.createSoundBuffer("assets/jump.wav")
```

---

### `loadMusic(filename: str, loop: bool = True) -> None`

Load and immediately play background music from a file.

**Arguments:**
- `filename` (*str*): Path to the music file (WAV, OGG, FLAC)
- `loop` (*bool*): Whether to loop the music (default: True)

**Note:** Only one music track can play at a time. Loading new music stops the current track.

**Example:**
```python
mcrfpy.loadMusic("assets/background.ogg", True)
```

---

### `playSound(buffer_id: int) -> None`

Play a sound effect using a previously loaded buffer.

**Arguments:**
- `buffer_id` (*int*): Sound buffer ID returned by createSoundBuffer()

**Raises:** RuntimeError: If the buffer ID is invalid

**Example:**
```python
mcrfpy.playSound(jump_sound)
```

---

### `getMusicVolume() -> int`

Get the current music volume level.

**Returns:** int: Current volume (0-100)

**Example:**
```python
current_volume = mcrfpy.getMusicVolume()
```

---

### `getSoundVolume() -> int`

Get the current sound effects volume level.

**Returns:** int: Current volume (0-100)

**Example:**
```python
current_volume = mcrfpy.getSoundVolume()
```

---

### `setMusicVolume(volume: int) -> None`

Set the global music volume.

**Arguments:**
- `volume` (*int*): Volume level from 0 (silent) to 100 (full volume)

**Example:**
```python
mcrfpy.setMusicVolume(50)  # Set to 50% volume
```

---

### `setSoundVolume(volume: int) -> None`

Set the global sound effects volume.

**Arguments:**
- `volume` (*int*): Volume level from 0 (silent) to 100 (full volume)

**Example:**
```python
mcrfpy.setSoundVolume(75)  # Set to 75% volume
```

---

### UI Utilities

### `find(name: str, scene: str = None) -> UIDrawable | None`

Find the first UI element with the specified name.

**Arguments:**
- `name` (*str*): Exact name to search for
- `scene` (*str*): Scene to search in (default: current scene)

**Returns:** UIDrawable or None: The found element, or None if not found

**Note:** Searches scene UI elements and entities within grids.

**Example:**
```python
button = mcrfpy.find("start_button")
```

---

### `findAll(pattern: str, scene: str = None) -> list`

Find all UI elements matching a name pattern.

**Arguments:**
- `pattern` (*str*): Name pattern with optional wildcards (* matches any characters)
- `scene` (*str*): Scene to search in (default: current scene)

**Returns:** list: All matching UI elements and entities

**Example:**
```python
enemies = mcrfpy.findAll("enemy_*")
```

---

### System

### `exit() -> None`

Cleanly shut down the game engine and exit the application.

**Note:** This immediately closes the window and terminates the program.

**Example:**
```python
mcrfpy.exit()
```

---

### `getMetrics() -> dict`

Get current performance metrics.

**Returns:** dict: Performance data with keys:
- frame_time: Last frame duration in seconds
- avg_frame_time: Average frame time
- fps: Frames per second
- draw_calls: Number of draw calls
- ui_elements: Total UI element count
- visible_elements: Visible element count
- current_frame: Frame counter
- runtime: Total runtime in seconds

**Example:**
```python
metrics = mcrfpy.getMetrics()
```

---

### `setTimer(name: str, handler: callable, interval: int) -> None`

Create or update a recurring timer.

**Arguments:**
- `name` (*str*): Unique identifier for the timer
- `handler` (*callable*): Function called with (runtime: float) parameter
- `interval` (*int*): Time between calls in milliseconds

**Note:** If a timer with this name exists, it will be replaced.

**Example:**
```python
def update_score(runtime):
    score += 1
mcrfpy.setTimer("score_update", update_score, 1000)
```

---

### `delTimer(name: str) -> None`

Stop and remove a timer.

**Arguments:**
- `name` (*str*): Timer identifier to remove

**Note:** No error is raised if the timer doesn't exist.

**Example:**
```python
mcrfpy.delTimer("score_update")
```

---

### `setScale(multiplier: float) -> None`

Scale the game window size.

**Arguments:**
- `multiplier` (*float*): Scale factor (e.g., 2.0 for double size)

**Note:** The internal resolution remains 1024x768, but the window is scaled.

**Example:**
```python
mcrfpy.setScale(2.0)  # Double the window size
```

---

## Classes

### UI Components

### class `Frame`

A rectangular frame UI element that can contain other drawable elements.

#### Methods

#### `get_bounds()`

Get the bounding rectangle of this drawable element.

**Returns:** tuple: (x, y, width, height) representing the element's bounds

**Note:** The bounds are in screen coordinates and account for current position and size.

#### `resize(width, height)`

Resize the element to new dimensions.

**Arguments:**
- `width` (*float*): New width in pixels
- `height` (*float*): New height in pixels

**Note:** For Caption and Sprite, this may not change actual size if determined by content.

#### `move(dx, dy)`

Move the element by a relative offset.

**Arguments:**
- `dx` (*float*): Horizontal offset in pixels
- `dy` (*float*): Vertical offset in pixels

**Note:** This modifies the x and y position properties by the given amounts.

---

### class `Caption`

A text display UI element with customizable font and styling.

#### Methods

#### `get_bounds()`

Get the bounding rectangle of this drawable element.

**Returns:** tuple: (x, y, width, height) representing the element's bounds

**Note:** The bounds are in screen coordinates and account for current position and size.

#### `resize(width, height)`

Resize the element to new dimensions.

**Arguments:**
- `width` (*float*): New width in pixels
- `height` (*float*): New height in pixels

**Note:** For Caption and Sprite, this may not change actual size if determined by content.

#### `move(dx, dy)`

Move the element by a relative offset.

**Arguments:**
- `dx` (*float*): Horizontal offset in pixels
- `dy` (*float*): Vertical offset in pixels

**Note:** This modifies the x and y position properties by the given amounts.

---

### class `Sprite`

A sprite UI element that displays a texture or portion of a texture atlas.

#### Methods

#### `get_bounds()`

Get the bounding rectangle of this drawable element.

**Returns:** tuple: (x, y, width, height) representing the element's bounds

**Note:** The bounds are in screen coordinates and account for current position and size.

#### `resize(width, height)`

Resize the element to new dimensions.

**Arguments:**
- `width` (*float*): New width in pixels
- `height` (*float*): New height in pixels

**Note:** For Caption and Sprite, this may not change actual size if determined by content.

#### `move(dx, dy)`

Move the element by a relative offset.

**Arguments:**
- `dx` (*float*): Horizontal offset in pixels
- `dy` (*float*): Vertical offset in pixels

**Note:** This modifies the x and y position properties by the given amounts.

---

### class `Grid`

A grid-based tilemap UI element for rendering tile-based levels and game worlds.

#### Methods

#### `at(x, y)`

Get the GridPoint at the specified grid coordinates.

**Arguments:**
- `x` (*int*): Grid x coordinate
- `y` (*int*): Grid y coordinate

**Returns:** GridPoint or None: The grid point at (x, y), or None if out of bounds

#### `get_bounds()`

Get the bounding rectangle of this drawable element.

**Returns:** tuple: (x, y, width, height) representing the element's bounds

**Note:** The bounds are in screen coordinates and account for current position and size.

#### `resize(width, height)`

Resize the element to new dimensions.

**Arguments:**
- `width` (*float*): New width in pixels
- `height` (*float*): New height in pixels

**Note:** For Caption and Sprite, this may not change actual size if determined by content.

#### `move(dx, dy)`

Move the element by a relative offset.

**Arguments:**
- `dx` (*float*): Horizontal offset in pixels
- `dy` (*float*): Vertical offset in pixels

**Note:** This modifies the x and y position properties by the given amounts.

---

### class `Entity`

Game entity that can be placed in a Grid.

#### Methods

#### `die()`

Remove this entity from its parent grid.

**Note:** The entity object remains valid but is no longer rendered or updated.

#### `move(dx, dy)`

Move the element by a relative offset.

**Arguments:**
- `dx` (*float*): Horizontal offset in pixels
- `dy` (*float*): Vertical offset in pixels

**Note:** This modifies the x and y position properties by the given amounts.

#### `at(x, y)`

Check if this entity is at the specified grid coordinates.

**Arguments:**
- `x` (*int*): Grid x coordinate to check
- `y` (*int*): Grid y coordinate to check

**Returns:** bool: True if entity is at position (x, y), False otherwise

#### `get_bounds()`

Get the bounding rectangle of this drawable element.

**Returns:** tuple: (x, y, width, height) representing the element's bounds

**Note:** The bounds are in screen coordinates and account for current position and size.

#### `index()`

Get the index of this entity in its parent grid's entity list.

**Returns:** int: Index position, or -1 if not in a grid

#### `resize(width, height)`

Resize the element to new dimensions.

**Arguments:**
- `width` (*float*): New width in pixels
- `height` (*float*): New height in pixels

**Note:** For Caption and Sprite, this may not change actual size if determined by content.

---

### Collections

### class `EntityCollection`

Container for Entity objects in a Grid. Supports iteration and indexing.

#### Methods

#### `append(entity)`

Add an entity to the end of the collection.

**Arguments:**
- `entity` (*Entity*): The entity to add

#### `remove(entity)`

Remove the first occurrence of an entity from the collection.

**Arguments:**
- `entity` (*Entity*): The entity to remove

**Raises:** ValueError: If entity is not in collection

#### `count(entity)`

Count the number of occurrences of an entity in the collection.

**Arguments:**
- `entity` (*Entity*): The entity to count

**Returns:** int: Number of times entity appears in collection

#### `index(entity)`

Find the index of the first occurrence of an entity.

**Arguments:**
- `entity` (*Entity*): The entity to find

**Returns:** int: Index of entity in collection

**Raises:** ValueError: If entity is not in collection

#### `extend(iterable)`

Add all entities from an iterable to the collection.

**Arguments:**
- `iterable` (*Iterable[Entity]*): Entities to add

---

### class `UICollection`

Container for UI drawable elements. Supports iteration and indexing.

#### Methods

#### `append(drawable)`

Add a drawable element to the end of the collection.

**Arguments:**
- `drawable` (*UIDrawable*): The drawable element to add

#### `remove(drawable)`

Remove the first occurrence of a drawable from the collection.

**Arguments:**
- `drawable` (*UIDrawable*): The drawable to remove

**Raises:** ValueError: If drawable is not in collection

#### `count(drawable)`

Count the number of occurrences of a drawable in the collection.

**Arguments:**
- `drawable` (*UIDrawable*): The drawable to count

**Returns:** int: Number of times drawable appears in collection

#### `index(drawable)`

Find the index of the first occurrence of a drawable.

**Arguments:**
- `drawable` (*UIDrawable*): The drawable to find

**Returns:** int: Index of drawable in collection

**Raises:** ValueError: If drawable is not in collection

#### `extend(iterable)`

Add all drawables from an iterable to the collection.

**Arguments:**
- `iterable` (*Iterable[UIDrawable]*): Drawables to add

---

### class `UICollectionIter`

Iterator for UICollection. Automatically created when iterating over a UICollection.

---

### class `UIEntityCollectionIter`

Iterator for EntityCollection. Automatically created when iterating over an EntityCollection.

---

### System Types

### class `Color`

RGBA color representation.

#### Methods

#### `from_hex(hex_string)`

Create a Color from a hexadecimal color string.

**Arguments:**
- `hex_string` (*str*): Hex color string (e.g., "#FF0000" or "FF0000")

**Returns:** Color: New Color object from hex string

**Example:**
```python
red = Color.from_hex("#FF0000")
```

#### `to_hex()`

Convert this Color to a hexadecimal string.

**Returns:** str: Hex color string in format "#RRGGBB"

**Example:**
```python
hex_str = color.to_hex()  # Returns "#FF0000"
```

#### `lerp(other, t)`

Linearly interpolate between this color and another.

**Arguments:**
- `other` (*Color*): The color to interpolate towards
- `t` (*float*): Interpolation factor from 0.0 to 1.0

**Returns:** Color: New interpolated Color object

**Example:**
```python
mixed = red.lerp(blue, 0.5)  # 50% between red and blue
```

---

### class `Vector`

2D vector for positions and directions.

#### Methods

#### `magnitude()`

Calculate the length/magnitude of this vector.

**Returns:** float: The magnitude of the vector

#### `distance_to(other)`

Calculate the distance to another vector.

**Arguments:**
- `other` (*Vector*): The other vector

**Returns:** float: Distance between the two vectors

#### `dot(other)`

Calculate the dot product with another vector.

**Arguments:**
- `other` (*Vector*): The other vector

**Returns:** float: Dot product of the two vectors

#### `angle()`

Get the angle of this vector in radians.

**Returns:** float: Angle in radians from positive x-axis

#### `magnitude_squared()`

Calculate the squared magnitude of this vector.

**Returns:** float: The squared magnitude (faster than magnitude())

**Note:** Use this for comparisons to avoid expensive square root calculation.

#### `copy()`

Create a copy of this vector.

**Returns:** Vector: New Vector object with same x and y values

#### `normalize()`

Return a unit vector in the same direction.

**Returns:** Vector: New normalized vector with magnitude 1.0

**Raises:** ValueError: If vector has zero magnitude

---

### class `Texture`

Texture object for image data.

---

### class `Font`

Font object for text rendering.

---

### Other Classes

### class `Animation`

Animate UI element properties over time.

#### Properties

- **`property`**: str: Name of the property being animated (e.g., "x", "y", "scale")
- **`duration`**: float: Total duration of the animation in seconds
- **`elapsed_time`**: float: Time elapsed since animation started (read-only)
- **`current_value`**: float: Current interpolated value of the animation (read-only)
- **`is_running`**: bool: True if animation is currently running (read-only)
- **`is_finished`**: bool: True if animation has completed (read-only)

#### Methods

#### `update(delta_time)`

Update the animation by the given time delta.

**Arguments:**
- `delta_time` (*float*): Time elapsed since last update in seconds

**Returns:** bool: True if animation is still running, False if finished

#### `start(target)`

Start the animation on a target UI element.

**Arguments:**
- `target` (*UIDrawable*): The UI element to animate

**Note:** The target must have the property specified in the animation constructor.

#### `get_current_value()`

Get the current interpolated value of the animation.

**Returns:** float: Current animation value between start and end

---

### class `Drawable`

Base class for all drawable UI elements.

#### Methods

#### `get_bounds()`

Get the bounding rectangle of this drawable element.

**Returns:** tuple: (x, y, width, height) representing the element's bounds

**Note:** The bounds are in screen coordinates and account for current position and size.

#### `resize(width, height)`

Resize the element to new dimensions.

**Arguments:**
- `width` (*float*): New width in pixels
- `height` (*float*): New height in pixels

**Note:** For Caption and Sprite, this may not change actual size if determined by content.

#### `move(dx, dy)`

Move the element by a relative offset.

**Arguments:**
- `dx` (*float*): Horizontal offset in pixels
- `dy` (*float*): Vertical offset in pixels

**Note:** This modifies the x and y position properties by the given amounts.

---

### class `GridPoint`

Represents a single tile in a Grid.

#### Properties

- **`x`**: int: Grid x coordinate of this point
- **`y`**: int: Grid y coordinate of this point
- **`texture_index`**: int: Index of the texture/sprite to display at this point
- **`solid`**: bool: Whether this point blocks movement
- **`transparent`**: bool: Whether this point allows light/vision through
- **`color`**: Color: Color tint applied to the texture at this point

---

### class `GridPointState`

State information for a GridPoint.

#### Properties

- **`visible`**: bool: Whether this point is currently visible to the player
- **`discovered`**: bool: Whether this point has been discovered/explored
- **`custom_flags`**: int: Bitfield for custom game-specific flags

---

### class `Scene`

Base class for object-oriented scenes.

#### Methods

#### `register_keyboard(callable)`

Register a keyboard event handler function for the scene.

**Arguments:**
- `callable` (*callable*): Function that takes (key: str, action: str) parameters

**Note:** Alternative to overriding the on_keypress method when subclassing Scene objects.

**Example:**
```python
def handle_keyboard(key, action):
    print(f"Key '{key}' was {action}")
scene.register_keyboard(handle_keyboard)
```

#### `activate()`

Make this scene the active scene.

**Note:** Equivalent to calling setScene() with this scene's name.

#### `get_ui()`

Get the UI element collection for this scene.

**Returns:** UICollection: Collection of all UI elements in this scene

#### `keypress(handler)`

Register a keyboard handler function for this scene.

**Arguments:**
- `handler` (*callable*): Function that takes (key_name: str, is_pressed: bool)

**Note:** Alternative to overriding the on_keypress method.

---

### class `Timer`

Timer object for scheduled callbacks.

#### Methods

#### `restart()`

Restart the timer from the beginning.

**Note:** Resets the timer's internal clock to zero.

#### `cancel()`

Cancel the timer and remove it from the system.

**Note:** After cancelling, the timer object cannot be reused.

#### `pause()`

Pause the timer, stopping its callback execution.

**Note:** Use resume() to continue the timer from where it was paused.

#### `resume()`

Resume a paused timer.

**Note:** Has no effect if timer is not paused.

---

### class `Window`

Window singleton for accessing and modifying the game window properties.

#### Methods

#### `get()`

Get the Window singleton instance.

**Returns:** Window: The singleton window object

**Note:** This is a static method that returns the same instance every time.

#### `screenshot(filename)`

Take a screenshot and save it to a file.

**Arguments:**
- `filename` (*str*): Path where to save the screenshot

**Note:** Supports PNG, JPG, and BMP formats based on file extension.

#### `center()`

Center the window on the screen.

**Note:** Only works if the window is not fullscreen.

---

## Automation Module

The `mcrfpy.automation` module provides testing and automation capabilities.

### `automation.click`

Click at position

---

### `automation.doubleClick`

Double click at position

---

### `automation.dragRel`

Drag mouse relative to current position

---

### `automation.dragTo`

Drag mouse to position

---

### `automation.hotkey`

Press a hotkey combination (e.g., hotkey('ctrl', 'c'))

---

### `automation.keyDown`

Press and hold a key

---

### `automation.keyUp`

Release a key

---

### `automation.middleClick`

Middle click at position

---

### `automation.mouseDown`

Press mouse button

---

### `automation.mouseUp`

Release mouse button

---

### `automation.moveRel`

Move mouse relative to current position

---

### `automation.moveTo`

Move mouse to absolute position

---

### `automation.onScreen`

Check if coordinates are within screen bounds

---

### `automation.position`

Get current mouse position as (x, y) tuple

---

### `automation.rightClick`

Right click at position

---

### `automation.screenshot`

Save a screenshot to the specified file

---

### `automation.scroll`

Scroll wheel at position

---

### `automation.size`

Get screen size as (width, height) tuple

---

### `automation.tripleClick`

Triple click at position

---

### `automation.typewrite`

Type text with optional interval between keystrokes

---
