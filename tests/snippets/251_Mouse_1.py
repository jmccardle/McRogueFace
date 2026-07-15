# mcrf: objects=[Caption,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("mouse_quick_ref")
mcrfpy.current_scene = scene

caption = mcrfpy.Caption(text="Mouse Quick Reference", pos=(50, 50))
scene.children.append(caption)

# Check mouse position
x, y = mcrfpy.mouse.pos
print(f"Mouse at ({x}, {y})")

# Check button states
if mcrfpy.mouse.left:
    print("Left button is held")

# Hide cursor for custom cursor sprite
mcrfpy.mouse.visible = False

# Grab mouse for camera control
mcrfpy.mouse.grabbed = True
