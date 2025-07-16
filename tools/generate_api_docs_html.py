#!/usr/bin/env python3
"""Generate high-quality HTML API reference documentation for McRogueFace."""

import os
import sys
import datetime
import html
from pathlib import Path
import mcrfpy

def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return html.escape(text) if text else ""

def format_docstring_as_html(docstring: str) -> str:
    """Convert docstring to properly formatted HTML."""
    if not docstring:
        return ""
    
    # Split and process lines
    lines = docstring.strip().split('\n')
    result = []
    in_code_block = False
    
    for line in lines:
        # Convert \n to actual newlines
        line = line.replace('\\n', '\n')
        
        # Handle code blocks
        if line.strip().startswith('```'):
            if in_code_block:
                result.append('</pre></code>')
                in_code_block = False
            else:
                result.append('<code><pre>')
                in_code_block = True
            continue
            
        # Convert markdown-style code to HTML
        if '`' in line and not in_code_block:
            import re
            line = re.sub(r'`([^`]+)`', r'<code>\1</code>', line)
        
        if in_code_block:
            result.append(escape_html(line))
        else:
            result.append(escape_html(line) + '<br>')
    
    if in_code_block:
        result.append('</pre></code>')
    
    return '\n'.join(result)

def get_class_details(cls):
    """Get detailed information about a class."""
    info = {
        'name': cls.__name__,
        'doc': cls.__doc__ or "",
        'methods': {},
        'properties': {},
        'bases': []
    }
    
    # Get real base classes (excluding object)
    for base in cls.__bases__:
        if base.__name__ != 'object':
            info['bases'].append(base.__name__)
    
    # Special handling for Entity which doesn't inherit from Drawable
    if cls.__name__ == 'Entity' and 'Drawable' in info['bases']:
        info['bases'].remove('Drawable')
    
    # Get methods and properties
    for attr_name in dir(cls):
        if attr_name.startswith('__') and attr_name != '__init__':
            continue
            
        try:
            attr = getattr(cls, attr_name)
            
            if isinstance(attr, property):
                info['properties'][attr_name] = {
                    'doc': (attr.fget.__doc__ if attr.fget else "") or "",
                    'readonly': attr.fset is None
                }
            elif callable(attr) and not attr_name.startswith('_'):
                info['methods'][attr_name] = attr.__doc__ or ""
        except:
            pass
    
    return info

def generate_class_init_docs(class_name):
    """Generate initialization documentation for specific classes."""
    init_docs = {
        'Entity': {
            'signature': 'Entity(x=0, y=0, sprite_id=0)',
            'description': 'Game entity that can be placed in a Grid.',
            'args': [
                ('x', 'int', 'Grid x coordinate. Default: 0'),
                ('y', 'int', 'Grid y coordinate. Default: 0'),
                ('sprite_id', 'int', 'Sprite index for rendering. Default: 0')
            ],
            'example': '''entity = mcrfpy.Entity(5, 10, 42)
entity.move(1, 0)  # Move right one tile'''
        },
        'Color': {
            'signature': 'Color(r=255, g=255, b=255, a=255)',
            'description': 'RGBA color representation.',
            'args': [
                ('r', 'int', 'Red component (0-255). Default: 255'),
                ('g', 'int', 'Green component (0-255). Default: 255'),
                ('b', 'int', 'Blue component (0-255). Default: 255'),
                ('a', 'int', 'Alpha component (0-255). Default: 255')
            ],
            'example': 'red = mcrfpy.Color(255, 0, 0)'
        },
        'Font': {
            'signature': 'Font(filename)',
            'description': 'Load a font from file.',
            'args': [
                ('filename', 'str', 'Path to font file (TTF/OTF)')
            ]
        },
        'Texture': {
            'signature': 'Texture(filename)',
            'description': 'Load a texture from file.',
            'args': [
                ('filename', 'str', 'Path to image file (PNG/JPG/BMP)')
            ]
        },
        'Vector': {
            'signature': 'Vector(x=0.0, y=0.0)',
            'description': '2D vector for positions and directions.',
            'args': [
                ('x', 'float', 'X component. Default: 0.0'),
                ('y', 'float', 'Y component. Default: 0.0')
            ]
        },
        'Animation': {
            'signature': 'Animation(property_name, start_value, end_value, duration, transition="linear", loop=False)',
            'description': 'Animate UI element properties over time.',
            'args': [
                ('property_name', 'str', 'Property to animate (e.g., "x", "y", "scale")'),
                ('start_value', 'float', 'Starting value'),
                ('end_value', 'float', 'Ending value'),
                ('duration', 'float', 'Duration in seconds'),
                ('transition', 'str', 'Easing function. Default: "linear"'),
                ('loop', 'bool', 'Whether to loop. Default: False')
            ],
            'properties': ['current_value', 'elapsed_time', 'is_running', 'is_finished']
        },
        'GridPoint': {
            'description': 'Represents a single tile in a Grid.',
            'properties': ['x', 'y', 'texture_index', 'solid', 'transparent', 'color']
        },
        'GridPointState': {
            'description': 'State information for a GridPoint.',
            'properties': ['visible', 'discovered', 'custom_flags']
        },
        'Timer': {
            'signature': 'Timer(name, callback, interval_ms)',
            'description': 'Create a recurring timer.',
            'args': [
                ('name', 'str', 'Unique timer identifier'),
                ('callback', 'callable', 'Function to call'),
                ('interval_ms', 'int', 'Interval in milliseconds')
            ]
        }
    }
    
    return init_docs.get(class_name, {})

