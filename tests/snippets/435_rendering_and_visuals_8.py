# mcrf: objects=[Caption,Color,Frame,Scene,Sprite,Texture] verified=0.3.6 status=ok
import mcrfpy

scene = mcrfpy.Scene("perf_tips")
ui = scene.children

label1 = mcrfpy.Caption(text="Health", pos=(10, 10))
label2 = mcrfpy.Caption(text="Mana", pos=(10, 40))
label3 = mcrfpy.Caption(text="Gold", pos=(10, 70))

# region: draw-calls
# Good: Group related UI in Frames
hud_frame = mcrfpy.Frame(pos=(0, 0), size=(800, 600))
hud_frame.children.append(label1)
hud_frame.children.append(label2)
hud_frame.children.append(label3)

# Avoid: Many top-level UI elements
# (Each top-level element is a separate draw call)
# endregion

ui.append(hud_frame)

# Build the elements the visibility loop walks over, off to one side
# so the loop has some of each to hide
all_elements = []
for i in range(4):
    marker = mcrfpy.Frame(pos=(300 + i * 400, 100), size=(40, 40),
                          fill_color=mcrfpy.Color(200, 100, 50))
    ui.append(marker)
    all_elements.append(marker)


def in_viewport(element):
    return 0 <= element.x < 1024


# region: visibility
# Hide off-screen elements
for element in all_elements:
    if not in_viewport(element):
        element.visible = False
# endregion

# region: reuse-textures
# Good: One texture, many sprites
texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
for i in range(100):
    sprite = mcrfpy.Sprite(x=i * 20, y=300)
    sprite.texture = texture
    sprite.sprite_index = i
    ui.append(sprite)
# endregion

mcrfpy.current_scene = scene
