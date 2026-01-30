"""Affordance detection for the McRogueFace Game API.

Analyzes the UI hierarchy to extract semantic meaning and identify
interactive elements with their labels and action types.
"""

from typing import Dict, Any, List, Optional, Tuple

import mcrfpy


# Global affordance ID counter (reset per extraction)
_affordance_id = 0


def get_element_type(element) -> str:
    """Get the type name of a UI element."""
    return type(element).__name__


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


def find_label_in_children(element) -> Optional[str]:
    """Search children for Caption text to use as label."""
    if not hasattr(element, 'children'):
        return None

    try:
        for child in element.children:
            child_type = get_element_type(child)
            if child_type == "Caption":
                text = str(getattr(child, 'text', ''))
                if text.strip():
                    return text.strip()
            # Recurse into child frames
            if child_type == "Frame":
                label = find_label_in_children(child)
                if label:
                    return label
    except Exception:
        pass

    return None


def find_icon_in_children(element) -> Optional[int]:
    """Search children for Sprite to identify icon buttons."""
    if not hasattr(element, 'children'):
        return None

    try:
        for child in element.children:
            child_type = get_element_type(child)
            if child_type == "Sprite":
                return int(getattr(child, 'sprite_index', 0))
    except Exception:
        pass

    return None


def find_label(element) -> Optional[str]:
    """Find the best label for an interactive element.

    Priority:
    1. Caption child text (most user-visible)
    2. Element name property (developer hint)
    3. Nearby caption text (for icon buttons)

    Returns the most user-friendly label for display/matching.
    """
    element_type = get_element_type(element)

    # For Caption elements, use their text directly
    if element_type == "Caption":
        text = str(getattr(element, 'text', ''))
        if text.strip():
            return text.strip()

    # Search children for Caption first (most visible to user)
    label = find_label_in_children(element)
    if label:
        return label

    # Fall back to element name (developer hint)
    name = getattr(element, 'name', None)
    if name and str(name).strip():
        return str(name).strip()

    # For Sprite buttons, mention it's an icon
    if element_type == "Sprite":
        sprite_index = int(getattr(element, 'sprite_index', 0))
        return f"Icon button (sprite #{sprite_index})"

    return None


def classify_affordance(element) -> str:
    """Classify what type of affordance this element represents."""
    element_type = get_element_type(element)

    if element_type == "Grid":
        if getattr(element, 'on_cell_click', None):
            return "interactive_grid"
        return "grid"

    if element_type == "Caption":
        if getattr(element, 'on_click', None):
            return "text_button"
        return "label"

    if element_type == "Sprite":
        if getattr(element, 'on_click', None):
            return "icon_button"
        return "icon"

    if element_type == "Frame":
        has_click = getattr(element, 'on_click', None) is not None

        # Frame with click + caption child = button
        if has_click:
            label = find_label_in_children(element)
            icon = find_icon_in_children(element)
            if label and icon is not None:
                return "button"  # Has both text and icon
            elif label:
                return "text_button"
            elif icon is not None:
                return "icon_button"
            return "clickable_area"

        # Frame without click but with children = container
        if hasattr(element, 'children'):
            try:
                if len(list(element.children)) > 0:
                    return "container"
            except Exception:
                pass

        return "panel"

    return "unknown"


def get_accepted_actions(element, affordance_type: str) -> List[str]:
    """Determine what actions an affordance accepts."""
    actions = []

    if getattr(element, 'on_click', None):
        actions.append("click")

    if getattr(element, 'on_enter', None) or getattr(element, 'on_exit', None):
        actions.append("hover")

    if affordance_type == "interactive_grid":
        actions.append("grid_cell_click")
        if getattr(element, 'on_cell_enter', None):
            actions.append("grid_cell_hover")

    return actions if actions else ["none"]