def generate_method_docs(method_name, class_name):
    """Generate documentation for specific methods."""
    method_docs = {
        # Base Drawable methods (inherited by all UI elements)
        'Drawable': {
            'get_bounds': {
                'signature': 'get_bounds()',
                'description': 'Get the bounding rectangle of this drawable element.',
                'returns': 'tuple: (x, y, width, height) representing the element\'s bounds',
                'note': 'The bounds are in screen coordinates and account for current position and size.'
            },
            'move': {
                'signature': 'move(dx, dy)',
                'description': 'Move the element by a relative offset.',
                'args': [
                    ('dx', 'float', 'Horizontal offset in pixels'),
                    ('dy', 'float', 'Vertical offset in pixels')
                ],
                'note': 'This modifies the x and y position properties by the given amounts.'
            },
            'resize': {
                'signature': 'resize(width, height)',
                'description': 'Resize the element to new dimensions.',
                'args': [
                    ('width', 'float', 'New width in pixels'),
                    ('height', 'float', 'New height in pixels')
                ],
                'note': 'Behavior varies by element type. Some elements may ignore or constrain dimensions.'
            }
        },
        
        # Caption-specific methods
        'Caption': {
            'get_bounds': {
                'signature': 'get_bounds()',
                'description': 'Get the bounding rectangle of the text.',
                'returns': 'tuple: (x, y, width, height) based on text content and font size',
                'note': 'Bounds are automatically calculated from the rendered text dimensions.'
            },
            'move': {
                'signature': 'move(dx, dy)',
                'description': 'Move the caption by a relative offset.',
                'args': [
                    ('dx', 'float', 'Horizontal offset in pixels'),
                    ('dy', 'float', 'Vertical offset in pixels')
                ]
            },
            'resize': {
                'signature': 'resize(width, height)',
                'description': 'Set text wrapping bounds (limited support).',
                'args': [
                    ('width', 'float', 'Maximum width for text wrapping'),
                    ('height', 'float', 'Currently unused')
                ],
                'note': 'Full text wrapping is not yet implemented. This prepares for future multiline support.'
            }
        },
        
        # Entity-specific methods
        'Entity': {
            'at': {
                'signature': 'at(x, y)',
                'description': 'Get the GridPointState at the specified grid coordinates relative to this entity.',
                'args': [
                    ('x', 'int', 'Grid x offset from entity position'),
                    ('y', 'int', 'Grid y offset from entity position')
                ],
                'returns': 'GridPointState: State of the grid point at the specified position',
                'note': 'Requires entity to be associated with a grid. Raises ValueError if not.'
            },
            'die': {
                'signature': 'die()',
                'description': 'Remove this entity from its parent grid.',
                'returns': 'None',
                'note': 'The entity object remains valid but is no longer rendered or updated.'
            },
            'index': {
                'signature': 'index()',
                'description': 'Get the index of this entity in its grid\'s entity collection.',
                'returns': 'int: Zero-based index in the parent grid\'s entity list',
                'note': 'Raises RuntimeError if not associated with a grid, ValueError if not found.'
            },
            'get_bounds': {
                'signature': 'get_bounds()',
                'description': 'Get the bounding rectangle of the entity\'s sprite.',
                'returns': 'tuple: (x, y, width, height) of the sprite bounds',
                'note': 'Delegates to the internal sprite\'s get_bounds method.'
            },
            'move': {
                'signature': 'move(dx, dy)',
                'description': 'Move the entity by a relative offset in pixels.',
                'args': [
                    ('dx', 'float', 'Horizontal offset in pixels'),
                    ('dy', 'float', 'Vertical offset in pixels')
                ],
                'note': 'Updates both sprite position and entity grid position.'
            },
            'resize': {
                'signature': 'resize(width, height)',
                'description': 'Entities do not support direct resizing.',
                'args': [
                    ('width', 'float', 'Ignored'),
                    ('height', 'float', 'Ignored')
                ],
                'note': 'This method exists for interface compatibility but has no effect.'
            }
        },
        
        # Frame-specific methods
        'Frame': {
            'get_bounds': {
                'signature': 'get_bounds()',
                'description': 'Get the bounding rectangle of the frame.',
                'returns': 'tuple: (x, y, width, height) representing the frame bounds'
            },
            'move': {
                'signature': 'move(dx, dy)',
                'description': 'Move the frame and all its children by a relative offset.',
                'args': [
                    ('dx', 'float', 'Horizontal offset in pixels'),
                    ('dy', 'float', 'Vertical offset in pixels')
                ],
                'note': 'Child elements maintain their relative positions within the frame.'
            },
            'resize': {
                'signature': 'resize(width, height)',
                'description': 'Resize the frame to new dimensions.',
                'args': [
                    ('width', 'float', 'New width in pixels'),
                    ('height', 'float', 'New height in pixels')
                ],
                'note': 'Does not automatically resize children. Set clip_children=True to clip overflow.'
            }
        },
        
        # Grid-specific methods
        'Grid': {
            'at': {
                'signature': 'at(x, y) or at((x, y))',
                'description': 'Get the GridPoint at the specified grid coordinates.',
                'args': [
                    ('x', 'int', 'Grid x coordinate (0-based)'),
                    ('y', 'int', 'Grid y coordinate (0-based)')
                ],
                'returns': 'GridPoint: The grid point at (x, y)',
                'note': 'Raises IndexError if coordinates are out of range. Accepts either two arguments or a tuple.',
                'example': 'point = grid.at(5, 3)  # or grid.at((5, 3))'
            },
            'get_bounds': {
                'signature': 'get_bounds()',
                'description': 'Get the bounding rectangle of the entire grid.',
                'returns': 'tuple: (x, y, width, height) of the grid\'s display area'
            },
            'move': {
                'signature': 'move(dx, dy)',
                'description': 'Move the grid display by a relative offset.',
                'args': [
                    ('dx', 'float', 'Horizontal offset in pixels'),
                    ('dy', 'float', 'Vertical offset in pixels')
                ],
                'note': 'Moves the entire grid viewport. Use center property to pan within the grid.'
            },
            'resize': {
                'signature': 'resize(width, height)',
                'description': 'Resize the grid\'s display viewport.',
                'args': [
                    ('width', 'float', 'New viewport width in pixels'),
                    ('height', 'float', 'New viewport height in pixels')
                ],
                'note': 'Changes the visible area, not the grid dimensions. Use zoom to scale content.'
            }
        },
        
        # Sprite-specific methods
        'Sprite': {
            'get_bounds': {
                'signature': 'get_bounds()',
                'description': 'Get the bounding rectangle of the sprite.',
                'returns': 'tuple: (x, y, width, height) based on texture size and scale',
                'note': 'Bounds account for current scale. Returns (x, y, 0, 0) if no texture.'
            },
            'move': {
                'signature': 'move(dx, dy)',
                'description': 'Move the sprite by a relative offset.',
                'args': [
                    ('dx', 'float', 'Horizontal offset in pixels'),
                    ('dy', 'float', 'Vertical offset in pixels')
                ]
            },
            'resize': {
                'signature': 'resize(width, height)',
                'description': 'Resize the sprite by adjusting its scale.',
                'args': [
                    ('width', 'float', 'Target width in pixels'),
                    ('height', 'float', 'Target height in pixels')
                ],
                'note': 'Calculates and applies uniform scale to best fit the target dimensions.'
            }
        },
        
        'Animation': {
            'get_current_value': {
                'signature': 'get_current_value()',
                'description': 'Get the current interpolated value.',
                'returns': 'float: Current animation value'
            },
            'start': {
                'signature': 'start(target)',
                'description': 'Start the animation on a target UI element.',
                'args': [('target', 'UIDrawable', 'The element to animate')]
            }
        },
        
        # Collection methods (shared by EntityCollection and UICollection)
        'EntityCollection': {
            'append': {
                'signature': 'append(entity)',
                'description': 'Add an entity to the end of the collection.',
                'args': [
                    ('entity', 'Entity', 'The entity to add')
                ]
            },
            'remove': {
                'signature': 'remove(entity)',
                'description': 'Remove the first occurrence of an entity from the collection.',
                'args': [
                    ('entity', 'Entity', 'The entity to remove')
                ],
                'note': 'Raises ValueError if entity is not found.'
            },
            'extend': {
                'signature': 'extend(iterable)',
                'description': 'Add multiple entities from an iterable.',
                'args': [
                    ('iterable', 'iterable', 'An iterable of Entity objects')
                ]
            },
            'count': {
                'signature': 'count(entity)',
                'description': 'Count occurrences of an entity in the collection.',
                'args': [
                    ('entity', 'Entity', 'The entity to count')
                ],
                'returns': 'int: Number of times the entity appears'
            },
            'index': {
                'signature': 'index(entity)',
                'description': 'Find the index of the first occurrence of an entity.',
                'args': [
                    ('entity', 'Entity', 'The entity to find')
                ],
                'returns': 'int: Zero-based index of the entity',
                'note': 'Raises ValueError if entity is not found.'
            }
        },
        
        'UICollection': {
            'append': {
                'signature': 'append(drawable)',
                'description': 'Add a drawable element to the end of the collection.',
                'args': [
                    ('drawable', 'Drawable', 'Any UI element (Frame, Caption, Sprite, Grid)')
                ]
            },
            'remove': {
                'signature': 'remove(drawable)',
                'description': 'Remove the first occurrence of a drawable from the collection.',
                'args': [
                    ('drawable', 'Drawable', 'The drawable to remove')
                ],
                'note': 'Raises ValueError if drawable is not found.'
            },
            'extend': {
                'signature': 'extend(iterable)',
                'description': 'Add multiple drawables from an iterable.',
                'args': [
                    ('iterable', 'iterable', 'An iterable of Drawable objects')
                ]
            },
            'count': {
                'signature': 'count(drawable)',
                'description': 'Count occurrences of a drawable in the collection.',
                'args': [
                    ('drawable', 'Drawable', 'The drawable to count')
                ],
                'returns': 'int: Number of times the drawable appears'
            },
            'index': {
                'signature': 'index(drawable)',
                'description': 'Find the index of the first occurrence of a drawable.',
                'args': [
                    ('drawable', 'Drawable', 'The drawable to find')
                ],
                'returns': 'int: Zero-based index of the drawable',
                'note': 'Raises ValueError if drawable is not found.'
            }
        }
    }
    
    return method_docs.get(class_name, {}).get(method_name, {})

