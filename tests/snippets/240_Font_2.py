# mcrf: objects=[Caption,Color,Font,Scene] verified=0.2.8-dev status=ok
import mcrfpy

# Load font
font = mcrfpy.Font("assets/JetbrainsMono.ttf")

# Create a scene to hold the caption
scene = mcrfpy.Scene("title_screen")
mcrfpy.current_scene = scene

# Create caption with font
title = mcrfpy.Caption(
    text="Game Title",
    pos=(400, 100),
    font=font
)
title.font_size = 48
title.fill_color = mcrfpy.Color(255, 255, 255)

scene.children.append(title)
