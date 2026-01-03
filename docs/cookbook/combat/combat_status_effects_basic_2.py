"""McRogueFace - Status Effects (basic_2)

Documentation: https://mcrogueface.github.io/cookbook/combat_status_effects
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/combat/combat_status_effects_basic_2.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

def apply_effect(self, effect):
       if effect.name in self.immunities:
           print(f"{self.name} is immune to {effect.name}!")
           return
       if effect.name in self.resistances:
           effect.duration //= 2  # Half duration
       self.effects.add_effect(effect)