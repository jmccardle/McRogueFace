# mcrf: objects=[Caption,Color,Easing,Frame,Scene,Sprite,Timer] verified=0.2.8-dev status=ok
# Animation Sprite Index - Sprite animation
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(
    pos=(0, 0), size=(1024, 768),
    fill_color=mcrfpy.Color(30, 30, 40)
))

# Large sprite for visibility
sprite = mcrfpy.Sprite(
    texture=mcrfpy.default_texture,
    sprite_index=84,
    pos=(400, 250),
    scale=12.0
)
scene.children.append(sprite)

_caption = mcrfpy.Caption(
    text="Animating sprite_index (84 -> 120)",
    pos=(360, 600))
_caption.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(_caption)

def restart_animation(timer, runtime):
    sprite.sprite_index = 84
    sprite.animate("sprite_index", 120, 3.0, mcrfpy.Easing.LINEAR)

# Animate through sprite indices
sprite.animate("sprite_index", 120, 3.0, mcrfpy.Easing.LINEAR)
loop_timer = mcrfpy.Timer("loop", restart_animation, 8000)
