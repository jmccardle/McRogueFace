# mcrf: objects=[Caption,Color,Easing,Frame,Scene,Timer] verified=0.2.8-dev status=ok
# Animations List - View all active animations
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

_caption = mcrfpy.Caption(
    text="Active Animations",
    pos=(400, 80))
_caption.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(_caption)

# Create frames with animations
frames = []
for i in range(3):
    frame = mcrfpy.Frame(
        pos=(150 + i * 250, 200), size=(100, 100),
        fill_color=mcrfpy.Color(100 + i * 50, 100, 200 - i * 50)
    )
    scene.children.append(frame)
    frames.append(frame)

# Start various animations
frames[0].animate("x", 150, 5.0, mcrfpy.Easing.EASE_IN_OUT)
frames[1].animate("opacity", 0.2, 4.0, mcrfpy.Easing.LINEAR)
frames[2].animate("fill_color", (255, 100, 100, 255), 3.0, mcrfpy.Easing.EASE_OUT)

# Display panel
anim_display = mcrfpy.Frame(
    pos=(162, 400), size=(700, 250),
    fill_color=mcrfpy.Color(40, 40, 60)
)
scene.children.append(anim_display)

def update_display(timer, runtime):
    # Clear previous
    while len(anim_display.children) > 0:
        anim_display.children.remove(anim_display.children[0])

    y = 20
    anim_display.children.append(mcrfpy.Caption(
        text=f"Total animations: {len(mcrfpy.animations)}",
        pos=(20, y)
    ))
    y += 40

    for anim in mcrfpy.animations:
        info = f"property='{anim.property}', elapsed={anim.elapsed:.1f}s/{anim.duration:.1f}s"
        cap = mcrfpy.Caption(text=info, pos=(20, y))
        anim_display.children.append(cap)
        y += 35

display_timer = mcrfpy.Timer("display", update_display, 100)
