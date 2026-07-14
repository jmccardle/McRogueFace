# mcrf: objects=[Caption,Color,Scene,Sprite] verified=0.2.8-dev@a7ba486 status=ok
# Sprite Tint - Note: Sprite tinting requires shader
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

# Note: Direct sprite color tinting is not available
# Use opacity or shaders for color effects

opacities = [1.0, 0.8, 0.6, 0.4, 0.2]
labels = ["100%", "80%", "60%", "40%", "20%"]

for i, (opacity, label_text) in enumerate(zip(opacities, labels)):
    x = 100 + (i % 3) * 300
    y = 200 + (i // 3) * 280

    sprite = mcrfpy.Sprite(
        texture=mcrfpy.default_texture,
        sprite_index=84,
        pos=(x, y),
        scale=8.0
    )
    sprite.opacity = opacity
    scene.children.append(sprite)

    label = mcrfpy.Caption(text=f"opacity={label_text}", pos=(x, y + 150))
    scene.children.append(label)

title = mcrfpy.Caption(text="Sprite Opacity Levels", pos=(380, 80))
title.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(title)
