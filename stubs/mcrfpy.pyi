"""Type stubs for McRogueFace Python API.

Core game engine interface for creating roguelike games with Python.
"""

from typing import Any, List, Dict, Tuple, Optional, Callable, Union, overload

# Type aliases
UIElement = Union['Frame', 'Caption', 'Sprite', 'Grid', 'Line', 'Circle', 'Arc']
Transition = Union[str, None]

# Classes

class Color:
    """RGBA color representation.

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
    """

    r: int
    g: int
    b: int
    a: int

    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, r: int, g: int, b: int, a: int = 255) -> None: ...

    def from_hex(self, hex_string: str) -> 'Color':
        """Create color from hex string (e.g., '#FF0000' or 'FF0000')."""
        ...

    def to_hex(self) -> str:
        """Convert color to hex string format."""
        ...

    def lerp(self, other: 'Color', t: float) -> 'Color':
        """Linear interpolation between two colors."""
        ...

class Vector:
    """SFML Vector Object for 2D coordinates."""
    
    x: float
    y: float
    
    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, x: float, y: float) -> None: ...
    
    def add(self, other: 'Vector') -> 'Vector': ...
    def subtract(self, other: 'Vector') -> 'Vector': ...
    def multiply(self, scalar: float) -> 'Vector': ...
    def divide(self, scalar: float) -> 'Vector': ...
    def distance(self, other: 'Vector') -> float: ...
    def normalize(self) -> 'Vector': ...
    def dot(self, other: 'Vector') -> float: ...

class Texture:
    """SFML Texture Object for images."""
    
    def __init__(self, filename: str) -> None: ...
    
    filename: str
    width: int
    height: int
    sprite_count: int

class Font:
    """SFML Font Object for text rendering."""

    def __init__(self, filename: str) -> None: ...

    filename: str
    family: str

class Sound:
    """Sound effect object for short audio clips.

    Sounds are loaded entirely into memory, making them suitable for
    short sound effects that need to be played with minimal latency.
    Multiple Sound instances can play simultaneously.
    """

    def __init__(self, filename: str) -> None:
        """Load a sound effect from a file.

        Args:
            filename: Path to the sound file (WAV, OGG, FLAC supported)

        Raises:
            RuntimeError: If the file cannot be loaded
        """
        ...

    volume: float
    """Volume level from 0 (silent) to 100 (full volume)."""

    loop: bool
    """Whether the sound loops when it reaches the end."""

    playing: bool
    """True if the sound is currently playing (read-only)."""

    duration: float
    """Total duration of the sound in seconds (read-only)."""

    source: str
    """Filename path used to load this sound (read-only)."""

    def play(self) -> None:
        """Start or resume playing the sound."""
        ...

    def pause(self) -> None:
        """Pause the sound. Use play() to resume."""
        ...

    def stop(self) -> None:
        """Stop playing and reset to the beginning."""
        ...

class Music:
    """Streaming music object for longer audio tracks.

    Music is streamed from disk rather than loaded entirely into memory,
    making it suitable for longer audio tracks like background music.
    """

    def __init__(self, filename: str) -> None:
        """Load a music track from a file.

        Args:
            filename: Path to the music file (WAV, OGG, FLAC supported)

        Raises:
            RuntimeError: If the file cannot be loaded
        """
        ...

    volume: float
    """Volume level from 0 (silent) to 100 (full volume)."""

    loop: bool
    """Whether the music loops when it reaches the end."""

    playing: bool
    """True if the music is currently playing (read-only)."""

    duration: float
    """Total duration of the music in seconds (read-only)."""

    position: float
    """Current playback position in seconds. Can be set to seek."""

    source: str
    """Filename path used to load this music (read-only)."""

    def play(self) -> None:
        """Start or resume playing the music."""
        ...

    def pause(self) -> None:
        """Pause the music. Use play() to resume."""
        ...

    def stop(self) -> None:
        """Stop playing and reset to the beginning."""
        ...

class Keyboard:
    """Keyboard state singleton for checking modifier keys.

    Access via mcrfpy.keyboard (singleton instance).
    Queries real-time keyboard state from SFML.
    """

    shift: bool
    """True if either Shift key is currently pressed (read-only)."""

    ctrl: bool
    """True if either Control key is currently pressed (read-only)."""

    alt: bool
    """True if either Alt key is currently pressed (read-only)."""

    system: bool
    """True if either System key (Win/Cmd) is currently pressed (read-only)."""

