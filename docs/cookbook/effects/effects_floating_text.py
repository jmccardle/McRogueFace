"""McRogueFace - Floating Damage Numbers (effects_floating_text)

Documentation: https://mcrogueface.github.io/cookbook/effects_floating_text
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/effects/effects_floating_text.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

class StackedFloatingText:
    """Prevents overlapping text by stacking vertically."""

    def __init__(self, scene_name, grid=None):
        self.manager = FloatingTextManager(scene_name, grid)
        self.position_stack = {}  # Track recent spawns per position

    def spawn_stacked(self, x, y, text, color, **kwargs):
        """Spawn with automatic vertical stacking."""
        key = (int(x), int(y))

        # Calculate offset based on recent spawns at this position
        offset = self.position_stack.get(key, 0)
        actual_y = y - (offset * 20)  # 20 pixels between stacked texts

        self.manager.spawn(x, actual_y, text, color, **kwargs)

        # Increment stack counter
        self.position_stack[key] = offset + 1

        # Reset stack after delay
        def reset_stack(timer_name, k=key):
            if k in self.position_stack:
                self.position_stack[k] = max(0, self.position_stack[k] - 1)

        mcrfpy.Timer(f"stack_reset_{x}_{y}_{offset}", reset_stack, 300, once=True)

# Usage
stacked = StackedFloatingText("game", grid)
# Rapid hits will stack vertically instead of overlapping
stacked.spawn_stacked(5, 5, "-10", (255, 0, 0), is_grid_pos=True)
stacked.spawn_stacked(5, 5, "-8", (255, 0, 0), is_grid_pos=True)
stacked.spawn_stacked(5, 5, "-12", (255, 0, 0), is_grid_pos=True)