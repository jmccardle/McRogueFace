"""McRogueFace - Dijkstra Distance Maps (multi)

Documentation: https://mcrogueface.github.io/cookbook/grid_dijkstra
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/grid/grid_dijkstra_multi.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

# Cache Dijkstra maps when possible
class CachedDijkstra:
    """Cache Dijkstra computations."""

    def __init__(self, grid):
        self.grid = grid
        self.cache = {}
        self.cache_valid = False

    def invalidate(self):
        """Call when map changes."""
        self.cache = {}
        self.cache_valid = False

    def get_distance(self, from_x, from_y, to_x, to_y):
        """Get cached distance or compute."""
        key = (to_x, to_y)  # Cache by destination

        if key not in self.cache:
            self.grid.compute_dijkstra(to_x, to_y)
            # Store all distances from this computation
            self.cache[key] = self._snapshot_distances()

        return self.cache[key].get((from_x, from_y), float('inf'))

    def _snapshot_distances(self):
        """Capture current distance values."""
        grid_w, grid_h = self.grid.grid_size
        distances = {}
        for x in range(grid_w):
            for y in range(grid_h):
                dist = self.grid.get_dijkstra_distance(x, y)
                if dist != float('inf'):
                    distances[(x, y)] = dist
        return distances