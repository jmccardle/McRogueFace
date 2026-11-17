# mcrf: objects=[Grid,Scene] verified=0.3.6-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("cave-tunnels")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(grid_size=(40, 30), texture=mcrfpy.default_texture,
                   pos=(0, 0), size=(960, 720))
scene.children.append(grid)

# Solid rock with two separate floor pockets (the "regions" the recipe connects)
for y in range(30):
    for x in range(40):
        cell = grid.at((x, y))
        cell.walkable = False
        cell.tilesprite = 1

pocket_a = [(x, y) for x in range(3, 8) for y in range(3, 8)]
pocket_b = [(x, y) for x in range(30, 36) for y in range(20, 26)]
for x, y in pocket_a + pocket_b:
    cell = grid.at((x, y))
    cell.walkable = True
    cell.tilesprite = 0


# region: connect
def connect_caves(grid, regions):
    """Connect separate cave regions with tunnels."""
    if len(regions) < 2:
        return

    # Sort by size, connect smaller to larger
    regions = sorted(regions, key=len, reverse=True)
    main_region = set(regions[0])

    for region in regions[1:]:
        # Find closest points between regions
        best_dist = float('inf')
        best_pair = None

        for x1, y1 in region:
            for x2, y2 in main_region:
                dist = abs(x2 - x1) + abs(y2 - y1)  # Manhattan distance
                if dist < best_dist:
                    best_dist = dist
                    best_pair = ((x1, y1), (x2, y2))

        # Dig tunnel
        if best_pair:
            dig_tunnel(grid, best_pair[0], best_pair[1])
            main_region.update(region)

def dig_tunnel(grid, start, end):
    """Dig a tunnel between two points."""
    x1, y1 = start
    x2, y2 = end

    # Horizontal then vertical
    x = x1
    while x != x2:
        cell = grid.at((x, y1))
        cell.walkable = True
        cell.tilesprite = 0
        x += 1 if x2 > x1 else -1

    y = y1
    while y != y2:
        cell = grid.at((x2, y))
        cell.walkable = True
        cell.tilesprite = 0
        y += 1 if y2 > y1 else -1
# endregion


connect_caves(grid, [pocket_a, pocket_b])
