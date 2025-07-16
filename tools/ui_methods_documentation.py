# Comprehensive UI Element Method Documentation
# This can be inserted into generate_api_docs_html.py in the method_docs dictionary

ui_method_docs = {
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

# Additional property documentation to complement the methods
ui_property_docs = {
    'Drawable': {
        'visible': 'bool: Whether this element is rendered (default: True)',
        'opacity': 'float: Transparency level from 0.0 (invisible) to 1.0 (opaque)',
        'z_index': 'int: Rendering order, higher values appear on top',
        'name': 'str: Optional name for finding elements',
        'x': 'float: Horizontal position in pixels',
        'y': 'float: Vertical position in pixels',
        'click': 'callable: Click event handler function'
    },
    'Caption': {
        'text': 'str: The displayed text content',
        'font': 'Font: Font used for rendering',
        'fill_color': 'Color: Text color',
        'outline_color': 'Color: Text outline color',
        'outline': 'float: Outline thickness in pixels',
        'w': 'float: Read-only computed width based on text',
        'h': 'float: Read-only computed height based on text'
    },
    'Entity': {
        'grid_x': 'float: X position in grid coordinates',
        'grid_y': 'float: Y position in grid coordinates',
        'sprite_index': 'int: Index of sprite in texture atlas',
        'texture': 'Texture: Texture used for rendering',
        'gridstate': 'list: Read-only list of GridPointState objects'
    },
    'Frame': {
        'w': 'float: Width in pixels',
        'h': 'float: Height in pixels',
        'fill_color': 'Color: Background fill color',
        'outline_color': 'Color: Border color',
        'outline': 'float: Border thickness in pixels',
        'children': 'UICollection: Child drawable elements',
        'clip_children': 'bool: Whether to clip children to frame bounds'
    },
    'Grid': {
        'grid_size': 'tuple: Read-only (width, height) in tiles',
        'grid_x': 'int: Read-only width in tiles',
        'grid_y': 'int: Read-only height in tiles',
        'tile_width': 'int: Width of each tile in pixels',
        'tile_height': 'int: Height of each tile in pixels',
        'center': 'tuple: (x, y) center point for viewport',
        'zoom': 'float: Scale factor for rendering',
        'texture': 'Texture: Tile texture atlas',
        'background_color': 'Color: Grid background color',
        'entities': 'EntityCollection: Entities in this grid',
        'points': 'list: 2D array of GridPoint objects'
    },
    'Sprite': {
        'texture': 'Texture: The displayed texture',
        'sprite_index': 'int: Index in texture atlas',
        'scale': 'float: Scaling factor',
        'w': 'float: Read-only computed width (texture width * scale)',
        'h': 'float: Read-only computed height (texture height * scale)'
    }
}