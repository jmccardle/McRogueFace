# mcrf: objects=[Caption,Color,Frame,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Window Properties - Access window settings
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

# Display window info
window = mcrfpy.window
info = [
    f"Resolution: {window.resolution}",
    f"Game Resolution: {window.game_resolution}",
    f"Title: {window.title}",
    f"Fullscreen: {window.fullscreen}",
    f"VSync: {window.vsync}",
    f"Framerate Limit: {window.framerate_limit}",
    f"Scaling Mode: {window.scaling_mode}",
]

_caption = mcrfpy.Caption(
    text="Window Properties",
    pos=(400, 100))
_caption.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(_caption)

y = 200
for line in info:
    cap = mcrfpy.Caption(text=line, pos=(300, y))
    cap.fill_color = mcrfpy.Color(200, 200, 200)
    scene.children.append(cap)
    y += 60