def generate_function_docs():
    """Generate documentation for all mcrfpy module functions."""
    function_docs = {
        # Scene Management
        'createScene': {
            'signature': 'createScene(name: str) -> None',
            'description': 'Create a new empty scene.',
            'args': [
                ('name', 'str', 'Unique name for the new scene')
            ],
            'returns': 'None',
            'exceptions': [
                ('ValueError', 'If a scene with this name already exists')
            ],
            'note': 'The scene is created but not made active. Use setScene() to switch to it.',
            'example': '''mcrfpy.createScene("game")
mcrfpy.createScene("menu")
mcrfpy.setScene("game")'''
        },
        
        'setScene': {
            'signature': 'setScene(scene: str, transition: str = None, duration: float = 0.0) -> None',
            'description': 'Switch to a different scene with optional transition effect.',
            'args': [
                ('scene', 'str', 'Name of the scene to switch to'),
                ('transition', 'str', 'Transition type ("fade", "slide_left", "slide_right", "slide_up", "slide_down"). Default: None'),
                ('duration', 'float', 'Transition duration in seconds. Default: 0.0 for instant')
            ],
            'returns': 'None',
            'exceptions': [
                ('KeyError', 'If the scene doesn\'t exist'),
                ('ValueError', 'If the transition type is invalid')
            ],
            'example': '''mcrfpy.setScene("menu")
mcrfpy.setScene("game", "fade", 0.5)
mcrfpy.setScene("credits", "slide_left", 1.0)'''
        },
        
        'currentScene': {
            'signature': 'currentScene() -> str',
            'description': 'Get the name of the currently active scene.',
            'args': [],
            'returns': 'str: Name of the current scene',
            'example': '''scene = mcrfpy.currentScene()
print(f"Currently in scene: {scene}")'''
        },
        
        'sceneUI': {
            'signature': 'sceneUI(scene: str = None) -> list',
            'description': 'Get all UI elements for a scene.',
            'args': [
                ('scene', 'str', 'Scene name. If None, uses current scene. Default: None')
            ],
            'returns': 'list: All UI elements (Frame, Caption, Sprite, Grid) in the scene',
            'exceptions': [
                ('KeyError', 'If the specified scene doesn\'t exist')
            ],
            'example': '''# Get UI for current scene
ui_elements = mcrfpy.sceneUI()

# Get UI for specific scene
menu_ui = mcrfpy.sceneUI("menu")
for element in menu_ui:
    print(f"{element.name}: {type(element).__name__}")'''
        },
        
        'keypressScene': {
            'signature': 'keypressScene(handler: callable) -> None',
            'description': 'Set the keyboard event handler for the current scene.',
            'args': [
                ('handler', 'callable', 'Function that receives (key_name: str, is_pressed: bool)')
            ],
            'returns': 'None',
            'note': 'The handler is called for every key press and release event. Key names are single characters (e.g., "A", "1") or special keys (e.g., "Space", "Enter", "Escape").',
            'example': '''def on_key(key, pressed):
    if pressed:
        if key == "Space":
            player.jump()
        elif key == "Escape":
            mcrfpy.setScene("pause_menu")
    else:
        # Handle key release
        if key in ["A", "D"]:
            player.stop_moving()
            
mcrfpy.keypressScene(on_key)'''
        },
        
        # Audio Functions
        'createSoundBuffer': {
            'signature': 'createSoundBuffer(filename: str) -> int',
            'description': 'Load a sound effect from a file and return its buffer ID.',
            'args': [
                ('filename', 'str', 'Path to the sound file (WAV, OGG, FLAC)')
            ],
            'returns': 'int: Buffer ID for use with playSound()',
            'exceptions': [
                ('RuntimeError', 'If the file cannot be loaded')
            ],
            'note': 'Sound buffers are stored in memory for fast playback. Load sound effects once and reuse the buffer ID.',
            'example': '''# Load sound effects
jump_sound = mcrfpy.createSoundBuffer("assets/sounds/jump.wav")
coin_sound = mcrfpy.createSoundBuffer("assets/sounds/coin.ogg")

# Play later
mcrfpy.playSound(jump_sound)'''
        },
        
        'loadMusic': {
            'signature': 'loadMusic(filename: str, loop: bool = True) -> None',
            'description': 'Load and immediately play background music from a file.',
            'args': [
                ('filename', 'str', 'Path to the music file (WAV, OGG, FLAC)'),
                ('loop', 'bool', 'Whether to loop the music. Default: True')
            ],
            'returns': 'None',
            'note': 'Only one music track can play at a time. Loading new music stops the current track.',
            'example': '''# Play looping background music
mcrfpy.loadMusic("assets/music/theme.ogg")

# Play music once without looping
mcrfpy.loadMusic("assets/music/victory.ogg", loop=False)'''
        },
        
        'playSound': {
            'signature': 'playSound(buffer_id: int) -> None',
            'description': 'Play a sound effect using a previously loaded buffer.',
            'args': [
                ('buffer_id', 'int', 'Sound buffer ID returned by createSoundBuffer()')
            ],
            'returns': 'None',
            'exceptions': [
                ('RuntimeError', 'If the buffer ID is invalid')
            ],
            'note': 'Multiple sounds can play simultaneously. Each call creates a new sound instance.',
            'example': '''# Load once
explosion_sound = mcrfpy.createSoundBuffer("explosion.wav")

# Play multiple times
for enemy in destroyed_enemies:
    mcrfpy.playSound(explosion_sound)'''
        },
        
        'getMusicVolume': {
            'signature': 'getMusicVolume() -> int',
            'description': 'Get the current music volume level.',
            'args': [],
            'returns': 'int: Current volume (0-100)',
            'example': '''volume = mcrfpy.getMusicVolume()
print(f"Music volume: {volume}%")'''
        },
        
        'getSoundVolume': {
            'signature': 'getSoundVolume() -> int',
            'description': 'Get the current sound effects volume level.',
            'args': [],
            'returns': 'int: Current volume (0-100)',
            'example': '''volume = mcrfpy.getSoundVolume()
print(f"Sound effects volume: {volume}%")'''
        },
        
        'setMusicVolume': {
            'signature': 'setMusicVolume(volume: int) -> None',
            'description': 'Set the global music volume.',
            'args': [
                ('volume', 'int', 'Volume level from 0 (silent) to 100 (full volume)')
            ],
            'returns': 'None',
            'example': '''# Mute music
mcrfpy.setMusicVolume(0)

# Half volume
mcrfpy.setMusicVolume(50)

# Full volume
mcrfpy.setMusicVolume(100)'''
        },
        
        'setSoundVolume': {
            'signature': 'setSoundVolume(volume: int) -> None',
            'description': 'Set the global sound effects volume.',
            'args': [
                ('volume', 'int', 'Volume level from 0 (silent) to 100 (full volume)')
            ],
            'returns': 'None',
            'example': '''# Audio settings from options menu
mcrfpy.setSoundVolume(sound_slider.value)
mcrfpy.setMusicVolume(music_slider.value)'''
        },
        
        # UI Utilities
        'find': {
            'signature': 'find(name: str, scene: str = None) -> UIDrawable | None',
            'description': 'Find the first UI element with the specified name.',
            'args': [
                ('name', 'str', 'Exact name to search for'),
                ('scene', 'str', 'Scene to search in. Default: current scene')
            ],
            'returns': 'Frame, Caption, Sprite, Grid, or Entity if found; None otherwise',
            'note': 'Searches scene UI elements and entities within grids. Returns the first match found.',
            'example': '''# Find in current scene
player = mcrfpy.find("player")
if player:
    player.x = 100
    
# Find in specific scene
menu_button = mcrfpy.find("start_button", "main_menu")'''
        },
        
        'findAll': {
            'signature': 'findAll(pattern: str, scene: str = None) -> list',
            'description': 'Find all UI elements matching a name pattern.',
            'args': [
                ('pattern', 'str', 'Name pattern with optional wildcards (* matches any characters)'),
                ('scene', 'str', 'Scene to search in. Default: current scene')
            ],
            'returns': 'list: All matching UI elements and entities',
            'note': 'Supports wildcard patterns for flexible searching.',
            'example': '''# Find all enemies
enemies = mcrfpy.findAll("enemy*")
for enemy in enemies:
    enemy.sprite_id = 0  # Reset sprite
    
# Find all buttons
buttons = mcrfpy.findAll("*_button")
for btn in buttons:
    btn.visible = True
    
# Find exact matches
health_bars = mcrfpy.findAll("health_bar")  # No wildcards = exact match'''
        },
        
        # System Functions
        'exit': {
            'signature': 'exit() -> None',
            'description': 'Cleanly shut down the game engine and exit the application.',
            'args': [],
            'returns': 'None',
            'note': 'This immediately closes the window and terminates the program. Ensure any necessary cleanup is done before calling.',
            'example': '''def quit_game():
    # Save game state
    save_progress()
    
    # Exit
    mcrfpy.exit()'''
        },
        
        'getMetrics': {
            'signature': 'getMetrics() -> dict',
            'description': 'Get current performance metrics.',
            'args': [],
            'returns': '''dict: Performance data with keys:
    - frame_time: Last frame duration in seconds
    - avg_frame_time: Average frame time
    - fps: Frames per second
    - draw_calls: Number of draw calls
    - ui_elements: Total UI element count
    - visible_elements: Visible element count
    - current_frame: Frame counter
    - runtime: Total runtime in seconds''',
            'example': '''metrics = mcrfpy.getMetrics()
print(f"FPS: {metrics['fps']}")
print(f"Frame time: {metrics['frame_time']*1000:.1f}ms")
print(f"Draw calls: {metrics['draw_calls']}")
print(f"Runtime: {metrics['runtime']:.1f}s")

# Performance monitoring
if metrics['fps'] < 30:
    print("Performance warning: FPS below 30")'''
        },
        
        'setTimer': {
            'signature': 'setTimer(name: str, handler: callable, interval: int) -> None',
            'description': 'Create or update a recurring timer.',
            'args': [
                ('name', 'str', 'Unique identifier for the timer'),
                ('handler', 'callable', 'Function called with (runtime: float) parameter'),
                ('interval', 'int', 'Time between calls in milliseconds')
            ],
            'returns': 'None',
            'note': 'If a timer with this name exists, it will be replaced. The handler receives the total runtime in seconds as its argument.',
            'example': '''# Simple repeating timer
def spawn_enemy(runtime):
    enemy = mcrfpy.Entity()
    enemy.x = random.randint(0, 800)
    grid.entities.append(enemy)
    
mcrfpy.setTimer("enemy_spawner", spawn_enemy, 2000)  # Every 2 seconds

# Timer with runtime check
def update_timer(runtime):
    time_left = 60 - runtime
    timer_text.text = f"Time: {int(time_left)}"
    if time_left <= 0:
        mcrfpy.delTimer("game_timer")
        game_over()
        
mcrfpy.setTimer("game_timer", update_timer, 100)  # Update every 100ms'''
        },
        
        'delTimer': {
            'signature': 'delTimer(name: str) -> None',
            'description': 'Stop and remove a timer.',
            'args': [
                ('name', 'str', 'Timer identifier to remove')
            ],
            'returns': 'None',
            'note': 'No error is raised if the timer doesn\'t exist.',
            'example': '''# Stop spawning enemies
mcrfpy.delTimer("enemy_spawner")

# Clean up all game timers
for timer_name in ["enemy_spawner", "powerup_timer", "score_updater"]:
    mcrfpy.delTimer(timer_name)'''
        },
        
        'setScale': {
            'signature': 'setScale(multiplier: float) -> None',
            'description': 'Scale the game window size.',
            'args': [
                ('multiplier', 'float', 'Scale factor (e.g., 2.0 for double size)')
            ],
            'returns': 'None',
            'exceptions': [
                ('ValueError', 'If multiplier is not between 0.2 and 4.0')
            ],
            'note': 'The internal resolution remains 1024x768, but the window is scaled. This is deprecated - use Window.resolution instead.',
            'example': '''# Double the window size
mcrfpy.setScale(2.0)

# Half size window
mcrfpy.setScale(0.5)

# Better approach (not deprecated):
mcrfpy.Window.resolution = (1920, 1080)'''
        }
    }
    
    return function_docs

