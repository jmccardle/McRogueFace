# mcrf: objects=[Caption,Color,Frame,Scene,Sprite] verified=0.3.6-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("colors")
ui = scene.children

frame = mcrfpy.Frame(pos=(100, 100), size=(200, 150))
ui.append(frame)

caption = mcrfpy.Caption(text="Yellow text", pos=(120, 120))
ui.append(caption)

sprite = mcrfpy.Sprite(x=350, y=120, sprite_index=0)
ui.append(sprite)

# region: color-creation
# RGB
red = mcrfpy.Color(255, 0, 0)

# RGBA (with alpha/transparency)
semi_transparent = mcrfpy.Color(255, 255, 255, 128)

# Access components
color = mcrfpy.Color(100, 150, 200, 255)
# color.r, color.g, color.b, color.a
# endregion

# region: color-application
# Frame colors
frame.fill_color = mcrfpy.Color(50, 50, 50)
frame.outline_color = mcrfpy.Color(255, 255, 255)

# Text color
caption.fill_color = mcrfpy.Color(255, 255, 0)  # Yellow text

# Opacity
sprite.opacity = 0.5  # 50% transparent
# endregion

mcrfpy.current_scene = scene
