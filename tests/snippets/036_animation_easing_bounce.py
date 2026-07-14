# mcrf: objects=[Caption,Color,Easing,Frame,Scene,Timer] verified=0.2.8-dev status=ok
# Easing: BOUNCE - Bouncy effect
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(
    pos=(0, 0), size=(1024, 768),
    fill_color=mcrfpy.Color(30, 30, 40)
))

# Ball that bounces
ball = mcrfpy.Frame(
    pos=(462, 100), size=(100, 100),
    fill_color=mcrfpy.Color(255, 100, 100)
)
scene.children.append(ball)

# Ground line
scene.children.append(mcrfpy.Frame(
    pos=(0, 600), size=(1024, 5),
    fill_color=mcrfpy.Color(100, 100, 100)
))

_caption = mcrfpy.Caption(
    text="EASE_OUT_BOUNCE - Ball drop effect",
    pos=(340, 680))
_caption.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(_caption)

def restart_animation(timer, runtime):
    ball.y = 100
    ball.animate("y", 500, 2.0, mcrfpy.Easing.EASE_OUT_BOUNCE)

ball.animate("y", 500, 2.0, mcrfpy.Easing.EASE_OUT_BOUNCE)
loop_timer = mcrfpy.Timer("loop", restart_animation, 7000)  # 2s animation + 5s pause
