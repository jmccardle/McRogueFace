# mcrf: objects=[Caption,Color,Frame,InputState,Scene] verified=0.2.8-dev status=ok
# UI Button - Interactive button with hover
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

def make_button(x, y, text, callback):
    btn = mcrfpy.Frame(
        pos=(x, y), size=(200, 60),
        fill_color=mcrfpy.Color(80, 80, 120),
        outline=2.0,
        outline_color=mcrfpy.Color(120, 120, 180)
    )
    label = mcrfpy.Caption(text=text, pos=(60, 18))
    btn.children.append(label)

    def on_enter(pos):
        btn.fill_color = mcrfpy.Color(100, 100, 150)

    def on_exit(pos):
        btn.fill_color = mcrfpy.Color(80, 80, 120)

    def on_click(pos, button, action):
        if action == mcrfpy.InputState.PRESSED:
            btn.fill_color = mcrfpy.Color(60, 60, 100)
            callback()
        elif action == mcrfpy.InputState.RELEASED:
            btn.fill_color = mcrfpy.Color(100, 100, 150)

    btn.on_enter = on_enter
    btn.on_exit = on_exit
    btn.on_click = on_click
    return btn

status = mcrfpy.Caption(text="Click a button", pos=(420, 600))
scene.children.append(status)

def click1(): status.text = "Button 1 clicked!"
def click2(): status.text = "Button 2 clicked!"
def click3(): status.text = "Button 3 clicked!"

scene.children.append(make_button(412, 200, "Button 1", click1))
scene.children.append(make_button(412, 300, "Button 2", click2))
scene.children.append(make_button(412, 400, "Button 3", click3))
