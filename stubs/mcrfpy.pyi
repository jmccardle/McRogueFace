"""Type stubs for McRogueFace Python API.

Core game engine interface for creating roguelike games with Python.
"""

from typing import Any, List, Dict, Tuple, Optional, Callable, Union, overload
from enum import IntEnum

# Type aliases
UIElement = Union['Frame', 'Caption', 'Sprite', 'Grid', 'Line', 'Circle', 'Arc']
Transition = Union[str, None]

# Enums

class Key(IntEnum):
    """Keyboard key codes.

    These enum values compare equal to their legacy string equivalents
    for backwards compatibility:
        Key.ESCAPE == 'Escape'  # True
        Key.LEFT_SHIFT == 'LShift'  # True
    """
    # Letters
    A = 0
    B = 1
    C = 2
    D = 3
    E = 4
    F = 5
    G = 6
    H = 7
    I = 8
    J = 9
    K = 10
    L = 11
    M = 12
    N = 13
    O = 14
    P = 15
    Q = 16
    R = 17
    S = 18
    T = 19
    U = 20
    V = 21
    W = 22
    X = 23
    Y = 24
    Z = 25
    # Number row
    NUM_0 = 26
    NUM_1 = 27
    NUM_2 = 28
    NUM_3 = 29
    NUM_4 = 30
    NUM_5 = 31
    NUM_6 = 32
    NUM_7 = 33
    NUM_8 = 34
    NUM_9 = 35
    # Control keys
    ESCAPE = 36
    LEFT_CONTROL = 37
    LEFT_SHIFT = 38
    LEFT_ALT = 39
    LEFT_SYSTEM = 40
    RIGHT_CONTROL = 41
    RIGHT_SHIFT = 42
    RIGHT_ALT = 43
    RIGHT_SYSTEM = 44
    MENU = 45
    # Punctuation
    LEFT_BRACKET = 46
    RIGHT_BRACKET = 47
    SEMICOLON = 48
    COMMA = 49
    PERIOD = 50
    APOSTROPHE = 51
    SLASH = 52
    BACKSLASH = 53
    GRAVE = 54
    EQUAL = 55
    HYPHEN = 56
    # Whitespace/editing
    SPACE = 57
    ENTER = 58
    BACKSPACE = 59
    TAB = 60
    # Navigation
    PAGE_UP = 61
    PAGE_DOWN = 62
    END = 63
    HOME = 64
    INSERT = 65
    DELETE = 66
    # Numpad operators
    ADD = 67
    SUBTRACT = 68
    MULTIPLY = 69
    DIVIDE = 70
    # Arrows
    LEFT = 71
    RIGHT = 72
    UP = 73
    DOWN = 74
    # Numpad numbers
    NUMPAD_0 = 75
    NUMPAD_1 = 76
    NUMPAD_2 = 77
    NUMPAD_3 = 78
    NUMPAD_4 = 79
    NUMPAD_5 = 80
    NUMPAD_6 = 81
    NUMPAD_7 = 82
    NUMPAD_8 = 83
    NUMPAD_9 = 84
    # Function keys
    F1 = 85
    F2 = 86
    F3 = 87
    F4 = 88
    F5 = 89
    F6 = 90
    F7 = 91
    F8 = 92
    F9 = 93
    F10 = 94
    F11 = 95
    F12 = 96
    F13 = 97
    F14 = 98
    F15 = 99
    # Misc
    PAUSE = 100
    UNKNOWN = -1

class MouseButton(IntEnum):
    """Mouse button codes.

    These enum values compare equal to their legacy string equivalents
    for backwards compatibility:
        MouseButton.LEFT == 'left'  # True
        MouseButton.RIGHT == 'right'  # True
    """
    LEFT = 0
    RIGHT = 1
    MIDDLE = 2
    X1 = 3
    X2 = 4

class InputState(IntEnum):
    """Input event states (pressed/released).

    These enum values compare equal to their legacy string equivalents
    for backwards compatibility:
        InputState.PRESSED == 'start'  # True
        InputState.RELEASED == 'end'  # True
    """
    PRESSED = 0
    RELEASED = 1

class Easing(IntEnum):
    """Easing functions for animations."""
    LINEAR = 0
    EASE_IN = 1
    EASE_OUT = 2
    EASE_IN_OUT = 3
    EASE_IN_QUAD = 4
    EASE_OUT_QUAD = 5
    EASE_IN_OUT_QUAD = 6
    EASE_IN_CUBIC = 7
    EASE_OUT_CUBIC = 8
    EASE_IN_OUT_CUBIC = 9
    EASE_IN_QUART = 10
    EASE_OUT_QUART = 11
    EASE_IN_OUT_QUART = 12
    EASE_IN_SINE = 13
    EASE_OUT_SINE = 14
    EASE_IN_OUT_SINE = 15
    EASE_IN_EXPO = 16
    EASE_OUT_EXPO = 17
    EASE_IN_OUT_EXPO = 18
    EASE_IN_CIRC = 19
    EASE_OUT_CIRC = 20
    EASE_IN_OUT_CIRC = 21
    EASE_IN_ELASTIC = 22
    EASE_OUT_ELASTIC = 23
    EASE_IN_OUT_ELASTIC = 24
    EASE_IN_BACK = 25
    EASE_OUT_BACK = 26
    EASE_IN_OUT_BACK = 27
    EASE_IN_BOUNCE = 28
    EASE_OUT_BOUNCE = 29
    EASE_IN_OUT_BOUNCE = 30

