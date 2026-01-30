"""Game metadata management for the McRogueFace Game API.

Stores and retrieves game-specific metadata that helps external clients
understand the game's controls, purpose, and current state.
"""

from typing import Dict, Any, List, Optional
import time

# Global metadata storage
_metadata: Dict[str, Any] = {
    "game_name": "McRogueFace Game",
    "version": "0.1.0",
    "description": "A game built with McRogueFace engine",
    "controls": {
        "movement": "W/A/S/D or Arrow keys",
        "interact": "Space or Enter",
        "cancel": "Escape",
    },
    "scenes": [],
    "custom_hints": "",
    "keyboard_hints": [],
}


def get_game_metadata() -> Dict[str, Any]:
    """Get the current game metadata.

    Returns:
        Dictionary containing game metadata
    """
    import mcrfpy

    # Add dynamic data
    result = dict(_metadata)
    scene = mcrfpy.current_scene
    result["current_scene"] = scene.name if scene else "unknown"
    result["timestamp"] = time.time()

    # Get viewport size
    try:
        width, height = mcrfpy.automation.size()
        result["viewport"] = {"width": width, "height": height}
    except Exception:
        result["viewport"] = {"width": 1024, "height": 768}

    return result


def set_game_metadata(data: Dict[str, Any]) -> None:
    """Update game metadata.

    Games can call this to provide richer information to API clients.

    Args:
        data: Dictionary of metadata fields to update
    """
    global _metadata

    # Allowed fields to update
    allowed_fields = {
        "game_name",
        "version",
        "description",
        "controls",
        "scenes",
        "custom_hints",
        "keyboard_hints",
        "author",
        "url",
        "tags",
    }

    for key, value in data.items():
        if key in allowed_fields:
            _metadata[key] = value


def set_game_info(
    name: Optional[str] = None,
    version: Optional[str] = None,
    description: Optional[str] = None,
    author: Optional[str] = None,
) -> None:
    """Convenience function to set basic game info.

    Args:
        name: Game name
        version: Game version string
        description: Brief description
        author: Author name
    """
    if name is not None:
        _metadata["game_name"] = name
    if version is not None:
        _metadata["version"] = version
    if description is not None:
        _metadata["description"] = description
    if author is not None:
        _metadata["author"] = author


def set_controls(controls: Dict[str, str]) -> None:
    """Set control descriptions.

    Args:
        controls: Dict mapping action names to control descriptions
    """
    _metadata["controls"] = controls


def set_keyboard_hints(hints: List[Dict[str, str]]) -> None:
    """Set keyboard hints for the API.

    Args:
        hints: List of dicts with 'key' and 'action' fields
    """
    _metadata["keyboard_hints"] = hints


def add_keyboard_hint(key: str, action: str) -> None:
    """Add a single keyboard hint.

    Args:
        key: Key or key combination
        action: Description of what it does
    """
    if "keyboard_hints" not in _metadata:
        _metadata["keyboard_hints"] = []

    _metadata["keyboard_hints"].append({
        "key": key,
        "action": action
    })


def set_custom_hints(hints: str) -> None:
    """Set custom hints text for LLM context.

    This can be any text that helps an LLM understand
    the game better - strategy tips, game rules, etc.

    Args:
        hints: Free-form hint text
    """
    _metadata["custom_hints"] = hints


def register_scene(scene_name: str, description: Optional[str] = None) -> None:
    """Register a scene for the API.

    Args:
        scene_name: Name of the scene
        description: Optional description of what this scene is for
    """
    if "scenes" not in _metadata:
        _metadata["scenes"] = []

    scene_info = {"name": scene_name}
    if description:
        scene_info["description"] = description

    # Update if exists, add if not
    for i, s in enumerate(_metadata["scenes"]):
        if s.get("name") == scene_name:
            _metadata["scenes"][i] = scene_info
            return

    _metadata["scenes"].append(scene_info)
