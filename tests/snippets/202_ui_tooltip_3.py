# mcrf: objects=[Caption,Color,Frame,Scene] verified=0.2.8-dev status=ok
import mcrfpy

def create_info_icon(x, y, tooltip_text, ui):
    """
    Create an info icon that shows tooltip on hover.

    Args:
        x, y: Position of the icon
        tooltip_text: Text to show
        ui: Scene UI to add elements to
    """
    # Info icon (small circle with "i")
    icon = mcrfpy.Frame(pos=(x, y), size=(20, 20))
    icon.fill_color = mcrfpy.Color(70, 130, 180)
    icon.outline = 1
    icon.outline_color = mcrfpy.Color(100, 160, 210)

    icon_label = mcrfpy.Caption(text="i", pos=(x + 6, y + 2))
    icon_label.fill_color = mcrfpy.Color(255, 255, 255)

    # Tooltip (positioned to the right of icon)
    tip_frame = mcrfpy.Frame(pos=(x + 25, y - 5), size=(180, 50))
    tip_frame.fill_color = mcrfpy.Color(40, 40, 55, 240)
    tip_frame.outline = 1
    tip_frame.outline_color = mcrfpy.Color(80, 80, 100)
    tip_frame.visible = False

    tip_text = mcrfpy.Caption(text=tooltip_text, pos=(x + 33, y + 3))
    tip_text.fill_color = mcrfpy.Color(220, 220, 220)
    tip_text.visible = False

    # Hover behavior — enter/exit fire directly, no polling needed
    def on_icon_enter(pos):
        tip_frame.visible = True
        tip_text.visible = True

    def on_icon_exit(pos):
        tip_frame.visible = False
        tip_text.visible = False

    icon.on_enter = on_icon_enter
    icon.on_exit = on_icon_exit

    # Add to scene
    ui.append(icon)
    ui.append(icon_label)
    ui.append(tip_frame)
    ui.append(tip_text)

    return icon


# Usage
scene = mcrfpy.Scene("info_demo")
mcrfpy.current_scene = scene

# Setting with info icon
setting_label = mcrfpy.Caption(text="Difficulty:", pos=(100, 100))
setting_label.fill_color = mcrfpy.Color(200, 200, 200)
scene.children.append(setting_label)

create_info_icon(200, 98, "Affects enemy\nHP and damage", scene.children)
