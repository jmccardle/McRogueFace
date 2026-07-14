# mcrf: objects=[Caption,Color,Scene,Sprite] verified=0.2.8-dev status=ok
# Sprite Atlas - Browse texture atlas
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

# Display a grid of sprites from the default texture
title = mcrfpy.Caption(text="Default Texture Atlas (kenney_tinydungeon)", pos=(250, 30))
title.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(title)

# Show sprites 0-99 in a 10x10 grid
for row in range(10):
    for col in range(10):
        idx = row * 10 + col
        sprite = mcrfpy.Sprite(
            texture=mcrfpy.default_texture,
            sprite_index=idx,
            pos=(112 + col * 80, 80 + row * 65),
            scale=3.0
        )
        scene.children.append(sprite)

        # Index label
        label = mcrfpy.Caption(text=str(idx), pos=(112 + col * 80 + 20, 80 + row * 65 + 48))
        label.fill_color = mcrfpy.Color(120, 120, 120)
        scene.children.append(label)
