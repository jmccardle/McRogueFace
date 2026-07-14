# mcrf: objects=[Caption,Color,Frame,Scene,Sprite] verified=0.2.8-dev@a7ba486 status=ok
# Texture Properties - Texture information
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

# Get default texture info
tex = mcrfpy.default_texture

_caption = mcrfpy.Caption(
    text="Default Texture Properties",
    pos=(350, 100))
_caption.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(_caption)

info = [
    f"Source: {tex.source}",
    f"Sprite Width: {tex.sprite_width}",
    f"Sprite Height: {tex.sprite_height}",
    f"Sprite Count: {tex.sprite_count}",
    f"Sheet Width: {tex.sheet_width}",
    f"Sheet Height: {tex.sheet_height}",
]

y = 200
for line in info:
    cap = mcrfpy.Caption(text=line, pos=(200, y))
    scene.children.append(cap)
    y += 50

# Show sample sprites
scene.children.append(mcrfpy.Caption(text="Sample sprites:", pos=(200, 500)))

for i in range(8):
    sprite = mcrfpy.Sprite(
        texture=tex,
        sprite_index=i * 10,
        pos=(200 + i * 90, 550),
        scale=4.0
    )
    scene.children.append(sprite)
    _caption = mcrfpy.Caption(
        text=str(i * 10),
        pos=(220 + i * 90, 630))
    _caption.fill_color = mcrfpy.Color(150, 150, 150)
    scene.children.append(_caption)
