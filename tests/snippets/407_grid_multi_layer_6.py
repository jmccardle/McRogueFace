# mcrf: objects=[Color,ColorLayer,Grid,Scene,TileLayer] verified=0.3.6 status=ok
import mcrfpy

scene = mcrfpy.Scene("layer-perf")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(grid_size=(20, 15), pos=(10, 10), size=(640, 480),
                   texture=mcrfpy.default_texture)
scene.children.append(grid)

base = mcrfpy.TileLayer(z_index=0, name="base", texture=mcrfpy.default_texture)
grid.add_layer(base)
base.fill(48)

effect_layer = mcrfpy.ColorLayer(name="effects", z_index=2)
grid.add_layer(effect_layer)


# region: optimized
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
                layer.set((x, y), value)
        self.batch_updates = []

    def update_dirty_only(self, effect_layer, effect_calculator):
        """Only update cells marked dirty."""
        for x, y in self.dirty_effects:
            color = effect_calculator(x, y)
            effect_layer.set((x, y), color)
        self.dirty_effects.clear()
# endregion


layers = OptimizedLayers(grid)
layers.batch_set(effect_layer, [(1, 1, mcrfpy.Color(255, 0, 0, 128)),
                                (2, 1, mcrfpy.Color(0, 255, 0, 128))])
layers.flush()

layers.mark_dirty(3, 3)
layers.update_dirty_only(effect_layer, lambda x, y: mcrfpy.Color(0, 0, 255, 128))
