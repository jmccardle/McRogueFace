"""McRogueFace - Selection Menu Widget (basic)

Documentation: https://mcrogueface.github.io/cookbook/ui_menu
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/ui/ui_menu_basic.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

import mcrfpy

# Setup
mcrfpy.createScene("main_menu")
mcrfpy.setScene("main_menu")
ui = mcrfpy.sceneUI("main_menu")

# Background
bg = mcrfpy.Frame(0, 0, 1024, 768)
bg.fill_color = mcrfpy.Color(20, 20, 35)
ui.append(bg)

# Title
title = mcrfpy.Caption("DUNGEON QUEST", mcrfpy.default_font, 350, 100)
title.fill_color = mcrfpy.Color(255, 200, 50)
ui.append(title)

# Menu
def start_game():
    print("Starting game...")

def show_options():
    print("Options...")

menu = Menu(
    362, 250,
    ["New Game", "Continue", "Options", "Quit"],
    lambda i, opt: {
        0: start_game,
        1: lambda: print("Continue..."),
        2: show_options,
        3: mcrfpy.exit
    }.get(i, lambda: None)(),
    title="Main Menu"
)
menu.add_to_scene(ui)

# Input
def on_key(key, state):
    if state != "start":
        return
    menu.handle_key(key)

mcrfpy.keypressScene(on_key)