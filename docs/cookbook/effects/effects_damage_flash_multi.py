"""McRogueFace - Damage Flash Effect (multi)

Documentation: https://mcrogueface.github.io/cookbook/effects_damage_flash
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/effects/effects_damage_flash_multi.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

import mcrfpy

def multi_flash(grid, x, y, color, flashes=3, flash_duration=0.1):
    """Flash a cell multiple times for emphasis."""
    delay = 0

    for i in range(flashes):
        # Schedule each flash with increasing delay
        def do_flash(timer_name, fx=x, fy=y, fc=color, fd=flash_duration):
            flash_cell(grid, fx, fy, fc, fd)

        mcrfpy.Timer(f"flash_{x}_{y}_{i}", do_flash, int(delay * 1000), once=True)
        delay += flash_duration * 1.5  # Gap between flashes

# Usage for critical hit
multi_flash(grid, int(enemy.x), int(enemy.y), (255, 255, 0), flashes=3)