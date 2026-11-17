"""Sustained-load soak for mcrfpy.lock() -- the #219 FrameLock barrier (#395, #535).

The property the simulator embedding needs is "an event handler sits on this barrier for
HOURS against a render loop". Hours are not available in a test suite, so this file runs a
FIXED amount of work -- ROUNDS frames, WORKERS threads, one acquire per worker per frame --
and gates the things that DEGRADE over a long run rather than fail outright: a ratchet in
admission, a leak of waiters, a leak of memory per acquire.

NO MACHINE SPEED IN ANY GATE (#535). The old soak ran for 3 wall-clock seconds and gated
ratios of acquire-wait and frame TIMES between its first and last fifth, minimum acquire
and frame counts for that interval, and a minimum elapsed wall fraction. None of that says
anything about the barrier on a busy machine. Now:

  1  fixed workload, exact counts. Every round is a rendezvous: wait until all WORKERS are
     blocked in lock() (get_metrics 'lock_waiting' == WORKERS), run ONE frame, which must
     admit each worker exactly once in exactly one window. After ROUNDS rounds each worker
     has acquired exactly ROUNDS times: no MIN_TOTAL_ACQUIRES / MIN_ACQUIRES_PER_WORKER, an
     equality.
  2  no drift in admission: the run is cut into five equal fifths of the WORKLOAD (by round)
     and each fifth is summarised by admissions per window. It must be exactly WORKERS in
     every fifth: a barrier that grows less willing to admit (a starvation ratchet, a leaked
     waiter) shows as a fifth below WORKERS, or as a rendezvous that never completes (the
     supervisor's hang detector). Admissions per window replaces wall-clock acquire-wait
     ratios; the time-valued drift numbers are reported, unthresholded, by
     tests/benchmarks/frame_lock_soak_bench.py.
  3  no unbounded resource growth: sys.getallocatedblocks() across the post-warmup rounds,
     after gc.collect(). Blocks, not RSS: one leaked object per acquire is one block per
     acquire and cannot hide, whereas a ~320 KB leak hides under an RSS threshold.
     MAX_BLOCK_GROWTH is kept; it is a count.
  4  clean end state: lock_waiting == 0, 'lock_windows' advanced by exactly ROUNDS, and every
     worker thread has exited.

WHY A CHILD PROCESS and what "hang" means: tests/integration/_frame_lock_supervisor.py. A hang
is "no progress for STALL_SECONDS", never a performance bound.

FIXTURE NOTE. The workers mutate Frame.x, not Entity.cell_pos (which leaks one allocator
block per assignment on this build) so a fixture leak cannot masquerade as a barrier leak.

WHAT THIS COVERAGE FOUND (#412, fixed): two concurrent background lock users wedged the
engine through a GIL-vs-FrameLock::mtx inversion in acquire(); see the stress test.

Run: ./mcrogueface --headless --exec ../tests/integration/frame_lock_soak_test.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _frame_lock_supervisor as sup

WORKERS = 3
ROUNDS = 500             # a multiple of FIFTHS
FIFTHS = 5
WARMUP_ROUNDS = 50       # before the allocator baseline is taken
MAX_BLOCK_GROWTH = 150   # measured: a fixed cost of the heartbeat thread, flat in the acquire count

failures = []


def check(condition, message):
    if not condition:
        failures.append(message)
    return condition


SOAK_BODY = r'''
import gc, json, sys, threading, time
import mcrfpy

scene = mcrfpy.Scene("frame_lock_soak")
mcrfpy.current_scene = scene
targets = []
for r in range(WORKERS):
    f = mcrfpy.Frame(pos=(0, r * 4), size=(4, 4))
    scene.children.append(f)
    targets.append(f)

counts = [0] * WORKERS
errors = []
steps_box = [0]
stop_hb = threading.Event()


def worker(r):
    target = targets[r]
    try:
        for i in range(ROUNDS):
            with mcrfpy.lock():
                target.x = float(i % 50 + 1)
                counts[r] += 1
    except BaseException as exc:
        errors.append("worker %d: %r" % (r, exc))


def heartbeat():
    while not stop_hb.is_set():
        print("HB steps=%d counts=%d" % (steps_box[0], sum(counts)), flush=True)
        time.sleep(0.05)


threads = [threading.Thread(target=worker, args=(r,), name="soak-%d" % r, daemon=True)
           for r in range(WORKERS)]
threading.Thread(target=heartbeat, name="hb", daemon=True).start()
for t in threads:
    t.start()

m0 = mcrfpy.get_metrics()
fifth_rounds = ROUNDS // FIFTHS
fifths = []                       # (admissions, windows) per fifth of the workload
f_adm0, f_win0 = m0["lock_admissions"], m0["lock_windows"]
blocks_before = None
violations = []

for rnd in range(ROUNDS):
    while mcrfpy.get_metrics()["lock_waiting"] != WORKERS:
        time.sleep(0.0005)        # the supervisor's progress token is the hang detector
    if rnd == WARMUP_ROUNDS:
        gc.collect()
        blocks_before = sys.getallocatedblocks()
    mcrfpy.step(0.016)
    steps_box[0] += 1
    if (rnd + 1) % fifth_rounds == 0:
        m = mcrfpy.get_metrics()
        fifths.append((m["lock_admissions"] - f_adm0, m["lock_windows"] - f_win0))
        f_adm0, f_win0 = m["lock_admissions"], m["lock_windows"]

gc.collect()
blocks_after = sys.getallocatedblocks()
for t in threads:
    t.join()
m1 = mcrfpy.get_metrics()
stop_hb.set()

print("RESULT " + json.dumps({
    "steps": steps_box[0],
    "counts": counts,
    "fifths": fifths,
    "windows": m1["lock_windows"] - m0["lock_windows"],
    "admissions": m1["lock_admissions"] - m0["lock_admissions"],
    "waiting_at_end": m1["lock_waiting"],
    "blocks_before": blocks_before,
    "blocks_after": blocks_after,
    "block_growth": blocks_after - blocks_before,
    "errors": errors,
    "alive": [t.name for t in threads if t.is_alive()],
}), flush=True)
sys.exit(0)
'''

verdict, soak, info = sup.run_child(
    "soak", sup.child_source(SOAK_BODY, WORKERS=WORKERS, ROUNDS=ROUNDS, FIFTHS=FIFTHS,
                             WARMUP_ROUNDS=WARMUP_ROUNDS))

print()
print("soak child: verdict=%s heartbeats=%d last=%s" % (verdict, info["heartbeats"], info["last_heartbeat"]))

if verdict != "ok" or soak is None:
    check(False, sup.wedge_message("soak", verdict, info))
else:
    acquires = ROUNDS - WARMUP_ROUNDS
    print()
    print("soak (%d workers x %d rounds)" % (WORKERS, ROUNDS))
    print("  acquires per worker           : %s" % (soak["counts"],))
    print("  admissions / windows          : %d / %d" % (soak["admissions"], soak["windows"]))
    print("  (admissions, windows) / fifth : %s" % (soak["fifths"],))
    print("  allocated blocks              : %d -> %d  (growth %d over %d post-warmup rounds, "
          "%.4f per acquire)" % (soak["blocks_before"], soak["blocks_after"], soak["block_growth"],
                                  acquires, soak["block_growth"] / float(acquires * WORKERS)))
    print("  worker errors / alive         : %s / %s" % (soak["errors"], soak["alive"]))
    print()

    check(not soak["errors"], "soak workers raised: %s" % (soak["errors"],))
    # 1 -- exact counts
    check(soak["counts"] == [ROUNDS] * WORKERS,
          "every worker must have acquired exactly %d times: %s" % (ROUNDS, soak["counts"]))
    check(soak["admissions"] == WORKERS * ROUNDS,
          "lock_admissions rose by %d, expected exactly %d" % (soak["admissions"], WORKERS * ROUNDS))
    # 2 -- no drift: admissions per window, per fifth of the workload
    check(len(soak["fifths"]) == FIFTHS, "expected %d fifths, got %d" % (FIFTHS, len(soak["fifths"])))
    for i, (adm, win) in enumerate(soak["fifths"]):
        per = adm / float(win) if win else None
        check(win == ROUNDS // FIFTHS and adm == win * WORKERS,
              "fifth %d: %d admissions in %d windows (%s per window); every window must "
              "admit exactly %d, in every fifth: a lower fifth is a starvation ratchet or "
              "a leaked waiter" % (i, adm, win, per, WORKERS))
    # 3 -- allocator growth
    check(soak["block_growth"] <= MAX_BLOCK_GROWTH,
          "sys.getallocatedblocks() grew by %d across %d acquires (gate %d), i.e. %.4f "
          "blocks per acquire; one leaked object per acquire would be 1.0"
          % (soak["block_growth"], acquires * WORKERS, MAX_BLOCK_GROWTH,
             soak["block_growth"] / float(acquires * WORKERS)))
    # 4 -- clean end state
    check(soak["waiting_at_end"] == 0, "lock_waiting is %d at the end" % soak["waiting_at_end"])
    check(soak["windows"] == ROUNDS,
          "%d windows opened for %d rounds; one per frame that had waiters" % (soak["windows"], ROUNDS))
    check(not soak["alive"], "worker threads still running: %s" % (soak["alive"],))

if failures:
    for message in failures:
        print("FAILURE: %s" % message)
    sys.exit(1)

print("PASS")
sys.exit(0)
