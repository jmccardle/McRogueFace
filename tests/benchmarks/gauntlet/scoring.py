"""Ramp control and scoring for The Gauntlet.

The RampController is a small state machine driven by a scoring "sample" call
(nominally a 16 ms Timer). It sets a trial's load, discards a settle window,
collects frame-time samples over a hold window, and decides pass/fail:

  pass  : p95 <= budget_ms          -> record as new peak, ramp load up one step
  fail  : p95 >  budget_ms          -> stop; score = last passing load
  bail  : HARD_CAP_STRIKES samples > hard_cap_ms in one window -> stop (fail)

The bail requires sustained overload (3 strikes) rather than a single sample:
on a live desktop one stray >100 ms frame (compositor, GC, notification) is
common and was observed zeroing entire trials, while a genuinely overloaded
engine trips 3 strikes within ~50 ms of wall time anyway. Lone spikes still
count toward p95. (Deviation 8 in DESIGN.md.)

frame_time is read from get_metrics()["frame_time"] and is already in
milliseconds in this engine build (see DESIGN.md deviation 1).
"""

BUDGET_MS = 16.67
HARD_CAP_MS = 100.0
HARD_CAP_STRIKES = 3
SETTLE_MS = 1000
HOLD_MS = 2000
MAX_STEPS = 40  # safety ceiling so a trial that never breaks budget still terminates


def percentile(values, q):
    """Nearest-rank percentile of an unsorted list. q in [0, 1]."""
    if not values:
        return 0.0
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    idx = int(round(q * (len(s) - 1)))
    idx = max(0, min(len(s) - 1, idx))
    return s[idx]


def load_at_step(base_load, growth, k):
    """Geometric ramp: load_k = round(base * growth**k)."""
    return int(round(base_load * (growth ** k)))


def grade_for_ratio(ratio):
    """Letter grade vs baseline ratio (max_load / baseline_max_load)."""
    if ratio >= 1.50:
        return "S"
    if ratio >= 1.00:
        return "A"
    if ratio >= 0.80:
        return "B"
    if ratio >= 0.60:
        return "C"
    return "D"


class RampController:
    """Drives one trial through its auto-ramp and produces a result dict.

    Usage: create, call start(), then call sample(now_ms, metrics) repeatedly
    from the scoring timer. When .done is True, .result holds the final dict.
    """

    def __init__(self, trial, metrics_provider,
                 budget_ms=BUDGET_MS, hard_cap_ms=HARD_CAP_MS,
                 settle_ms=SETTLE_MS, hold_ms=HOLD_MS, max_steps=MAX_STEPS,
                 hard_cap_strikes=HARD_CAP_STRIKES, on_finish=None):
        self.hard_cap_strikes = hard_cap_strikes
        self.strikes = 0
        self.trial = trial
        self.metrics_provider = metrics_provider  # callable -> full get_metrics() dict
        self.budget_ms = budget_ms
        self.hard_cap_ms = hard_cap_ms
        self.settle_ms = settle_ms
        self.hold_ms = hold_ms
        self.max_steps = max_steps
        self.on_finish = on_finish

        self.k = 0
        self.load = trial.base_load
        self.phase = "idle"          # idle | settle | hold | done
        self.phase_start = None
        self.samples = []
        self.last_pass = None        # dict of last passing window
        self.done = False
        self.result = None

    # -- public API -------------------------------------------------------
    def start(self):
        self.k = 0
        self.load = int(self.trial.base_load)
        self.trial.set_load(self.load)
        self.phase = "settle"
        self.phase_start = None
        self.samples = []
        self.strikes = 0
        self.last_pass = None
        self.done = False
        self.result = None

    @property
    def ramp_tag(self):
        if self.done:
            return "[DONE]"
        if self.phase == "hold":
            return "[HOLD]"
        return "[RAMP %d]" % self.k

    def sample(self, now_ms, metrics=None):
        if self.done or self.phase == "idle":
            return
        if metrics is None:
            metrics = self.metrics_provider()
        ft = float(metrics.get("frame_time", 0.0))

        if self.phase_start is None:
            self.phase_start = now_ms
        elapsed = now_ms - self.phase_start

        if self.phase == "settle":
            if elapsed >= self.settle_ms:
                self.phase = "hold"
                self.phase_start = now_ms
                self.samples = []
                self.strikes = 0
            return

        # hold phase
        self.samples.append(ft)
        if ft > self.hard_cap_ms:
            self.strikes += 1
            if self.strikes >= self.hard_cap_strikes:
                self._evaluate(metrics, forced_fail=True)
                return
        if elapsed >= self.hold_ms:
            self._evaluate(metrics, forced_fail=False)

    # -- internal ---------------------------------------------------------
    def _evaluate(self, metrics, forced_fail):
        p50 = percentile(self.samples, 0.50)
        p95 = percentile(self.samples, 0.95)
        passed = (not forced_fail) and (p95 <= self.budget_ms)

        if passed:
            self.last_pass = {
                "load": self.load,
                "p50_ms": round(p50, 3),
                "p95_ms": round(p95, 3),
                "samples": len(self.samples),
                "metrics_at_peak": dict(metrics),
            }
            if self.k + 1 > self.max_steps:
                self._finish()
                return
            self.k += 1
            self.load = load_at_step(self.trial.base_load, self.trial.growth, self.k)
            self.trial.set_load(self.load)
            self.phase = "settle"
            self.phase_start = None
            self.samples = []
        else:
            self._finish()

    def _finish(self):
        self.phase = "done"
        self.done = True
        if self.last_pass is not None:
            lp = self.last_pass
            self.result = {
                "unit": self.trial.unit,
                "max_load": lp["load"],
                "p50_ms": lp["p50_ms"],
                "p95_ms": lp["p95_ms"],
                "samples": lp["samples"],
                "metrics_at_peak": lp["metrics_at_peak"],
            }
        else:
            # First load already failed -- record a zero score honestly.
            self.result = {
                "unit": self.trial.unit,
                "max_load": 0,
                "p50_ms": round(percentile(self.samples, 0.50), 3),
                "p95_ms": round(percentile(self.samples, 0.95), 3),
                "samples": len(self.samples),
                "metrics_at_peak": self.metrics_provider(),
            }
        if self.on_finish:
            self.on_finish(self)
