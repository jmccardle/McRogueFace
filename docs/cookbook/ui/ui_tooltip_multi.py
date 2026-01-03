"""McRogueFace - Tooltip on Hover (multi)

Documentation: https://mcrogueface.github.io/cookbook/ui_tooltip
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/ui/ui_tooltip_multi.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

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
    icon = mcrfpy.Frame(x, y, 20, 20)
    icon.fill_color = mcrfpy.Color(70, 130, 180)
    icon.outline = 1
    icon.outline_color = mcrfpy.Color(100, 160, 210)

    icon_label = mcrfpy.Caption("i", mcrfpy.default_font, x + 6, y + 2)
    icon_label.fill_color = mcrfpy.Color(255, 255, 255)

    # Tooltip (positioned to the right of icon)
    tip_frame = mcrfpy.Frame(x + 25, y - 5, 180, 50)
    tip_frame.fill_color = mcrfpy.Color(40, 40, 55, 240)
    tip_frame.outline = 1
    tip_frame.outline_color = mcrfpy.Color(80, 80, 100)
    tip_frame.visible = False

    tip_text = mcrfpy.Caption(tooltip_text, mcrfpy.default_font, x + 33, y + 3)
    tip_text.fill_color = mcrfpy.Color(220, 220, 220)
    tip_text.visible = False

    # Hover behavior
    def on_icon_hover(mx, my, button, action):
        tip_frame.visible = True
        tip_text.visible = True

    icon.click = on_icon_hover

    # Track when to hide
    def check_hover(dt):
        from mcrfpy import automation
        mx, my = automation.position()
        if not (icon.x <= mx <= icon.x + icon.w and
                icon.y <= my <= icon.y + icon.h):
            if tip_frame.visible:
                tip_frame.visible = False
                tip_text.visible = False

    timer_name = f"info_hover_{id(icon)}"
    mcrfpy.setTimer(timer_name, check_hover, 100)

    # Add to scene
    ui.append(icon)
    ui.append(icon_label)
    ui.append(tip_frame)
    ui.append(tip_text)

    return icon


# Usage
mcrfpy.createScene("info_demo")
mcrfpy.setScene("info_demo")
ui = mcrfpy.sceneUI("info_demo")

# Setting with info icon
setting_label = mcrfpy.Caption("Difficulty:", mcrfpy.default_font, 100, 100)
setting_label.fill_color = mcrfpy.Color(200, 200, 200)
ui.append(setting_label)

create_info_icon(200, 98, "Affects enemy\nHP and damage", ui)