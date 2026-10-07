#!/usr/bin/env python3
"""Run tests/stress/thread_safety_probe.py across builds, scenarios and modes.

    python3 tests/stress/run_thread_matrix.py [--reps N] [--seconds S]
        [--configs release,debug,ft,ft-nogil,tsan,tsan-nogil]
        [--scenarios ui,entity,step,anim,timer,cells] [--modes nolock,lock]
        [--render 0,1]

Host python3 (it only launches the engine). Needs xvfb-run. Each run is
classified: ok / exc (unexpected Python exception) / invariant (broken
collection invariant) / crash (killed by a signal) / hang (timeout) /
noresult (exited without a RESULT line) / tsan (ThreadSanitizer report).
Logs of non-ok runs go to build/thread-matrix/.
"""
import argparse
import collections
import json
import os
import re
import signal
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "tests" / "stress" / "thread_safety_probe.py"
LOGDIR = ROOT / "build" / "thread-matrix"
TSAN_SUPP = ROOT / "modules" / "cpython" / "Tools" / "tsan" / "suppressions_free_threading.txt"

CONFIGS = {
    # name: (build dir, extra env)
    "release":    ("build", {}),
    "debug":      ("build-debug", {}),
    "ft":         ("build-ft", {}),
    "ft-nogil":   ("build-ft", {"MCRF_UNSAFE_NOGIL": "1"}),
    "tsan":       ("build-tsan", {}),
    "tsan-nogil": ("build-tsan", {"MCRF_UNSAFE_NOGIL": "1"}),
}

TSAN_RE = re.compile(r"WARNING: ThreadSanitizer: (.+?) \(")
FRAME_RE = re.compile(r"#\d+ (\S+) ")


def tsan_signatures(text):
    """De-duplicate TSan reports by kind + first frame inside our code."""
    sigs = []
    for block in text.split("==================")[1:]:
        m = TSAN_RE.search(block)
        if not m:
            continue
        frames = [f for f in FRAME_RE.findall(block)]
        ours = next((f for f in frames if "McRogueFace/src" in block and f[0].isupper()
                     or "::" in f), frames[0] if frames else "?")
        sigs.append(f"{m.group(1)} @ {ours}")
    return sigs


def run_one(cfg, scenario, mode, render, seconds, threads, rep):
    build, extra = CONFIGS[cfg]
    exe = ROOT / build / "mcrogueface"
    env = dict(os.environ, ALSOFT_DRIVERS="null", MCRF_TS_SCENARIO=scenario,
               MCRF_TS_MODE=mode, MCRF_TS_SECONDS=str(seconds),
               MCRF_TS_THREADS=str(threads), MCRF_TS_RENDER=str(render), **extra)
    if cfg.startswith("tsan"):
        env["TSAN_OPTIONS"] = (f"suppressions={TSAN_SUPP}:halt_on_error=0:"
                               "report_signal_unsafe=0:second_deadlock_stack=1")
    cmd = ["xvfb-run", "-a", str(exe)]
    if not render:
        cmd.append("--headless")
    cmd += ["--exec", str(PROBE)]
    timeout = seconds * (12 if cfg.startswith("tsan") else 4) + 30
    try:
        p = subprocess.run(cmd, cwd=exe.parent, env=env, capture_output=True,
                           text=True, errors="replace", timeout=timeout)
        out, rc = p.stdout + p.stderr, p.returncode
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or b"").decode(errors="replace") + (e.stderr or b"").decode(errors="replace")
        return "hang", None, [], out
    result = None
    for line in out.splitlines():
        if line.startswith("RESULT "):
            result = json.loads(line[7:])
    sigs = tsan_signatures(out) if cfg.startswith("tsan") else []
    # xvfb-run returns the child's status; a signal shows as 128+N or negative
    if rc < 0 or rc >= 128:
        signo = -rc if rc < 0 else rc - 128
        try:
            name = signal.Signals(signo).name
        except ValueError:
            name = str(signo)
        return f"crash:{name}", result, sigs, out
    if result is None:
        return "noresult", None, sigs, out
    if result["invariant"]:
        return "invariant", result, sigs, out
    if result["exc"]:
        return "exc", result, sigs, out
    if sigs:
        return "tsan", result, sigs, out
    return "ok", result, sigs, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--seconds", type=float, default=3)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--configs", default="release,debug,ft,ft-nogil")
    ap.add_argument("--scenarios", default="ui,entity,step,anim,timer,cells")
    ap.add_argument("--modes", default="nolock,lock")
    ap.add_argument("--render", default="0,1")
    a = ap.parse_args()
    LOGDIR.mkdir(parents=True, exist_ok=True)

    rows = []
    all_sigs = collections.Counter()
    for cfg in a.configs.split(","):
        if not (ROOT / CONFIGS[cfg][0] / "mcrogueface").exists():
            print(f"skip {cfg}: {CONFIGS[cfg][0]}/mcrogueface not built", flush=True)
            continue
        for scenario in a.scenarios.split(","):
            for mode in a.modes.split(","):
                for render in (int(r) for r in a.render.split(",")):
                    outcomes = collections.Counter()
                    detected = 0
                    excs = collections.Counter()
                    for rep in range(a.reps):
                        kind, res, sigs, out = run_one(cfg, scenario, mode, render,
                                                       a.seconds, a.threads, rep)
                        outcomes[kind] += 1
                        all_sigs.update(f"{cfg}/{scenario}/{mode}: {s}" for s in set(sigs))
                        if res:
                            detected += res.get("detected", 0)
                            excs.update(res.get("exc", {}).keys())
                        if kind != "ok":
                            tag = f"{cfg}-{scenario}-{mode}-r{render}-{rep}"
                            (LOGDIR / f"{tag}.log").write_text(out)
                    row = (cfg, scenario, mode, "render" if render else "step",
                           dict(outcomes), detected, sorted(excs))
                    rows.append(row)
                    print(f"{cfg:10s} {scenario:7s} {mode:6s} {row[3]:6s} "
                          f"{dict(outcomes)} detected={detected}"
                          + (f" exc={sorted(excs)}" if excs else ""), flush=True)

    if all_sigs:
        print("\nTSan report signatures (runs containing each):")
        for s, n in all_sigs.most_common(40):
            print(f"  {n:3d}  {s}")
    print(f"\nlogs of non-ok runs: {LOGDIR}")


if __name__ == "__main__":
    main()
