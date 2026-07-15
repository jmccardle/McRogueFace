# mcrf: objects=[Caption,Color,Frame,Scene,Sprite] verified=0.2.8-dev status=ok
import mcrfpy

# Create scene
scene = mcrfpy.Scene("game")
ui = scene.children

# Rectangle/Frame
frame = mcrfpy.Frame(pos=(100, 100), size=(200, 150),
                      fill_color=mcrfpy.Color(50, 50, 50))
frame.outline_color = mcrfpy.Color(255, 255, 255)
frame.outline = 2
ui.append(frame)

# Text
label = mcrfpy.Caption(text="Hello World!", pos=(10, 10))
label.font_size = 24
label.fill_color = mcrfpy.Color(255, 255, 255)
ui.append(label)

# Sprite
sprite = mcrfpy.Sprite(x=50, y=50, sprite_index=0)
ui.append(sprite)

mcrfpy.current_scene = scene
