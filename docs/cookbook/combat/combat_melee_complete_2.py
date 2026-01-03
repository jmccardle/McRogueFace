"""McRogueFace - Melee Combat System (complete_2)

Documentation: https://mcrogueface.github.io/cookbook/combat_melee
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/combat/combat_melee_complete_2.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

@dataclass
   class AdvancedFighter(Fighter):
       fire_resist: float = 0.0
       ice_resist: float = 0.0
       physical_resist: float = 0.0