# mcrf: objects=[Alignment,Caption,Color,Frame,Scene,Sprite] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("alignment_demo")
mcrfpy.current_scene = scene

container = mcrfpy.Frame(pos=(50, 50), size=(400, 300), fill_color=mcrfpy.Color(40, 40, 60))
scene.children.append(container)

# Center a caption in its parent frame
caption = mcrfpy.Caption(text="Centered", pos=(0, 0))
caption.align = mcrfpy.Alignment.CENTER
container.children.append(caption)

# Position a sprite in the top-right corner with margin
sprite = mcrfpy.Sprite(texture=mcrfpy.default_texture, pos=(0, 0))
sprite.align = mcrfpy.Alignment.TOP_RIGHT
sprite.horiz_margin = 10
sprite.vert_margin = 10
container.children.append(sprite)
