"""McRogueFace - Health Bar Widget (basic)

Documentation: https://mcrogueface.github.io/cookbook/ui_health_bar
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/ui/ui_health_bar_basic.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

import mcrfpy

mcrfpy.createScene("game")
mcrfpy.setScene("game")
ui = mcrfpy.sceneUI("game")

# Player health bar at top
player_hp = EnhancedHealthBar(10, 10, 300, 30, 100, 100)
player_hp.add_to_scene(ui)

# Enemy health bar
enemy_hp = EnhancedHealthBar(400, 10, 200, 20, 50, 50)
enemy_hp.add_to_scene(ui)

# Simulate combat
def combat_tick(dt):
    import random
    if random.random() < 0.3:
        player_hp.damage(random.randint(5, 15))
    if random.random() < 0.4:
        enemy_hp.damage(random.randint(3, 8))

mcrfpy.setTimer("combat", combat_tick, 1000)

# Keyboard controls for testing
def on_key(key, state):
    if state != "start":
        return
    if key == "H":
        player_hp.heal(20)
    elif key == "D":
        player_hp.damage(10)

mcrfpy.keypressScene(on_key)