# mcrf: objects=[Caption,InputState,Key,Scene] verified=0.2.8-dev status=ok
import mcrfpy

# Create and populate a scene
menu = mcrfpy.Scene("menu")
menu.children.append(mcrfpy.Caption(
    text="Press ENTER to start",
    pos=(400, 300)
))

def menu_keys(key, action):
    if key == mcrfpy.Key.ENTER and action == mcrfpy.InputState.PRESSED:
        mcrfpy.Scene("game").activate()

menu.on_key = menu_keys
menu.activate()

mcrfpy.current_scene = menu
