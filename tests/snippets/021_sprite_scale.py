# mcrf: objects=[Caption,Color,Scene,Sprite] verified=0.2.8-dev status=ok
# Sprite Scale - Resize sprites
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scales = [1.0, 2.0, 4.0, 8.0, 16.0]
for i, scale in enumerate(scales):
    sprite = mcrfpy.Sprite(
        texture=mcrfpy.default_texture,
        sprite_index=84,  # Knight
        pos=(100 + i * 180, 300),
        scale=scale
    )
    scene.children.append(sprite)

    label = mcrfpy.Caption(text=f"scale={scale}", pos=(100 + i * 180, 550))
    label.fill_color = mcrfpy.Color(200, 200, 200)
    scene.children.append(label)

title = mcrfpy.Caption(text="Sprite Scaling", pos=(420, 100))
title.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(title)
