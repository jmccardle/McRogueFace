"""Type stubs for McRogueFace Python API.

Core game engine interface for creating roguelike games with Python.
"""

from typing import Any, List, Dict, Tuple, Optional, Callable, Union, overload

# Type aliases
UIElement = Union['Frame', 'Caption', 'Sprite', 'Grid', 'Line', 'Circle', 'Arc']
Transition = Union[str, None]

# Enums

class Key:
    """Keyboard key codes enum.

    All standard keyboard keys are available as class attributes:
    A-Z, Num0-Num9, F1-F15, Arrow keys, modifiers, etc.
    """
    A: 'Key'
    B: 'Key'
    C: 'Key'
    # ... (all letters A-Z)
    Num0: 'Key'
    Num1: 'Key'
    Num2: 'Key'
    # ... (Num0-Num9)
    ESCAPE: 'Key'
    ENTER: 'Key'
    SPACE: 'Key'
    TAB: 'Key'
    BACKSPACE: 'Key'
    DELETE: 'Key'
    UP: 'Key'
    DOWN: 'Key'
    LEFT: 'Key'
    RIGHT: 'Key'
    LSHIFT: 'Key'
    RSHIFT: 'Key'
    LCTRL: 'Key'
    RCTRL: 'Key'
    LALT: 'Key'
    RALT: 'Key'
    # ... (additional keys)

class MouseButton:
    """Mouse button enum for click callbacks."""
    LEFT: 'MouseButton'
    RIGHT: 'MouseButton'
    MIDDLE: 'MouseButton'

class InputState:
    """Input action state enum for callbacks."""
    PRESSED: 'InputState'
    RELEASED: 'InputState'

