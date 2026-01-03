"""McRogueFace - Basic Enemy AI (multi)

Documentation: https://mcrogueface.github.io/cookbook/combat_enemy_ai
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/combat/combat_enemy_ai_multi.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

# Filter to cardinal directions only
   path = [p for p in path if abs(p[0] - ex) + abs(p[1] - ey) == 1]