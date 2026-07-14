# mcrf: objects=[Caption,Color,Frame,InputState,Scene] verified=0.2.8-dev status=ok
# Input Keyboard - Key press handling
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(
    pos=(0, 0), size=(1024, 768),
    fill_color=mcrfpy.Color(30, 30, 40)
))

key_display = mcrfpy.Caption(
    text="Press any key...",
    pos=(380, 300))
key_display.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(key_display)

state_display = mcrfpy.Caption(
    text="State: waiting",
    pos=(420, 400))
state_display.fill_color = mcrfpy.Color(200, 200, 200)
scene.children.append(state_display)

def on_key(key, action):
    key_display.text = f"Key: {key}"

    if action == mcrfpy.InputState.PRESSED:
        state_display.text = "State: PRESSED"
        state_display.fill_color = mcrfpy.Color(100, 255, 100)
    elif action == mcrfpy.InputState.RELEASED:
        state_display.text = "State: RELEASED"
        state_display.fill_color = mcrfpy.Color(255, 100, 100)
    elif action == mcrfpy.InputState.HELD:
        state_display.text = "State: HELD"
        state_display.fill_color = mcrfpy.Color(255, 255, 100)

scene.on_key = on_key