def generate_collection_docs(class_name):
    """Generate documentation for collection classes."""
    collection_docs = {
        'EntityCollection': {
            'description': 'Container for Entity objects in a Grid. Supports iteration and indexing.',
            'methods': {
                'append': 'Add an entity to the collection',
                'remove': 'Remove an entity from the collection',
                'extend': 'Add multiple entities from an iterable',
                'count': 'Count occurrences of an entity',
                'index': 'Find the index of an entity'
            }
        },
        'UICollection': {
            'description': 'Container for UI drawable elements. Supports iteration and indexing.',
            'methods': {
                'append': 'Add a UI element to the collection',
                'remove': 'Remove a UI element from the collection',
                'extend': 'Add multiple UI elements from an iterable',
                'count': 'Count occurrences of a UI element',
                'index': 'Find the index of a UI element'
            }
        },
        'UICollectionIter': {
            'description': 'Iterator for UICollection. Automatically created when iterating over a UICollection.'
        },
        'UIEntityCollectionIter': {
            'description': 'Iterator for EntityCollection. Automatically created when iterating over an EntityCollection.'
        }
    }
    
    return collection_docs.get(class_name, {})

def format_class_html(cls_info, class_name):
    """Format a class as HTML with proper structure."""
    html_parts = []
    
    # Class header
    html_parts.append(f'<div class="class-section" id="class-{class_name}">')
    html_parts.append(f'<h3>class <span class="class-name">{class_name}</span></h3>')
    
    # Inheritance
    if cls_info['bases']:
        html_parts.append(f'<p class="inheritance"><em>Inherits from: {", ".join(cls_info["bases"])}</em></p>')
    
    # Get additional documentation
    init_info = generate_class_init_docs(class_name)
    collection_info = generate_collection_docs(class_name)
    
    # Constructor signature for classes with __init__
    if init_info.get('signature'):
        html_parts.append('<div class="constructor">')
        html_parts.append('<pre><code class="language-python">')
        html_parts.append(escape_html(init_info['signature']))
        html_parts.append('</code></pre>')
        html_parts.append('</div>')
    
    # Description
    description = ""
    if collection_info.get('description'):
        description = collection_info['description']
    elif init_info.get('description'):
        description = init_info['description']
    elif cls_info['doc']:
        # Parse description from docstring
        doc_lines = cls_info['doc'].strip().split('\n')
        # Skip constructor line if present
        start_idx = 1 if doc_lines and '(' in doc_lines[0] else 0
        if start_idx < len(doc_lines):
            description = '\n'.join(doc_lines[start_idx:]).strip()
    
    if description:
        html_parts.append('<div class="description">')
        html_parts.append(f'<p>{format_docstring_as_html(description)}</p>')
        html_parts.append('</div>')
    
    # Constructor arguments
    if init_info.get('args'):
        html_parts.append('<div class="arguments">')
        html_parts.append('<h4>Arguments:</h4>')
        html_parts.append('<dl>')
        for arg_name, arg_type, arg_desc in init_info['args']:
            html_parts.append(f'<dt><code>{arg_name}</code> (<em>{arg_type}</em>)</dt>')
            html_parts.append(f'<dd>{escape_html(arg_desc)}</dd>')
        html_parts.append('</dl>')
        html_parts.append('</div>')
    
    # Properties/Attributes
    props = cls_info.get('properties', {})
    if props or init_info.get('properties'):
        html_parts.append('<div class="properties">')
        html_parts.append('<h4>Attributes:</h4>')
        html_parts.append('<dl>')
        
        # Add documented properties from init_info
        if init_info.get('properties'):
            for prop_name in init_info['properties']:
                html_parts.append(f'<dt><code class="property">{prop_name}</code></dt>')
                html_parts.append(f'<dd>Property of {class_name}</dd>')
        
        # Add actual properties
        for prop_name, prop_info in props.items():
            readonly = ' <em>(read-only)</em>' if prop_info.get('readonly') else ''
            html_parts.append(f'<dt><code class="property">{prop_name}</code>{readonly}</dt>')
            if prop_info.get('doc'):
                html_parts.append(f'<dd>{escape_html(prop_info["doc"])}</dd>')
        
        html_parts.append('</dl>')
        html_parts.append('</div>')
    
    # Methods
    methods = cls_info.get('methods', {})
    collection_methods = collection_info.get('methods', {})
    
    if methods or collection_methods:
        html_parts.append('<div class="methods">')
        html_parts.append('<h4>Methods:</h4>')
        
        for method_name, method_doc in {**collection_methods, **methods}.items():
            if method_name == '__init__':
                continue
                
            html_parts.append('<div class="method">')
            
            # Get specific method documentation
            method_info = generate_method_docs(method_name, class_name)
            
            if method_info:
                # Use detailed documentation
                html_parts.append(f'<h5><code class="method">{method_info["signature"]}</code></h5>')
                html_parts.append(f'<p>{escape_html(method_info["description"])}</p>')
                
                if method_info.get('args'):
                    html_parts.append('<p><strong>Arguments:</strong></p>')
                    html_parts.append('<ul>')
                    for arg in method_info['args']:
                        if len(arg) == 3:
                            html_parts.append(f'<li><code>{arg[0]}</code> ({arg[1]}): {arg[2]}</li>')
                        else:
                            html_parts.append(f'<li><code>{arg[0]}</code> ({arg[1]})</li>')
                    html_parts.append('</ul>')
                
                if method_info.get('returns'):
                    html_parts.append(f'<p><strong>Returns:</strong> {escape_html(method_info["returns"])}</p>')
                
                if method_info.get('note'):
                    html_parts.append(f'<p><strong>Note:</strong> {escape_html(method_info["note"])}</p>')
            else:
                # Use docstring
                html_parts.append(f'<h5><code class="method">{method_name}(...)</code></h5>')
                if isinstance(method_doc, str) and method_doc:
                    html_parts.append(f'<p>{escape_html(method_doc)}</p>')
            
            html_parts.append('</div>')
        
        html_parts.append('</div>')
    
    # Example
    if init_info.get('example'):
        html_parts.append('<div class="example">')
        html_parts.append('<h4>Example:</h4>')
        html_parts.append('<pre><code class="language-python">')
        html_parts.append(escape_html(init_info['example']))
        html_parts.append('</code></pre>')
        html_parts.append('</div>')
    
    html_parts.append('</div>')
    html_parts.append('<hr>')
    
    return '\n'.join(html_parts)

