# mcrf: objects=[Caption,Color,Frame,InputState,Key,Scene,Timer] verified=0.2.8-dev@a7ba486 status=ok
# Effect Screen Shake - Impact feedback
import mcrfpy
import random

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

# Container for all game elements
game_container = mcrfpy.Frame(
    pos=(0, 0), size=(1024, 768),
    fill_color=mcrfpy.Color(30, 30, 40)
)
scene.children.append(game_container)

# Some game content
for i in range(5):
    frame = mcrfpy.Frame(
        pos=(150 + i * 150, 300), size=(100, 100),
        fill_color=mcrfpy.Color(100 + i * 30, 100, 200 - i * 30)
    )
    game_container.children.append(frame)

original_pos = (0, 0)
shake_timer = None

def do_shake(timer, runtime):
    offset_x = random.randint(-10, 10)
    offset_y = random.randint(-10, 10)
    game_container.x = offset_x
    game_container.y = offset_y

def end_shake(timer, runtime):
    global shake_timer
    if shake_timer:
        shake_timer.stop()
        shake_timer = None
    game_container.x = original_pos[0]
    game_container.y = original_pos[1]

def trigger_shake():
    global shake_timer
    shake_timer = mcrfpy.Timer("shake", do_shake, 16)
    mcrfpy.Timer("shake_end", end_shake, 300, once=True)

game_container.children.append(mcrfpy.Caption(
    text="Press SPACE for screen shake",
    pos=(350, 550)
))

def on_key(key, action):
    if key == mcrfpy.Key.SPACE and action == mcrfpy.InputState.PRESSED:
        trigger_shake()

scene.on_key = on_key
