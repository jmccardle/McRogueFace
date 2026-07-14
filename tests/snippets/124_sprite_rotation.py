# mcrf: objects=[Caption,Color,Frame,Scene,Sprite] verified=0.2.8-dev@a7ba486 status=ok
# Sprite Rotation - Rotate sprite images
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

_caption = mcrfpy.Caption(
    text="Sprite Rotation",
    pos=(430, 80))
_caption.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(_caption)

rotations = [0, 45, 90, 135, 180, 225, 270, 315]

for i, angle in enumerate(rotations):
    x = 130 + (i % 4) * 200
    y = 200 + (i // 4) * 250

    sprite = mcrfpy.Sprite(
        texture=mcrfpy.default_texture,
        sprite_index=84,
        pos=(x, y),
        scale=6.0
    )
    sprite.rotation = angle  # Set rotation after creation
    scene.children.append(sprite)

    label = mcrfpy.Caption(text=f"{angle}°", pos=(x + 30, y + 120))
    scene.children.append(label)
