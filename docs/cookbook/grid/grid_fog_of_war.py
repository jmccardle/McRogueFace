"""McRogueFace - Basic Fog of War (grid_fog_of_war)

Documentation: https://mcrogueface.github.io/cookbook/grid_fog_of_war
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/grid/grid_fog_of_war.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

# Shadowcasting (default) - fast and produces nice results
grid.compute_fov(x, y, 10, mcrfpy.FOV.SHADOW)

# Recursive shadowcasting - slightly different corner behavior
grid.compute_fov(x, y, 10, mcrfpy.FOV.RECURSIVE_SHADOW)

# Diamond - simple but produces diamond-shaped FOV
grid.compute_fov(x, y, 10, mcrfpy.FOV.DIAMOND)

# Permissive - sees more tiles, good for tactical games
grid.compute_fov(x, y, 10, mcrfpy.FOV.PERMISSIVE)