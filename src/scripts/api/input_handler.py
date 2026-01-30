"""Input action handling for the McRogueFace Game API.

Dispatches input actions to the mcrfpy.automation module for
keyboard/mouse injection into the game.
"""

from typing import Dict, Any, Optional

import mcrfpy

from .affordances import find_affordance_by_id, find_affordance_by_label


def execute_action(action_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute an input action.

    Args:
        action_data: Dictionary describing the action to perform

    Returns:
        Result dictionary with success status

    Raises:
        ValueError: If action is invalid or missing required fields
    """
    action = action_data.get("action")

    if action == "click":
        return execute_click(action_data)
    elif action == "click_affordance":
        return execute_click_affordance(action_data)
    elif action == "type":
        return execute_type(action_data)
    elif action == "key":
        return execute_key(action_data)
    elif action == "hotkey":
        return execute_hotkey(action_data)
    elif action == "grid_click":
        return execute_grid_click(action_data)
    elif action == "move":
        return execute_move(action_data)
    elif action == "drag":
        return execute_drag(action_data)
    else:
        raise ValueError(f"Unknown action: {action}")


def execute_click(data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a mouse click at coordinates.

    Required fields:
        x: X coordinate
        y: Y coordinate

    Optional fields:
        button: 'left', 'right', or 'middle' (default: 'left')
        clicks: Number of clicks (default: 1)
    """
    x = data.get("x")
    y = data.get("y")

    if x is None or y is None:
        raise ValueError("click requires 'x' and 'y' coordinates")

    button = data.get("button", "left")
    clicks = data.get("clicks", 1)

    # Validate button
    if button not in ("left", "right", "middle"):
        raise ValueError(f"Invalid button: {button}")

    # Use automation module - click expects pos as tuple
    mcrfpy.automation.click(pos=(int(x), int(y)), clicks=clicks, button=button)

    return {
        "success": True,
        "action": "click",
        "x": x,
        "y": y,
        "button": button,
        "clicks": clicks
    }


def execute_click_affordance(data: Dict[str, Any]) -> Dict[str, Any]:
    """Click an affordance by ID or label.

    Required fields (one of):
        id: Affordance ID
        label: Affordance label (supports fuzzy matching)

    Optional fields:
        button: 'left', 'right', or 'middle' (default: 'left')
    """
    affordance = None

    if "id" in data:
        affordance = find_affordance_by_id(int(data["id"]))
        if not affordance:
            raise ValueError(f"Affordance with ID {data['id']} not found")
    elif "label" in data:
        affordance = find_affordance_by_label(data["label"], fuzzy=True)
        if not affordance:
            raise ValueError(f"Affordance with label '{data['label']}' not found")
    else:
        raise ValueError("click_affordance requires 'id' or 'label'")

    # Get center of affordance bounds
    bounds = affordance["bounds"]
    center_x = bounds["x"] + bounds["w"] / 2
    center_y = bounds["y"] + bounds["h"] / 2

    button = data.get("button", "left")

    mcrfpy.automation.click(pos=(int(center_x), int(center_y)), button=button)

    return {
        "success": True,
        "action": "click_affordance",
        "affordance_id": affordance["id"],
        "affordance_label": affordance.get("label"),
        "x": center_x,
        "y": center_y,
        "button": button
    }


def execute_type(data: Dict[str, Any]) -> Dict[str, Any]:
    """Type text into the game.

    Required fields:
        text: String to type

    Optional fields:
        interval: Delay between keystrokes in seconds (default: 0)
    """
    text = data.get("text")
    if text is None:
        raise ValueError("type requires 'text' field")

    interval = float(data.get("interval", 0))

    mcrfpy.automation.typewrite(str(text), interval=interval)

    return {
        "success": True,
        "action": "type",
        "text": text,
        "length": len(text)
    }


def execute_key(data: Dict[str, Any]) -> Dict[str, Any]:
    """Press a single key.

    Required fields:
        key: Key name (e.g., 'ESCAPE', 'SPACE', 'W', 'F1')
    """
    key = data.get("key")
    if key is None:
        raise ValueError("key requires 'key' field")

    # Normalize key name
    key = str(key).upper()

    # Map common key names
    key_map = {
        "ESCAPE": "escape",
        "ESC": "escape",
        "SPACE": "space",
        "ENTER": "return",
        "RETURN": "return",
        "TAB": "tab",
        "BACKSPACE": "backspace",
        "DELETE": "delete",
        "UP": "up",
        "DOWN": "down",
        "LEFT": "left",
        "RIGHT": "right",
        "SHIFT": "shift",
        "CTRL": "ctrl",
        "CONTROL": "ctrl",
        "ALT": "alt",
    }

    normalized_key = key_map.get(key, key.lower())

    # Press and release
    mcrfpy.automation.keyDown(normalized_key)
    mcrfpy.automation.keyUp(normalized_key)

    return {
        "success": True,
        "action": "key",
        "key": key
    }


def execute_hotkey(data: Dict[str, Any]) -> Dict[str, Any]:
    """Press a key combination.

    Required fields:
        keys: List of keys to press together (e.g., ['ctrl', 's'])
    """
    keys = data.get("keys")
    if keys is None or not isinstance(keys, list):
        raise ValueError("hotkey requires 'keys' as a list")

    if len(keys) == 0:
        raise ValueError("hotkey requires at least one key")

    # Press all modifier keys down
    for key in keys[:-1]:
        mcrfpy.automation.keyDown(str(key).lower())

    # Press and release the final key
    final_key = str(keys[-1]).lower()
    mcrfpy.automation.keyDown(final_key)
    mcrfpy.automation.keyUp(final_key)

    # Release modifier keys in reverse order
    for key in reversed(keys[:-1]):
        mcrfpy.automation.keyUp(str(key).lower())

    return {
        "success": True,
        "action": "hotkey",
        "keys": keys
    }


def execute_grid_click(data: Dict[str, Any]) -> Dict[str, Any]:
    """Click a specific cell in a grid.

    Required fields:
        cell: Dict with 'x' and 'y' grid coordinates

    Optional fields:
        grid_id: Name of the grid (uses first grid if not specified)
        button: 'left', 'right', or 'middle' (default: 'left')
    """
    cell = data.get("cell")
    if cell is None or "x" not in cell or "y" not in cell:
        raise ValueError("grid_click requires 'cell' with 'x' and 'y'")

    cell_x = int(cell["x"])
    cell_y = int(cell["y"])
    button = data.get("button", "left")
    grid_name = data.get("grid_id")

    # Find the grid
    scene = mcrfpy.current_scene
    if not scene:
        raise ValueError("No active scene")

    target_grid = None
    for element in scene.children:
        if type(element).__name__ == "Grid":
            name = getattr(element, 'name', None)
            if grid_name is None or name == grid_name:
                target_grid = element
                break

    if target_grid is None:
        raise ValueError(f"Grid not found" + (f": {grid_name}" if grid_name else ""))

    # Calculate pixel position from cell coordinates
    # Get grid bounds and cell size
    try:
        gx, gy, gw, gh = target_grid.get_bounds()
    except Exception:
        gx = float(target_grid.x)
        gy = float(target_grid.y)
        gw = float(target_grid.w)
        gh = float(target_grid.h)

    grid_size = target_grid.grid_size
    grid_w = int(grid_size.x) if hasattr(grid_size, 'x') else int(grid_size[0])
    grid_h = int(grid_size.y) if hasattr(grid_size, 'y') else int(grid_size[1])

    zoom = float(getattr(target_grid, 'zoom', 1.0))
    center = getattr(target_grid, 'center', None)

    # Calculate cell size in pixels
    # This is approximate - actual rendering may differ based on zoom/center
    if grid_w > 0 and grid_h > 0:
        cell_pixel_w = gw / grid_w
        cell_pixel_h = gh / grid_h

        # Calculate center of target cell
        pixel_x = gx + (cell_x + 0.5) * cell_pixel_w
        pixel_y = gy + (cell_y + 0.5) * cell_pixel_h

        mcrfpy.automation.click(pos=(int(pixel_x), int(pixel_y)), button=button)

        return {
            "success": True,
            "action": "grid_click",
            "cell": {"x": cell_x, "y": cell_y},
            "pixel": {"x": pixel_x, "y": pixel_y},
            "button": button
        }
    else:
        raise ValueError("Grid has invalid dimensions")


def execute_move(data: Dict[str, Any]) -> Dict[str, Any]:
    """Move the mouse to coordinates without clicking.

    Required fields:
        x: X coordinate
        y: Y coordinate

    Optional fields:
        duration: Time to move in seconds (default: 0)
    """
    x = data.get("x")
    y = data.get("y")

    if x is None or y is None:
        raise ValueError("move requires 'x' and 'y' coordinates")

    duration = float(data.get("duration", 0))

    mcrfpy.automation.moveTo(int(x), int(y), duration=duration)

    return {
        "success": True,
        "action": "move",
        "x": x,
        "y": y,
        "duration": duration
    }


def execute_drag(data: Dict[str, Any]) -> Dict[str, Any]:
    """Drag from current position or specified start to end.

    Required fields:
        end_x: End X coordinate
        end_y: End Y coordinate

    Optional fields:
        start_x: Start X coordinate
        start_y: Start Y coordinate
        button: 'left', 'right', or 'middle' (default: 'left')
        duration: Time to drag in seconds (default: 0)
    """
    end_x = data.get("end_x")
    end_y = data.get("end_y")

    if end_x is None or end_y is None:
        raise ValueError("drag requires 'end_x' and 'end_y' coordinates")

    start_x = data.get("start_x")
    start_y = data.get("start_y")
    button = data.get("button", "left")
    duration = float(data.get("duration", 0))

    # Move to start if specified
    if start_x is not None and start_y is not None:
        mcrfpy.automation.moveTo(int(start_x), int(start_y))

    mcrfpy.automation.dragTo(int(end_x), int(end_y), duration=duration, button=button)

    return {
        "success": True,
        "action": "drag",
        "end_x": end_x,
        "end_y": end_y,
        "button": button,
        "duration": duration
    }
