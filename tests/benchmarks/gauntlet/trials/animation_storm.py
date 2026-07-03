"""Trial 2: ANIMATION STORM -- animation manager stress.

N small Frames, each running two concurrent, self-relaunching animations
(position with random easing + a fill_color pulse). Load = live animations = 2N.
"""
import random

import mcrfpy

from . import Trial

ARENA_X, ARENA_Y = 20, 110
ARENA_W, ARENA_H = 984, 620
BOX = 16


class AnimationStorm(Trial):
    key = "animation_storm"
    name = "ANIMATION STORM"
    unit = "animations"
    accent = (229, 85, 157)
    description = "N frames x 2 self-sustaining animations"
    base_load = 60
    growth = 1.6

    def setup(self, scene, ui):
        super().setup(scene, ui)
        self.rng = random.Random(0xA817)
        self.frames = []
        self.live = set()
        self.easings = [
            mcrfpy.Easing.LINEAR, mcrfpy.Easing.EASE_IN_OUT_SINE,
            mcrfpy.Easing.EASE_OUT_CUBIC, mcrfpy.Easing.EASE_IN_OUT_BACK,
            mcrfpy.Easing.EASE_OUT_BOUNCE,
        ]

    def _new_frame(self):
        x = self.rng.uniform(ARENA_X, ARENA_X + ARENA_W - BOX)
        y = self.rng.uniform(ARENA_Y, ARENA_Y + ARENA_H - BOX)
        fr = mcrfpy.Frame(pos=(x, y), size=(BOX, BOX))
        fr.fill_color = mcrfpy.Color(self.rng.randint(80, 255),
                                     self.rng.randint(40, 200),
                                     self.rng.randint(120, 255))
        self.ui.append(fr)
        self.frames.append(fr)
        self.live.add(fr)
        self._launch_pos(fr)
        self._launch_color(fr)

    def _launch_pos(self, fr):
        if fr not in self.live:
            return
        tx = self.rng.uniform(ARENA_X, ARENA_X + ARENA_W - BOX)
        dur = self.rng.uniform(0.4, 1.2)
        fr.animate("x", tx, dur, self.rng.choice(self.easings),
                   callback=self._on_pos_done)

    def _launch_color(self, fr):
        if fr not in self.live:
            return
        tgt = float(self.rng.choice((40, 255)))
        dur = self.rng.uniform(0.3, 0.9)
        fr.animate("fill_color.r", tgt, dur, mcrfpy.Easing.EASE_IN_OUT_SINE,
                   callback=self._on_color_done)

    def _on_pos_done(self, target, prop, val):
        self._launch_pos(target)

    def _on_color_done(self, target, prop, val):
        self._launch_color(target)

    def set_load(self, level_value):
        target_frames = max(1, int(level_value) // 2)
        while len(self.frames) < target_frames:
            self._new_frame()
        while len(self.frames) > target_frames:
            fr = self.frames.pop()
            self.live.discard(fr)
            try:
                self.ui.remove(fr)
            except Exception:
                pass
        self.load = len(self.frames) * 2

    def teardown(self):
        self.live = set()
        self.frames = []
        super().teardown()