class Drawable:
    """Base class for all drawable UI elements."""

    x: float
    y: float
    visible: bool
    z_index: int
    name: str
    pos: Vector

    # Mouse event callbacks (#140, #141)
    on_click: Optional[Callable[[float, float, int, str], None]]
    on_enter: Optional[Callable[[float, float, int, str], None]]
    on_exit: Optional[Callable[[float, float, int, str], None]]
    on_move: Optional[Callable[[float, float, int, str], None]]

    # Read-only hover state (#140)
    hovered: bool

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get bounding box as (x, y, width, height)."""
        ...

    def move(self, dx: float, dy: float) -> None:
        """Move by relative offset (dx, dy)."""
        ...

    def resize(self, width: float, height: float) -> None:
        """Resize to new dimensions (width, height)."""
        ...

class Frame(Drawable):
    """Frame(x=0, y=0, w=0, h=0, fill_color=None, outline_color=None, outline=0, on_click=None, children=None)

    A rectangular frame UI element that can contain other drawable elements.
    """

    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, x: float = 0, y: float = 0, w: float = 0, h: float = 0,
                 fill_color: Optional[Color] = None, outline_color: Optional[Color] = None,
                 outline: float = 0, on_click: Optional[Callable] = None,
                 children: Optional[List[UIElement]] = None) -> None: ...

    w: float
    h: float
    fill_color: Color
    outline_color: Color
    outline: float
    on_click: Optional[Callable[[float, float, int], None]]
    children: 'UICollection'
    clip_children: bool

class Caption(Drawable):
    """Caption(text='', x=0, y=0, font=None, fill_color=None, outline_color=None, outline=0, on_click=None)

    A text display UI element with customizable font and styling.
    """

    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, text: str = '', x: float = 0, y: float = 0,
                 font: Optional[Font] = None, fill_color: Optional[Color] = None,
                 outline_color: Optional[Color] = None, outline: float = 0,
                 on_click: Optional[Callable] = None) -> None: ...

    text: str
    font: Font
    fill_color: Color
    outline_color: Color
    outline: float
    on_click: Optional[Callable[[float, float, int], None]]
    w: float  # Read-only, computed from text
    h: float  # Read-only, computed from text

class Sprite(Drawable):
    """Sprite(x=0, y=0, texture=None, sprite_index=0, scale=1.0, on_click=None)

    A sprite UI element that displays a texture or portion of a texture atlas.
    """

    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, x: float = 0, y: float = 0, texture: Optional[Texture] = None,
                 sprite_index: int = 0, scale: float = 1.0,
                 on_click: Optional[Callable] = None) -> None: ...

    texture: Texture
    sprite_index: int
    scale: float
    on_click: Optional[Callable[[float, float, int], None]]
    w: float  # Read-only, computed from texture
    h: float  # Read-only, computed from texture

class Grid(Drawable):
    """Grid(x=0, y=0, grid_size=(20, 20), texture=None, tile_width=16, tile_height=16, scale=1.0, on_click=None)

    A grid-based tilemap UI element for rendering tile-based levels and game worlds.
    """

    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, x: float = 0, y: float = 0, grid_size: Tuple[int, int] = (20, 20),
                 texture: Optional[Texture] = None, tile_width: int = 16, tile_height: int = 16,
                 scale: float = 1.0, on_click: Optional[Callable] = None) -> None: ...

    grid_size: Tuple[int, int]
    tile_width: int
    tile_height: int
    texture: Texture
    scale: float
    points: List[List['GridPoint']]
    entities: 'EntityCollection'
    background_color: Color
    on_click: Optional[Callable[[int, int, int], None]]

    def at(self, x: int, y: int) -> 'GridPoint':
        """Get grid point at tile coordinates."""
        ...

class Line(Drawable):
    """Line(start=None, end=None, thickness=1.0, color=None, on_click=None, **kwargs)

    A line UI element for drawing straight lines between two points.
    """

    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, start: Optional[Tuple[float, float]] = None,
                 end: Optional[Tuple[float, float]] = None,
                 thickness: float = 1.0, color: Optional[Color] = None,
                 on_click: Optional[Callable] = None) -> None: ...

    start: Vector
    end: Vector
    thickness: float
    color: Color
    on_click: Optional[Callable[[float, float, int], None]]

class Circle(Drawable):
    """Circle(radius=0, center=None, fill_color=None, outline_color=None, outline=0, on_click=None, **kwargs)

    A circle UI element for drawing filled or outlined circles.
    """

    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, radius: float = 0, center: Optional[Tuple[float, float]] = None,
                 fill_color: Optional[Color] = None, outline_color: Optional[Color] = None,
                 outline: float = 0, on_click: Optional[Callable] = None) -> None: ...

    radius: float
    center: Vector
    fill_color: Color
    outline_color: Color
    outline: float
    on_click: Optional[Callable[[float, float, int], None]]

class Arc(Drawable):
    """Arc(center=None, radius=0, start_angle=0, end_angle=90, color=None, thickness=1, on_click=None, **kwargs)

    An arc UI element for drawing curved line segments.
    """

    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, center: Optional[Tuple[float, float]] = None, radius: float = 0,
                 start_angle: float = 0, end_angle: float = 90,
                 color: Optional[Color] = None, thickness: float = 1.0,
                 on_click: Optional[Callable] = None) -> None: ...

    center: Vector
    radius: float
    start_angle: float
    end_angle: float
    color: Color
    thickness: float
    on_click: Optional[Callable[[float, float, int], None]]

class GridPoint:
    """Grid point representing a single tile."""
    
    texture_index: int
    solid: bool
    color: Color

class GridPointState:
    """State information for a grid point."""
    
    texture_index: int
    color: Color

class Entity(Drawable):
    """Entity(grid_x=0, grid_y=0, texture=None, sprite_index=0, name='')
    
    Game entity that lives within a Grid.
    """
    
    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, grid_x: float = 0, grid_y: float = 0, texture: Optional[Texture] = None,
                 sprite_index: int = 0, name: str = '') -> None: ...
    
    grid_x: float
    grid_y: float
    texture: Texture
    sprite_index: int
    grid: Optional[Grid]
    
    def at(self, grid_x: float, grid_y: float) -> None:
        """Move entity to grid position."""
        ...
    
    def die(self) -> None:
        """Remove entity from its grid."""
        ...
    
    def index(self) -> int:
        """Get index in parent grid's entity collection."""
        ...

