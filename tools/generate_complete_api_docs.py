#!/usr/bin/env python3
"""Generate COMPLETE HTML API reference documentation for McRogueFace with NO missing methods."""

import os
import sys
import datetime
import html
from pathlib import Path
import mcrfpy

def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return html.escape(text) if text else ""

def get_complete_method_documentation():
    """Return complete documentation for ALL methods across all classes."""
    return {
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
                'note': 'For Caption and Sprite, this may not change actual size if determined by content.'
            }
        },
        
        # Entity-specific methods
        'Entity': {
            'at': {
                'signature': 'at(x, y)',
                'description': 'Check if this entity is at the specified grid coordinates.',
                'args': [
                    ('x', 'int', 'Grid x coordinate to check'),
                    ('y', 'int', 'Grid y coordinate to check')
                ],
                'returns': 'bool: True if entity is at position (x, y), False otherwise'
            },
            'die': {
                'signature': 'die()',
                'description': 'Remove this entity from its parent grid.',
                'note': 'The entity object remains valid but is no longer rendered or updated.'
            },
            'index': {
                'signature': 'index()',
                'description': 'Get the index of this entity in its parent grid\'s entity list.',
                'returns': 'int: Index position, or -1 if not in a grid'
            }
        },
        
        # Grid-specific methods
        'Grid': {
            'at': {
                'signature': 'at(x, y)',
                'description': 'Get the GridPoint at the specified grid coordinates.',
                'args': [
                    ('x', 'int', 'Grid x coordinate'),
                    ('y', 'int', 'Grid y coordinate')
                ],
                'returns': 'GridPoint or None: The grid point at (x, y), or None if out of bounds'
            }
        },
        
        # Collection methods
        'EntityCollection': {
            'append': {
                'signature': 'append(entity)',
                'description': 'Add an entity to the end of the collection.',
                'args': [('entity', 'Entity', 'The entity to add')]
            },
            'remove': {
                'signature': 'remove(entity)',
                'description': 'Remove the first occurrence of an entity from the collection.',
                'args': [('entity', 'Entity', 'The entity to remove')],
                'raises': 'ValueError: If entity is not in collection'
            },
            'extend': {
                'signature': 'extend(iterable)',
                'description': 'Add all entities from an iterable to the collection.',
                'args': [('iterable', 'Iterable[Entity]', 'Entities to add')]
            },
            'count': {
                'signature': 'count(entity)',
                'description': 'Count the number of occurrences of an entity in the collection.',
                'args': [('entity', 'Entity', 'The entity to count')],
                'returns': 'int: Number of times entity appears in collection'
            },
            'index': {
                'signature': 'index(entity)',
                'description': 'Find the index of the first occurrence of an entity.',
                'args': [('entity', 'Entity', 'The entity to find')],
                'returns': 'int: Index of entity in collection',
                'raises': 'ValueError: If entity is not in collection'
            }
        },
        
        'UICollection': {
            'append': {
                'signature': 'append(drawable)',
                'description': 'Add a drawable element to the end of the collection.',
                'args': [('drawable', 'UIDrawable', 'The drawable element to add')]
            },
            'remove': {
                'signature': 'remove(drawable)',
                'description': 'Remove the first occurrence of a drawable from the collection.',
                'args': [('drawable', 'UIDrawable', 'The drawable to remove')],
                'raises': 'ValueError: If drawable is not in collection'
            },
            'extend': {
                'signature': 'extend(iterable)',
                'description': 'Add all drawables from an iterable to the collection.',
                'args': [('iterable', 'Iterable[UIDrawable]', 'Drawables to add')]
            },
            'count': {
                'signature': 'count(drawable)',
                'description': 'Count the number of occurrences of a drawable in the collection.',
                'args': [('drawable', 'UIDrawable', 'The drawable to count')],
                'returns': 'int: Number of times drawable appears in collection'
            },
            'index': {
                'signature': 'index(drawable)',
                'description': 'Find the index of the first occurrence of a drawable.',
                'args': [('drawable', 'UIDrawable', 'The drawable to find')],
                'returns': 'int: Index of drawable in collection',
                'raises': 'ValueError: If drawable is not in collection'
            }
        },
        
        # Animation methods
        'Animation': {
            'get_current_value': {
                'signature': 'get_current_value()',
                'description': 'Get the current interpolated value of the animation.',
                'returns': 'float: Current animation value between start and end'
            },
            'start': {
                'signature': 'start(target)',
                'description': 'Start the animation on a target UI element.',
                'args': [('target', 'UIDrawable', 'The UI element to animate')],
                'note': 'The target must have the property specified in the animation constructor.'
            },
            'update': {
                'signature': 'update(delta_time)',
                'description': 'Update the animation by the given time delta.',
                'args': [('delta_time', 'float', 'Time elapsed since last update in seconds')],
                'returns': 'bool: True if animation is still running, False if finished'
            }
        },
        
        # Color methods
        'Color': {
            'from_hex': {
                'signature': 'from_hex(hex_string)',
                'description': 'Create a Color from a hexadecimal color string.',
                'args': [('hex_string', 'str', 'Hex color string (e.g., "#FF0000" or "FF0000")')],
                'returns': 'Color: New Color object from hex string',
                'example': 'red = Color.from_hex("#FF0000")'
            },
            'to_hex': {
                'signature': 'to_hex()',
                'description': 'Convert this Color to a hexadecimal string.',
                'returns': 'str: Hex color string in format "#RRGGBB"',
                'example': 'hex_str = color.to_hex()  # Returns "#FF0000"'
            },
            'lerp': {
                'signature': 'lerp(other, t)',
                'description': 'Linearly interpolate between this color and another.',
                'args': [
                    ('other', 'Color', 'The color to interpolate towards'),
                    ('t', 'float', 'Interpolation factor from 0.0 to 1.0')
                ],
                'returns': 'Color: New interpolated Color object',
                'example': 'mixed = red.lerp(blue, 0.5)  # 50% between red and blue'
            }
        },
        
        # Vector methods
        'Vector': {
            'magnitude': {
                'signature': 'magnitude()',
                'description': 'Calculate the length/magnitude of this vector.',
                'returns': 'float: The magnitude of the vector',
                'example': 'length = vector.magnitude()'
            },
            'magnitude_squared': {
                'signature': 'magnitude_squared()',
                'description': 'Calculate the squared magnitude of this vector.',
                'returns': 'float: The squared magnitude (faster than magnitude())',
                'note': 'Use this for comparisons to avoid expensive square root calculation.'
            },
            'normalize': {
                'signature': 'normalize()',
                'description': 'Return a unit vector in the same direction.',
                'returns': 'Vector: New normalized vector with magnitude 1.0',
                'raises': 'ValueError: If vector has zero magnitude'
            },
            'dot': {
                'signature': 'dot(other)',
                'description': 'Calculate the dot product with another vector.',
                'args': [('other', 'Vector', 'The other vector')],
                'returns': 'float: Dot product of the two vectors'
            },
            'distance_to': {
                'signature': 'distance_to(other)',
                'description': 'Calculate the distance to another vector.',
                'args': [('other', 'Vector', 'The other vector')],
                'returns': 'float: Distance between the two vectors'
            },
            'angle': {
                'signature': 'angle()',
                'description': 'Get the angle of this vector in radians.',
                'returns': 'float: Angle in radians from positive x-axis'
            },
            'copy': {
                'signature': 'copy()',
                'description': 'Create a copy of this vector.',
                'returns': 'Vector: New Vector object with same x and y values'
            }
        },
        
        # Scene methods
        'Scene': {
            'activate': {
                'signature': 'activate()',
                'description': 'Make this scene the active scene.',
                'note': 'Equivalent to calling setScene() with this scene\'s name.'
            },
            'get_ui': {
                'signature': 'get_ui()',
                'description': 'Get the UI element collection for this scene.',
                'returns': 'UICollection: Collection of all UI elements in this scene'
            },
            'keypress': {
                'signature': 'keypress(handler)',
                'description': 'Register a keyboard handler function for this scene.',
                'args': [('handler', 'callable', 'Function that takes (key_name: str, is_pressed: bool)')],
                'note': 'Alternative to overriding the on_keypress method.'
            },
            'register_keyboard': {
                'signature': 'register_keyboard(callable)',
                'description': 'Register a keyboard event handler function for the scene.',
                'args': [('callable', 'callable', 'Function that takes (key: str, action: str) parameters')],
                'note': 'Alternative to overriding the on_keypress method when subclassing Scene objects.',
                'example': '''def handle_keyboard(key, action):
    print(f"Key '{key}' was {action}")
    if key == "q" and action == "press":
        # Handle quit
        pass
scene.register_keyboard(handle_keyboard)'''
            }
        },
        
        # Timer methods
        'Timer': {
            'pause': {
                'signature': 'pause()',
                'description': 'Pause the timer, stopping its callback execution.',
                'note': 'Use resume() to continue the timer from where it was paused.'
            },
            'resume': {
                'signature': 'resume()',
                'description': 'Resume a paused timer.',
                'note': 'Has no effect if timer is not paused.'
            },
            'cancel': {
                'signature': 'cancel()',
                'description': 'Cancel the timer and remove it from the system.',
                'note': 'After cancelling, the timer object cannot be reused.'
            },
            'restart': {
                'signature': 'restart()',
                'description': 'Restart the timer from the beginning.',
                'note': 'Resets the timer\'s internal clock to zero.'
            }
        },
        
        # Window methods
        'Window': {
            'get': {
                'signature': 'get()',
                'description': 'Get the Window singleton instance.',
                'returns': 'Window: The singleton window object',
                'note': 'This is a static method that returns the same instance every time.'
            },
            'center': {
                'signature': 'center()',
                'description': 'Center the window on the screen.',
                'note': 'Only works if the window is not fullscreen.'
            },
            'screenshot': {
                'signature': 'screenshot(filename)',
                'description': 'Take a screenshot and save it to a file.',
                'args': [('filename', 'str', 'Path where to save the screenshot')],
                'note': 'Supports PNG, JPG, and BMP formats based on file extension.'
            }
        }
    }

