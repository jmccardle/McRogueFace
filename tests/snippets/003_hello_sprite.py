# mcrf: objects=[Caption,Scene,Sprite] verified=0.2.8-dev@a7ba486 status=ok
# Hello Sprite - Display a textured sprite
import mcrfpy

scene = mcrfpy.Scene("hello")
mcrfpy.current_scene = scene

# Create a large sprite using default texture
sprite = mcrfpy.Sprite(
    texture=mcrfpy.default_texture,
    sprite_index=84,  # Knight character
    pos=(412, 284),
    scale=12.0
)
scene.children.append(sprite)

# Add a label
label = mcrfpy.Caption(text="Sprite Index: 84", pos=(412, 550))
scene.children.append(label)
