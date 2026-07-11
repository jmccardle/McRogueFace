"""Trial 3: GRID TITAN -- grid render + layer-write stress.

Square SxS grid with a TileLayer base and a ColorLayer overlay. Every tick a
32x32 ColorLayer region is rewritten (rolling window) and the camera orbits so
render chunks keep invalidating. Load = S (grid side); cells = S*S.
"""
import math

import mcrfpy

from . import Trial

VIEW_PX = 620
ARENA_X, ARENA_Y = 200, 115
REGION = 32


class GridTitan(Trial):
    key = "grid_titan"
    name = "GRID TITAN"
    unit = "grid side"
    accent = (53, 193, 214)
    description = "SxS grid, rolling color region + orbiting camera"
    base_load = 20
    growth = 1.4

    # Cost scales as S*S (cells) but the render is viewport-bounded, so frame
    # time can stay under budget while allocation runs away. Cap the grid side
    # and predict the footprint so the ramp bails BEFORE a fatal allocation.
    # ~28 bytes/cell: 2 uint8 planes + int32 TileLayer + RGBA ColorLayer + TCOD
    # map cell + slack. max_load derived from a 512 MB grid-data budget.
    CELL_BYTES_EST = 28
    max_load = 4300  # ~4300^2 * 28 B ~= 494 MB

    def predict_bytes(self, load):
        side = max(4, int(load))
        return side * side * self.CELL_BYTES_EST

    def setup(self, scene, ui):
        super().setup(scene, ui)
        self.grid = None
        self.color = None
        self.angle = 0.0
        self.roll = 0
        self.side = 0

    def _build(self, side):
        if self.grid is not None:
            try:
                self.ui.remove(self.grid)
            except Exception:
                pass
        self.side = side
        grid = mcrfpy.Grid(grid_size=(side, side),
                           pos=(ARENA_X, ARENA_Y),
                           size=(VIEW_PX, VIEW_PX),
                           texture=mcrfpy.default_texture)
        grid.zoom = VIEW_PX / float(side * 16)
        grid.fill_color = mcrfpy.Color(10, 12, 18)
        base = mcrfpy.TileLayer(z_index=-2, name="base", texture=mcrfpy.default_texture)
        grid.add_layer(base)
        base.fill(0)
        color = mcrfpy.ColorLayer(z_index=-1, name="overlay")
        grid.add_layer(color)
        color.fill(mcrfpy.Color(20, 26, 38, 120))
        self.ui.append(grid)
        self.grid = grid
        self.color = color
        grid.center_camera((side / 2.0, side / 2.0))

    def set_load(self, level_value):
        side = max(4, int(level_value))
        self._build(side)
        self.load = side

    def tick(self, dt_ms):
        if self.grid is None:
            return
        s = self.side
        # Orbit the camera around the grid centre.
        self.angle += 0.18
        r = s * 0.15
        cx, cy = s / 2.0, s / 2.0
        self.grid.center_camera((cx + r * math.cos(self.angle),
                                 cy + r * math.sin(self.angle)))
        # Rewrite a rolling REGIONxREGION color window.
        w = min(REGION, s)
        span = max(1, s - w)
        self.roll = (self.roll + 3) % span
        ox = self.roll
        oy = (self.roll * 2) % span
        phase = (self.angle * 40) % 255
        col = mcrfpy.Color(int(phase), int(255 - phase), 160, 180)
        self.color.fill_rect((ox, oy), (w, w), col)

    def teardown(self):
        self.grid = None
        self.color = None
        super().teardown()
