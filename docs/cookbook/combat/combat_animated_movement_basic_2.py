"""McRogueFace - Animated Movement (basic_2)

Documentation: https://mcrogueface.github.io/cookbook/combat_animated_movement
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/combat/combat_animated_movement_basic_2.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

current_anim = mcrfpy.Animation("x", 100.0, 0.5, "linear")
   current_anim.start(entity)
   # Later: current_anim = None  # Let it complete or create new one