"""Tests for pathfinding with collision labels (#302)

Tests Grid.find_path(collide=), Grid.get_dijkstra_map(collide=),
and Entity.find_path() convenience method.
"""
import mcrfpy
import sys

PASS = 0
FAIL = 0

def test(name, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
    else:
        FAIL += 1
        print(f"FAIL: {name}")


def make_grid():
    """Create a 10x10 grid with all cells walkable."""
    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    g = mcrfpy.Grid(grid_size=(10, 10), texture=tex,
                    pos=(0, 0), size=(160, 160))
    # Make all cells walkable
    for y in range(10):
        for x in range(10):
            pt = g.at(x, y)
            pt.walkable = True
            pt.transparent = True
    return g


def test_find_path_no_collide():
    """find_path without collide should ignore entity labels."""
    g = make_grid()
    scene = mcrfpy.Scene("test_fp_nocollide")
    scene.children.append(g)

    # Place a blocking entity at (3, 0) with label "enemy"
    e = mcrfpy.Entity((3, 0), grid=g)
    e.add_label("enemy")

    # Without collide, path should go through (3, 0)
    path = g.find_path((0, 0), (5, 0))
    test("find_path without collide returns path", path is not None)
    if path:
        steps = [s for s in path]
        coords = [(int(s.x), int(s.y)) for s in steps]
        test("find_path without collide goes through entity cell",
             (3, 0) in coords)


def test_find_path_with_collide():
    """find_path with collide should avoid entities with that label."""
    g = make_grid()
    scene = mcrfpy.Scene("test_fp_collide")
    scene.children.append(g)

    # Place blocking entities in a line at y=0, x=3
    e = mcrfpy.Entity((3, 0), grid=g)
    e.add_label("enemy")

    # With collide="enemy", path must avoid (3, 0)
    path = g.find_path((0, 0), (5, 0), collide="enemy")
    test("find_path with collide returns path", path is not None)
    if path:
        steps = [s for s in path]
        coords = [(int(s.x), int(s.y)) for s in steps]
        test("find_path with collide avoids entity cell",
             (3, 0) not in coords)


def test_find_path_collide_different_label():
    """find_path with collide should only block matching labels."""
    g = make_grid()
    scene = mcrfpy.Scene("test_fp_difflabel")
    scene.children.append(g)

    e = mcrfpy.Entity((3, 0), grid=g)
    e.add_label("friend")

    # Collide with "enemy" should not block "friend" entities
    path = g.find_path((0, 0), (5, 0), collide="enemy")
    test("find_path collide ignores non-matching labels", path is not None)
    if path:
        steps = [s for s in path]
        coords = [(int(s.x), int(s.y)) for s in steps]
        test("find_path goes through non-matching label entity",
             (3, 0) in coords)


def test_find_path_collide_restores_walkability():
    """After find_path with collide, cell walkability is restored."""
    g = make_grid()
    scene = mcrfpy.Scene("test_fp_restore")
    scene.children.append(g)

    e = mcrfpy.Entity((3, 0), grid=g)
    e.add_label("enemy")

    # Check walkability before
    test("cell walkable before find_path", g.at(3, 0).walkable)

    path = g.find_path((0, 0), (5, 0), collide="enemy")

    # Cell should be walkable again after
    test("cell walkable after find_path with collide", g.at(3, 0).walkable)


def test_find_path_collide_blocks_path():
    """If colliding entities block the only path, find_path returns None."""
    g = make_grid()
    scene = mcrfpy.Scene("test_fp_blocked")
    scene.children.append(g)

    # Create a wall of enemies across the middle
    for x in range(10):
        e = mcrfpy.Entity((x, 5), grid=g)
        e.add_label("wall")

    path = g.find_path((0, 0), (0, 9), collide="wall")
    test("find_path returns None when collide blocks all paths", path is None)


def test_dijkstra_no_collide():
    """get_dijkstra_map without collide ignores labels."""
    g = make_grid()
    scene = mcrfpy.Scene("test_dij_nocollide")
    scene.children.append(g)

    e = mcrfpy.Entity((3, 0), grid=g)
    e.add_label("enemy")

    dmap = g.get_dijkstra_map((0, 0))
    dist = dmap.distance((3, 0))
    test("dijkstra without collide reaches entity cell", dist is not None)
    test("dijkstra distance to (3,0) is 3", abs(dist - 3.0) < 0.01)


def test_dijkstra_with_collide():
    """get_dijkstra_map with collide blocks labeled entities."""
    g = make_grid()
    scene = mcrfpy.Scene("test_dij_collide")
    scene.children.append(g)

    e = mcrfpy.Entity((3, 0), grid=g)
    e.add_label("enemy")

    dmap = g.get_dijkstra_map((0, 0), collide="enemy")
    dist = dmap.distance((3, 0))
    # (3,0) is blocked, so distance should be None (unreachable as walkable)
    # Actually, the cell is marked non-walkable for computation, but libtcod
    # may still report a distance. Let's check that path avoids it.
    path = dmap.path_from((5, 0))
    test("dijkstra with collide returns path", path is not None)
    if path:
        steps = [s for s in path]
        coords = [(int(s.x), int(s.y)) for s in steps]
        test("dijkstra path avoids collide entity cell",
             (3, 0) not in coords)


def test_dijkstra_cache_separate_keys():
    """Dijkstra maps with different collide labels are cached separately."""
    g = make_grid()
    scene = mcrfpy.Scene("test_dij_cache")
    scene.children.append(g)

    e = mcrfpy.Entity((3, 0), grid=g)
    e.add_label("enemy")

    dmap_none = g.get_dijkstra_map((0, 0))
    dmap_enemy = g.get_dijkstra_map((0, 0), collide="enemy")

    # Same root, different collide label = different maps
    dist_none = dmap_none.distance((3, 0))
    dist_enemy = dmap_enemy.distance((3, 0))

    test("dijkstra no-collide reaches (3,0)", dist_none is not None and dist_none >= 0)
    # With collide, (3,0) is non-walkable, distance should be different
    # (either None or a longer path distance)
    test("dijkstra cache separates collide labels",
         dist_none != dist_enemy or dist_enemy is None)


def test_dijkstra_collide_restores_walkability():
    """After get_dijkstra_map with collide, walkability is restored."""
    g = make_grid()
    scene = mcrfpy.Scene("test_dij_restore")
    scene.children.append(g)

    e = mcrfpy.Entity((3, 0), grid=g)
    e.add_label("enemy")

    test("cell walkable before dijkstra", g.at(3, 0).walkable)
    dmap = g.get_dijkstra_map((0, 0), collide="enemy")
    test("cell walkable after dijkstra with collide", g.at(3, 0).walkable)


def test_entity_find_path():
    """Entity.find_path() convenience method."""
    g = make_grid()
    scene = mcrfpy.Scene("test_efp")
    scene.children.append(g)

    player = mcrfpy.Entity((0, 0), grid=g)
    target = mcrfpy.Entity((5, 5), grid=g)

    path = player.find_path((5, 5))
    test("entity.find_path returns AStarPath", path is not None)
    test("entity.find_path type is AStarPath",
         type(path).__name__ == "AStarPath")
    if path:
        test("entity.find_path origin is entity pos",
             int(path.origin.x) == 0 and int(path.origin.y) == 0)
        test("entity.find_path destination is target",
             int(path.destination.x) == 5 and int(path.destination.y) == 5)


def test_entity_find_path_with_collide():
    """Entity.find_path() with collide kwarg."""
    g = make_grid()
    scene = mcrfpy.Scene("test_efp_collide")
    scene.children.append(g)

    player = mcrfpy.Entity((0, 0), grid=g)
    enemy = mcrfpy.Entity((3, 0), grid=g)
    enemy.add_label("enemy")

    path = player.find_path((5, 0), collide="enemy")
    test("entity.find_path with collide returns path", path is not None)
    if path:
        steps = [s for s in path]
        coords = [(int(s.x), int(s.y)) for s in steps]
        test("entity.find_path with collide avoids enemy",
             (3, 0) not in coords)


def test_entity_find_path_to_entity():
    """Entity.find_path() accepts an Entity as target."""
    g = make_grid()
    scene = mcrfpy.Scene("test_efp_entity")
    scene.children.append(g)

    player = mcrfpy.Entity((0, 0), grid=g)
    goal = mcrfpy.Entity((5, 5), grid=g)

    path = player.find_path(goal)
    test("entity.find_path(entity) returns path", path is not None)
    if path:
        test("entity.find_path(entity) destination correct",
             int(path.destination.x) == 5 and int(path.destination.y) == 5)


def test_entity_find_path_no_grid():
    """Entity.find_path() raises if entity has no grid."""
    e = mcrfpy.Entity((0, 0))
    try:
        path = e.find_path((5, 5))
        test("entity.find_path without grid raises", False)
    except ValueError:
        test("entity.find_path without grid raises", True)


if __name__ == "__main__":
    test_find_path_no_collide()
    test_find_path_with_collide()
    test_find_path_collide_different_label()
    test_find_path_collide_restores_walkability()
    test_find_path_collide_blocks_path()
    test_dijkstra_no_collide()
    test_dijkstra_with_collide()
    test_dijkstra_cache_separate_keys()
    test_dijkstra_collide_restores_walkability()
    test_entity_find_path()
    test_entity_find_path_with_collide()
    test_entity_find_path_to_entity()
    test_entity_find_path_no_grid()

    total = PASS + FAIL
    print(f"\n{PASS}/{total} tests passed")
    if FAIL:
        print(f"{FAIL} FAILED")
        sys.exit(1)
    else:
        print("PASS")
        sys.exit(0)
