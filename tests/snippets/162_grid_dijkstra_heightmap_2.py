# mcrf: objects=[Color,ColorLayer,Grid,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("dijkstra_gradient")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(grid_size=(20, 20))
for y in range(20):
    for x in range(20):
        grid.at((x, y)).walkable = True
scene.children.append(grid)

color_layer = mcrfpy.ColorLayer(z_index=1, name="dijkstra_vis")
grid.add_layer(color_layer)


def visualize_dijkstra(grid, color_layer, source):
    """Render dijkstra distances as a color gradient."""
    dijkstra = grid.get_dijkstra_map(source)
    hmap = dijkstra.to_heightmap(unreachable=-1.0)

    width, height = int(grid.grid_size[0]), int(grid.grid_size[1])

    # Find max distance for normalization
    max_dist = 0
    for y in range(height):
        for x in range(width):
            d = hmap[(x, y)]
            if d > max_dist and d != -1.0:
                max_dist = d

    # Color each cell
    for y in range(height):
        for x in range(width):
            dist = hmap[(x, y)]

            if dist == -1.0:
                # Unreachable - dark red
                color = mcrfpy.Color(60, 0, 0)
            elif dist == 0:
                # Source - bright yellow
                color = mcrfpy.Color(255, 255, 0)
            else:
                # Gradient from green (near) to blue (far)
                t = dist / max_dist
                r = 0
                g = int(255 * (1 - t))
                b = int(255 * t)
                color = mcrfpy.Color(r, g, b)

            color_layer.set((x, y), color)


visualize_dijkstra(grid, color_layer, (10, 10))
