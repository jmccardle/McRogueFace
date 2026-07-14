# mcrf: objects=[Caption,Color,Easing,Frame,Scene,Timer] verified=0.2.8-dev status=ok
# Animation Chain - Sequential animations
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(
    pos=(0, 0), size=(1024, 768),
    fill_color=mcrfpy.Color(30, 30, 40)
))

frame = mcrfpy.Frame(
    pos=(100, 100), size=(100, 100),
    fill_color=mcrfpy.Color(255, 100, 100)
)
scene.children.append(frame)

status = mcrfpy.Caption(text="Step 1: Moving right", pos=(380, 620))
scene.children.append(status)

def step2(target, prop, value):
    status.text = "Step 2: Moving down"
    target.fill_color = mcrfpy.Color(100, 255, 100)
    target.animate("y", 568, 1.0, mcrfpy.Easing.EASE_IN_OUT, callback=step3)

def step3(target, prop, value):
    status.text = "Step 3: Moving left"
    target.fill_color = mcrfpy.Color(100, 100, 255)
    target.animate("x", 100, 1.0, mcrfpy.Easing.EASE_IN_OUT, callback=step4)

def step4(target, prop, value):
    status.text = "Step 4: Moving up - Complete!"
    target.fill_color = mcrfpy.Color(255, 255, 100)
    target.animate("y", 100, 1.0, mcrfpy.Easing.EASE_IN_OUT)

def restart_animation(timer, runtime):
    frame.x = 100
    frame.y = 100
    frame.fill_color = mcrfpy.Color(255, 100, 100)
    status.text = "Step 1: Moving right"
    frame.animate("x", 824, 1.0, mcrfpy.Easing.EASE_IN_OUT, callback=step2)

# Start chain
frame.animate("x", 824, 1.0, mcrfpy.Easing.EASE_IN_OUT, callback=step2)
loop_timer = mcrfpy.Timer("loop", restart_animation, 9000)  # 4s animation + 5s pause