class Easing:
    """Animation easing function enum.

    Available easing functions for smooth animations.
    """
    LINEAR: 'Easing'
    EASE_IN: 'Easing'
    EASE_OUT: 'Easing'
    EASE_IN_OUT: 'Easing'
    EASE_IN_QUAD: 'Easing'
    EASE_OUT_QUAD: 'Easing'
    EASE_IN_OUT_QUAD: 'Easing'
    EASE_IN_CUBIC: 'Easing'
    EASE_OUT_CUBIC: 'Easing'
    EASE_IN_OUT_CUBIC: 'Easing'
    EASE_IN_QUART: 'Easing'
    EASE_OUT_QUART: 'Easing'
    EASE_IN_OUT_QUART: 'Easing'
    EASE_IN_SINE: 'Easing'
    EASE_OUT_SINE: 'Easing'
    EASE_IN_OUT_SINE: 'Easing'
    EASE_IN_EXPO: 'Easing'
    EASE_OUT_EXPO: 'Easing'
    EASE_IN_OUT_EXPO: 'Easing'
    EASE_IN_CIRC: 'Easing'
    EASE_OUT_CIRC: 'Easing'
    EASE_IN_OUT_CIRC: 'Easing'
    EASE_IN_ELASTIC: 'Easing'
    EASE_OUT_ELASTIC: 'Easing'
    EASE_IN_OUT_ELASTIC: 'Easing'
    EASE_IN_BACK: 'Easing'
    EASE_OUT_BACK: 'Easing'
    EASE_IN_OUT_BACK: 'Easing'
    EASE_IN_BOUNCE: 'Easing'
    EASE_OUT_BOUNCE: 'Easing'
    EASE_IN_OUT_BOUNCE: 'Easing'

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

    # Mouse event callbacks (#140, #141, #230)
    # on_click receives (pos: Vector, button: MouseButton, action: InputState)
    on_click: Optional[Callable[['Vector', 'MouseButton', 'InputState'], None]]
    # Hover callbacks receive only position per #230
    on_enter: Optional[Callable[['Vector'], None]]
    on_exit: Optional[Callable[['Vector'], None]]
    on_move: Optional[Callable[['Vector'], None]]

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
    """Grid(pos=(0,0), size=(0,0), grid_size=(2,2), texture=None, ...)

    A grid-based tilemap UI element for rendering tile-based levels and game worlds.
    Supports layers, FOV, pathfinding, and entity management.
    """

    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, pos: Tuple[float, float] = (0, 0),
                 size: Tuple[float, float] = (0, 0),
                 grid_size: Tuple[int, int] = (2, 2),
                 texture: Optional[Texture] = None,
                 fill_color: Optional[Color] = None,
                 on_click: Optional[Callable] = None,
                 center_x: float = 0, center_y: float = 0, zoom: float = 1.0,
                 visible: bool = True, opacity: float = 1.0,
                 z_index: int = 0, name: str = '') -> None: ...

    # Dimensions
    grid_size: Tuple[int, int]  # Read-only (grid_w, grid_h)
    grid_w: int  # Read-only
    grid_h: int  # Read-only

    # Position and size
    position: Tuple[float, float]
    size: Vector
    w: float
    h: float

    # Camera/viewport
    center: Vector  # Viewport center point (pan position)
    center_x: float
    center_y: float
    zoom: float  # Scale factor for rendering

    # Collections
    entities: 'EntityCollection'  # Entities on this grid
    children: 'UICollection'  # UI overlays (speech bubbles, effects)
    layers: List[Union['ColorLayer', 'TileLayer']]  # Grid layers sorted by z_index

    # Appearance
    texture: Texture  # Read-only
    fill_color: Color  # Background fill color

    # Perspective/FOV
    perspective: Optional['Entity']  # Entity for FOV rendering (None = omniscient)
    perspective_enabled: bool  # Whether to use perspective-based FOV
    fov: 'FOV'  # FOV algorithm enum
    fov_radius: int  # Default FOV radius

    # Cell-level mouse events (#230)
    # on_cell_click receives (cell_pos: Vector, button: MouseButton, action: InputState)
    on_cell_click: Optional[Callable[['Vector', 'MouseButton', 'InputState'], None]]
    # Cell hover callbacks receive only position per #230
    on_cell_enter: Optional[Callable[['Vector'], None]]
    on_cell_exit: Optional[Callable[['Vector'], None]]
    hovered_cell: Optional[Tuple[int, int]]  # Read-only

    def at(self, x: int, y: int) -> 'GridPoint':
        """Get grid point at tile coordinates."""
        ...

    def center_camera(self, pos: Optional[Tuple[float, float]] = None) -> None:
        """Center the camera on a tile coordinate."""
        ...

    # FOV methods
    def compute_fov(self, pos: Tuple[int, int], radius: int = 0,
                    light_walls: bool = True, algorithm: Optional['FOV'] = None) -> None:
        """Compute field of view from a position."""
        ...

    def is_in_fov(self, pos: Tuple[int, int]) -> bool:
        """Check if a cell is in the field of view."""
        ...

    # Pathfinding methods
    def find_path(self, start: Union[Tuple[int, int], 'Vector', 'Entity'],
                  end: Union[Tuple[int, int], 'Vector', 'Entity'],
                  diagonal_cost: float = 1.41) -> Optional['AStarPath']:
        """Compute A* path between two points."""
        ...

    def get_dijkstra_map(self, root: Union[Tuple[int, int], 'Vector', 'Entity'],
                         diagonal_cost: float = 1.41) -> 'DijkstraMap':
        """Get or create a Dijkstra distance map for a root position."""
        ...

    def clear_dijkstra_maps(self) -> None:
        """Clear all cached Dijkstra maps."""
        ...

    # Layer methods
    def add_layer(self, type: str, z_index: int = -1,
                  texture: Optional[Texture] = None) -> Union['ColorLayer', 'TileLayer']:
        """Add a new layer to the grid."""
        ...

    def remove_layer(self, layer: Union['ColorLayer', 'TileLayer']) -> None:
        """Remove a layer from the grid."""
        ...

    def layer(self, z_index: int) -> Optional[Union['ColorLayer', 'TileLayer']]:
        """Get layer by z_index."""
        ...

    # Spatial queries
    def entities_in_radius(self, pos: Union[Tuple[float, float], 'Vector'],
                           radius: float) -> List['Entity']:
        """Query entities within radius using spatial hash."""
        ...

    # HeightMap application
    def apply_threshold(self, source: 'HeightMap', range: Tuple[float, float],
                        walkable: Optional[bool] = None,
                        transparent: Optional[bool] = None) -> 'Grid':
        """Apply walkable/transparent properties where heightmap values are in range."""
        ...

    def apply_ranges(self, source: 'HeightMap',
                     ranges: List[Tuple[Tuple[float, float], Dict[str, bool]]]) -> 'Grid':
        """Apply multiple thresholds in a single pass."""
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
    """Grid point representing a single tile's properties.

    Accessed via Grid.at(x, y). Controls walkability and transparency
    for pathfinding and FOV calculations.
    """

    walkable: bool  # Whether entities can walk through this cell
    transparent: bool  # Whether light/sight passes through this cell
    entities: List['Entity']  # Read-only list of entities at this cell
    grid_pos: Tuple[int, int]  # Read-only (x, y) position in grid

