# mcrf: objects=[Frame,InputState,Scene] verified=0.2.8-dev status=ok
import mcrfpy

def handle_input(key, state):
    if state == mcrfpy.InputState.PRESSED:
        print(f"{key} was pressed")
    elif state == mcrfpy.InputState.RELEASED:
        print(f"{key} was released")

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene
scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(800, 600)))
scene.on_key = handle_input