def get_complete_function_documentation():
    """Return complete documentation for ALL module functions."""
    return {
        # Scene Management
        'createScene': {
            'signature': 'createScene(name: str) -> None',
            'description': 'Create a new empty scene with the given name.',
            'args': [('name', 'str', 'Unique name for the new scene')],
            'raises': 'ValueError: If a scene with this name already exists',
            'note': 'The scene is created but not made active. Use setScene() to switch to it.',
            'example': 'mcrfpy.createScene("game_over")'
        },
        'setScene': {
            'signature': 'setScene(scene: str, transition: str = None, duration: float = 0.0) -> None',
            'description': 'Switch to a different scene with optional transition effect.',
            'args': [
                ('scene', 'str', 'Name of the scene to switch to'),
                ('transition', 'str', 'Transition type: "fade", "slide_left", "slide_right", "slide_up", "slide_down"'),
                ('duration', 'float', 'Transition duration in seconds (default: 0.0 for instant)')
            ],
            'raises': 'KeyError: If the scene doesn\'t exist',
            'example': 'mcrfpy.setScene("game", "fade", 0.5)'
        },
        'currentScene': {
            'signature': 'currentScene() -> str',
            'description': 'Get the name of the currently active scene.',
            'returns': 'str: Name of the current scene',
            'example': 'scene_name = mcrfpy.currentScene()'
        },
        'sceneUI': {
            'signature': 'sceneUI(scene: str = None) -> UICollection',
            'description': 'Get all UI elements for a scene.',
            'args': [('scene', 'str', 'Scene name. If None, uses current scene')],
            'returns': 'UICollection: All UI elements in the scene',
            'raises': 'KeyError: If the specified scene doesn\'t exist',
            'example': 'ui_elements = mcrfpy.sceneUI("game")'
        },
        'keypressScene': {
            'signature': 'keypressScene(handler: callable) -> None',
            'description': 'Set the keyboard event handler for the current scene.',
            'args': [('handler', 'callable', 'Function that receives (key_name: str, is_pressed: bool)')],
            'example': '''def on_key(key, pressed):
    if key == "SPACE" and pressed:
        player.jump()
mcrfpy.keypressScene(on_key)'''
        },
        
        # Audio Functions
        'createSoundBuffer': {
            'signature': 'createSoundBuffer(filename: str) -> int',
            'description': 'Load a sound effect from a file and return its buffer ID.',
            'args': [('filename', 'str', 'Path to the sound file (WAV, OGG, FLAC)')],
            'returns': 'int: Buffer ID for use with playSound()',
            'raises': 'RuntimeError: If the file cannot be loaded',
            'example': 'jump_sound = mcrfpy.createSoundBuffer("assets/jump.wav")'
        },
        'loadMusic': {
            'signature': 'loadMusic(filename: str, loop: bool = True) -> None',
            'description': 'Load and immediately play background music from a file.',
            'args': [
                ('filename', 'str', 'Path to the music file (WAV, OGG, FLAC)'),
                ('loop', 'bool', 'Whether to loop the music (default: True)')
            ],
            'note': 'Only one music track can play at a time. Loading new music stops the current track.',
            'example': 'mcrfpy.loadMusic("assets/background.ogg", True)'
        },
        'playSound': {
            'signature': 'playSound(buffer_id: int) -> None',
            'description': 'Play a sound effect using a previously loaded buffer.',
            'args': [('buffer_id', 'int', 'Sound buffer ID returned by createSoundBuffer()')],
            'raises': 'RuntimeError: If the buffer ID is invalid',
            'example': 'mcrfpy.playSound(jump_sound)'
        },
        'getMusicVolume': {
            'signature': 'getMusicVolume() -> int',
            'description': 'Get the current music volume level.',
            'returns': 'int: Current volume (0-100)',
            'example': 'current_volume = mcrfpy.getMusicVolume()'
        },
        'getSoundVolume': {
            'signature': 'getSoundVolume() -> int',
            'description': 'Get the current sound effects volume level.',
            'returns': 'int: Current volume (0-100)',
            'example': 'current_volume = mcrfpy.getSoundVolume()'
        },
        'setMusicVolume': {
            'signature': 'setMusicVolume(volume: int) -> None',
            'description': 'Set the global music volume.',
            'args': [('volume', 'int', 'Volume level from 0 (silent) to 100 (full volume)')],
            'example': 'mcrfpy.setMusicVolume(50)  # Set to 50% volume'
        },
        'setSoundVolume': {
            'signature': 'setSoundVolume(volume: int) -> None',
            'description': 'Set the global sound effects volume.',
            'args': [('volume', 'int', 'Volume level from 0 (silent) to 100 (full volume)')],
            'example': 'mcrfpy.setSoundVolume(75)  # Set to 75% volume'
        },
        
        # UI Utilities
        'find': {
            'signature': 'find(name: str, scene: str = None) -> UIDrawable | None',
            'description': 'Find the first UI element with the specified name.',
            'args': [
                ('name', 'str', 'Exact name to search for'),
                ('scene', 'str', 'Scene to search in (default: current scene)')
            ],
            'returns': 'UIDrawable or None: The found element, or None if not found',
            'note': 'Searches scene UI elements and entities within grids.',
            'example': 'button = mcrfpy.find("start_button")'
        },
        'findAll': {
            'signature': 'findAll(pattern: str, scene: str = None) -> list',
            'description': 'Find all UI elements matching a name pattern.',
            'args': [
                ('pattern', 'str', 'Name pattern with optional wildcards (* matches any characters)'),
                ('scene', 'str', 'Scene to search in (default: current scene)')
            ],
            'returns': 'list: All matching UI elements and entities',
            'example': 'enemies = mcrfpy.findAll("enemy_*")'
        },
        
        # System Functions
        'exit': {
            'signature': 'exit() -> None',
            'description': 'Cleanly shut down the game engine and exit the application.',
            'note': 'This immediately closes the window and terminates the program.',
            'example': 'mcrfpy.exit()'
        },
        'getMetrics': {
            'signature': 'getMetrics() -> dict',
            'description': 'Get current performance metrics.',
            'returns': '''dict: Performance data with keys:
- frame_time: Last frame duration in seconds
- avg_frame_time: Average frame time
- fps: Frames per second
- draw_calls: Number of draw calls
- ui_elements: Total UI element count
- visible_elements: Visible element count
- current_frame: Frame counter
- runtime: Total runtime in seconds''',
            'example': 'metrics = mcrfpy.getMetrics()'
        },
        'setTimer': {
            'signature': 'setTimer(name: str, handler: callable, interval: int) -> None',
            'description': 'Create or update a recurring timer.',
            'args': [
                ('name', 'str', 'Unique identifier for the timer'),
                ('handler', 'callable', 'Function called with (runtime: float) parameter'),
                ('interval', 'int', 'Time between calls in milliseconds')
            ],
            'note': 'If a timer with this name exists, it will be replaced.',
            'example': '''def update_score(runtime):
    score += 1
mcrfpy.setTimer("score_update", update_score, 1000)'''
        },
        'delTimer': {
            'signature': 'delTimer(name: str) -> None',
            'description': 'Stop and remove a timer.',
            'args': [('name', 'str', 'Timer identifier to remove')],
            'note': 'No error is raised if the timer doesn\'t exist.',
            'example': 'mcrfpy.delTimer("score_update")'
        },
        'setScale': {
            'signature': 'setScale(multiplier: float) -> None',
            'description': 'Scale the game window size.',
            'args': [('multiplier', 'float', 'Scale factor (e.g., 2.0 for double size)')],
            'note': 'The internal resolution remains 1024x768, but the window is scaled.',
            'example': 'mcrfpy.setScale(2.0)  # Double the window size'
        }
    }

