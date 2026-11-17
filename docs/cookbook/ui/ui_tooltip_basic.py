"""McRogueFace - Tooltip on Hover (basic)

Documentation: https://mcrogueface.github.io/cookbook/ui_tooltip
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/ui/ui_tooltip_basic.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

import mcrfpy

mcrfpy.createScene("game")
mcrfpy.setScene("game")
ui = mcrfpy.sceneUI("game")

# Background
bg = mcrfpy.Frame(0, 0, 1024, 768)
bg.fill_color = mcrfpy.Color(25, 25, 35)
ui.append(bg)

# Create inventory slots with tooltips
class InventorySlot:
    def __init__(self, x, y, item_name, item_desc, tooltip_mgr):
        self.frame = mcrfpy.Frame(x, y, 50, 50)
        self.frame.fill_color = mcrfpy.Color(50, 50, 60)
        self.frame.outline = 1
        self.frame.outline_color = mcrfpy.Color(80, 80, 90)

        self.label = mcrfpy.Caption(item_name[:3], mcrfpy.default_font, x + 10, y + 15)
        self.label.fill_color = mcrfpy.Color(200, 200, 200)

        tooltip_mgr.register(self.frame, item_desc, title=item_name)

    def add_to_scene(self, ui):
        ui.append(self.frame)
        ui.append(self.label)

# Setup tooltip manager
tips = TooltipManager()
tips.hover_delay = 300

# Create inventory
items = [
    ("Health Potion", "Restores 50 HP\nConsumable"),
    ("Mana Crystal", "Restores 30 MP\nConsumable"),
    ("Iron Key", "Opens iron doors\nQuest Item"),
    ("Gold Ring", "Worth 100 gold\nSell to merchant"),
]

slots = []
for i, (name, desc) in enumerate(items):
    slot = InventorySlot(100 + i * 60, 100, name, desc, tips)
    slot.add_to_scene(ui)
    slots.append(slot)

# Add tooltip last
tips.add_to_scene(ui)

# Update loop
def update(dt):
    from mcrfpy import automation
    x, y = automation.position()
    tips.update(x, y)

mcrfpy.setTimer("update", update, 50)