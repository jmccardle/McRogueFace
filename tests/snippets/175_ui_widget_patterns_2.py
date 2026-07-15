# mcrf: objects=[Caption,Color,Frame,InputState,MouseButton,Scene] verified=0.2.8-dev status=ok
# Button pattern - a clickable frame with label and hover feedback.
import mcrfpy

scene = mcrfpy.Scene("menu")
ui = scene.children

root = mcrfpy.Frame(pos=(50, 50), size=(300, 400),
                     fill_color=mcrfpy.Color(30, 30, 40))
root.outline_color = mcrfpy.Color(80, 80, 100)
root.outline = 2
ui.append(root)


def make_button(parent, pos, text, on_click):
    """Create a button with hover effects."""
    btn = mcrfpy.Frame(pos=pos, size=(120, 32),
                        fill_color=mcrfpy.Color(60, 60, 80))
    btn.outline_color = mcrfpy.Color(100, 100, 140)
    btn.outline = 1

    label = mcrfpy.Caption(text=text, pos=(10, 6))
    label.fill_color = mcrfpy.Color(220, 220, 220)
    btn.children.append(label)

    # Hover effects - on_enter/on_exit receive (pos: Vector)
    btn.on_enter = lambda pos: setattr(btn, 'fill_color',
                                        mcrfpy.Color(80, 80, 110))
    btn.on_exit = lambda pos: setattr(btn, 'fill_color',
                                       mcrfpy.Color(60, 60, 80))

    # Click handler receives (pos: Vector, button: MouseButton, action: InputState)
    def handle_click(pos, button, action):
        if button == mcrfpy.MouseButton.LEFT and action == mcrfpy.InputState.PRESSED:
            on_click()
    btn.on_click = handle_click

    parent.children.append(btn)
    return btn


def start_new_game():
    print("Starting new game...")


def show_options():
    print("Showing options...")


# Usage
make_button(root, (20, 20), "New Game", lambda: start_new_game())
make_button(root, (20, 60), "Options", lambda: show_options())
make_button(root, (20, 100), "Quit", lambda: mcrfpy.current_scene.on_key)

mcrfpy.current_scene = scene