def generate_html_documentation():
    """Generate complete HTML API documentation."""
    html_parts = []
    
    # HTML header
    html_parts.append('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>McRogueFace API Reference</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f8f9fa;
        }
        
        .container {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        h1 { 
            color: #2c3e50; 
            border-bottom: 3px solid #3498db; 
            padding-bottom: 15px;
            margin-bottom: 30px;
        }
        
        h2 { 
            color: #34495e; 
            border-bottom: 2px solid #ecf0f1; 
            padding-bottom: 10px;
            margin-top: 40px;
        }
        
        h3 { 
            color: #2c3e50; 
            margin-top: 30px;
        }
        
        h4 {
            color: #34495e;
            margin-top: 20px;
            font-size: 1.1em;
        }
        
        h5 {
            color: #555;
            margin-top: 15px;
            font-size: 1em;
        }
        
        code {
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: "SF Mono", Monaco, "Cascadia Code", "Roboto Mono", Consolas, monospace;
            font-size: 0.9em;
        }
        
        pre {
            background: #f8f8f8;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            padding: 16px;
            overflow-x: auto;
            margin: 15px 0;
        }
        
        pre code {
            background: none;
            padding: 0;
            font-size: 0.875em;
            line-height: 1.45;
        }
        
        .class-name {
            color: #8e44ad;
            font-weight: bold;
        }
        
        .property {
            color: #27ae60;
            font-weight: 600;
        }
        
        .method {
            color: #2980b9;
            font-weight: 600;
        }
        
        .inheritance {
            color: #7f8c8d;
            font-size: 0.9em;
            margin-top: -10px;
        }
        
        .toc {
            background: #f8f9fa;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            padding: 20px;
            margin: 20px 0;
        }
        
        .toc h2 {
            margin-top: 0;
            border: none;
            padding: 0;
        }
        
        .toc ul {
            list-style: none;
            padding-left: 0;
        }
        
        .toc li {
            margin: 8px 0;
        }
        
        .toc a {
            color: #3498db;
            text-decoration: none;
            font-weight: 500;
        }
        
        .toc a:hover {
            text-decoration: underline;
        }
        
        .class-section, .function-section {
            margin: 30px 0;
            padding: 20px;
            background: #fafbfc;
            border-radius: 6px;
            border: 1px solid #e1e4e8;
        }
        
        .description {
            margin: 15px 0;
            color: #4a5568;
        }
        
        .arguments, .properties, .methods {
            margin: 20px 0;
        }
        
        dl {
            margin: 10px 0;
        }
        
        dt {
            font-weight: 600;
            margin-top: 10px;
            color: #2c3e50;
        }
        
        dd {
            margin-left: 20px;
            margin-bottom: 10px;
            color: #555;
        }
        
        .example {
            margin: 20px 0;
            padding: 15px;
            background: #f0f7ff;
            border-left: 4px solid #3498db;
            border-radius: 4px;
        }
        
        .example h4 {
            margin-top: 0;
            color: #2980b9;
        }
        
        hr {
            border: none;
            border-top: 1px solid #e1e4e8;
            margin: 30px 0;
        }
        
        .timestamp {
            color: #7f8c8d;
            font-style: italic;
            font-size: 0.9em;
        }
        
        .overview {
            background: #e8f4fd;
            border-left: 4px solid #3498db;
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }
        
        .overview pre {
            background: white;
            border: 1px solid #d6e9f5;
        }
        
        strong {
            color: #2c3e50;
        }
        
        em {
            color: #555;
        }
        
        .automation-section {
            background: #f0f9ff;
            border: 1px solid #b8daff;
            border-radius: 6px;
            padding: 20px;
            margin-top: 30px;
        }
        
        .automation-section h2 {
            color: #004085;
            border-bottom: 2px solid #b8daff;
        }
        
        .function-signature {
            font-family: "SF Mono", Monaco, monospace;
            font-size: 1.1em;
            color: #d73a49;
        }
    </style>
</head>
<body>
    <div class="container">
''')
    
    # Title and timestamp
    html_parts.append('<h1>McRogueFace API Reference</h1>')
    html_parts.append(f'<p class="timestamp">Generated on {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>')
    
    # Overview
    if mcrfpy.__doc__:
        html_parts.append('<div class="overview">')
        html_parts.append('<h2>Overview</h2>')
        # Process the docstring properly
        doc_lines = mcrfpy.__doc__.strip().split('\\n')
        for line in doc_lines:
            if line.strip().startswith('Example:'):
                html_parts.append('<h4>Example:</h4>')
                html_parts.append('<pre><code class="language-python">')
            elif line.strip() and not line.startswith(' '):
                html_parts.append(f'<p>{escape_html(line)}</p>')
            elif line.strip():
                # Code line
                html_parts.append(escape_html(line))
        html_parts.append('</code></pre>')
        html_parts.append('</div>')
    
    # Table of Contents
    html_parts.append('<div class="toc">')
    html_parts.append('<h2>Table of Contents</h2>')
    html_parts.append('<ul>')
    html_parts.append('<li><a href="#classes">Classes</a>')
    html_parts.append('<ul>')
    html_parts.append('<li><a href="#ui-components">UI Components</a></li>')
    html_parts.append('<li><a href="#collections">Collections</a></li>')
    html_parts.append('<li><a href="#system-types">System Types</a></li>')
    html_parts.append('<li><a href="#other-classes">Other Classes</a></li>')
    html_parts.append('</ul>')
    html_parts.append('</li>')
    html_parts.append('<li><a href="#functions">Functions</a>')
    html_parts.append('<ul>')
    html_parts.append('<li><a href="#scene-management">Scene Management</a></li>')
    html_parts.append('<li><a href="#audio">Audio</a></li>')
    html_parts.append('<li><a href="#ui-utilities">UI Utilities</a></li>')
    html_parts.append('<li><a href="#system">System</a></li>')
    html_parts.append('</ul>')
    html_parts.append('</li>')
    html_parts.append('<li><a href="#automation">Automation Module</a></li>')
    html_parts.append('</ul>')
    html_parts.append('</div>')
    
    # Collect all components
    classes = {}
    functions = {}
    
    for name in sorted(dir(mcrfpy)):
        if name.startswith('_'):
            continue
        
        obj = getattr(mcrfpy, name)
        
        if isinstance(obj, type):
            classes[name] = obj
        elif callable(obj) and not isinstance(obj, type):
            # Include built-in functions and other callables (but not classes)
            functions[name] = obj
    
    
    # Classes section
    html_parts.append('<h2 id="classes">Classes</h2>')
    
    # Group classes
    ui_classes = ['Frame', 'Caption', 'Sprite', 'Grid', 'Entity']
    collection_classes = ['EntityCollection', 'UICollection', 'UICollectionIter', 'UIEntityCollectionIter']
    system_classes = ['Color', 'Vector', 'Texture', 'Font']
    other_classes = [name for name in classes if name not in ui_classes + collection_classes + system_classes]
    
    # UI Components
    html_parts.append('<h3 id="ui-components">UI Components</h3>')
    for class_name in ui_classes:
        if class_name in classes:
            cls_info = get_class_details(classes[class_name])
            html_parts.append(format_class_html(cls_info, class_name))
    
    # Collections
    html_parts.append('<h3 id="collections">Collections</h3>')
    for class_name in collection_classes:
        if class_name in classes:
            cls_info = get_class_details(classes[class_name])
            html_parts.append(format_class_html(cls_info, class_name))
    
    # System Types
    html_parts.append('<h3 id="system-types">System Types</h3>')
    for class_name in system_classes:
        if class_name in classes:
            cls_info = get_class_details(classes[class_name])
            html_parts.append(format_class_html(cls_info, class_name))
    
    # Other Classes
    html_parts.append('<h3 id="other-classes">Other Classes</h3>')
    for class_name in other_classes:
        if class_name in classes:
            cls_info = get_class_details(classes[class_name])
            html_parts.append(format_class_html(cls_info, class_name))
    
    # Functions section
    html_parts.append('<h2 id="functions">Functions</h2>')
    
    # Group functions by category
    scene_funcs = ['createScene', 'setScene', 'currentScene', 'sceneUI', 'keypressScene']
    audio_funcs = ['createSoundBuffer', 'loadMusic', 'playSound', 'getMusicVolume', 
                   'getSoundVolume', 'setMusicVolume', 'setSoundVolume']
    ui_funcs = ['find', 'findAll']
    system_funcs = ['exit', 'getMetrics', 'setTimer', 'delTimer', 'setScale']
    
    # Scene Management
    html_parts.append('<h3 id="scene-management">Scene Management</h3>')
    for func_name in scene_funcs:
        if func_name in functions:
            html_parts.append(format_function_html(func_name, functions[func_name]))
    
    # Audio
    html_parts.append('<h3 id="audio">Audio</h3>')
    for func_name in audio_funcs:
        if func_name in functions:
            html_parts.append(format_function_html(func_name, functions[func_name]))
    
    # UI Utilities
    html_parts.append('<h3 id="ui-utilities">UI Utilities</h3>')
    for func_name in ui_funcs:
        if func_name in functions:
            html_parts.append(format_function_html(func_name, functions[func_name]))
    
    # System
    html_parts.append('<h3 id="system">System</h3>')
    for func_name in system_funcs:
        if func_name in functions:
            html_parts.append(format_function_html(func_name, functions[func_name]))
    
    # Automation Module
    if hasattr(mcrfpy, 'automation'):
        html_parts.append('<div class="automation-section">')
        html_parts.append('<h2 id="automation">Automation Module</h2>')
        html_parts.append('<p>The <code>mcrfpy.automation</code> module provides testing and automation capabilities for simulating user input and capturing screenshots.</p>')
        
        automation = mcrfpy.automation
        auto_funcs = []
        
        for name in sorted(dir(automation)):
            if not name.startswith('_'):
                obj = getattr(automation, name)
                if callable(obj):
                    auto_funcs.append((name, obj))
        
        for name, func in auto_funcs:
            html_parts.append('<div class="function-section">')
            html_parts.append(f'<h4><code class="function-signature">automation.{name}</code></h4>')
            if func.__doc__:
                # Extract just the description, not the repeated signature
                doc_lines = func.__doc__.strip().split(' - ')
                if len(doc_lines) > 1:
                    description = doc_lines[1]
                else:
                    description = func.__doc__.strip()
                html_parts.append(f'<p>{escape_html(description)}</p>')
            html_parts.append('</div>')
        
        html_parts.append('</div>')
    
    # Close HTML
    html_parts.append('''
    </div>
</body>
</html>''')
    
    return '\n'.join(html_parts)

def format_function_html(func_name, func):
    """Format a function as HTML using enhanced documentation."""
    html_parts = []
    
    html_parts.append('<div class="function-section">')
    
    # Get enhanced documentation
    func_docs = generate_function_docs()
    
    if func_name in func_docs:
        doc_info = func_docs[func_name]
        
        # Signature
        signature = doc_info.get('signature', f'{func_name}(...)')
        html_parts.append(f'<h4><code class="function-signature">{escape_html(signature)}</code></h4>')
        
        # Description
        if 'description' in doc_info:
            html_parts.append(f'<p class="description">{escape_html(doc_info["description"])}</p>')
        
        # Arguments
        if 'args' in doc_info and doc_info['args']:
            html_parts.append('<div class="arguments">')
            html_parts.append('<h5>Arguments:</h5>')
            html_parts.append('<dl>')
            for arg_name, arg_type, arg_desc in doc_info['args']:
                html_parts.append(f'<dt><code>{escape_html(arg_name)}</code> : <em>{escape_html(arg_type)}</em></dt>')
                html_parts.append(f'<dd>{escape_html(arg_desc)}</dd>')
            html_parts.append('</dl>')
            html_parts.append('</div>')
        
        # Returns
        if 'returns' in doc_info and doc_info['returns']:
            html_parts.append('<div class="returns">')
            html_parts.append('<h5>Returns:</h5>')
            html_parts.append(f'<p>{escape_html(doc_info["returns"])}</p>')
            html_parts.append('</div>')
        
        # Exceptions
        if 'exceptions' in doc_info and doc_info['exceptions']:
            html_parts.append('<div class="exceptions">')
            html_parts.append('<h5>Raises:</h5>')
            html_parts.append('<dl>')
            for exc_type, exc_desc in doc_info['exceptions']:
                html_parts.append(f'<dt><code>{escape_html(exc_type)}</code></dt>')
                html_parts.append(f'<dd>{escape_html(exc_desc)}</dd>')
            html_parts.append('</dl>')
            html_parts.append('</div>')
        
        # Note
        if 'note' in doc_info:
            html_parts.append('<div class="note">')
            html_parts.append(f'<p><strong>Note:</strong> {escape_html(doc_info["note"])}</p>')
            html_parts.append('</div>')
        
        # Example
        if 'example' in doc_info:
            html_parts.append('<div class="example">')
            html_parts.append('<h5>Example:</h5>')
            html_parts.append('<pre><code class="language-python">')
            html_parts.append(escape_html(doc_info['example']))
            html_parts.append('</code></pre>')
            html_parts.append('</div>')
    else:
        # Fallback to parsing docstring if not in enhanced docs
        doc = func.__doc__ or ""
        lines = doc.strip().split('\n') if doc else []
        
        # Extract signature
        signature = func_name + '(...)'
        if lines and '(' in lines[0]:
            signature = lines[0].strip()
        
        html_parts.append(f'<h4><code class="function-signature">{escape_html(signature)}</code></h4>')
        
        # Process rest of docstring
        if len(lines) > 1:
            in_section = None
            for line in lines[1:]:
                stripped = line.strip()
                
                if stripped in ['Args:', 'Returns:', 'Raises:', 'Note:', 'Example:']:
                    in_section = stripped[:-1]
                    html_parts.append(f'<p><strong>{in_section}:</strong></p>')
                elif in_section == 'Example':
                    if not stripped:
                        continue
                    if stripped.startswith('>>>') or (len(lines) > lines.index(line) + 1 and 
                                                      lines[lines.index(line) + 1].strip().startswith('>>>')):
                        html_parts.append('<pre><code class="language-python">')
                        html_parts.append(escape_html(stripped))
                        # Get rest of example
                        idx = lines.index(line) + 1
                        while idx < len(lines) and lines[idx].strip():
                            html_parts.append(escape_html(lines[idx]))
                            idx += 1
                        html_parts.append('</code></pre>')
                        break
                elif in_section and stripped:
                    if in_section == 'Args':
                        # Format arguments nicely
                        if ':' in stripped:
                            param, desc = stripped.split(':', 1)
                            html_parts.append(f'<p style="margin-left: 20px;"><code>{escape_html(param.strip())}</code>: {escape_html(desc.strip())}</p>')
                        else:
                            html_parts.append(f'<p style="margin-left: 20px;">{escape_html(stripped)}</p>')
                    else:
                        html_parts.append(f'<p style="margin-left: 20px;">{escape_html(stripped)}</p>')
                elif stripped and not in_section:
                    html_parts.append(f'<p>{escape_html(stripped)}</p>')
    
    html_parts.append('</div>')
    html_parts.append('<hr>')
    
    return '\n'.join(html_parts)

def main():
    """Generate improved HTML API documentation."""
    print("Generating improved HTML API documentation...")
    
    # Generate HTML
    html_content = generate_html_documentation()
    
    # Write to file
    output_path = Path("docs/api_reference_improved.html")
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ Generated {output_path}")
    print(f"  File size: {len(html_content):,} bytes")
    
    # Also generate a test to verify the HTML
    test_content = '''#!/usr/bin/env python3
"""Test the improved HTML API documentation."""

import os
import sys
from pathlib import Path

def test_html_quality():
    """Test that the HTML documentation meets quality standards."""
    html_path = Path("docs/api_reference_improved.html")
    
    if not html_path.exists():
        print("ERROR: HTML documentation not found")
        return False
        
    with open(html_path, 'r') as f:
        content = f.read()
    
    # Check for common issues
    issues = []
    
    # Check that \\n is not present literally
    if '\\\\n' in content:
        issues.append("Found literal \\\\n in HTML content")
    
    # Check that markdown links are converted
    if '[' in content and '](#' in content:
        issues.append("Found unconverted markdown links")
    
    # Check for proper HTML structure
    if '<h4>Args:</h4>' in content:
        issues.append("Args: should not be an H4 heading")
    
    if '<h4>Attributes:</h4>' not in content:
        issues.append("Missing proper Attributes: headings")
    
    # Check for duplicate method descriptions
    if content.count('Get bounding box as (x, y, width, height)') > 20:
        issues.append("Too many duplicate method descriptions")
    
    # Check specific improvements
    if 'Entity' in content and 'Inherits from: Drawable' in content:
        issues.append("Entity incorrectly shown as inheriting from Drawable")
    
    if not issues:
        print("✓ HTML documentation passes all quality checks")
        return True
    else:
        print("Issues found:")
        for issue in issues:
            print(f"  - {issue}")
        return False

if __name__ == '__main__':
    if test_html_quality():
        print("PASS")
        sys.exit(0)
    else:
        print("FAIL")
        sys.exit(1)
'''
    
    test_path = Path("tests/test_html_quality.py")
    with open(test_path, 'w') as f:
        f.write(test_content)
    
    print(f"✓ Generated test at {test_path}")

if __name__ == '__main__':
    main()