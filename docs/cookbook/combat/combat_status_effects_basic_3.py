"""McRogueFace - Status Effects (basic_3)

Documentation: https://mcrogueface.github.io/cookbook/combat_status_effects
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/combat/combat_status_effects_basic_3.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

def serialize_effects(effect_manager):
       return [{"name": e.name, "duration": e.duration}
               for e in effect_manager.effects]