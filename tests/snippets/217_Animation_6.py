# mcrf: objects=[Scene,Sprite,Texture] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
sprite = mcrfpy.Sprite(texture=texture, sprite_index=84, pos=(100, 100))
scene.children.append(sprite)

# Cycle through frames 84-87 forever (0.6 seconds per cycle)
walk = sprite.animate("sprite_index", [84, 85, 86, 87], 0.6, loop=True)

# Later, to stop the loop:
walk.stop()
