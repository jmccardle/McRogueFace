# mcrf: objects=[Caption,Color,Frame,Scene,Timer] verified=0.2.8-dev@a7ba486 status=ok
# Timers List - View all active timers
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

_caption = mcrfpy.Caption(
    text="Active Timers",
    pos=(430, 80))
_caption.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(_caption)

# Create several timers
def tick1(t, r): pass
def tick2(t, r): pass
def tick3(t, r): pass

timer1 = mcrfpy.Timer("fast_timer", tick1, 100)
timer2 = mcrfpy.Timer("slow_timer", tick2, 2000)
timer3 = mcrfpy.Timer("paused_timer", tick3, 500)
timer3.pause()

# Display
timer_display = mcrfpy.Frame(
    pos=(162, 150), size=(700, 400),
    fill_color=mcrfpy.Color(40, 40, 60)
)
scene.children.append(timer_display)

def update_display(timer, runtime):
    # Clear existing
    while len(timer_display.children) > 0:
        timer_display.children.remove(timer_display.children[0])

    y = 20
    for t in mcrfpy.timers:
        info = f"{t.name}: interval={t.interval}ms, remaining={t.remaining}ms, paused={t.paused}"
        cap = mcrfpy.Caption(text=info, pos=(20, y))
        timer_display.children.append(cap)
        y += 50

display_timer = mcrfpy.Timer("display", update_display, 100)
