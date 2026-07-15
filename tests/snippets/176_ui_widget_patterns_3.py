# mcrf: objects=[Caption,Color,Frame,InputState,MouseButton,Scene] verified=0.2.8-dev status=ok
# Toggle / Checkbox pattern - a button that toggles state and updates its appearance.
import mcrfpy

scene = mcrfpy.Scene("menu")
ui = scene.children

root = mcrfpy.Frame(pos=(50, 50), size=(300, 400),
                     fill_color=mcrfpy.Color(30, 30, 40))
root.outline_color = mcrfpy.Color(80, 80, 100)
root.outline = 2
ui.append(root)


def make_toggle(parent, pos, label_text, initial=False, on_change=None):
    """Create a toggle with visual state indicator."""
    state = {"checked": initial}

    frame = mcrfpy.Frame(pos=pos, size=(160, 28),
                          fill_color=mcrfpy.Color(40, 40, 50))

    # Checkbox indicator
    indicator = mcrfpy.Frame(pos=(6, 6), size=(16, 16))
    indicator.outline = 1
    indicator.outline_color = mcrfpy.Color(120, 120, 140)
    frame.children.append(indicator)

    # Label
    label = mcrfpy.Caption(text=label_text, pos=(30, 5))
    label.fill_color = mcrfpy.Color(200, 200, 200)
    frame.children.append(label)

    def update_visual():
        if state["checked"]:
            indicator.fill_color = mcrfpy.Color(100, 180, 100)
        else:
            indicator.fill_color = mcrfpy.Color(50, 50, 60)

    def toggle(pos, button, action):
        if button == mcrfpy.MouseButton.LEFT and action == mcrfpy.InputState.PRESSED:
            state["checked"] = not state["checked"]
            update_visual()
            if on_change:
                on_change(state["checked"])

    frame.on_click = toggle
    update_visual()

    parent.children.append(frame)
    return state  # Return state dict for external access


def set_music_volume(v):
    print(f"music volume: {v}")


# Usage
music_toggle = make_toggle(root, (20, 20), "Music", initial=True,
                            on_change=lambda on: set_music_volume(1.0 if on else 0.0))

mcrfpy.current_scene = scene
