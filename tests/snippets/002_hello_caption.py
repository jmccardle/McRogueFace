# mcrf: objects=[Caption,Color,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Hello Caption - Display text on screen
import mcrfpy

scene = mcrfpy.Scene("hello")
mcrfpy.current_scene = scene

# Large centered text
caption = mcrfpy.Caption(
    text="Hello, McRogueFace!",
    pos=(512, 350)
)
caption.fill_color = mcrfpy.Color(255, 220, 100)
# Center the text by adjusting position after creation
caption.x -= caption.w / 2
scene.children.append(caption)
