# mcrf: objects=[Caption,Frame,Scene,Sprite] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("drawable_demo")
mcrfpy.current_scene = scene

# Drawable is abstract - use subclasses
frame = mcrfpy.Frame(pos=(0, 0), size=(100, 100))
caption = mcrfpy.Caption(text="Hello", pos=(10, 10))
sprite = mcrfpy.Sprite(texture=mcrfpy.default_texture, pos=(50, 50))

# Common Drawable properties
frame.visible = True
frame.opacity = 0.5
frame.z_index = 10

# Common Drawable methods
frame.move(50, 25)
frame.resize(200, 150)

# Click handling
def on_click(pos, button, action):
    print(f"Clicked at ({pos.x}, {pos.y})")

frame.on_click = on_click

scene.children.append(frame)
scene.children.append(caption)
scene.children.append(sprite)
