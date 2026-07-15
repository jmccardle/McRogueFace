# mcrf: objects=[Caption,Font,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("font_demo")
mcrfpy.current_scene = scene

# Load a font
font = mcrfpy.Font("assets/JetbrainsMono.ttf")

# Use with Caption
caption = mcrfpy.Caption(
    text="Hello, World!",
    pos=(100, 100),
    font=font
)

scene.children.append(caption)

# Check font properties
print(f"Font family: {font.family}")
print(f"Loaded from: {font.source}")
