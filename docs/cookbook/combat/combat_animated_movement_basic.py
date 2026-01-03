"""McRogueFace - Animated Movement (basic)

Documentation: https://mcrogueface.github.io/cookbook/combat_animated_movement
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/combat/combat_animated_movement_basic.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

if new_x != current_x:
       anim = mcrfpy.Animation("x", float(new_x), duration, "easeInOut", callback=done)
   else:
       anim = mcrfpy.Animation("y", float(new_y), duration, "easeInOut", callback=done)