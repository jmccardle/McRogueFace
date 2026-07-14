# mcrf: objects=[Caption,Color,Frame,Scene,Sprite] verified=0.2.8-dev status=ok
# Game Inventory - Grid-based inventory UI
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

# Inventory grid
inv_frame = mcrfpy.Frame(
    pos=(262, 184), size=(500, 400),
    fill_color=mcrfpy.Color(40, 40, 60),
    outline=3.0, outline_color=mcrfpy.Color(100, 100, 140)
)
scene.children.append(inv_frame)

inv_frame.children.append(mcrfpy.Caption(text="Inventory", pos=(200, 20)))

# Create inventory slots
slots = []
items = [84, 17, 65, 0, 0, 0, 112, 0, 88, 0, 0, 0]  # Sprite indices, 0 = empty

for i in range(12):
    x = 30 + (i % 4) * 115
    y = 70 + (i // 4) * 100

    slot = mcrfpy.Frame(
        pos=(x, y), size=(90, 80),
        fill_color=mcrfpy.Color(60, 60, 80),
        outline=2.0, outline_color=mcrfpy.Color(80, 80, 100)
    )
    inv_frame.children.append(slot)

    if items[i] > 0:
        sprite = mcrfpy.Sprite(
            texture=mcrfpy.default_texture,
            sprite_index=items[i],
            pos=(25, 15),
            scale=3.0
        )
        slot.children.append(sprite)

    # Hover effect
    def make_hover(s):
        def enter(pos): s.fill_color = mcrfpy.Color(80, 80, 100)
        def exit(pos): s.fill_color = mcrfpy.Color(60, 60, 80)
        return enter, exit

    enter, exit = make_hover(slot)
    slot.on_enter = enter
    slot.on_exit = exit

status = mcrfpy.Caption(text="Hover over slots to highlight", pos=(400, 620))
status.outline = 2
status.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(status)