def extract_affordance(element, parent_bounds: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
    """Extract affordance information from a single element.

    Args:
        element: UI element to analyze
        parent_bounds: Parent's bounds for relative positioning

    Returns:
        Affordance dict or None if not interactive
    """
    global _affordance_id

    element_type = get_element_type(element)
    has_click = getattr(element, 'on_click', None) is not None
    has_cell_click = getattr(element, 'on_cell_click', None) is not None
    has_hover = (getattr(element, 'on_enter', None) is not None or
                 getattr(element, 'on_exit', None) is not None)

    # Skip non-interactive elements (unless they're grids with cell callbacks)
    if not (has_click or has_cell_click or has_hover):
        return None

    bounds = get_bounds(element)
    label = find_label(element)
    affordance_type = classify_affordance(element)
    actions = get_accepted_actions(element, affordance_type)

    _affordance_id += 1

    affordance = {
        "id": _affordance_id,
        "type": affordance_type,
        "element_type": element_type,
        "label": label,
        "bounds": bounds,
        "actions": actions,
    }

    # Add grid-specific info
    if element_type == "Grid":
        grid_size = getattr(element, 'grid_size', None)
        if grid_size:
            try:
                grid_w = int(grid_size.x) if hasattr(grid_size, 'x') else int(grid_size[0])
                grid_h = int(grid_size.y) if hasattr(grid_size, 'y') else int(grid_size[1])
                affordance["grid_size"] = {"w": grid_w, "h": grid_h}
            except Exception:
                pass

        # Count entities
        try:
            entity_count = len(list(element.entities))
            affordance["entity_count"] = entity_count
        except Exception:
            pass

    # Add hint if name was used
    name = getattr(element, 'name', None)
    if name and str(name).strip():
        affordance["hint"] = f"Developer label: {name}"

    return affordance


def extract_affordances_recursive(element, affordances: List[Dict], depth: int = 0, max_depth: int = 10) -> None:
    """Recursively extract affordances from element and children.

    Args:
        element: Current element to process
        affordances: List to append affordances to
        depth: Current recursion depth
        max_depth: Maximum depth to recurse
    """
    if depth > max_depth:
        return

    # Extract affordance for this element
    affordance = extract_affordance(element)
    if affordance:
        affordances.append(affordance)

    # Process children
    if hasattr(element, 'children'):
        try:
            for child in element.children:
                extract_affordances_recursive(child, affordances, depth + 1, max_depth)
        except Exception:
            pass


def extract_affordances() -> List[Dict[str, Any]]:
    """Extract all interactive affordances from the current scene.

    Returns:
        List of affordance dictionaries
    """
    global _affordance_id
    _affordance_id = 0  # Reset counter

    scene = mcrfpy.current_scene
    affordances = []

    try:
        if scene:
            for element in scene.children:
                extract_affordances_recursive(element, affordances)
    except Exception as e:
        pass

    return affordances


def extract_keyboard_hints() -> List[Dict[str, str]]:
    """Extract keyboard control hints.

    This is a placeholder that returns common roguelike controls.
    Games can override this via the metadata endpoint.

    Returns:
        List of keyboard hint dictionaries
    """
    # Default roguelike controls - games should customize via metadata
    return [
        {"key": "W/A/S/D", "action": "Move"},
        {"key": "Arrow keys", "action": "Move (alternative)"},
        {"key": "ESCAPE", "action": "Menu/Cancel"},
        {"key": "SPACE", "action": "Confirm/Interact"},
        {"key": "1-9", "action": "Use inventory item"},
    ]


def find_affordance_by_id(affordance_id: int) -> Optional[Dict[str, Any]]:
    """Find an affordance by its ID.

    Args:
        affordance_id: The ID to search for

    Returns:
        The affordance dict or None
    """
    affordances = extract_affordances()
    for aff in affordances:
        if aff.get("id") == affordance_id:
            return aff
    return None


def find_affordance_by_label(label: str, fuzzy: bool = True) -> Optional[Dict[str, Any]]:
    """Find an affordance by its label.

    Args:
        label: The label to search for
        fuzzy: If True, do case-insensitive substring matching

    Returns:
        The affordance dict or None
    """
    affordances = extract_affordances()
    label_lower = label.lower()

    for aff in affordances:
        aff_label = aff.get("label")
        if aff_label is None:
            continue

        if fuzzy:
            if label_lower in aff_label.lower():
                return aff
        else:
            if aff_label == label:
                return aff

    return None
