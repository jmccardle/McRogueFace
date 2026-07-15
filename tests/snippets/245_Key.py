# mcrf: objects=[Caption,InputState,Key,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("key_demo")


def handle_key(key, state):
    if state == mcrfpy.InputState.PRESSED:
        if key == mcrfpy.Key.ESCAPE:
            print("Escape pressed")
        elif key == mcrfpy.Key.SPACE:
            print("Space pressed")
        elif key == mcrfpy.Key.W:
            print("W pressed")


scene.on_key = handle_key
scene.children.append(mcrfpy.Caption(text="Press a key", pos=(10, 10)))
mcrfpy.current_scene = scene
