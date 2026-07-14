# mcrf: objects=[Caption,Color,Easing,Frame,Scene,Timer] verified=0.2.8-dev@a7ba486 status=ok
# Color Channel Animation - Animate individual RGBA
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

_caption = mcrfpy.Caption(
    text="Animating Color Channels",
    pos=(380, 80))
_caption.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(_caption)

# Red channel animation
r_frame = mcrfpy.Frame(
    pos=(150, 200), size=(200, 100),
    fill_color=mcrfpy.Color(128, 50, 50)
)
scene.children.append(r_frame)
r_label = mcrfpy.Caption(text="fill_color.r: 128 -> 255", pos=(150, 320))
r_label.outline = 2
r_label.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(r_label)

# Green channel animation
g_frame = mcrfpy.Frame(
    pos=(400, 200), size=(200, 100),
    fill_color=mcrfpy.Color(50, 128, 50)
)
scene.children.append(g_frame)
g_label = mcrfpy.Caption(text="fill_color.g: 128 -> 255", pos=(400, 320))
g_label.outline = 2
g_label.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(g_label)

# Blue channel animation
b_frame = mcrfpy.Frame(
    pos=(650, 200), size=(200, 100),
    fill_color=mcrfpy.Color(50, 50, 128)
)
scene.children.append(b_frame)
b_label = mcrfpy.Caption(text="fill_color.b: 128 -> 255", pos=(650, 320))
b_label.outline = 2
b_label.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(b_label)

# Alpha channel animation
a_frame = mcrfpy.Frame(
    pos=(400, 450), size=(200, 100),
    fill_color=mcrfpy.Color(200, 200, 200, 255)
)
scene.children.append(a_frame)
a_label = mcrfpy.Caption(text="fill_color.a: 255 -> 50", pos=(400, 570))
a_label.outline = 2
a_label.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(a_label)

def restart_animation(timer, runtime):
    r_frame.fill_color = mcrfpy.Color(128, 50, 50)
    g_frame.fill_color = mcrfpy.Color(50, 128, 50)
    b_frame.fill_color = mcrfpy.Color(50, 50, 128)
    a_frame.fill_color = mcrfpy.Color(200, 200, 200, 255)
    r_frame.animate("fill_color.r", 255, 3.0, mcrfpy.Easing.LINEAR)
    g_frame.animate("fill_color.g", 255, 3.0, mcrfpy.Easing.LINEAR)
    b_frame.animate("fill_color.b", 255, 3.0, mcrfpy.Easing.LINEAR)
    a_frame.animate("fill_color.a", 50, 3.0, mcrfpy.Easing.LINEAR)

# Start animations
r_frame.animate("fill_color.r", 255, 3.0, mcrfpy.Easing.LINEAR)
g_frame.animate("fill_color.g", 255, 3.0, mcrfpy.Easing.LINEAR)
b_frame.animate("fill_color.b", 255, 3.0, mcrfpy.Easing.LINEAR)
a_frame.animate("fill_color.a", 50, 3.0, mcrfpy.Easing.LINEAR)
loop_timer = mcrfpy.Timer("loop", restart_animation, 8000)
