"""Trial 1: ENTITY SWARM -- entity step + render stress.

One 40x25 grid, N entities with SEEK behavior chasing a wandering target via a
Dijkstra map, advanced with grid.step() on the sim tick. Load = entity count.
"""
import random

import mcrfpy

from . import Trial

GRID_W, GRID_H = 40, 25
CELL = 24  # display px per cell (zoom applied)
ARENA_X, ARENA_Y = 40, 110
SEEK = int(mcrfpy.Behavior.SEEK)


class EntitySwarm(Trial):
    key = "entity_swarm"
    name = "ENTITY SWARM"
    unit = "entities"
    accent = (245, 165, 36)
    description = "N seeking entities, grid.step() every tick"
    base_load = 60
    growth = 1.6

    def setup(self, scene, ui):
        super().setup(scene, ui)
        self.rng = random.Random(0xE117)
        self.ticks = 0
        self.target = (GRID_W // 2, GRID_H // 2)

        grid = mcrfpy.Grid(grid_size=(GRID_W, GRID_H),
                           pos=(ARENA_X, ARENA_Y),
                           size=(GRID_W * CELL, GRID_H * CELL))
        grid.zoom = CELL / 16.0
        grid.fill_color = mcrfpy.Color(18, 22, 30)
        for y in range(GRID_H):
            for x in range(GRID_W):
                c = grid.at(x, y)
                edge = (x == 0 or y == 0 or x == GRID_W - 1 or y == GRID_H - 1)
                c.walkable = not edge
                c.transparent = not edge
        ui.append(grid)
        self.grid = grid
        self.entities = []
        self.dmap = grid.get_dijkstra_map(self.target)
        grid.center_camera((GRID_W / 2.0, GRID_H / 2.0))

    def _spawn(self):
        while True:
            x = self.rng.randint(1, GRID_W - 2)
            y = self.rng.randint(1, GRID_H - 2)
            if (x, y) != self.target:
                break
        e = mcrfpy.Entity((x, y), grid=self.grid)
        e.sprite_index = self.rng.choice((84, 85, 86, 100, 101))
        e.move_speed = 0.3  # animate between cells so the swarm spreads visually
        e.set_behavior(SEEK, pathfinder=self.dmap)
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

    def _move_target(self):
        self.target = (self.rng.randint(1, GRID_W - 2),
                       self.rng.randint(1, GRID_H - 2))
        self.grid.clear_dijkstra_maps()
        self.dmap = self.grid.get_dijkstra_map(self.target)
        for e in self.entities:
            e.set_behavior(SEEK, pathfinder=self.dmap)

    def tick(self, dt_ms):
        self.ticks += 1
        if self.ticks % 4 == 0:
            self._move_target()
        self.grid.step()

    def teardown(self):
        self.entities = []
        self.grid = None
        self.dmap = None
        super().teardown()
