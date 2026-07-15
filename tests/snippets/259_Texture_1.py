# mcrf: objects=[Scene,Sprite,Texture] verified=0.2.8-dev status=ok
import mcrfpy

# Load a sprite sheet
texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)

# Create sprites using different indices
floor = mcrfpy.Sprite(pos=(0, 0), texture=texture, sprite_index=0)
wall = mcrfpy.Sprite(pos=(16, 0), texture=texture, sprite_index=1)
player = mcrfpy.Sprite(pos=(32, 0), texture=texture, sprite_index=84)

scene = mcrfpy.Scene("texture_demo")
scene.children.append(floor)
scene.children.append(wall)
scene.children.append(player)
mcrfpy.current_scene = scene
