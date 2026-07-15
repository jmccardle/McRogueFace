# mcrf: objects=[Caption,Color,Frame,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("color_demo")
mcrfpy.current_scene = scene

# Create colors
red = mcrfpy.Color(255, 0, 0)
semi_transparent = mcrfpy.Color(100, 100, 255, 128)

# From hex string
blue = mcrfpy.Color.from_hex("#0066CC")
white = mcrfpy.Color.from_hex("FFFFFF")

# Color interpolation
start = mcrfpy.Color(255, 0, 0)
end = mcrfpy.Color(0, 0, 255)
middle = start.lerp(end, 0.5)  # Purple

# Apply to elements
frame = mcrfpy.Frame(pos=(0, 0), size=(200, 100), fill_color=mcrfpy.Color(40, 40, 60))
caption = mcrfpy.Caption(text="Hello", pos=(10, 10), fill_color=mcrfpy.Color(255, 255, 255))

scene.children.append(frame)
scene.children.append(caption)

# Read-modify-writeback idiom (frame.fill_color.r = 255 has no effect)
color = frame.fill_color
color.r = 255
frame.fill_color = color  # Reassign to apply
