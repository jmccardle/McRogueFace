"""McRogueFace - Dijkstra Distance Maps (basic)

Documentation: https://mcrogueface.github.io/cookbook/grid_dijkstra
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/grid/grid_dijkstra_basic.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

def ai_flee(entity, threat_x, threat_y):
    """Move entity away from threat using Dijkstra map."""
    grid.compute_dijkstra(threat_x, threat_y)

    ex, ey = entity.pos
    current_dist = grid.get_dijkstra_distance(ex, ey)

    # Find neighbor with highest distance
    best_move = None
    best_dist = current_dist

    for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
        nx, ny = ex + dx, ey + dy

        if grid.at(nx, ny).walkable:
            dist = grid.get_dijkstra_distance(nx, ny)
            if dist > best_dist:
                best_dist = dist
                best_move = (nx, ny)

    if best_move:
        entity.pos = best_move