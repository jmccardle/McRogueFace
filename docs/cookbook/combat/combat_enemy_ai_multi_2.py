"""McRogueFace - Basic Enemy AI (multi_2)

Documentation: https://mcrogueface.github.io/cookbook/combat_enemy_ai
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/combat/combat_enemy_ai_multi_2.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

def alert_nearby(x, y, radius, enemies):
       for enemy in enemies:
           dist = abs(enemy.entity.x - x) + abs(enemy.entity.y - y)
           if dist <= radius and hasattr(enemy.ai, 'alert'):
               enemy.ai.alert = True