# mcrf: objects=[Color,Frame,InputState,MouseButton,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("mousebutton_demo")
mcrfpy.current_scene = scene

my_button = mcrfpy.Frame(
    pos=(50, 50), size=(200, 80),
    fill_color=mcrfpy.Color(100, 100, 200)
)
scene.children.append(my_button)


def activate_button():
    print("activated")


def show_context_menu(x, y):
    print(f"context menu at ({x}, {y})")


def button_click(pos, button, action):
    if action != mcrfpy.InputState.PRESSED:
        return
    if button == mcrfpy.MouseButton.LEFT:
        activate_button()
    elif button == mcrfpy.MouseButton.RIGHT:
        show_context_menu(pos.x, pos.y)


my_button.on_click = button_click
