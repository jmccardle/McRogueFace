"""The Gauntlet -- unattended full run.

Runs all six trials back-to-back with auto-ramp, shows the results screen, and
writes tests/benchmarks/baseline/gauntlet/latest.json (promoting to baseline.json
if none exists). Intended to run windowed (or under xvfb); in headless mode
frame_time is 0.0 so no meaningful score is produced (see DESIGN.md deviation 6).

Run:  make gauntlet          (from the repo root: memory cgroup backstop, #469)
      ./mcrogueface tests/benchmarks/gauntlet/run_gauntlet.py   (no backstop)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import mcrfpy

from gauntlet_main import Gauntlet, disable_vsync
import baseline_io
import safety


def _print_summary(record):
    print("=" * 60)
    print("GAUNTLET COMPLETE")
    print("  version : %s" % record.get("version"))
    print("  commit  : %s" % record.get("commit"))
    print("  platform: %s" % record.get("platform"))
    for key, res in record.get("trials", {}).items():
        print("  %-16s max_load=%-6d p50=%.1fms p95=%.1fms n=%d"
              % (key, res["max_load"], res["p50_ms"], res["p95_ms"], res["samples"]))
    print("  score_vs_baseline: %.3f" % record.get("gauntlet_score_vs_baseline", 1.0))
    print("  latest.json : %s" % baseline_io.latest_path())
    if record.get("_promoted_baseline"):
        print("  baseline.json promoted (first run)")
    print("=" * 60)
    sys.stdout.flush()


def main():
    # No in-process address-space cap (#469): GPU drivers map buffers into the
    # process, so RLIMIT_AS made render textures fail and Mesa segfault. The
    # machine-saver backstop is a memory cgroup around the process instead:
    # run via `make gauntlet` (systemd-run MemoryMax). See safety.py.
    print("[safety] RSS ceiling %.0f MB; run under `make gauntlet` for the "
          "memory-cgroup backstop" % safety.DEFAULT_RSS_CEILING_MB)
    sys.stdout.flush()

    disable_vsync()
    app = Gauntlet(autorun=True)

    def on_results(record):
        _print_summary(record)

        def shot_and_exit(timer, rt):
            try:
                from mcrfpy import automation
                automation.screenshot("gauntlet_results.png")
            except Exception:
                pass
            mcrfpy.exit()

        # give the results scene a frame to render before capturing
        mcrfpy.Timer("gt_done", shot_and_exit, 400, once=True)

    app.on_results = on_results
    app.install_timers()
    app.begin_autorun()


if __name__ == "__main__":
    main()
