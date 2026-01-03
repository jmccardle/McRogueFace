"""McRogueFace - Turn-Based Game Loop (combat_turn_system)

Documentation: https://mcrogueface.github.io/cookbook/combat_turn_system
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/combat/combat_turn_system.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

def create_turn_order_ui(turn_manager, x=800, y=50):
    """Create a visual turn order display."""
    ui = mcrfpy.sceneUI(mcrfpy.currentScene())

    # Background frame
    frame = mcrfpy.Frame(x, y, 200, 300)
    frame.fill_color = mcrfpy.Color(30, 30, 30, 200)
    frame.outline = 2
    frame.outline_color = mcrfpy.Color(100, 100, 100)
    ui.append(frame)

    # Title
    title = mcrfpy.Caption("Turn Order", x + 10, y + 10)
    title.fill_color = mcrfpy.Color(255, 255, 255)
    ui.append(title)

    return frame

def update_turn_order_display(frame, turn_manager, x=800, y=50):
    """Update the turn order display."""
    ui = mcrfpy.sceneUI(mcrfpy.currentScene())

    # Clear old entries (keep frame and title)
    # In practice, store references to caption objects and update them

    for i, actor_data in enumerate(turn_manager.actors):
        actor = actor_data["actor"]
        is_current = (i == turn_manager.current)

        # Actor name/type
        name = getattr(actor, 'name', f"Actor {i}")
        color = mcrfpy.Color(255, 255, 0) if is_current else mcrfpy.Color(200, 200, 200)

        caption = mcrfpy.Caption(name, x + 10, y + 40 + i * 25)
        caption.fill_color = color
        ui.append(caption)