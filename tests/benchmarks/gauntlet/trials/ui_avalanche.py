"""Trial 5: UI AVALANCHE -- UI hierarchy + draw-call stress.

Nested Frame trees (depth 5), each level carrying a Caption and a Sprite, plus a
z-order shuffle of the top-level frames every tick to defeat render caching.
Load = total UI elements.
"""
import random

import mcrfpy

from . import Trial

ARENA_X, ARENA_Y = 20, 108
COL_W, ROW_H = 132, 132
COLS = 7
DEPTH = 5
PER_TREE = 15  # 1 root frame + 5*(caption+sprite) + 4 nested frames


class UIAvalanche(Trial):
    key = "ui_avalanche"
    name = "UI AVALANCHE"
    unit = "elements"
    accent = (154, 110, 245)
    description = "Depth-5 frame trees, z-shuffled every tick"
    base_load = 60
    growth = 1.6

    def setup(self, scene, ui):
        super().setup(scene, ui)
        self.rng = random.Random(0x5A1A)
        self.trees = []      # list of root Frames
        self.total = 0

    def _build_tree(self, index):
        col = index % COLS
        row = index // COLS
        x = ARENA_X + col * COL_W
        y = ARENA_Y + row * ROW_H
        root = mcrfpy.Frame(pos=(x, y), size=(120, 120))
        root.fill_color = mcrfpy.Color(self.rng.randint(30, 90),
                                       self.rng.randint(20, 70),
                                       self.rng.randint(60, 120))
        root.outline = 1
        root.outline_color = mcrfpy.Color(154, 110, 245)
        self.ui.append(root)
        count = 1
        parent = root
        size = 120
        for d in range(DEPTH):
            cap = mcrfpy.Caption(text="L%d" % d, pos=(4, 2))
            cap.fill_color = mcrfpy.Color(220, 220, 240)
            parent.children.append(cap)
            count += 1
            spr = mcrfpy.Sprite(pos=(4, 18), texture=mcrfpy.default_texture,
                                sprite_index=self.rng.randint(0, 120))
            parent.children.append(spr)
            count += 1
            if d < DEPTH - 1:
                size -= 18
                child = mcrfpy.Frame(pos=(10, 30), size=(size, size))
                child.fill_color = mcrfpy.Color(self.rng.randint(30, 90),
                                                self.rng.randint(20, 70),
                                                self.rng.randint(60, 120))
                parent.children.append(child)
                count += 1
                parent = child
        self.trees.append(root)
        self.total += count

    def set_load(self, level_value):
        target = max(PER_TREE, int(level_value))
        while self.total < target:
            self._build_tree(len(self.trees))
        # Shed whole trees while we can stay at or above target.
        while self.trees and (self.total - PER_TREE) >= target:
            root = self.trees.pop()
            try:
                self.ui.remove(root)
            except Exception:
                pass
            self.total -= PER_TREE
        self.load = self.total

    def tick(self, dt_ms):
        # Shuffle z-order of top-level frames to invalidate caches.
        order = list(range(len(self.trees)))
        self.rng.shuffle(order)
        for z, root in zip(order, self.trees):
            root.z_index = z

    def teardown(self):
        self.trees = []
        self.total = 0
        super().teardown()
