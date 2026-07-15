# mcrf: objects=[Caption,InputState,Key,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene
scene.children.append(mcrfpy.Caption(text="Press S, Ctrl+S, or Shift+S", pos=(50, 50)))

def handle_key(key, state):
    if state == mcrfpy.InputState.PRESSED:
        if key == mcrfpy.Key.S:
            if mcrfpy.keyboard.ctrl:
                save_game()  # Ctrl+S
            elif mcrfpy.keyboard.shift:
                save_as()    # Shift+S
            else:
                move_south() # Just S

scene.on_key = handle_key

# Check modifier states anywhere
if mcrfpy.keyboard.shift:
    print("Shift is currently held")
