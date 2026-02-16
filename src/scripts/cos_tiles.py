import mcrfpy

# Load tileset and Wang set once at module level
_tileset = mcrfpy.TileSetFile("assets/kenney_TD_MR_IP.tsx")
_wang_set = _tileset.wang_set("dungeon")
_Terrain = _wang_set.terrain_enum()
# _Terrain.WALL = 1, _Terrain.GROUND = 2


def paint_tiles(grid):
    """Apply Wang tile autotiling based on grid walkability."""
    w = int(grid.grid_size.x)
    h = int(grid.grid_size.y)

    # Build terrain map from walkability
    dm = mcrfpy.DiscreteMap((w, h))
    for y in range(h):
        for x in range(w):
            if grid.at((x, y)).walkable:
                dm.set(x, y, int(_Terrain.GROUND))
            else:
                dm.set(x, y, int(_Terrain.WALL))

    # Resolve Wang tiles
    tiles = _wang_set.resolve(dm)

    # Apply to grid, with fallback for unmatched patterns
    for y in range(h):
        for x in range(w):
            tile_id = tiles[y * w + x]
            if tile_id >= 0:
                grid.at((x, y)).tilesprite = tile_id
            else:
                # Fallback: open floor (145) for ground, solid wall (251) for walls
                if grid.at((x, y)).walkable:
                    grid.at((x, y)).tilesprite = 145
                else:
                    grid.at((x, y)).tilesprite = 251
