"""Helper for Phase 5.2 benchmark scripts to write JSON baselines.

Each bench script calls `_baseline.write("name.json", out_dict)` to save its
results to `tests/benchmarks/baseline/phase5_2/<name>`. Future runs can be
diffed against these for regression detection.
"""
import json
import os


def write(filename, payload):
    base = os.path.join(os.path.dirname(__file__), "baseline", "phase5_2")
    os.makedirs(base, exist_ok=True)
    path = os.path.join(base, filename)
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"  baseline written: {path}")
    return path
