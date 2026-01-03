"""McRogueFace - Multi-Layer Tiles (complete)

Documentation: https://mcrogueface.github.io/cookbook/grid_multi_layer
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/grid/grid_multi_layer_complete.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

class OptimizedLayers:
    """Performance-optimized layer management."""

    def __init__(self, grid):
        self.grid = grid
        self.dirty_effects = set()  # Only update changed cells
        self.batch_updates = []

    def mark_dirty(self, x, y):
        """Mark a cell as needing update."""
        self.dirty_effects.add((x, y))

    def batch_set(self, layer, cells_and_values):
        """Queue batch updates."""
        self.batch_updates.append((layer, cells_and_values))

    def flush(self):
        """Apply all queued updates."""
        for layer, updates in self.batch_updates:
            for x, y, value in updates:
                layer.set(x, y, value)
        self.batch_updates = []

    def update_dirty_only(self, effect_layer, effect_calculator):
        """Only update cells marked dirty."""
        for x, y in self.dirty_effects:
            color = effect_calculator(x, y)
            effect_layer.set(x, y, color)
        self.dirty_effects.clear()