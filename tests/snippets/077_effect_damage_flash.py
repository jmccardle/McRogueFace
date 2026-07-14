# mcrf: objects=[Caption,Color,Easing,Frame,InputState,Key,Scene,Sprite,Timer] verified=0.2.8-dev status=ok
# Effect Damage Flash - Hit feedback on frame
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

# Character frame (use Frame since Sprite doesn't support color tinting)
character = mcrfpy.Frame(
    pos=(400, 250), size=(200, 200),
    fill_color=mcrfpy.Color(100, 150, 255)
)
scene.children.append(character)

# Add sprite inside frame
sprite = mcrfpy.Sprite(
    texture=mcrfpy.default_texture,
    sprite_index=84,
    pos=(50, 50),
    scale=6.0
)
character.children.append(sprite)

scene.children.append(mcrfpy.Caption(
    text="Press SPACE to damage",
    pos=(400, 550)
))

hp_label = mcrfpy.Caption(text="HP: 100", pos=(450, 500))
hp_label.fill_color = mcrfpy.Color(100, 255, 100)
scene.children.append(hp_label)

hp = 100

def flash_damage():
    global hp
    hp = max(0, hp - 10)
    hp_label.text = f"HP: {hp}"

    # Flash white then red then back
    character.fill_color = mcrfpy.Color(255, 255, 255)
    character.animate("fill_color", (255, 100, 100, 255), 0.1, mcrfpy.Easing.LINEAR)

    def restore(timer, runtime):
        character.animate("fill_color", (100, 150, 255, 255), 0.2, mcrfpy.Easing.EASE_OUT)

    mcrfpy.Timer("flash_restore", restore, 150, once=True)

def on_key(key, action):
    if key == mcrfpy.Key.SPACE and action == mcrfpy.InputState.PRESSED:
        flash_damage()

scene.on_key = on_key
