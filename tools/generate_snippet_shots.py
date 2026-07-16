#!/usr/bin/env python3
"""
Generate a rendered preview PNG for every documentation snippet.

Each snippet in tests/snippets/ is a display script that builds a scene (see
_harness.py). This tool captures what that scene looks like, so the docs site can show
the rendered result next to the code. The images are a VISUAL-REGRESSION ORACLE: they
are deterministic, so a changed image means the snippet's behaviour changed and wants
review -- see Gitea #381.

    python3 tools/generate_snippet_shots.py            # capture all
    python3 tools/generate_snippet_shots.py 086 224    # capture a subset (by number)

For each snippet it runs a THREE-stage --exec chain in headless mode:

    _seed.py  ->  <snippet>.py  ->  _screenshot.py

_seed.py seeds the interpreter RNG before the snippet draws (procedural snippets draw
at import); _screenshot.py advances a few frames and saves the PNG. Output lands in a
gitignored SHOT_DIR -- the images belong in the doc-site repo, not this one; the site
build pulls them from here.

CAPTURE MODEL (Phase 1: STATIC only)
Every snippet defaults to a static capture: step a few frames, then screenshot. That is
correct for the ~180 snippets whose visual is fully drawn at load. The exceptions live
in OVERRIDES below:
  * noshot=True        -- no meaningful single frame (API/audio/text-only demos); skip.
  * setup_steps=N      -- needs more frames than default (e.g. a first timer fire that
                          fills a caption at t>=0.1s).
Animation target-time (shot_at) and scripted interaction (action) are later phases and
are not captured yet; snippets needing them get a default static frame for now.
"""

import argparse
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNIPPET_DIR = os.path.join(ROOT, "tests", "snippets")
BUILD_DIR = os.path.join(ROOT, "build")
MCROGUEFACE = os.path.join(BUILD_DIR, "mcrogueface")
SEED = os.path.join(SNIPPET_DIR, "_seed.py")
SCREENSHOT = os.path.join(SNIPPET_DIR, "_screenshot.py")
SHOT_DIR = os.path.join(ROOT, "snippet-shots")

DEFAULT_SETUP_STEPS = 3
TIMEOUT = 30

# Per-snippet capture overrides, keyed by the snippet's numeric prefix. Anything not
# listed here uses the STATIC default (setup_steps=3, capture). Grounded in the
# 4-agent taxonomy audit on #381.
OVERRIDES = {
    # noshot: no meaningful single-frame visual (opt-out)
    142: {"noshot": True},   # scene-switch API demo, one default frame
    161: {"noshot": True},   # dijkstra heightmap: scalar value print
    225: {"noshot": True},   # BSP traversal: status caption only
    226: {"noshot": True},   # BSP adjacency: status caption only
    251: {"noshot": True},   # mcrfpy.mouse state text
    253: {"noshot": True},   # audio demo, no visual
    254: {"noshot": True},   # NoiseSource numbers printed to a caption
    255: {"noshot": True},   # NoiseSource size printed to a caption
    265: {"noshot": True},   # BSP traversal: status caption only
    268: {"noshot": True},   # Window API demo, calls window.screenshot()
    # setup_steps: a first timer fire (>=0.1s) fills a caption that is otherwise
    # placeholder text at the default 3 steps (~0.048s).
    85:  {"setup_steps": 12},  # entity_visibility status caption
    91:  {"setup_steps": 12},  # metrics_display labels
}


def snippet_paths():
    names = sorted(
        n for n in os.listdir(SNIPPET_DIR)
        if n.endswith(".py") and not n.startswith("_")
    )
    return [os.path.join(SNIPPET_DIR, n) for n in names]


def number_of(name):
    """Leading integer of a snippet filename, or None."""
    head = os.path.basename(name).split("_", 1)[0]
    return int(head) if head.isdigit() else None


def capture(path, env_base):
    """Run one snippet through the seed->snippet->screenshot chain."""
    num = number_of(path)
    cfg = OVERRIDES.get(num, {})
    if cfg.get("noshot"):
        return "skip", "noshot"

    base = os.path.basename(path)[:-3]  # drop .py
    out = os.path.join(SHOT_DIR, base + ".png")
    env = env_base.copy()
    env["MCRF_SHOT_OUT"] = out
    env["MCRF_SHOT_SETUP_STEPS"] = str(cfg.get("setup_steps", DEFAULT_SETUP_STEPS))

    try:
        proc = subprocess.run(
            [MCROGUEFACE, "--headless",
             "--exec", SEED, "--exec", path, "--exec", SCREENSHOT],
            capture_output=True, text=True, timeout=TIMEOUT, cwd=BUILD_DIR, env=env,
        )
    except subprocess.TimeoutExpired:
        return "fail", "timeout"

    log = proc.stdout + proc.stderr
    if "SHOT_OK" in log and os.path.exists(out):
        return "ok", out
    if "Traceback (most recent call last)" in log:
        last = [l for l in log.strip().splitlines() if l.strip()]
        return "fail", last[-1][:120] if last else "traceback"
    if "SHOT_FAIL" in log:
        line = next((l for l in log.splitlines() if "SHOT_FAIL" in l), "")
        return "fail", line.split("SHOT_FAIL:", 1)[-1].strip()[:120]
    if "SNIPPET_FAIL" in log:
        return "fail", "snippet raised before capture"
    return "fail", f"no SHOT_OK (exit {proc.returncode})"


def main():
    ap = argparse.ArgumentParser(description="Generate snippet preview screenshots.")
    ap.add_argument("only", nargs="*",
                    help="capture only these snippet numbers (e.g. 086 224)")
    args = ap.parse_args()

    if not os.path.exists(MCROGUEFACE):
        sys.exit(f"engine not built: {MCROGUEFACE} (run `make` first)")

    os.makedirs(SHOT_DIR, exist_ok=True)
    env_base = os.environ.copy()
    lib = os.path.join(BUILD_DIR, "lib")
    env_base["LD_LIBRARY_PATH"] = os.pathsep.join(
        p for p in (lib, env_base.get("LD_LIBRARY_PATH", "")) if p
    )

    wanted = {int(x) for x in args.only} if args.only else None
    paths = [p for p in snippet_paths()
             if wanted is None or number_of(p) in wanted]

    captured, skipped, failed = 0, 0, []
    for path in paths:
        status, detail = capture(path, env_base)
        name = os.path.basename(path)
        if status == "ok":
            captured += 1
        elif status == "skip":
            skipped += 1
        else:
            failed.append((name, detail))
            print(f"  FAIL {name}: {detail}")

    print(f"\nsnippet-shots: {captured} captured, {skipped} skipped (noshot), "
          f"{len(failed)} failed -> {SHOT_DIR}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
