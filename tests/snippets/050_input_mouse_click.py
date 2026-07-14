# mcrf: objects=[Caption,Color,Frame,InputState,Scene] verified=0.2.8-dev status=ok
# Input Mouse Click - Click on frames
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(
    pos=(0, 0), size=(1024, 768),
    fill_color=mcrfpy.Color(30, 30, 40)
))

# Clickable button
button = mcrfpy.Frame(
    pos=(362, 284), size=(300, 200),
    fill_color=mcrfpy.Color(100, 100, 200),
    outline=3.0,
    outline_color=mcrfpy.Color(150, 150, 255)
)
scene.children.append(button)

label = mcrfpy.Caption(
    text="Click me!",
    pos=(100, 80)
)
button.children.append(label)

click_count = 0
status = mcrfpy.Caption(text="Clicks: 0", pos=(450, 550))
scene.children.append(status)

def on_click(pos, button_type, action):
    global click_count
    if action == mcrfpy.InputState.PRESSED:
        click_count += 1
        status.text = f"Clicks: {click_count}"
        button.fill_color = mcrfpy.Color(150, 150, 255)
    elif action == mcrfpy.InputState.RELEASED:
        button.fill_color = mcrfpy.Color(100, 100, 200)

button.on_click = on_click
