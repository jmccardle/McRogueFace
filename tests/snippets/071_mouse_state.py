# mcrf: objects=[Caption,Color,Frame,Scene,Timer,Vector] verified=0.2.8-dev@a7ba486 status=ok
# Mouse State - Track mouse position and buttons
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

_caption = mcrfpy.Caption(text="Mouse State", pos=(430, 100))
_caption.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(_caption)

pos_label = mcrfpy.Caption(text="Position: (0, 0)", pos=(300, 250))
scene.children.append(pos_label)

button_label = mcrfpy.Caption(text="Buttons: none", pos=(300, 350))
scene.children.append(button_label)

# Cursor follower
cursor = mcrfpy.Frame(pos=(0, 0), size=(20, 20), fill_color=mcrfpy.Color(255, 100, 100))
scene.children.append(cursor)

def update_display(timer, runtime):
    mouse = mcrfpy.mouse
    pos = mouse.pos

    pos_label.text = f"Position: ({pos.x:.0f}, {pos.y:.0f})"

    # Check button states
    buttons = []
    if mouse.left: buttons.append("LEFT")
    if mouse.middle: buttons.append("MIDDLE")
    if mouse.right: buttons.append("RIGHT")
    button_label.text = f"Buttons: {', '.join(buttons) if buttons else 'none'}"

    cursor.pos = mcrfpy.Vector(pos.x - 10, pos.y - 10)

timer = mcrfpy.Timer("mouse_poll", update_display, 16)
