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

import os
# Hang detector only, never a performance bound. Scaled like the runner's own per-test
# timeout (valgrind runs at x50) and always below it (run_tests.py SLOW_TESTS gives 60 s).
HANG_SECONDS = 30.0 * float(os.environ.get("MCRF_TIMEOUT_MULTIPLIER", "1"))
ROUNDS = 25


def start_watchdog():
    """Progress-based hang detector for calls that block (step() parked in closeWindow()).

    Fires only if NOTHING advanced for HANG_SECONDS: no frame, no admission, no window.
    A slow machine still makes progress; a deadlock does not.
    """
    def progress():
        m = mcrfpy.get_metrics()
        return (m["current_frame"], m["lock_admissions"], m["lock_windows"], m["lock_waiting"])

    def run():
        last = progress()
        since = time.monotonic()
        while True:
            time.sleep(0.5)
            now = progress()
            if now != last:
                last, since = now, time.monotonic()
            elif time.monotonic() - since > HANG_SECONDS:
                print("FAIL: deadlock/hang: no frame, window or admission for %.0fs (%r)"
                      % (HANG_SECONDS, now), flush=True)
                os._exit(1)

    threading.Thread(target=run, name="hang-watchdog", daemon=True).start()


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


def mid_window_arrival():
    """A holds (blocked on an Event) keeping the window open; B, admitted by the same
    window, leaves and re-enters lock() while A still holds. B must be deferred."""
    a_in = threading.Event()
    a_release = threading.Event()
    b_first_done = threading.Event()
    b_second_in = threading.Event()
    snap = {}
    problems = []

    def a():
        with mcrfpy.lock():
            a_in.set()
            if not a_release.wait(HANG_SECONDS):
                snap["a_hang"] = True

    def b():
        with mcrfpy.lock():
            pass
        b_first_done.set()
        with mcrfpy.lock():      # second acquire, while A still holds the first window
            b_second_in.set()

    def watcher(before):
        # Wait on counters: B deferred ('lock_waiting' == 1) or, under a broken rule,
        # B admitted again (b_second_in).
        deadline = time.monotonic() + HANG_SECONDS
        while not (b_first_done.is_set() and a_in.is_set()
                   and (mcrfpy.get_metrics()["lock_waiting"] == 1 or b_second_in.is_set())):
            if time.monotonic() > deadline:
                snap["watch_hang"] = True
                break
            time.sleep(0.0005)
        m = mcrfpy.get_metrics()
        snap["adm"] = m["lock_admissions"] - before["lock_admissions"]
        snap["win"] = m["lock_windows"] - before["lock_windows"]
        snap["waiting"] = m["lock_waiting"]
        snap["b_second_early"] = b_second_in.is_set()
        a_release.set()

    ta = threading.Thread(target=a, daemon=True)
    tb = threading.Thread(target=b, daemon=True)
    ta.start()
    tb.start()
    wait_until(lambda: mcrfpy.get_metrics()["lock_waiting"] == 2, "A and B never both blocked in lock()")
    before = mcrfpy.get_metrics()
    tw = threading.Thread(target=watcher, args=(before,), daemon=True)
    tw.start()
    mcrfpy.step(0.016)          # parks until A (released by the watcher) and B are out
    tw.join()
    if snap.get("a_hang") or snap.get("watch_hang"):
        hang("mid-window scenario never reached its rendezvous")
    if snap["b_second_early"]:
        problems.append("B was admitted a second time by the window that had already served it")
    if snap["adm"] != 2 or snap["win"] != 1 or snap["waiting"] != 1:
        problems.append("while A held the window: admissions +%d (want 2), windows +%d (want 1), "
                        "lock_waiting %d (want 1)" % (snap["adm"], snap["win"], snap["waiting"]))
    mcrfpy.step(0.016)          # next window: only now may B's second acquire run
    wait_until(b_second_in.is_set, "B never served by the next window")
    after = mcrfpy.get_metrics()
    if after["lock_admissions"] - before["lock_admissions"] != 3 or after["lock_windows"] - before["lock_windows"] != 2:
        problems.append("after the next step: admissions +%d (want 3), windows +%d (want 2)"
                        % (after["lock_admissions"] - before["lock_admissions"],
                           after["lock_windows"] - before["lock_windows"]))
    ta.join(HANG_SECONDS)
    tb.join(HANG_SECONDS)
    return problems


mcrfpy.current_scene = mcrfpy.Scene("issue_410")
start_watchdog()
ok = True
problems = mid_window_arrival()
print("mid_window_arrival: %s" % ("ok" if not problems else "; ".join(problems)))
ok = ok and not problems
for name, w, h in (("greedy W=1 hold=2ms", 1, 0.002),
                   ("W=8 hold=1ms", 8, 0.001),
                   ("W=64 hold=0", 64, 0)):
    problems = run(w, h)
    print("%s: %s" % (name, "ok" if not problems else "; ".join(problems)))
    ok = ok and not problems
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
