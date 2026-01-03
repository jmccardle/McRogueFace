"""McRogueFace - Melee Combat System (complete)

Documentation: https://mcrogueface.github.io/cookbook/combat_melee
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/combat/combat_melee_complete.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

def die_with_animation(entity):
       # Play death animation
       anim = mcrfpy.Animation("opacity", 0.0, 0.5, "linear")
       anim.start(entity)
       # Remove after animation
       mcrfpy.setTimer("remove", lambda dt: remove_entity(entity), 500)