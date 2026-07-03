"""Trial 4: PATHFINDER RUSH -- A* query stress.

A static maze grid; every tick issues Q grid.find_path queries between random
walkable pairs. Load = queries per tick.
"""
import random

import mcrfpy

from . import Trial

GRID_W, GRID_H = 60, 40
CELL = 15
ARENA_X, ARENA_Y = 60, 120


class PathfinderRush(Trial):
    key = "pathfinder_rush"
    name = "PATHFINDER RUSH"
    unit = "queries/tick"
    accent = (76, 194, 110)
    description = "A* find_path queries across a static maze"
    base_load = 5
    growth = 1.6

    def setup(self, scene, ui):
        super().setup(scene, ui)
        self.rng = random.Random(0x9A2E)
        self.queries = 0

        grid = mcrfpy.Grid(grid_size=(GRID_W, GRID_H),
                           pos=(ARENA_X, ARENA_Y),
                           size=(GRID_W * CELL, GRID_H * CELL))
        grid.zoom = CELL / 16.0
        grid.fill_color = mcrfpy.Color(10, 14, 20)
        floor = mcrfpy.ColorLayer(z_index=-1, name="floor")
        grid.add_layer(floor)
        floor.fill(mcrfpy.Color(40, 54, 44))

        wall_c = mcrfpy.Color(14, 20, 16)
        self.walkables = []
        for y in range(GRID_H):
            for x in range(GRID_W):
                c = grid.at(x, y)
                wall = (x == 0 or y == 0 or x == GRID_W - 1 or y == GRID_H - 1)
                # Pillar/room maze: isolated blockers keep the map connected but windy.
                if not wall and x % 4 == 2 and y % 3 == 1:
                    wall = True
                c.walkable = not wall
                c.transparent = not wall
                if wall:
                    floor.set((x, y), wall_c)
                else:
                    self.walkables.append((x, y))
        ui.append(grid)
        self.grid = grid

    def set_load(self, level_value):
        self.queries = max(1, int(level_value))
        self.load = self.queries

    def tick(self, dt_ms):
        if self.grid is None:
            return
        w = self.walkables
        for _ in range(self.queries):
            a = w[self.rng.randrange(len(w))]
            b = w[self.rng.randrange(len(w))]
            self.grid.find_path(a, b)

    def teardown(self):
        self.grid = None
        self.walkables = []
        super().teardown()
