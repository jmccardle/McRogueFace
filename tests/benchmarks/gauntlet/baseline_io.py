"""Baseline JSON read/write/compare for The Gauntlet.

Path: tests/benchmarks/baseline/gauntlet/. Every full run writes latest.json;
baseline.json is written only if absent (never auto-overwritten once it exists).
Schema documented in DESIGN.md.
"""
import datetime
import json
import os
import platform as _platform

import mcrfpy

SCHEMA = 1
BUDGET_MS = 16.67

_HERE = os.path.dirname(os.path.abspath(__file__))
BASELINE_DIR = os.path.normpath(os.path.join(_HERE, "..", "baseline", "gauntlet"))


def _ensure_dir():
    if not os.path.isdir(BASELINE_DIR):
        os.makedirs(BASELINE_DIR, exist_ok=True)


def latest_path():
    return os.path.join(BASELINE_DIR, "latest.json")


def baseline_path():
    return os.path.join(BASELINE_DIR, "baseline.json")


def git_short_hash():
    """Best-effort short commit hash. Guarded -- returns None on any failure.

    Kept out of the engine hot path; only called when writing JSON.
    """
    try:
        import subprocess
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=_HERE, stderr=subprocess.DEVNULL)
        return out.decode("ascii", "replace").strip() or None
    except Exception:
        return None


def load_baseline():
    p = baseline_path()
    if not os.path.isfile(p):
        return None
    try:
        with open(p, "r") as f:
            return json.load(f)
    except Exception:
        return None


def geomean(ratios):
    ratios = [r for r in ratios if r and r > 0]
    if not ratios:
        return 1.0
    prod = 1.0
    for r in ratios:
        prod *= r
    return prod ** (1.0 / len(ratios))


def compare(latest, baseline):
    """Return per-trial ratios + geomean of max_load / baseline_max_load."""
    result = {"has_baseline": baseline is not None, "per_trial": {}, "geomean": 1.0}
    if baseline is None:
        return result
    bt = baseline.get("trials", {})
    ratios = []
    for key, cur in latest.get("trials", {}).items():
        base = bt.get(key)
        if not base:
            continue
        b_load = base.get("max_load", 0)
        if b_load <= 0:
            continue
        ratio = float(cur.get("max_load", 0)) / float(b_load)
        result["per_trial"][key] = ratio
        ratios.append(ratio)
    result["geomean"] = geomean(ratios)
    return result


def build_record(results, budget_ms=BUDGET_MS):
    """results: dict trial_key -> RampController result dict."""
    baseline = load_baseline()
    latest = {
        "schema": SCHEMA,
        "version": getattr(mcrfpy, "__version__", None),
        "commit": git_short_hash(),
        "date": datetime.date.today().isoformat(),
        "platform": _platform.platform(),
        "budget_ms": budget_ms,
        "trials": results,
    }
    cmp = compare(latest, baseline)
    latest["gauntlet_score_vs_baseline"] = cmp["geomean"] if baseline else 1.0
    return latest


def write_run(results, budget_ms=BUDGET_MS):
    """Write latest.json (always) and baseline.json (only if absent). Returns record."""
    _ensure_dir()
    record = build_record(results, budget_ms)
    with open(latest_path(), "w") as f:
        json.dump(record, f, indent=2)
    if not os.path.isfile(baseline_path()):
        with open(baseline_path(), "w") as f:
            json.dump(record, f, indent=2)
        record["_promoted_baseline"] = True
    return record
