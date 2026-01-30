"""Scene graph introspection for the McRogueFace Game API.

Provides functions to serialize the current scene graph to JSON,
extracting element types, bounds, properties, and children.
"""

import hashlib
import json
import time
from typing import Dict, Any, List, Optional, Tuple

import mcrfpy


def get_element_type(element) -> str:
    """Get the type name of a UI element."""
    type_name = type(element).__name__
    # Handle potential wrapper types
    if hasattr(element, '__class__'):
        return element.__class__.__name__
    return type_name


def get_bounds(element) -> Dict[str, float]:
    """Extract bounding box from an element."""
    try:
        if hasattr(element, 'get_bounds'):
            x, y, w, h = element.get_bounds()
            return {"x": x, "y": y, "w": w, "h": h}
        elif hasattr(element, 'x') and hasattr(element, 'y'):
            x = float(element.x) if element.x is not None else 0
            y = float(element.y) if element.y is not None else 0
            w = float(getattr(element, 'w', 0) or 0)
            h = float(getattr(element, 'h', 0) or 0)
            return {"x": x, "y": y, "w": w, "h": h}
    except Exception:
        pass
    return {"x": 0, "y": 0, "w": 0, "h": 0}


def is_interactive(element) -> bool:
    """Check if an element has interactive callbacks."""
    return (
        getattr(element, 'on_click', None) is not None or
        getattr(element, 'on_enter', None) is not None or
        getattr(element, 'on_exit', None) is not None or
        getattr(element, 'on_cell_click', None) is not None
    )


def serialize_color(color) -> Optional[Dict[str, int]]:
    """Serialize a color object to dict."""
    if color is None:
        return None
    try:
        return {
            "r": int(color.r),
            "g": int(color.g),
            "b": int(color.b),
            "a": int(getattr(color, 'a', 255))
        }
    except Exception:
        return None


def serialize_vector(vec) -> Optional[Dict[str, float]]:
    """Serialize a Vector object to dict."""
    if vec is None:
        return None
    try:
        return {"x": float(vec.x), "y": float(vec.y)}
    except Exception:
        return None


def serialize_entity(entity) -> Dict[str, Any]:
    """Serialize an Entity to dict."""
    data = {
        "type": "Entity",
        "name": getattr(entity, 'name', None) or "",
        "grid_x": float(getattr(entity, 'grid_x', 0)),
        "grid_y": float(getattr(entity, 'grid_y', 0)),
        "sprite_index": int(getattr(entity, 'sprite_index', 0)),
        "visible": bool(getattr(entity, 'visible', True)),
    }
    return data


def serialize_grid(grid, respect_perspective: bool = True) -> Dict[str, Any]:
    """Serialize a Grid element with its entities.

    Args:
        grid: The Grid element to serialize
        respect_perspective: If True and grid has a perspective entity,
            only include entities visible to that entity's FOV

    Returns:
        Dictionary representation of the grid
    """
    bounds = get_bounds(grid)

    # Get grid dimensions
    grid_size = getattr(grid, 'grid_size', None)
    if grid_size:
        try:
            grid_w = int(grid_size.x) if hasattr(grid_size, 'x') else int(grid_size[0])
            grid_h = int(grid_size.y) if hasattr(grid_size, 'y') else int(grid_size[1])
        except Exception:
            grid_w = grid_h = 0
    else:
        grid_w = int(getattr(grid, 'grid_w', 0))
        grid_h = int(getattr(grid, 'grid_h', 0))

    # Get camera info
    center = getattr(grid, 'center', None)
    zoom = float(getattr(grid, 'zoom', 1.0))

    # Check for perspective (player POV)
    perspective_entity = getattr(grid, 'perspective', None)
    perspective_enabled = bool(getattr(grid, 'perspective_enabled', False))
    has_perspective = perspective_entity is not None and perspective_enabled

    # Serialize entities, optionally filtering by FOV
    entities = []
    hidden_count = 0
    try:
        for entity in grid.entities:
            # Check if entity is visible from perspective
            if has_perspective and respect_perspective:
                try:
                    entity_pos = (int(entity.grid_x), int(entity.grid_y))
                    in_fov = grid.is_in_fov(entity_pos)
                    if not in_fov:
                        hidden_count += 1
                        continue  # Skip entities not in FOV
                except Exception:
                    pass  # If FOV check fails, include the entity

            entities.append(serialize_entity(entity))
    except Exception:
        pass

    data = {
        "type": "Grid",
        "name": getattr(grid, 'name', None) or "",
        "bounds": bounds,
        "visible": bool(getattr(grid, 'visible', True)),
        "interactive": is_interactive(grid),
        "grid_size": {"w": grid_w, "h": grid_h},
        "zoom": zoom,
        "center": serialize_vector(center),
        "entity_count": len(entities),
        "entities": entities,
        "has_cell_click": getattr(grid, 'on_cell_click', None) is not None,
        "has_cell_enter": getattr(grid, 'on_cell_enter', None) is not None,
    }

    # Add perspective info
    if has_perspective:
        data["perspective"] = {
            "enabled": True,
            "entity_name": getattr(perspective_entity, 'name', None) or "",
            "entity_pos": {
                "x": float(getattr(perspective_entity, 'grid_x', 0)),
                "y": float(getattr(perspective_entity, 'grid_y', 0))
            },
            "fov_radius": int(getattr(grid, 'fov_radius', 0)),
            "hidden_entities": hidden_count,
            "note": "Entities filtered by FOV - only showing what perspective entity can see"
        }
    else:
        data["perspective"] = {
            "enabled": False,
            "note": "No perspective set - showing all entities (omniscient view)"
        }

    # Add cell size estimate if texture available
    texture = getattr(grid, 'texture', None)
    if texture:
        data["has_texture"] = True

    return data