class UICollection:
    """Collection of UI drawable elements (Frame, Caption, Sprite, Grid, Line, Circle, Arc)."""
    
    def __len__(self) -> int: ...
    def __getitem__(self, index: int) -> UIElement: ...
    def __setitem__(self, index: int, value: UIElement) -> None: ...
    def __delitem__(self, index: int) -> None: ...
    def __contains__(self, item: UIElement) -> bool: ...
    def __iter__(self) -> Any: ...
    def __add__(self, other: 'UICollection') -> 'UICollection': ...
    def __iadd__(self, other: 'UICollection') -> 'UICollection': ...
    
    def append(self, item: UIElement) -> None: ...
    def extend(self, items: List[UIElement]) -> None: ...
    def remove(self, item: UIElement) -> None: ...
    def index(self, item: UIElement) -> int: ...
    def count(self, item: UIElement) -> int: ...

class EntityCollection:
    """Collection of Entity objects."""
    
    def __len__(self) -> int: ...
    def __getitem__(self, index: int) -> Entity: ...
    def __setitem__(self, index: int, value: Entity) -> None: ...
    def __delitem__(self, index: int) -> None: ...
    def __contains__(self, item: Entity) -> bool: ...
    def __iter__(self) -> Any: ...
    def __add__(self, other: 'EntityCollection') -> 'EntityCollection': ...
    def __iadd__(self, other: 'EntityCollection') -> 'EntityCollection': ...
    
    def append(self, item: Entity) -> None: ...
    def extend(self, items: List[Entity]) -> None: ...
    def remove(self, item: Entity) -> None: ...
    def index(self, item: Entity) -> int: ...
    def count(self, item: Entity) -> int: ...

class Scene:
    """Base class for object-oriented scenes."""

    name: str
    children: UICollection  # #151: UI elements collection (read-only alias for get_ui())
    on_key: Optional[Callable[[str, str], None]]  # Keyboard handler (key, action)

    def __init__(self, name: str) -> None: ...

    def activate(self) -> None:
        """Called when scene becomes active."""
        ...

    def deactivate(self) -> None:
        """Called when scene becomes inactive."""
        ...

    def get_ui(self) -> UICollection:
        """Get UI elements collection."""
        ...

    def on_keypress(self, key: str, pressed: bool) -> None:
        """Handle keyboard events (override in subclass)."""
        ...

    def on_click(self, x: float, y: float, button: int) -> None:
        """Handle mouse clicks (override in subclass)."""
        ...

    def on_enter(self) -> None:
        """Called when entering the scene (override in subclass)."""
        ...

    def on_exit(self) -> None:
        """Called when leaving the scene (override in subclass)."""
        ...

    def on_resize(self, width: int, height: int) -> None:
        """Handle window resize events (override in subclass)."""
        ...

    def update(self, dt: float) -> None:
        """Update scene logic (override in subclass)."""
        ...

