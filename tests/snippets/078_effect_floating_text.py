# mcrf: objects=[Caption,Color,Easing,Frame,InputState,Scene,Timer] verified=0.2.8-dev@a7ba486 status=ok
# Effect Floating Text - Damage numbers
import mcrfpy
import random

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

# Target
target = mcrfpy.Frame(
    pos=(412, 284), size=(200, 200),
    fill_color=mcrfpy.Color(100, 80, 80)
)
scene.children.append(target)

scene.children.append(mcrfpy.Caption(text="Click target to deal damage", pos=(360, 550)))

text_id = 0

def spawn_damage_text(x, y, damage):
    global text_id
    text_id += 1
    text = mcrfpy.Caption(text=f"-{damage}", pos=(x, y))
    text.fill_color = mcrfpy.Color(255, 100, 100)
    text.font_size = 32
    scene.children.append(text)

    # Float up and fade
    text.animate("y", y - 100, 1.0, mcrfpy.Easing.EASE_OUT)
    text.animate("opacity", 0.0, 1.0, mcrfpy.Easing.EASE_IN)

    # Remove after animation using closure to capture text reference
    current_text = text
    def remove(timer, runtime):
        try:
            scene.children.remove(current_text)
        except:
            pass

    mcrfpy.Timer(f"remove_{text_id}", remove, 1100, once=True)

def on_click(pos, button, action):
    if action == mcrfpy.InputState.PRESSED:
        damage = random.randint(10, 99)
        # pos is relative to target, add target position
        spawn_damage_text(pos.x + 412 + 50, pos.y + 284, damage)

target.on_click = on_click
