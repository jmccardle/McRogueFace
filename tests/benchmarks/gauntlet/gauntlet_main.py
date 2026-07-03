"""The Gauntlet -- interactive entry point.

Menu scene -> pick a trial (1-6) and watch it, drive load manually (-/+) or
toggle auto-ramp (A); R runs the whole gauntlet back-to-back and shows the
results screen. See DESIGN.md.

Run windowed:  ./mcrogueface tests/benchmarks/gauntlet/gauntlet_main.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import mcrfpy

import hud as hud_mod
import baseline_io
from hud import HUD, color, BG, PANEL, OUTLINE, TEXT, DIM, OK, FAIL, WARN, SCREEN_W, SCREEN_H
from scoring import RampController, grade_for_ratio
from trials import make_trials, TRIALS


def disable_vsync():
    """frame_time floors at the vsync budget otherwise (DESIGN.md deviation 2)."""
    try:
        mcrfpy.window.vsync = False
        mcrfpy.window.framerate_limit = 0
    except Exception:
        pass


def make_bg(scene):
    bg = mcrfpy.Frame(pos=(0, 0), size=(SCREEN_W, SCREEN_H))
    bg.fill_color = color(BG)
    bg.z_index = 0
    scene.children.append(bg)
    return bg


def trial_meta():
    """key -> (name, accent, unit) for results/menu display."""
    meta = {}
    for cls in TRIALS:
        meta[cls.key] = (cls.name, cls.accent, cls.unit)
    return meta


# ------------------------------------------------------------------ results
def build_results_scene(record):
    # If this run was just promoted to baseline.json, it IS the baseline --
    # show FIRST RUN rather than comparing the run against itself.
    if record.get("_promoted_baseline"):
        baseline = None
    else:
        baseline = baseline_io.load_baseline()
    cmp = baseline_io.compare(record, baseline)
    meta = trial_meta()

    scene = mcrfpy.Scene("gt_results")
    make_bg(scene)

    title = mcrfpy.Caption(text="GAUNTLET RESULTS", pos=(40, 30))
    title.font_size = 34
    title.fill_color = color(TEXT)
    scene.children.append(title)

    sub = mcrfpy.Caption(text="version %s   commit %s   %s" % (
        record.get("version"), record.get("commit"), record.get("platform")),
        pos=(42, 74))
    sub.font_size = 13
    sub.fill_color = color(DIM)
    scene.children.append(sub)

    # header row
    y0 = 120
    headers = [("TRIAL", 42), ("MAX LOAD", 320), ("p95 @ PEAK", 560), ("vs BASE", 760)]
    for txt, x in headers:
        h = mcrfpy.Caption(text=txt, pos=(x, y0))
        h.font_size = 14
        h.fill_color = color(DIM)
        scene.children.append(h)

    row_h = 42
    for i, cls in enumerate(TRIALS):
        key = cls.key
        res = record.get("trials", {}).get(key)
        y = y0 + 30 + i * row_h
        name, accent, unit = meta[key]

        nm = mcrfpy.Caption(text=name, pos=(42, y))
        nm.font_size = 20
        nm.fill_color = color(accent)
        scene.children.append(nm)

        if res is None:
            continue
        ld = mcrfpy.Caption(text="%d %s" % (res["max_load"], unit), pos=(320, y + 2))
        ld.font_size = 18
        ld.fill_color = color(TEXT)
        scene.children.append(ld)

        p95 = mcrfpy.Caption(text="%.1f ms" % res["p95_ms"], pos=(560, y + 2))
        p95.font_size = 18
        p95.fill_color = color(TEXT)
        scene.children.append(p95)

        if cmp["has_baseline"] and key in cmp["per_trial"]:
            ratio = cmp["per_trial"][key]
            pct = (ratio - 1.0) * 100.0
            if pct > 1.0:
                dtxt, dcol = "^ +%.0f%% %s" % (pct, grade_for_ratio(ratio)), OK
            elif pct < -1.0:
                dtxt, dcol = "v %.0f%% %s" % (pct, grade_for_ratio(ratio)), FAIL
            else:
                dtxt, dcol = "= same %s" % grade_for_ratio(ratio), DIM
            dc = mcrfpy.Caption(text=dtxt, pos=(760, y + 2))
            dc.font_size = 18
            dc.fill_color = color(dcol)
            scene.children.append(dc)

    # footer score
    fy = y0 + 30 + len(TRIALS) * row_h + 24
    if cmp["has_baseline"]:
        geo = cmp["geomean"]
        stext = "GAUNTLET SCORE   x%.1f%% vs baseline   grade %s" % (
            geo * 100.0, grade_for_ratio(geo))
        scol = OK if geo >= 1.0 else FAIL
    else:
        stext = "FIRST RUN -- baseline recorded"
        scol = TEXT
    sc = mcrfpy.Caption(text=stext, pos=(42, fy))
    sc.font_size = 24
    sc.fill_color = color(scol)
    scene.children.append(sc)

    hint = mcrfpy.Caption(text="[ESC] menu   [S] screenshot", pos=(42, fy + 40))
    hint.font_size = 13
    hint.fill_color = color(DIM)
    scene.children.append(hint)
    return scene


# ------------------------------------------------------------------ app
class Gauntlet:
    def __init__(self, autorun=False):
        self.trials = make_trials()
        self.idx = 0
        self.trial = None
        self.hud = None
        self.scene = None
        self.state = "menu"      # menu | trial | results
        self.mode = "manual"     # manual | ramp
        self.autorun = autorun
        self.manual_load = 0
        self.ramp = None
        self.paused = False
        self.results = {}
        self.shot_n = 0
        self.menu_scene = None
        self.menu_title = None
        self.menu_accent = 0
        self.on_results = None   # optional hook(record) fired after results built

    # -- timers -----------------------------------------------------------
    def install_timers(self):
        mcrfpy.Timer("gt_sim", self._on_sim, 100)
        mcrfpy.Timer("gt_hud", self._on_hud, 100)
        mcrfpy.Timer("gt_sample", self._on_sample, 16)

    def _on_sim(self, timer, rt):
        if self.state == "trial" and not self.paused and self.trial:
            self.trial.tick(100)

    def _on_hud(self, timer, rt):
        if self.state == "trial" and self.hud:
            self.hud.refresh(mcrfpy.get_metrics(), self._load_value(), self._ramp_tag())

    def _on_sample(self, timer, rt):
        if self.state != "trial" or self.mode != "ramp" or not self.ramp:
            return
        if not self.ramp.done:
            self.ramp.sample(rt, mcrfpy.get_metrics())
            if self.ramp.done:
                self._ramp_finished()

    # -- helpers ----------------------------------------------------------
    def _load_value(self):
        if self.mode == "ramp" and self.ramp:
            return self.ramp.load
        return self.manual_load

    def _ramp_tag(self):
        if self.paused:
            return "[PAUSE]"
        if self.mode == "ramp" and self.ramp:
            return self.ramp.ramp_tag
        return "[MANUAL]"

    # -- menu -------------------------------------------------------------
    def show_menu(self):
        if self.trial:
            self.trial.teardown()
            self.trial = None
        self.state = "menu"
        self.mode = "manual"
        self.ramp = None
        baseline = baseline_io.load_baseline()
        bt = baseline.get("trials", {}) if baseline else {}

        scene = mcrfpy.Scene("gt_menu")
        make_bg(scene)
        title = mcrfpy.Caption(text="THE GAUNTLET", pos=(0, 70))
        title.font_size = 60
        title.fill_color = color(TRIALS[0].accent)
        title.x = (SCREEN_W - title.w) / 2 if title.w else 300
        scene.children.append(title)
        self.menu_title = title

        subtitle = mcrfpy.Caption(text="McRogueFace stress benchmark", pos=(0, 150))
        subtitle.font_size = 18
        subtitle.fill_color = color(DIM)
        subtitle.x = (SCREEN_W - subtitle.w) / 2 if subtitle.w else 380
        scene.children.append(subtitle)

        y = 230
        for i, cls in enumerate(TRIALS):
            row = mcrfpy.Caption(
                text="%d.  %s" % (i + 1, cls.name), pos=(260, y))
            row.font_size = 24
            row.fill_color = color(cls.accent)
            scene.children.append(row)
            info = "unit: %s" % cls.unit
            base = bt.get(cls.key)
            if base:
                info += "    baseline: %d" % base.get("max_load", 0)
            ic = mcrfpy.Caption(text=info, pos=(640, y + 4))
            ic.font_size = 14
            ic.fill_color = color(DIM)
            scene.children.append(ic)
            y += 48

        ver = getattr(mcrfpy, "__version__", "?")
        commit = baseline_io.git_short_hash() or "?"
        vc = mcrfpy.Caption(text="engine %s  (%s)" % (ver, commit), pos=(16, SCREEN_H - 30))
        vc.font_size = 13
        vc.fill_color = color(DIM)
        scene.children.append(vc)

        hint = mcrfpy.Caption(
            text="[1-6] watch trial   [R] run full gauntlet   [ESC] quit",
            pos=(300, SCREEN_H - 60))
        hint.font_size = 15
        hint.fill_color = color(TEXT)
        scene.children.append(hint)

        scene.on_key = self._menu_key
        self.menu_scene = scene
        mcrfpy.current_scene = scene
        self.menu_accent = 0
        self._cycle_title(None, None, None)

    def _cycle_title(self, target, prop, val):
        if self.state != "menu" or self.menu_title is None:
            return
        self.menu_accent = (self.menu_accent + 1) % len(TRIALS)
        acc = TRIALS[self.menu_accent].accent
        # 2 s per accent, 6 accents -> 12 s loop; only re-arm on one channel.
        self.menu_title.animate("fill_color.r", float(acc[0]), 2.0,
                                mcrfpy.Easing.EASE_IN_OUT_SINE, callback=self._cycle_title)
        self.menu_title.animate("fill_color.g", float(acc[1]), 2.0,
                                mcrfpy.Easing.EASE_IN_OUT_SINE)
        self.menu_title.animate("fill_color.b", float(acc[2]), 2.0,
                                mcrfpy.Easing.EASE_IN_OUT_SINE)

    def _menu_key(self, key, state):
        if state != mcrfpy.InputState.PRESSED:
            return
        digits = {mcrfpy.Key.NUM_1: 0, mcrfpy.Key.NUM_2: 1, mcrfpy.Key.NUM_3: 2,
                  mcrfpy.Key.NUM_4: 3, mcrfpy.Key.NUM_5: 4, mcrfpy.Key.NUM_6: 5}
        if key in digits:
            self.enter_trial(digits[key], ramp=False)
        elif key == mcrfpy.Key.R:
            self.begin_autorun()
        elif key == mcrfpy.Key.ESCAPE:
            mcrfpy.exit()

    # -- trial ------------------------------------------------------------
    def enter_trial(self, idx, ramp=False):
        if self.trial:
            self.trial.teardown()
        self.idx = idx % len(self.trials)
        self.trial = self.trials[self.idx]
        self.scene = mcrfpy.Scene("gt_%s" % self.trial.key)
        make_bg(self.scene)
        self.trial.setup(self.scene, self.scene.children)
        self.trial.set_load(self.trial.base_load)
        self.manual_load = self.trial.base_load
        self.hud = HUD()
        self.hud.build(self.scene, self.trial)
        self.scene.on_key = self._trial_key
        self.paused = False
        self.state = "trial"
        mcrfpy.current_scene = self.scene
        if ramp:
            self._begin_ramp()
        else:
            self.mode = "manual"
            self.ramp = None

    def _begin_ramp(self):
        self.mode = "ramp"
        self.ramp = RampController(self.trial, mcrfpy.get_metrics)
        self.ramp.start()
        self.manual_load = self.trial.base_load

    def _ramp_finished(self):
        self.results[self.trial.key] = self.ramp.result
        if self.autorun:
            nxt = self.idx + 1
            if nxt < len(self.trials):
                self.enter_trial(nxt, ramp=True)
            else:
                self.finish_autorun()
        else:
            # interactive single-trial ramp: settle into manual at the peak load
            self.mode = "manual"
            self.manual_load = self.ramp.result["max_load"] or self.trial.base_load

    def _trial_key(self, key, state):
        if state != mcrfpy.InputState.PRESSED:
            return
        K = mcrfpy.Key
        if key == K.ESCAPE:
            self.autorun = False
            self.show_menu()
        elif key == K.SPACE:
            self.paused = not self.paused
        elif key == K.LEFT:
            self.enter_trial(self.idx - 1, ramp=False)
        elif key == K.RIGHT:
            self.enter_trial(self.idx + 1, ramp=False)
        elif key in (K.EQUAL, K.ADD):
            self._adjust_load(1.5)
        elif key in (K.HYPHEN, K.SUBTRACT):
            self._adjust_load(1.0 / 1.5)
        elif key == K.A:
            if self.mode == "ramp":
                self.mode = "manual"
                self.ramp = None
            else:
                self._begin_ramp()
        elif key == K.R:
            self.begin_autorun()
        elif key == K.S:
            self._screenshot()

    def _adjust_load(self, factor):
        if self.mode == "ramp":
            self.mode = "manual"
            self.ramp = None
        self.manual_load = max(1, int(round(self.manual_load * factor)))
        self.trial.set_load(self.manual_load)

    def _screenshot(self):
        from mcrfpy import automation
        self.shot_n += 1
        automation.screenshot("gauntlet_shot_%d.png" % self.shot_n)

    # -- autorun ----------------------------------------------------------
    def begin_autorun(self):
        self.autorun = True
        self.results = {}
        self.enter_trial(0, ramp=True)

    def finish_autorun(self):
        if self.trial:
            self.trial.teardown()
            self.trial = None
        self.state = "results"
        record = baseline_io.write_run(self.results)
        scene = build_results_scene(record)
        scene.on_key = self._results_key
        mcrfpy.current_scene = scene
        if self.on_results:
            self.on_results(record)

    def _results_key(self, key, state):
        if state != mcrfpy.InputState.PRESSED:
            return
        if key == mcrfpy.Key.ESCAPE:
            self.autorun = False
            self.show_menu()
        elif key == mcrfpy.Key.S:
            self._screenshot()


def main():
    disable_vsync()
    app = Gauntlet(autorun=False)
    app.install_timers()
    app.show_menu()


if __name__ == "__main__":
    main()
