"""Type stubs for McRogueFace Python API.

Core game engine interface for creating roguelike games with Python.
"""

from typing import Any, List, Dict, Tuple, Optional, Callable, Union, overload

# Type aliases
UIElement = Union['Frame', 'Caption', 'Sprite', 'Grid']
Transition = Union[str, None]

# Classes

class Color:
    """SFML Color Object for RGBA colors."""
    
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

class Drawable:
    """Base class for all drawable UI elements."""
    
    x: float
    y: float
    visible: bool
    z_index: int
    name: str
    pos: Vector
    
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
    """Frame(x=0, y=0, w=0, h=0, fill_color=None, outline_color=None, outline=0, click=None, children=None)
    
    A rectangular frame UI element that can contain other drawable elements.
    """
    
    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, x: float = 0, y: float = 0, w: float = 0, h: float = 0,
                 fill_color: Optional[Color] = None, outline_color: Optional[Color] = None,
                 outline: float = 0, click: Optional[Callable] = None,
                 children: Optional[List[UIElement]] = None) -> None: ...
    
    w: float
    h: float
    fill_color: Color
    outline_color: Color
    outline: float
    click: Optional[Callable[[float, float, int], None]]
    children: 'UICollection'
    clip_children: bool

class Caption(Drawable):
    """Caption(text='', x=0, y=0, font=None, fill_color=None, outline_color=None, outline=0, click=None)
    
    A text display UI element with customizable font and styling.
    """
    
    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, text: str = '', x: float = 0, y: float = 0,
                 font: Optional[Font] = None, fill_color: Optional[Color] = None,
                 outline_color: Optional[Color] = None, outline: float = 0,
                 click: Optional[Callable] = None) -> None: ...
    
    text: str
    font: Font
    fill_color: Color
    outline_color: Color
    outline: float
    click: Optional[Callable[[float, float, int], None]]
    w: float  # Read-only, computed from text
    h: float  # Read-only, computed from text

class Sprite(Drawable):
    """Sprite(x=0, y=0, texture=None, sprite_index=0, scale=1.0, click=None)
    
    A sprite UI element that displays a texture or portion of a texture atlas.
    """
    
    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, x: float = 0, y: float = 0, texture: Optional[Texture] = None,
                 sprite_index: int = 0, scale: float = 1.0,
                 click: Optional[Callable] = None) -> None: ...
    
    texture: Texture
    sprite_index: int
    scale: float
    click: Optional[Callable[[float, float, int], None]]
    w: float  # Read-only, computed from texture
    h: float  # Read-only, computed from texture

class Grid(Drawable):
    """Grid(x=0, y=0, grid_size=(20, 20), texture=None, tile_width=16, tile_height=16, scale=1.0, click=None)
    
    A grid-based tilemap UI element for rendering tile-based levels and game worlds.
    """
    
    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, x: float = 0, y: float = 0, grid_size: Tuple[int, int] = (20, 20),
                 texture: Optional[Texture] = None, tile_width: int = 16, tile_height: int = 16,
                 scale: float = 1.0, click: Optional[Callable] = None) -> None: ...
    
    grid_size: Tuple[int, int]
    tile_width: int
    tile_height: int
    texture: Texture
    scale: float
    points: List[List['GridPoint']]
    entities: 'EntityCollection'
    background_color: Color
    click: Optional[Callable[[int, int, int], None]]
    
    def at(self, x: int, y: int) -> 'GridPoint':
        """Get grid point at tile coordinates."""
        ...

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
    """Collection of UI drawable elements (Frame, Caption, Sprite, Grid)."""
    
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
        """Handle keyboard events."""
        ...
    
    def on_click(self, x: float, y: float, button: int) -> None:
        """Handle mouse clicks."""
        ...
    
    def on_enter(self) -> None:
        """Called when entering the scene."""
        ...
    
    def on_exit(self) -> None:
        """Called when leaving the scene."""
        ...
    
    def on_resize(self, width: int, height: int) -> None:
        """Handle window resize events."""
        ...
    
    def update(self, dt: float) -> None:
        """Update scene logic."""
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
    """Animation object for animating UI properties."""
    
    target: Any
    property: str
    duration: float
    easing: str
    loop: bool
    on_complete: Optional[Callable]
    
    def __init__(self, target: Any, property: str, start_value: Any, end_value: Any,
                 duration: float, easing: str = 'linear', loop: bool = False,
                 on_complete: Optional[Callable] = None) -> None: ...
    
    def start(self) -> None:
        """Start the animation."""
        ...
    
    def update(self, dt: float) -> bool:
        """Update animation, returns True if still running."""
        ...
    
    def get_current_value(self) -> Any:
        """Get the current interpolated value."""
        ...

# Module functions

def createSoundBuffer(filename: str) -> int:
    """Load a sound effect from a file and return its buffer ID."""
    ...

def loadMusic(filename: str) -> None:
    """Load and immediately play background music from a file."""
    ...

def setMusicVolume(volume: int) -> None:
    """Set the global music volume (0-100)."""
    ...

def setSoundVolume(volume: int) -> None:
    """Set the global sound effects volume (0-100)."""
    ...

def playSound(buffer_id: int) -> None:
    """Play a sound effect using a previously loaded buffer."""
    ...

def getMusicVolume() -> int:
    """Get the current music volume level (0-100)."""
    ...

def getSoundVolume() -> int:
    """Get the current sound effects volume level (0-100)."""
    ...

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