def get_complete_property_documentation():
    """Return complete documentation for ALL properties."""
    return {
        'Animation': {
            'property': 'str: Name of the property being animated (e.g., "x", "y", "scale")',
            'duration': 'float: Total duration of the animation in seconds',
            'elapsed_time': 'float: Time elapsed since animation started (read-only)',
            'current_value': 'float: Current interpolated value of the animation (read-only)',
            'is_running': 'bool: True if animation is currently running (read-only)',
            'is_finished': 'bool: True if animation has completed (read-only)'
        },
        'GridPoint': {
            'x': 'int: Grid x coordinate of this point',
            'y': 'int: Grid y coordinate of this point',
            'texture_index': 'int: Index of the texture/sprite to display at this point',
            'solid': 'bool: Whether this point blocks movement',
            'transparent': 'bool: Whether this point allows light/vision through',
            'color': 'Color: Color tint applied to the texture at this point'
        },
        'GridPointState': {
            'visible': 'bool: Whether this point is currently visible to the player',
            'discovered': 'bool: Whether this point has been discovered/explored',
            'custom_flags': 'int: Bitfield for custom game-specific flags'
        }
    }

def generate_complete_html_documentation():
    """Generate complete HTML documentation with NO missing methods."""
    
    # Get all documentation data
    method_docs = get_complete_method_documentation()
    function_docs = get_complete_function_documentation()
    property_docs = get_complete_property_documentation()
    
    html_parts = []
    
    # HTML header with enhanced styling
    html_parts.append('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>McRogueFace API Reference - Complete Documentation</title>
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
        
        .function-signature {
            color: #d73a49;
            font-weight: 600;
        }
        
        .method-section {
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 6px;
            border-left: 4px solid #3498db;
        }
        
        .arg-list {
            margin: 10px 0;
        }
        
        .arg-item {
            margin: 8px 0;
            padding: 8px;
            background: #fff;
            border-radius: 4px;
            border: 1px solid #e1e4e8;
        }
        
        .arg-name {
            color: #d73a49;
            font-weight: 600;
        }
        
        .arg-type {
            color: #6f42c1;
            font-style: italic;
        }
        
        .returns {
            background: #e8f5e8;
            padding: 10px;
            border-radius: 4px;
            border-left: 4px solid #28a745;
            margin: 10px 0;
        }
        
        .note {
            background: #fff3cd;
            padding: 10px;
            border-radius: 4px;
            border-left: 4px solid #ffc107;
            margin: 10px 0;
        }
        
        .example {
            background: #e7f3ff;
            padding: 15px;
            border-radius: 4px;
            border-left: 4px solid #0366d6;
            margin: 15px 0;
        }
        
        .toc {
            background: #f8f9fa;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            padding: 20px;
            margin: 20px 0;
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
    </style>
</head>
<body>
    <div class="container">
''')
    
    # Title and overview
    html_parts.append('<h1>McRogueFace API Reference - Complete Documentation</h1>')
    html_parts.append(f'<p><em>Generated on {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</em></p>')
    
    # Table of contents
    html_parts.append('<div class="toc">')
    html_parts.append('<h2>Table of Contents</h2>')
    html_parts.append('<ul>')
    html_parts.append('<li><a href="#functions">Functions</a></li>')
    html_parts.append('<li><a href="#classes">Classes</a></li>')
    html_parts.append('<li><a href="#automation">Automation Module</a></li>')
    html_parts.append('</ul>')
    html_parts.append('</div>')
    
    # Functions section
    html_parts.append('<h2 id="functions">Functions</h2>')
    
    # Group functions by category
    categories = {
        'Scene Management': ['createScene', 'setScene', 'currentScene', 'sceneUI', 'keypressScene'],
        'Audio': ['createSoundBuffer', 'loadMusic', 'playSound', 'getMusicVolume', 'getSoundVolume', 'setMusicVolume', 'setSoundVolume'],
        'UI Utilities': ['find', 'findAll'],
        'System': ['exit', 'getMetrics', 'setTimer', 'delTimer', 'setScale']
    }
    
    for category, functions in categories.items():
        html_parts.append(f'<h3>{category}</h3>')
        for func_name in functions:
            if func_name in function_docs:
                html_parts.append(format_function_html(func_name, function_docs[func_name]))
    
    # Classes section
    html_parts.append('<h2 id="classes">Classes</h2>')
    
    # Get all classes from mcrfpy
    classes = []
    for name in sorted(dir(mcrfpy)):
        if not name.startswith('_'):
            obj = getattr(mcrfpy, name)
            if isinstance(obj, type):
                classes.append((name, obj))
    
    # Generate class documentation
    for class_name, cls in classes:
        html_parts.append(format_class_html_complete(class_name, cls, method_docs, property_docs))
    
    # Automation section
    if hasattr(mcrfpy, 'automation'):
        html_parts.append('<h2 id="automation">Automation Module</h2>')
        html_parts.append('<p>The <code>mcrfpy.automation</code> module provides testing and automation capabilities.</p>')
        
        automation = mcrfpy.automation
        for name in sorted(dir(automation)):
            if not name.startswith('_'):
                obj = getattr(automation, name)
                if callable(obj):
                    html_parts.append(f'<div class="method-section">')
                    html_parts.append(f'<h4><code class="function-signature">automation.{name}</code></h4>')
                    if obj.__doc__:
                        doc_parts = obj.__doc__.split(' - ')
                        if len(doc_parts) > 1:
                            html_parts.append(f'<p>{escape_html(doc_parts[1])}</p>')
                        else:
                            html_parts.append(f'<p>{escape_html(obj.__doc__)}</p>')
                    html_parts.append('</div>')
    
    html_parts.append('</div>')
    html_parts.append('</body>')
    html_parts.append('</html>')
    
    return '\n'.join(html_parts)

def format_function_html(func_name, func_doc):
    """Format a function with complete documentation."""
    html_parts = []
    
    html_parts.append('<div class="method-section">')
    html_parts.append(f'<h4><code class="function-signature">{func_doc["signature"]}</code></h4>')
    html_parts.append(f'<p>{escape_html(func_doc["description"])}</p>')
    
    # Arguments
    if 'args' in func_doc:
        html_parts.append('<div class="arg-list">')
        html_parts.append('<h5>Arguments:</h5>')
        for arg in func_doc['args']:
            html_parts.append('<div class="arg-item">')
            html_parts.append(f'<span class="arg-name">{arg[0]}</span> ')
            html_parts.append(f'<span class="arg-type">({arg[1]})</span>: ')
            html_parts.append(f'{escape_html(arg[2])}')
            html_parts.append('</div>')
        html_parts.append('</div>')
    
    # Returns
    if 'returns' in func_doc:
        html_parts.append('<div class="returns">')
        html_parts.append(f'<strong>Returns:</strong> {escape_html(func_doc["returns"])}')
        html_parts.append('</div>')
    
    # Raises
    if 'raises' in func_doc:
        html_parts.append('<div class="note">')
        html_parts.append(f'<strong>Raises:</strong> {escape_html(func_doc["raises"])}')
        html_parts.append('</div>')
    
    # Note
    if 'note' in func_doc:
        html_parts.append('<div class="note">')
        html_parts.append(f'<strong>Note:</strong> {escape_html(func_doc["note"])}')
        html_parts.append('</div>')
    
    # Example
    if 'example' in func_doc:
        html_parts.append('<div class="example">')
        html_parts.append('<h5>Example:</h5>')
        html_parts.append('<pre><code>')
        html_parts.append(escape_html(func_doc['example']))
        html_parts.append('</code></pre>')
        html_parts.append('</div>')
    
    html_parts.append('</div>')
    
    return '\n'.join(html_parts)

def format_class_html_complete(class_name, cls, method_docs, property_docs):
    """Format a class with complete documentation."""
    html_parts = []
    
    html_parts.append('<div class="method-section">')
    html_parts.append(f'<h3><span class="class-name">{class_name}</span></h3>')
    
    # Class description
    if cls.__doc__:
        html_parts.append(f'<p>{escape_html(cls.__doc__)}</p>')
    
    # Properties
    if class_name in property_docs:
        html_parts.append('<h4>Properties:</h4>')
        for prop_name, prop_desc in property_docs[class_name].items():
            html_parts.append(f'<div class="arg-item">')
            html_parts.append(f'<span class="property">{prop_name}</span>: {escape_html(prop_desc)}')
            html_parts.append('</div>')
    
    # Methods
    methods_to_document = []
    
    # Add inherited methods for UI classes
    if any(base.__name__ == 'Drawable' for base in cls.__bases__ if hasattr(base, '__name__')):
        methods_to_document.extend(['get_bounds', 'move', 'resize'])
    
    # Add class-specific methods
    if class_name in method_docs:
        methods_to_document.extend(method_docs[class_name].keys())
    
    # Add methods from introspection
    for attr_name in dir(cls):
        if not attr_name.startswith('_') and callable(getattr(cls, attr_name)):
            if attr_name not in methods_to_document:
                methods_to_document.append(attr_name)
    
    if methods_to_document:
        html_parts.append('<h4>Methods:</h4>')
        for method_name in set(methods_to_document):
            # Get method documentation
            method_doc = None
            if class_name in method_docs and method_name in method_docs[class_name]:
                method_doc = method_docs[class_name][method_name]
            elif method_name in method_docs.get('Drawable', {}):
                method_doc = method_docs['Drawable'][method_name]
            
            if method_doc:
                html_parts.append(format_method_html(method_name, method_doc))
            else:
                # Basic method with no documentation
                html_parts.append(f'<div class="arg-item">')
                html_parts.append(f'<span class="method">{method_name}(...)</span>')
                html_parts.append('</div>')
    
    html_parts.append('</div>')
    
    return '\n'.join(html_parts)

def format_method_html(method_name, method_doc):
    """Format a method with complete documentation."""
    html_parts = []
    
    html_parts.append('<div style="margin-left: 20px; margin-bottom: 15px;">')
    html_parts.append(f'<h5><code class="method">{method_doc["signature"]}</code></h5>')
    html_parts.append(f'<p>{escape_html(method_doc["description"])}</p>')
    
    # Arguments
    if 'args' in method_doc:
        for arg in method_doc['args']:
            html_parts.append(f'<div style="margin-left: 20px;">')
            html_parts.append(f'<span class="arg-name">{arg[0]}</span> ')
            html_parts.append(f'<span class="arg-type">({arg[1]})</span>: ')
            html_parts.append(f'{escape_html(arg[2])}')
            html_parts.append('</div>')
    
    # Returns
    if 'returns' in method_doc:
        html_parts.append(f'<div style="margin-left: 20px; color: #28a745;">')
        html_parts.append(f'<strong>Returns:</strong> {escape_html(method_doc["returns"])}')
        html_parts.append('</div>')
    
    # Note
    if 'note' in method_doc:
        html_parts.append(f'<div style="margin-left: 20px; color: #856404;">')
        html_parts.append(f'<strong>Note:</strong> {escape_html(method_doc["note"])}')
        html_parts.append('</div>')
    
    # Example
    if 'example' in method_doc:
        html_parts.append(f'<div style="margin-left: 20px;">')
        html_parts.append('<strong>Example:</strong>')
        html_parts.append('<pre><code>')
        html_parts.append(escape_html(method_doc['example']))
        html_parts.append('</code></pre>')
        html_parts.append('</div>')
    
    html_parts.append('</div>')
    
    return '\n'.join(html_parts)

def main():
    """Generate complete HTML documentation with zero missing methods."""
    print("Generating COMPLETE HTML API documentation...")
    
    # Generate HTML
    html_content = generate_complete_html_documentation()
    
    # Write to file
    output_path = Path("docs/api_reference_complete.html")
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ Generated {output_path}")
    print(f"  File size: {len(html_content):,} bytes")
    
    # Count "..." instances
    ellipsis_count = html_content.count('...')
    print(f"  Ellipsis instances: {ellipsis_count}")
    
    if ellipsis_count == 0:
        print("✅ SUCCESS: No missing documentation found!")
    else:
        print(f"❌ WARNING: {ellipsis_count} methods still need documentation")

if __name__ == '__main__':
    main()