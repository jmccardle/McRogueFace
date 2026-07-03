"""Trial 6: SIGHTLINE SIEGE -- FOV + perspective writeback stress.

A grid with scattered walls; N entities each recompute an active FOV (radius 10)
via update_visibility() on the sim tick as they random-walk. Load = FOV entities.
"""
import random

import mcrfpy

from . import Trial

GRID_W, GRID_H = 50, 32
CELL = 18
ARENA_X, ARENA_Y = 60, 118
SIGHT = 10
STEPS = ((1, 0), (-1, 0), (0, 1), (0, -1))


class SightlineSiege(Trial):
    key = "sightline_siege"
    name = "SIGHTLINE SIEGE"
    unit = "FOV entities"
    accent = (229, 72, 77)
    description = "N random-walking entities, per-entity FOV recompute"
    base_load = 20
    growth = 1.6

    def setup(self, scene, ui):
        super().setup(scene, ui)
        self.rng = random.Random(0xF0F0)

        grid = mcrfpy.Grid(grid_size=(GRID_W, GRID_H),
                           pos=(ARENA_X, ARENA_Y),
                           size=(GRID_W * CELL, GRID_H * CELL),
                           texture=mcrfpy.default_texture)
        grid.zoom = CELL / 16.0
        grid.fill_color = mcrfpy.Color(8, 10, 16)
        grid.fov_radius = SIGHT
        floor = mcrfpy.ColorLayer(z_index=-1, name="floor")
        grid.add_layer(floor)
        floor.fill(mcrfpy.Color(38, 30, 34))
        wall_c = mcrfpy.Color(16, 12, 14)

        self.walkables = []
        for y in range(GRID_H):
            for x in range(GRID_W):
                c = grid.at(x, y)
                wall = (x == 0 or y == 0 or x == GRID_W - 1 or y == GRID_H - 1)
                if not wall and self.rng.random() < 0.16:
                    wall = True
                c.walkable = not wall
                c.transparent = not wall
                if wall:
                    floor.set((x, y), wall_c)
                else:
                    self.walkables.append((x, y))
        ui.append(grid)
        self.grid = grid
        self.entities = []

    def _spawn(self):
        x, y = self.walkables[self.rng.randrange(len(self.walkables))]
        e = mcrfpy.Entity((x, y), grid=self.grid)
        e.sprite_index = 90
        e.sight_radius = SIGHT
        e.move_speed = 0.0
        e.update_visibility()
        self.entities.append(e)

    def set_load(self, level_value):
        target_n = max(1, int(level_value))
        while len(self.entities) < target_n:
            self._spawn()
        while len(self.entities) > target_n:
            e = self.entities.pop()
            try:
                e.die()
            except Exception:
                pass
        self.load = len(self.entities)

    def tick(self, dt_ms):
        g = self.grid
        for e in self.entities:
            x, y = e.grid_x, e.grid_y
            dirs = list(STEPS)
            self.rng.shuffle(dirs)
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                if 0 <= nx < GRID_W and 0 <= ny < GRID_H and g.at(nx, ny).walkable:
                    e.grid_x = nx
                    e.grid_y = ny
                    break
            e.update_visibility()

    def teardown(self):
        self.entities = []
        self.grid = None
        self.walkables = []
        super().teardown()
