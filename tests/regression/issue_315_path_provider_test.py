"""Phase C regression: PathProvider abstraction drives SEEK/FLEE via set_behavior.

Verifies that each of the three provider shapes (DijkstraMap, AStarPath, and
plain target tuple) produces a valid SEEK step, and that swapping pathfinder
mid-run changes the next step.
"""
import mcrfpy
import sys


def make_open_grid(w=20, h=20):
    scene = mcrfpy.Scene("issue315")
    mcrfpy.current_scene = scene
    grid = mcrfpy.Grid(grid_size=(w, h))
    scene.children.append(grid)
    for y in range(h):
        for x in range(w):
            c = grid.at(x, y)
            # Walkable interior, walls on the border.
            if x == 0 or y == 0 or x == w - 1 or y == h - 1:
                c.walkable = False
                c.transparent = False
            else:
                c.walkable = True
                c.transparent = True
    return grid


def closer_to(p, goal, start):
    """True when p is closer than start to goal (Chebyshev)."""
    def d(a, b): return max(abs(a[0] - b[0]), abs(a[1] - b[1]))
    return d(p, goal) < d(start, goal)


def test_dijkstra_provider():
    grid = make_open_grid()
    e = mcrfpy.Entity((5, 5), grid=grid)
    e.move_speed = 0
    goal = (15, 15)
    dmap = grid.get_dijkstra_map(goal)
    e.set_behavior(int(mcrfpy.Behavior.SEEK), pathfinder=dmap)

    start = (e.cell_x, e.cell_y)
    grid.step()
    ended = (e.cell_x, e.cell_y)
    assert ended != start, "DijkstraProvider SEEK must move the entity"
    assert closer_to(ended, goal, start), f"moved away from goal: {start} -> {ended}"
    print("  DijkstraProvider SEEK: OK")


def test_astar_provider():
    grid = make_open_grid()
    e = mcrfpy.Entity((5, 5), grid=grid)
    e.move_speed = 0
    goal = (10, 10)
    path = grid.find_path((5, 5), goal)
    assert path is not None
    e.set_behavior(int(mcrfpy.Behavior.SEEK), pathfinder=path)

    start = (e.cell_x, e.cell_y)
    grid.step()
    ended = (e.cell_x, e.cell_y)
    assert ended != start, "AStarProvider SEEK must move the entity"
    assert closer_to(ended, goal, start), f"moved away from goal: {start} -> {ended}"
    print("  AStarProvider SEEK: OK")


def test_target_provider():
    grid = make_open_grid()
    e = mcrfpy.Entity((5, 5), grid=grid)
    e.move_speed = 0
    goal = (10, 10)
    e.set_behavior(int(mcrfpy.Behavior.SEEK), pathfinder=goal)

    start = (e.cell_x, e.cell_y)
    grid.step()
    ended = (e.cell_x, e.cell_y)
    assert ended != start, "TargetProvider SEEK must move the entity"
    assert closer_to(ended, goal, start), f"moved away from target: {start} -> {ended}"
    print("  TargetProvider SEEK: OK")


def test_flee_via_inverted_dijkstra():
    grid = make_open_grid()
    e = mcrfpy.Entity((10, 10), grid=grid)
    e.move_speed = 0
    threat = (12, 10)
    threat_map = grid.get_dijkstra_map(threat)
    safety_map = threat_map.invert()
    e.set_behavior(int(mcrfpy.Behavior.FLEE), pathfinder=safety_map)

    start = (e.cell_x, e.cell_y)
    start_dist = threat_map.distance(start)
    grid.step()
    ended = (e.cell_x, e.cell_y)
    assert ended != start, "FLEE must move the entity"
    new_dist = threat_map.distance(ended)
    assert new_dist >= start_dist, (
        f"FLEE should not get closer: d={start_dist} -> {new_dist}")
    print("  FLEE via inverted DijkstraMap: OK")


def test_provider_swap_midrun():
    """Swapping pathfinder mid-run changes the next step."""
    grid = make_open_grid()
    e = mcrfpy.Entity((10, 10), grid=grid)
    e.move_speed = 0

    # First: seek (5, 10) - should move left.
    e.set_behavior(int(mcrfpy.Behavior.SEEK),
                   pathfinder=grid.get_dijkstra_map((5, 10)))
    grid.step()
    after_first = (e.cell_x, e.cell_y)
    assert after_first[0] < 10, f"expected leftward step, got {after_first}"

    # Swap pathfinder: now seek (15, 10) - should move right from here.
    e.set_behavior(int(mcrfpy.Behavior.SEEK),
                   pathfinder=grid.get_dijkstra_map((15, 10)))
    grid.step()
    after_second = (e.cell_x, e.cell_y)
    assert after_second[0] > after_first[0], (
        f"expected rightward step after swap, got {after_first} -> {after_second}")
    print("  Mid-run provider swap: OK")


def test_invalid_pathfinder_raises():
    grid = make_open_grid()
    e = mcrfpy.Entity((5, 5), grid=grid)
    try:
        e.set_behavior(int(mcrfpy.Behavior.SEEK), pathfinder="not a pathfinder")
    except TypeError:
        pass
    else:
        raise AssertionError("expected TypeError for bad pathfinder argument")
    print("  Invalid pathfinder rejected: OK")


def main():
    test_dijkstra_provider()
    test_astar_provider()
    test_target_provider()
    test_flee_via_inverted_dijkstra()
    test_provider_swap_midrun()
    test_invalid_pathfinder_raises()
    print("PASS")


if __name__ == "__main__":
    main()
    sys.exit(0)
