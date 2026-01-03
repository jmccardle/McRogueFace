"""McRogueFace - Modal Dialog Widget (basic)

Documentation: https://mcrogueface.github.io/cookbook/ui_modal_dialog
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/ui/ui_modal_dialog_basic.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

import mcrfpy

# Scene setup
mcrfpy.createScene("game")
mcrfpy.setScene("game")
ui = mcrfpy.sceneUI("game")

# Game background
bg = mcrfpy.Frame(0, 0, 1024, 768)
bg.fill_color = mcrfpy.Color(25, 35, 45)
ui.append(bg)

title = mcrfpy.Caption("My Game", mcrfpy.default_font, 450, 50)
title.fill_color = mcrfpy.Color(255, 255, 255)
ui.append(title)

# Quit button
quit_btn = mcrfpy.Frame(430, 400, 160, 50)
quit_btn.fill_color = mcrfpy.Color(150, 50, 50)
quit_btn.outline = 2
quit_btn.outline_color = mcrfpy.Color(200, 100, 100)
ui.append(quit_btn)

quit_label = mcrfpy.Caption("Quit Game", mcrfpy.default_font, 460, 415)
quit_label.fill_color = mcrfpy.Color(255, 255, 255)
ui.append(quit_label)

# Confirmation dialog
confirm_dialog = None

def show_quit_confirm():
    global confirm_dialog

    def on_response(index, label):
        if label == "Yes":
            mcrfpy.exit()

    confirm_dialog = EnhancedDialog(
        "Quit Game?",
        "Are you sure you want to quit?\nUnsaved progress will be lost.",
        ["Yes", "No"],
        DialogStyle.WARNING,
        on_response
    )
    confirm_dialog.add_to_scene(ui)
    confirm_dialog.show()

quit_btn.click = lambda x, y, b, a: show_quit_confirm() if a == "start" else None

def on_key(key, state):
    if state != "start":
        return

    if confirm_dialog and confirm_dialog.handle_key(key):
        return

    if key == "Escape":
        show_quit_confirm()

mcrfpy.keypressScene(on_key)