class Timer:
    """Timer object for scheduled callbacks."""
    
    name: str
    interval: int
    active: bool
    
    def __init__(self, name: str, callback: Callable[[float], None], interval: int) -> None: ...
    
    def pause(self) -> None:
        """Pause the timer."""
        ...
    
    def resume(self) -> None:
        """Resume the timer."""
        ...
    
    def cancel(self) -> None:
        """Cancel and remove the timer."""
        ...

class Window:
    """Window singleton for managing the game window."""
    
    resolution: Tuple[int, int]
    fullscreen: bool
    vsync: bool
    title: str
    fps_limit: int
    game_resolution: Tuple[int, int]
    scaling_mode: str
    
    @staticmethod
    def get() -> 'Window':
        """Get the window singleton instance."""
        ...

class Animation:
    """Animation for interpolating UI properties over time.

    Create an animation targeting a specific property, then call start() on a
    UI element to begin the animation. The AnimationManager handles updates
    automatically.

    Example:
        # Move a frame to x=500 over 2 seconds with easing
        anim = mcrfpy.Animation('x', 500.0, 2.0, 'easeInOut')
        anim.start(my_frame)

        # Animate color with completion callback
        def on_done(anim, target):
            print('Fade complete!')
        fade = mcrfpy.Animation('fill_color.a', 0, 1.0, callback=on_done)
        fade.start(my_sprite)
    """

    @property
    def property(self) -> str:
        """Target property name being animated (read-only)."""
        ...

    @property
    def duration(self) -> float:
        """Animation duration in seconds (read-only)."""
        ...

    @property
    def elapsed(self) -> float:
        """Time elapsed since animation started in seconds (read-only)."""
        ...

    @property
    def is_complete(self) -> bool:
        """Whether the animation has finished (read-only)."""
        ...

    @property
    def is_delta(self) -> bool:
        """Whether animation uses delta/additive mode (read-only)."""
        ...

    def __init__(self,
                 property: str,
                 target: Union[float, int, Tuple[float, float], Tuple[int, int, int], Tuple[int, int, int, int], List[int], str],
                 duration: float,
                 easing: str = 'linear',
                 delta: bool = False,
                 callback: Optional[Callable[['Animation', Any], None]] = None) -> None:
        """Create an animation for a UI property.

        Args:
            property: Property name to animate. Common properties:
                - Position/Size: 'x', 'y', 'w', 'h', 'pos', 'size'
                - Appearance: 'fill_color', 'outline_color', 'opacity'
                - Sprite: 'sprite_index', 'scale'
                - Grid: 'center', 'zoom'
                - Sub-properties: 'fill_color.r', 'fill_color.g', etc.
            target: Target value. Type depends on property:
                - float: For x, y, w, h, scale, opacity, zoom
                - int: For sprite_index
                - (r, g, b) or (r, g, b, a): For colors
                - (x, y): For pos, size, center
                - [int, ...]: For sprite animation sequences
                - str: For text animation
            duration: Animation duration in seconds.
            easing: Easing function. Options: 'linear', 'easeIn', 'easeOut',
                'easeInOut', 'easeInQuad', 'easeOutQuad', 'easeInOutQuad',
                'easeInCubic', 'easeOutCubic', 'easeInOutCubic',
                'easeInElastic', 'easeOutElastic', 'easeInOutElastic',
                'easeInBounce', 'easeOutBounce', 'easeInOutBounce', and more.
            delta: If True, target value is added to start value.
            callback: Function(animation, target) called on completion.
        """
        ...

    def start(self, target: UIElement, conflict_mode: str = 'replace') -> None:
        """Start the animation on a UI element.

        Args:
            target: The UI element to animate (Frame, Caption, Sprite, Grid, or Entity)
            conflict_mode: How to handle if property is already animating:
                - 'replace': Stop existing animation, start new one (default)
                - 'queue': Wait for existing animation to complete
                - 'error': Raise RuntimeError if property is busy
        """
        ...

    def update(self, dt: float) -> bool:
        """Update animation by time delta. Returns True if still running.

        Note: Normally called automatically by AnimationManager.
        """
        ...

    def get_current_value(self) -> Any:
        """Get the current interpolated value."""
        ...

    def complete(self) -> None:
        """Complete the animation immediately, jumping to final value."""
        ...

    def hasValidTarget(self) -> bool:
        """Check if the animation target still exists."""
        ...

    def __repr__(self) -> str:
        """Return string representation showing property, duration, and status."""
        ...

