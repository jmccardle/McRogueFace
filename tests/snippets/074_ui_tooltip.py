# mcrf: objects=[Caption,Color,Frame,Scene,Vector] verified=0.2.8-dev status=ok
# UI Tooltip - Hover tooltip display
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

# Tooltip (hidden by default)
tooltip = mcrfpy.Frame(
    pos=(0, 0), size=(200, 60),
    fill_color=mcrfpy.Color(40, 40, 50),
    outline=1.0, outline_color=mcrfpy.Color(150, 150, 150),
    visible=False
)
tooltip_text = mcrfpy.Caption(text="", pos=(10, 10))
tooltip.children.append(tooltip_text)

def make_item(x, y, name, description):
    item = mcrfpy.Frame(
        pos=(x, y), size=(150, 150),
        fill_color=mcrfpy.Color(80, 80, 120)
    )
    label = mcrfpy.Caption(text=name, pos=(30, 60))
    item.children.append(label)

    def on_enter(pos):
        tooltip.visible = True
        tooltip_text.text = description
        tooltip.pos = mcrfpy.Vector(pos.x + 20, pos.y + 20)

    def on_exit(pos):
        tooltip.visible = False

    def on_move(pos):
        tooltip.pos = mcrfpy.Vector(pos.x + 20, pos.y + 20)

    item.on_enter = on_enter
    item.on_exit = on_exit
    item.on_move = on_move
    return item

scene.children.append(make_item(200, 300, "Sword", "A sharp blade"))
scene.children.append(make_item(400, 300, "Shield", "Blocks attacks"))
scene.children.append(make_item(600, 300, "Potion", "Heals 50 HP"))
scene.children.append(tooltip)  # Add last for z-order

status = mcrfpy.Caption(text="Hover over items to see tooltips", pos=(350, 550))
status.outline = 2
status.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(status)
