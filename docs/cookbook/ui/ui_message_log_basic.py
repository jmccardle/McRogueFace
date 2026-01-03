"""McRogueFace - Message Log Widget (basic)

Documentation: https://mcrogueface.github.io/cookbook/ui_message_log
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/ui/ui_message_log_basic.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

import mcrfpy

# Initialize
mcrfpy.createScene("game")
mcrfpy.setScene("game")
ui = mcrfpy.sceneUI("game")

# Create log at bottom of screen
log = EnhancedMessageLog(10, 500, 700, 250, line_height=20)
ui.append(log.frame)

# Simulate game events
def simulate_combat(dt):
    import random
    events = [
        ("You swing your sword!", "combat"),
        ("The orc dodges!", "combat"),
        ("Critical hit!", "combat"),
        ("You found a potion!", "loot"),
    ]
    event = random.choice(events)
    log.add(event[0], event[1])

# Add messages every 2 seconds for demo
mcrfpy.setTimer("combat_sim", simulate_combat, 2000)

# Keyboard controls
def on_key(key, state):
    if state != "start":
        return
    if key == "PageUp":
        log.scroll_up(3)
    elif key == "PageDown":
        log.scroll_down(3)
    elif key == "C":
        log.set_filter('combat')
    elif key == "L":
        log.set_filter('loot')
    elif key == "A":
        log.set_filter(None)  # All

mcrfpy.keypressScene(on_key)

log.system("Press PageUp/PageDown to scroll")
log.system("Press C for combat, L for loot, A for all")