# Module-level attributes

__version__: str
"""McRogueFace version string (e.g., '1.0.0')."""

keyboard: Keyboard
"""Keyboard state singleton for checking modifier keys."""

# Module functions

def sceneUI(scene: Optional[str] = None) -> UICollection:
    """Get all UI elements for a scene."""
    ...

def currentScene() -> str:
    """Get the name of the currently active scene."""
    ...

def setScene(scene: str, transition: Optional[str] = None, duration: float = 0.0) -> None:
    """Switch to a different scene with optional transition effect."""
    ...

def createScene(name: str) -> None:
    """Create a new empty scene."""
    ...

def keypressScene(handler: Callable[[str, bool], None]) -> None:
    """Set the keyboard event handler for the current scene."""
    ...

def setTimer(name: str, handler: Callable[[float], None], interval: int) -> None:
    """Create or update a recurring timer."""
    ...

def delTimer(name: str) -> None:
    """Stop and remove a timer."""
    ...

def exit() -> None:
    """Cleanly shut down the game engine and exit the application."""
    ...

def setScale(multiplier: float) -> None:
    """Scale the game window size (deprecated - use Window.resolution)."""
    ...

def find(name: str, scene: Optional[str] = None) -> Optional[UIElement]:
    """Find the first UI element with the specified name."""
    ...

def findAll(pattern: str, scene: Optional[str] = None) -> List[UIElement]:
    """Find all UI elements matching a name pattern (supports * wildcards)."""
    ...

def getMetrics() -> Dict[str, Union[int, float]]:
    """Get current performance metrics."""
    ...

# Submodule
class automation:
    """Automation API for testing and scripting."""
    
    @staticmethod
    def screenshot(filename: str) -> bool:
        """Save a screenshot to the specified file."""
        ...
    
    @staticmethod
    def position() -> Tuple[int, int]:
        """Get current mouse position as (x, y) tuple."""
        ...
    
    @staticmethod
    def size() -> Tuple[int, int]:
        """Get screen size as (width, height) tuple."""
        ...
    
    @staticmethod
    def onScreen(x: int, y: int) -> bool:
        """Check if coordinates are within screen bounds."""
        ...
    
    @staticmethod
    def moveTo(x: int, y: int, duration: float = 0.0) -> None:
        """Move mouse to absolute position."""
        ...
    
    @staticmethod
    def moveRel(xOffset: int, yOffset: int, duration: float = 0.0) -> None:
        """Move mouse relative to current position."""
        ...
    
    @staticmethod
    def dragTo(x: int, y: int, duration: float = 0.0, button: str = 'left') -> None:
        """Drag mouse to position."""
        ...
    
    @staticmethod
    def dragRel(xOffset: int, yOffset: int, duration: float = 0.0, button: str = 'left') -> None:
        """Drag mouse relative to current position."""
        ...
    
    @staticmethod
    def click(x: Optional[int] = None, y: Optional[int] = None, clicks: int = 1,
              interval: float = 0.0, button: str = 'left') -> None:
        """Click mouse at position."""
        ...
    
    @staticmethod
    def mouseDown(x: Optional[int] = None, y: Optional[int] = None, button: str = 'left') -> None:
        """Press mouse button down."""
        ...
    
    @staticmethod
    def mouseUp(x: Optional[int] = None, y: Optional[int] = None, button: str = 'left') -> None:
        """Release mouse button."""
        ...
    
    @staticmethod
    def keyDown(key: str) -> None:
        """Press key down."""
        ...
    
    @staticmethod
    def keyUp(key: str) -> None:
        """Release key."""
        ...
    
    @staticmethod
    def press(key: str) -> None:
        """Press and release a key."""
        ...
    
    @staticmethod
    def typewrite(text: str, interval: float = 0.0) -> None:
        """Type text with optional interval between characters."""
        ...