class GridPointState:
    """Per-entity visibility state for a grid cell.

    Tracks what an entity has seen/discovered. Accessed via entity perspective system.
    """

    visible: bool  # Currently visible in FOV
    discovered: bool  # Has been seen at least once
    point: Optional['GridPoint']  # The GridPoint at this position (None if not discovered)

class ColorLayer:
    """A color overlay layer for Grid.

    Provides per-cell color values for tinting, fog of war, etc.
    """

    z_index: int
    grid: 'Grid'  # Read-only parent grid

    def fill(self, color: Color) -> None:
        """Fill entire layer with a single color."""
        ...

    def set_color(self, pos: Tuple[int, int], color: Color) -> None:
        """Set color at a specific cell."""
        ...

    def get_color(self, pos: Tuple[int, int]) -> Color:
        """Get color at a specific cell."""
        ...

class TileLayer:
    """A tile sprite layer for Grid.

    Provides per-cell tile indices for multi-layer tile rendering.
    """

    z_index: int
    grid: 'Grid'  # Read-only parent grid
    texture: Optional[Texture]

    def fill(self, tile_index: int) -> None:
        """Fill entire layer with a single tile index."""
        ...

    def set_tile(self, pos: Tuple[int, int], tile_index: int) -> None:
        """Set tile index at a specific cell."""
        ...

    def get_tile(self, pos: Tuple[int, int]) -> int:
        """Get tile index at a specific cell."""
        ...

class FOV:
    """Field of view algorithm enum.

    Available algorithms:
    - FOV.BASIC: Simple raycasting
    - FOV.DIAMOND: Diamond-shaped FOV
    - FOV.SHADOW: Shadow casting (recommended)
    - FOV.PERMISSIVE_0 through FOV.PERMISSIVE_8: Permissive algorithms
    - FOV.RESTRICTIVE: Restrictive precise angle shadowcasting
    """

    BASIC: 'FOV'
    DIAMOND: 'FOV'
    SHADOW: 'FOV'
    PERMISSIVE_0: 'FOV'
    PERMISSIVE_1: 'FOV'
    PERMISSIVE_2: 'FOV'
    PERMISSIVE_3: 'FOV'
    PERMISSIVE_4: 'FOV'
    PERMISSIVE_5: 'FOV'
    PERMISSIVE_6: 'FOV'
    PERMISSIVE_7: 'FOV'
    PERMISSIVE_8: 'FOV'
    RESTRICTIVE: 'FOV'

class AStarPath:
    """A* pathfinding result.

    Returned by Grid.find_path(). Can be iterated or walked step-by-step.
    """

    def __iter__(self) -> Any: ...
    def __len__(self) -> int: ...

    def walk(self) -> Optional[Tuple[int, int]]:
        """Get next step in path, or None if complete."""
        ...

    def reverse(self) -> 'AStarPath':
        """Return a reversed copy of the path."""
        ...