class FOV(IntEnum):
    """Field of view algorithms for visibility calculations."""
    BASIC = 0
    DIAMOND = 1
    SHADOW = 2
    PERMISSIVE_0 = 3
    PERMISSIVE_1 = 4
    PERMISSIVE_2 = 5
    PERMISSIVE_3 = 6
    PERMISSIVE_4 = 7
    PERMISSIVE_5 = 8
    PERMISSIVE_6 = 9
    PERMISSIVE_7 = 10
    PERMISSIVE_8 = 11
    RESTRICTIVE = 12
    SYMMETRIC_SHADOWCAST = 13

class Alignment(IntEnum):
    """Alignment positions for automatic child positioning relative to parent bounds.

    When a drawable has an alignment set and is added to a parent, its position
    is automatically calculated based on the parent's bounds. The position is
    updated whenever the parent is resized.

    Example:
        parent = mcrfpy.Frame(pos=(0, 0), size=(400, 300))
        child = mcrfpy.Caption(text="Centered!", align=mcrfpy.Alignment.CENTER)
        parent.children.append(child)  # child is auto-positioned to center
        parent.w = 800  # child position updates automatically

    Set align=None to disable automatic positioning and use manual coordinates.
    """
    TOP_LEFT = 0
    TOP_CENTER = 1
    TOP_RIGHT = 2
    CENTER_LEFT = 3
    CENTER = 4
    CENTER_RIGHT = 5
    BOTTOM_LEFT = 6
    BOTTOM_CENTER = 7
    BOTTOM_RIGHT = 8

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

class Mouse:
    """Mouse state singleton for reading button/position state and controlling cursor.

    Access via mcrfpy.mouse (singleton instance).
    Queries real-time mouse state from SFML. In headless mode, returns
    simulated position from mcrfpy.automation calls.
    """

    # Position (read-only)
    x: int
    """Current mouse X position in window coordinates (read-only)."""

    y: int
    """Current mouse Y position in window coordinates (read-only)."""

    pos: Vector
    """Current mouse position as Vector (read-only)."""

    # Button state (read-only)
    left: bool
    """True if left mouse button is currently pressed (read-only)."""

    right: bool
    """True if right mouse button is currently pressed (read-only)."""

    middle: bool
    """True if middle mouse button is currently pressed (read-only)."""

    # Cursor control (read-write)
    visible: bool
    """Whether the mouse cursor is visible (default: True)."""

    grabbed: bool
    """Whether the mouse cursor is confined to the window (default: False)."""

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

    # Alignment system - automatic positioning relative to parent
    align: Optional[Alignment]
    """Alignment relative to parent bounds. Set to None for manual positioning."""
    margin: float
    """General margin from edge when aligned (applies to both axes unless overridden)."""
    horiz_margin: float
    """Horizontal margin override (0 = use general margin)."""
    vert_margin: float
    """Vertical margin override (0 = use general margin)."""

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
                 children: Optional[List[UIElement]] = None,
                 visible: bool = True, opacity: float = 1.0, z_index: int = 0,
                 name: Optional[str] = None, pos: Optional[Tuple[float, float]] = None,
                 size: Optional[Tuple[float, float]] = None,
                 align: Optional[Alignment] = None, margin: float = 0.0,
                 horiz_margin: float = 0.0, vert_margin: float = 0.0) -> None: ...

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
                 on_click: Optional[Callable] = None,
                 visible: bool = True, opacity: float = 1.0, z_index: int = 0,
                 name: Optional[str] = None, pos: Optional[Tuple[float, float]] = None,
                 size: Optional[Tuple[float, float]] = None,
                 align: Optional[Alignment] = None, margin: float = 0.0,
                 horiz_margin: float = 0.0, vert_margin: float = 0.0) -> None: ...

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
                 on_click: Optional[Callable] = None,
                 visible: bool = True, opacity: float = 1.0, z_index: int = 0,
                 name: Optional[str] = None, pos: Optional[Tuple[float, float]] = None,
                 size: Optional[Tuple[float, float]] = None,
                 align: Optional[Alignment] = None, margin: float = 0.0,
                 horiz_margin: float = 0.0, vert_margin: float = 0.0) -> None: ...

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
                 scale: float = 1.0, on_click: Optional[Callable] = None,
                 visible: bool = True, opacity: float = 1.0, z_index: int = 0,
                 name: Optional[str] = None, pos: Optional[Tuple[float, float]] = None,
                 size: Optional[Tuple[float, float]] = None,
                 align: Optional[Alignment] = None, margin: float = 0.0,
                 horiz_margin: float = 0.0, vert_margin: float = 0.0) -> None: ...

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
                 on_click: Optional[Callable] = None,
                 visible: bool = True, opacity: float = 1.0, z_index: int = 0,
                 name: Optional[str] = None,
                 align: Optional[Alignment] = None, margin: float = 0.0,
                 horiz_margin: float = 0.0, vert_margin: float = 0.0) -> None: ...

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
                 outline: float = 0, on_click: Optional[Callable] = None,
                 visible: bool = True, opacity: float = 1.0, z_index: int = 0,
                 name: Optional[str] = None,
                 align: Optional[Alignment] = None, margin: float = 0.0,
                 horiz_margin: float = 0.0, vert_margin: float = 0.0) -> None: ...

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
                 on_click: Optional[Callable] = None,
                 visible: bool = True, opacity: float = 1.0, z_index: int = 0,
                 name: Optional[str] = None,
                 align: Optional[Alignment] = None, margin: float = 0.0,
                 horiz_margin: float = 0.0, vert_margin: float = 0.0) -> None: ...

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

mouse: Mouse
"""Mouse state singleton for reading button/position state and controlling cursor."""

window: Window
"""Window singleton for controlling window properties."""

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
