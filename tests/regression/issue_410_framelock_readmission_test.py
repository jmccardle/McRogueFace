"""#410 / #535: one safe window serves a thread at most once -- measured in counts.

FrameLock::closeWindow() used to wait for waiters to drain while safe_window was
still true, so a thread that re-acquired without yielding was served again inside the
same window, keeping it open (31 frames in 2 s). Later (#535) the same invariant failed
on a starved main thread: admission was keyed on `safe_window && !closing`, and the gap
between openWindow() and closeWindow() setting `closing` grows to whole scheduler quanta
under CPU oversubscription.

The property, with no clock in it:

    Rendezvous: wait until all W workers are blocked in lock() (get_metrics()
    'lock_waiting' == W), then run exactly ONE frame. That frame's window must serve
    each worker exactly once: 'lock_admissions' rises by exactly W, 'lock_windows' by
    exactly 1, and each worker saw a current_frame it had never seen before.

Repeated for several rounds and three topologies (one greedy thread that re-acquires
the instant it releases, 8 threads, 64 threads). Because the main thread decides when a
frame happens, machine speed cannot change any count here. The wall clock appears only
as a hang detector (HANG_SECONDS): a deadlock fails with "deadlock/hang", it is never
a performance bound.
"""
import sys
import threading
import time
import mcrfpy

HANG_SECONDS = 30.0
ROUNDS = 25


def hang(what):
    print("FAIL: deadlock/hang: %s (no progress for %.0fs)" % (what, HANG_SECONDS))
    sys.exit(1)


def wait_until(pred, what):
    """Spin (GIL released) until pred(); a hang detector, not a time budget."""
    deadline = time.monotonic() + HANG_SECONDS
    while not pred():
        if time.monotonic() > deadline:
            hang(what)
        time.sleep(0.0005)


def run(workers, hold):
    stop = threading.Event()
    seen = [[] for _ in range(workers)]

    def work(r):
        while not stop.is_set():
            with mcrfpy.lock():
                seen[r].append(mcrfpy.get_metrics()["current_frame"])
                if hold:
                    time.sleep(hold)  # makes a re-admission attempt likely; never asserted

    ts = [threading.Thread(target=work, args=(r,), daemon=True) for r in range(workers)]
    for t in ts:
        t.start()

    problems = []
    for rnd in range(ROUNDS):
        wait_until(lambda: mcrfpy.get_metrics()["lock_waiting"] == workers,
                   "%d workers never all blocked in lock() (round %d)" % (workers, rnd))
        before = mcrfpy.get_metrics()
        mcrfpy.step(0.016)
        after = mcrfpy.get_metrics()
        adm = after["lock_admissions"] - before["lock_admissions"]
        win = after["lock_windows"] - before["lock_windows"]
        if adm != workers:
            problems.append("round %d: %d admissions in one frame, expected %d" % (rnd, adm, workers))
        if win != 1:
            problems.append("round %d: %d windows opened by one frame, expected 1" % (rnd, win))

    stop.set()
    # Drain: workers parked in lock() need windows to leave.
    deadline = time.monotonic() + HANG_SECONDS
    while any(t.is_alive() for t in ts):
        if time.monotonic() > deadline:
            hang("workers did not shut down")
        mcrfpy.step(0.016)
        time.sleep(0.0005)
    for t in ts:
        t.join()

    repeats = sum(len(s) - len(set(s)) for s in seen)
    # Fairness: every worker served in every round (>= ROUNDS; the drain may add more).
    starved = [r for r, s in enumerate(seen) if len(s) < ROUNDS]
    if repeats:
        problems.append("%d acquires re-served in a frame that already served the thread" % repeats)
    if starved:
        problems.append("workers %s were served fewer than %d times" % (starved[:5], ROUNDS))
    return problems


mcrfpy.current_scene = mcrfpy.Scene("issue_410")
ok = True
for name, w, h in (("greedy W=1 hold=2ms", 1, 0.002),
                   ("W=8 hold=1ms", 8, 0.001),
                   ("W=64 hold=0", 64, 0)):
    problems = run(w, h)
    print("%s: %s" % (name, "ok" if not problems else "; ".join(problems)))
    ok = ok and not problems
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