class DijkstraMap:
    """Dijkstra distance map for pathfinding.

    Created by Grid.get_dijkstra_map(). Provides distance queries
    and path finding from the root position.
    """

    root: Tuple[int, int]  # Read-only root position

    def get_distance(self, pos: Tuple[int, int]) -> float:
        """Get distance from root to position (-1 if unreachable)."""
        ...

    def get_path(self, pos: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
        """Get path from position to root."""
        ...

class HeightMap:
    """2D height field for terrain generation.

    Used for procedural generation and applying terrain to grids.
    """

    width: int  # Read-only
    height: int  # Read-only

    def __init__(self, width: int, height: int) -> None: ...

    def get(self, x: int, y: int) -> float:
        """Get height value at position."""
        ...

    def set(self, x: int, y: int, value: float) -> None:
        """Set height value at position."""
        ...

    def fill(self, value: float) -> 'HeightMap':
        """Fill entire heightmap with a value."""
        ...

    def clear(self) -> 'HeightMap':
        """Clear heightmap to 0."""
        ...

    def normalize(self, min_val: float = 0.0, max_val: float = 1.0) -> 'HeightMap':
        """Normalize values to range."""
        ...

    def add_hill(self, center: Tuple[float, float], radius: float, height: float) -> 'HeightMap':
        """Add a hill at position."""
        ...

    def add_fbm(self, noise: 'NoiseSource', mulx: float = 1.0, muly: float = 1.0,
                addx: float = 0.0, addy: float = 0.0, octaves: int = 4,
                delta: float = 1.0, scale: float = 1.0) -> 'HeightMap':
        """Add fractal Brownian motion noise."""
        ...

    def scale(self, factor: float) -> 'HeightMap':
        """Scale all values by factor."""
        ...

    def clamp(self, min_val: float, max_val: float) -> 'HeightMap':
        """Clamp values to range."""
        ...

class NoiseSource:
    """Coherent noise generator for procedural generation.

    Supports various noise types: PERLIN, SIMPLEX, WAVELET, etc.
    """

    def __init__(self, type: str = 'SIMPLEX', seed: Optional[int] = None) -> None: ...

    def get(self, x: float, y: float, z: float = 0.0) -> float:
        """Get noise value at position."""
        ...

class BSP:
    """Binary space partitioning for dungeon generation.

    Recursively subdivides a rectangle into rooms.
    """

    x: int
    y: int
    width: int
    height: int
    level: int
    horizontal: bool
    position: int

    def __init__(self, x: int, y: int, width: int, height: int) -> None: ...

    def split_recursive(self, randomizer: Optional[Any] = None, nb: int = 8,
                        minHSize: int = 4, minVSize: int = 4,
                        maxHRatio: float = 1.5, maxVRatio: float = 1.5) -> None:
        """Recursively split the BSP tree."""
        ...

    def traverse(self, callback: Callable[['BSP'], bool],
                 order: str = 'PRE_ORDER') -> None:
        """Traverse BSP tree calling callback for each node."""
        ...

    def is_leaf(self) -> bool:
        """Check if this is a leaf node (no children)."""
        ...

    def contains(self, x: int, y: int) -> bool:
        """Check if point is within this node's bounds."""
        ...

    def get_left(self) -> Optional['BSP']:
        """Get left child node."""
        ...

    def get_right(self) -> Optional['BSP']:
        """Get right child node."""
        ...

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
    # Keyboard handler receives (key: Key, action: InputState) per #184
    on_key: Optional[Callable[['Key', 'InputState'], None]]

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
    """Animation object for animating UI properties.

    Note: The preferred way to create animations is via the .animate() method
    on drawable objects:
        frame.animate("x", 500.0, 2.0, mcrfpy.Easing.EASE_IN_OUT)

    Animation callbacks (#229) receive (target, property, final_value):
        def on_complete(target, prop, value):
            print(f"{type(target).__name__}.{prop} = {value}")
    """

    property: str
    duration: float
    easing: 'Easing'
    # Callback receives (target: Any, property: str, final_value: Any) per #229
    callback: Optional[Callable[[Any, str, Any], None]]

    def __init__(self, property: str, end_value: Any, duration: float,
                 easing: Union[str, 'Easing'] = 'linear',
                 callback: Optional[Callable[[Any, str, Any], None]] = None) -> None: ...

    def start(self, target: Any) -> None:
        """Start the animation on a target object."""
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
    """Set the keyboard event handler for the current scene.

    DEPRECATED: Use scene.on_key = handler instead.
    The new handler receives (key: Key, action: InputState) enums.
    """
    ...

def setTimer(name: str, handler: Callable[[float], None], interval: int) -> None:
    """Create or update a recurring timer.

    DEPRECATED: Use Timer(name, callback, interval) object instead.
    """
    ...

def delTimer(name: str) -> None:
    """Stop and remove a timer.

    DEPRECATED: Use timer.cancel() method instead.
    """
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
