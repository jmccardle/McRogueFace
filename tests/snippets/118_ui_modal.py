# mcrf: objects=[Caption,Color,Easing,Frame,InputState,Key,Scene] verified=0.2.8-dev@a7ba486 status=ok
# UI Modal Dialog - Popup confirmation
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

# Background content
for i in range(5):
    scene.children.append(mcrfpy.Frame(
        pos=(100 + i * 180, 300), size=(140, 100),
        fill_color=mcrfpy.Color(80, 80, 120)
    ))

scene.children.append(mcrfpy.Caption(text="Press SPACE to show modal", pos=(380, 600)))

# Modal overlay (semi-transparent background)
overlay = mcrfpy.Frame(
    pos=(0, 0), size=(1024, 768),
    fill_color=mcrfpy.Color(0, 0, 0, 150),
    visible=False
)
scene.children.append(overlay)

# Modal dialog
modal = mcrfpy.Frame(
    pos=(312, 234), size=(400, 300),
    fill_color=mcrfpy.Color(50, 50, 70),
    outline=3.0,
    outline_color=mcrfpy.Color(100, 100, 150),
    visible=False
)
scene.children.append(modal)

_caption = mcrfpy.Caption(text="Confirm Action?", pos=(120, 40))
_caption.fill_color = mcrfpy.Color(255, 220, 100)
modal.children.append(_caption)
modal.children.append(mcrfpy.Caption(text="Are you sure you want to proceed?", pos=(60, 120)))
modal.children.append(mcrfpy.Caption(text="Press Y=Yes, N=No", pos=(110, 200)))

status = mcrfpy.Caption(text="", pos=(420, 650))
scene.children.append(status)

def show_modal():
    overlay.visible = True
    modal.visible = True
    modal.opacity = 0
    modal.animate("opacity", 1.0, 0.3, mcrfpy.Easing.EASE_OUT)

def hide_modal(result):
    overlay.visible = False
    modal.visible = False
    status.text = f"Result: {result}"

def on_key(key, action):
    if action != mcrfpy.InputState.PRESSED: return
    if key == mcrfpy.Key.SPACE and not modal.visible:
        show_modal()
    elif modal.visible:
        if key == mcrfpy.Key.Y: hide_modal("Confirmed!")
        elif key == mcrfpy.Key.N: hide_modal("Cancelled")

scene.on_key = on_key
