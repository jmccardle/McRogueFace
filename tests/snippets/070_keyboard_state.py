# mcrf: objects=[Caption,Color,Frame,InputState,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Keyboard State - Track key presses
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

_caption = mcrfpy.Caption(text="Keyboard State", pos=(420, 100))
_caption.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(_caption)

last_key_label = mcrfpy.Caption(text="Last key: none", pos=(200, 250))
scene.children.append(last_key_label)

state_label = mcrfpy.Caption(text="State: waiting", pos=(200, 350))
scene.children.append(state_label)

modifier_label = mcrfpy.Caption(text="Modifiers: none", pos=(200, 450))
scene.children.append(modifier_label)

scene.children.append(mcrfpy.Caption(text="Press keys to see state", pos=(350, 550)))

def on_key(key, action):
    last_key_label.text = f"Last key: {key}"

    if action == mcrfpy.InputState.PRESSED:
        state_label.text = "State: PRESSED"
        state_label.fill_color = mcrfpy.Color(100, 255, 100)
    elif action == mcrfpy.InputState.RELEASED:
        state_label.text = "State: RELEASED"
        state_label.fill_color = mcrfpy.Color(255, 100, 100)
    elif action == mcrfpy.InputState.HELD:
        state_label.text = "State: HELD"
        state_label.fill_color = mcrfpy.Color(255, 255, 100)

    # Show modifiers
    kb = mcrfpy.keyboard
    mods = []
    if kb.ctrl: mods.append("CTRL")
    if kb.shift: mods.append("SHIFT")
    if kb.alt: mods.append("ALT")
    modifier_label.text = f"Modifiers: {', '.join(mods) if mods else 'none'}"

scene.on_key = on_key
