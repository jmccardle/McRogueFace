"""Shared HUD overlay for The Gauntlet -- identical on every trial scene.

Top strip: trial name + description (left), a 60-bar frame-time sparkline
(center), and an FPS / p95 / draw-calls / load readout (right). Bottom strip:
key legend. Refresh on a 100 ms Timer; frame_time is milliseconds (see DESIGN.md).
"""
import mcrfpy

# -- palette (r, g, b) ----------------------------------------------------
BG = (13, 15, 20)
PANEL = (22, 26, 34)
OUTLINE = (42, 49, 64)
TEXT = (232, 234, 240)
DIM = (138, 147, 166)
OK = (56, 217, 150)
WARN = (245, 184, 61)
FAIL = (229, 72, 77)

BUDGET_MS = 16.67
WARN_MS = 33.0

SCREEN_W = 1024
SCREEN_H = 768
PANEL_H = 100

# sparkline geometry
SPARK_N = 60
BAR_W = 4
BAR_GAP = 2
SPARK_X = 372
SPARK_TOP = 18
SPARK_H = 52
SPARK_BASE = SPARK_TOP + SPARK_H  # y of bar bottoms
FT_CLAMP = 50.0

LEGEND = ("[SPACE] pause  [LEFT/RIGHT] trial  [-/+] load  [A] auto-ramp  "
          "[R] run gauntlet  [S] shot  [ESC] menu/quit")


def color(rgb, a=255):
    return mcrfpy.Color(rgb[0], rgb[1], rgb[2], a)


def budget_color(ft_ms):
    if ft_ms <= 0:
        return DIM
    if ft_ms < BUDGET_MS:
        return OK
    if ft_ms < WARN_MS:
        return WARN
    return FAIL


def percentile(values, q):
    if not values:
        return 0.0
    s = sorted(values)
    idx = int(round(q * (len(s) - 1)))
    return s[max(0, min(len(s) - 1, idx))]


class HUD:
    def __init__(self):
        self.ring = []
        self.bars = []
        self._built = False

    def build(self, scene, trial):
        ui = scene.children
        acc = trial.accent

        panel = mcrfpy.Frame(pos=(0, 0), size=(SCREEN_W, PANEL_H))
        panel.fill_color = color(PANEL)
        panel.outline = 1
        panel.outline_color = color(OUTLINE)
        panel.z_index = 100
        ui.append(panel)

        self.name_cap = mcrfpy.Caption(text=trial.name, pos=(16, 10))
        self.name_cap.font_size = 28
        self.name_cap.fill_color = color(acc)
        self.name_cap.z_index = 102
        ui.append(self.name_cap)

        self.desc_cap = mcrfpy.Caption(text=trial.description, pos=(16, 50))
        self.desc_cap.font_size = 14
        self.desc_cap.fill_color = color(DIM)
        self.desc_cap.z_index = 102
        ui.append(self.desc_cap)

        # sparkline bars
        self.bars = []
        for i in range(SPARK_N):
            bx = SPARK_X + i * (BAR_W + BAR_GAP)
            bar = mcrfpy.Frame(pos=(bx, SPARK_BASE - 2), size=(BAR_W, 2))
            bar.fill_color = color(DIM)
            bar.z_index = 101
            ui.append(bar)
            self.bars.append(bar)

        # 16.7 ms budget hairline
        budget_h = 2 + (BUDGET_MS / FT_CLAMP) * (SPARK_H - 2)
        by = SPARK_BASE - budget_h
        line = mcrfpy.Line(start=(SPARK_X, by),
                           end=(SPARK_X + SPARK_N * (BAR_W + BAR_GAP), by),
                           color=color(TEXT, 120), thickness=1.0)
        line.z_index = 103
        ui.append(line)
        self.spark_label = mcrfpy.Caption(text="16.7ms", pos=(SPARK_X, SPARK_TOP - 2))
        self.spark_label.font_size = 10
        self.spark_label.fill_color = color(DIM)
        self.spark_label.z_index = 103
        ui.append(self.spark_label)

        # right readout block
        rx = 772
        self.fps_cap = mcrfpy.Caption(text="-- FPS", pos=(rx, 6))
        self.fps_cap.font_size = 34
        self.fps_cap.fill_color = color(TEXT)
        self.fps_cap.z_index = 102
        ui.append(self.fps_cap)

        self.p95_cap = mcrfpy.Caption(text="frame p95: -- ms", pos=(rx, 48))
        self.p95_cap.font_size = 14
        self.p95_cap.fill_color = color(DIM)
        self.p95_cap.z_index = 102
        ui.append(self.p95_cap)

        self.draw_cap = mcrfpy.Caption(text="draw calls: --", pos=(rx, 66))
        self.draw_cap.font_size = 14
        self.draw_cap.fill_color = color(DIM)
        self.draw_cap.z_index = 102
        ui.append(self.draw_cap)

        self.load_cap = mcrfpy.Caption(text="LOAD: -- [MANUAL]", pos=(rx, 82))
        self.load_cap.font_size = 14
        self.load_cap.fill_color = color(acc)
        self.load_cap.z_index = 102
        ui.append(self.load_cap)

        # bottom legend strip
        bottom = mcrfpy.Frame(pos=(0, SCREEN_H - 22), size=(SCREEN_W, 22))
        bottom.fill_color = color(PANEL)
        bottom.outline = 1
        bottom.outline_color = color(OUTLINE)
        bottom.z_index = 100
        ui.append(bottom)
        self.legend_cap = mcrfpy.Caption(text=LEGEND, pos=(12, SCREEN_H - 18))
        self.legend_cap.font_size = 12
        self.legend_cap.fill_color = color(DIM)
        self.legend_cap.z_index = 102
        ui.append(self.legend_cap)

        self.ring = []
        self.unit = trial.unit
        self._built = True

    def refresh(self, metrics, load_value, ramp_tag):
        if not self._built:
            return
        ft = float(metrics.get("frame_time", 0.0))
        self.ring.append(ft)
        if len(self.ring) > SPARK_N:
            self.ring = self.ring[-SPARK_N:]

        # bars: oldest at left, newest at right
        n = len(self.ring)
        for i, bar in enumerate(self.bars):
            src = i - (SPARK_N - n)
            if src < 0:
                bar.h = 2
                bar.y = SPARK_BASE - 2
                bar.fill_color = color(OUTLINE)
                continue
            v = self.ring[src]
            clamped = max(0.0, min(FT_CLAMP, v))
            h = 2 + (clamped / FT_CLAMP) * (SPARK_H - 2)
            bar.h = h
            bar.y = SPARK_BASE - h
            bar.fill_color = color(budget_color(v))

        bc = budget_color(ft)
        fps = int(round(1000.0 / ft)) if ft > 0 else 0
        self.fps_cap.text = "%d FPS" % fps
        self.fps_cap.fill_color = color(bc)
        self.p95_cap.text = "frame p95: %.1f ms" % percentile(self.ring, 0.95)
        self.draw_cap.text = "draw calls: %d" % int(metrics.get("draw_calls", 0))
        self.load_cap.text = "LOAD: %d %s %s" % (int(load_value), self.unit, ramp_tag)
