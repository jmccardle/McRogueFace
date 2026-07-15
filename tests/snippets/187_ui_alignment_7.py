# mcrf: objects=[Alignment,Caption,Color,Frame,Scene] verified=0.2.8-dev status=ok
import mcrfpy


def create_button_bar(parent):
    """Create a button bar at the bottom-center."""
    bar = mcrfpy.Frame(pos=(0, 0), size=(300, 50))
    bar.fill_color = mcrfpy.Color(30, 30, 40)
    bar.align = mcrfpy.Alignment.BOTTOM_CENTER
    bar.vert_margin = 20.0
    parent.children.append(bar)

    # Buttons spaced within the bar
    button_width = 80
    spacing = 20

    for i, label in enumerate(["Attack", "Defend", "Item"]):
        btn = mcrfpy.Frame(pos=(spacing + i * (button_width + spacing), 10),
                          size=(button_width, 30))
        btn.fill_color = mcrfpy.Color(60, 60, 80)

        text = mcrfpy.Caption(text=label, pos=(0, 0))
        text.align = mcrfpy.Alignment.CENTER
        btn.children.append(text)

        bar.children.append(btn)

    return bar


scene = mcrfpy.Scene("ui_alignment_buttonbar")
mcrfpy.current_scene = scene
parent = mcrfpy.Frame(pos=(0, 0), size=(400, 300))
scene.children.append(parent)
create_button_bar(parent)
