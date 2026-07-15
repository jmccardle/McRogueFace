# mcrf: objects=[Frame,InputState,Scene] verified=0.2.8-dev status=ok
import mcrfpy

# Create scene with object reference
scene = mcrfpy.Scene("game")

# Access children directly
scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(800, 600)))


def my_handler(key, action):
    if action == mcrfpy.InputState.PRESSED:
        print(f"Key pressed: {key}")


# Set input handler on any scene (not just active)
scene.on_key = my_handler

# Activate the scene
scene.activate()