def serialize_element(element, depth: int = 0, max_depth: int = 10,
                      respect_perspective: bool = True) -> Dict[str, Any]:
    """Serialize a UI element to a dictionary.

    Args:
        element: The UI element to serialize
        depth: Current recursion depth
        max_depth: Maximum recursion depth for children
        respect_perspective: If True, filter grid entities by perspective FOV

    Returns:
        Dictionary representation of the element
    """
    element_type = get_element_type(element)
    bounds = get_bounds(element)

    # Special handling for Grid
    if element_type == "Grid":
        return serialize_grid(element, respect_perspective=respect_perspective)

    data = {
        "type": element_type,
        "name": getattr(element, 'name', None) or "",
        "bounds": bounds,
        "visible": bool(getattr(element, 'visible', True)),
        "interactive": is_interactive(element),
        "z_index": int(getattr(element, 'z_index', 0)),
    }

    # Add type-specific properties
    if element_type == "Caption":
        data["text"] = str(getattr(element, 'text', ""))
        data["font_size"] = float(getattr(element, 'font_size', 12))
        data["fill_color"] = serialize_color(getattr(element, 'fill_color', None))

    elif element_type == "Frame":
        data["fill_color"] = serialize_color(getattr(element, 'fill_color', None))
        data["outline"] = float(getattr(element, 'outline', 0))
        data["clip_children"] = bool(getattr(element, 'clip_children', False))

    elif element_type == "Sprite":
        data["sprite_index"] = int(getattr(element, 'sprite_index', 0))
        data["scale"] = float(getattr(element, 'scale', 1.0))

    elif element_type in ("Line", "Circle", "Arc"):
        data["color"] = serialize_color(getattr(element, 'color', None))
        if element_type == "Circle":
            data["radius"] = float(getattr(element, 'radius', 0))
        elif element_type == "Arc":
            data["radius"] = float(getattr(element, 'radius', 0))
            data["start_angle"] = float(getattr(element, 'start_angle', 0))
            data["end_angle"] = float(getattr(element, 'end_angle', 0))

    # Handle children recursively
    if hasattr(element, 'children') and depth < max_depth:
        children = []
        try:
            for child in element.children:
                children.append(serialize_element(child, depth + 1, max_depth,
                                                  respect_perspective))
        except Exception:
            pass
        data["children"] = children
        data["child_count"] = len(children)

    return data


def serialize_scene(respect_perspective: bool = True) -> Dict[str, Any]:
    """Serialize the entire current scene graph.

    Args:
        respect_perspective: If True, filter grid entities by perspective FOV.
                            If False, show all entities (omniscient view).

    Returns:
        Dictionary with scene name, viewport info, and all elements
    """
    scene = mcrfpy.current_scene
    scene_name = scene.name if scene else "unknown"

    # Get viewport size
    try:
        width, height = mcrfpy.automation.size()
    except Exception:
        width, height = 1024, 768

    # Get scene UI elements from the scene object directly
    elements = []
    try:
        if scene:
            for element in scene.children:
                elements.append(serialize_element(element,
                                                  respect_perspective=respect_perspective))
    except Exception as e:
        pass

    return {
        "scene_name": scene_name,
        "timestamp": time.time(),
        "viewport": {"width": width, "height": height},
        "element_count": len(elements),
        "elements": elements,
        "perspective_mode": "respect_fov" if respect_perspective else "omniscient"
    }


def get_scene_hash() -> str:
    """Compute a hash of the current scene state for change detection.

    This is a lightweight hash that captures:
    - Scene name
    - Number of top-level elements
    - Element names and types

    Returns:
        Hex string hash of scene state
    """
    scene = mcrfpy.current_scene
    scene_name = scene.name if scene else "unknown"

    state_parts = [scene_name]

    try:
        if scene:
            ui = scene.children
            state_parts.append(str(len(ui)))

            for element in ui:
                element_type = get_element_type(element)
                name = getattr(element, 'name', '') or ''
                state_parts.append(f"{element_type}:{name}")

                # For captions, include text (truncated)
                if element_type == "Caption":
                    text = str(getattr(element, 'text', ''))[:50]
                    state_parts.append(text)

                # For grids, include entity count
                if element_type == "Grid":
                    try:
                        entity_count = len(list(element.entities))
                        state_parts.append(f"entities:{entity_count}")
                    except Exception:
                        pass
    except Exception:
        pass

    state_str = "|".join(state_parts)
    return hashlib.md5(state_str.encode()).hexdigest()[:16]
