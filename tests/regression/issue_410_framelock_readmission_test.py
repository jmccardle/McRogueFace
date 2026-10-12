"""#410: one safe window must serve a thread at most once.

FrameLock::closeWindow() used to wait for waiters to drain while safe_window was
still true, so a thread that re-acquired without yielding was served again inside the
same window, keeping it open (31 frames in 2 s). Each acquire must now observe a
distinct current_frame, for one greedy thread and for several polite threads whose
hold time exceeds their gap.
"""
import sys
import threading
import time
import mcrfpy

DURATION = 1.0


def run(workers, hold, gap):
    stop = threading.Event()
    seen = [[] for _ in range(workers)]

    def work(r):
        while not stop.is_set():
            with mcrfpy.lock():
                seen[r].append(mcrfpy.get_metrics()["current_frame"])
                time.sleep(hold)
            if gap:
                time.sleep(gap)

    ts = [threading.Thread(target=work, args=(r,), daemon=True) for r in range(workers)]
    for t in ts:
        t.start()
    end = time.perf_counter() + DURATION
    frames = 0
    while time.perf_counter() < end:
        mcrfpy.step(0.016)
        frames += 1
    stop.set()
    deadline = time.perf_counter() + 5
    while any(t.is_alive() for t in ts) and time.perf_counter() < deadline:
        mcrfpy.step(0.016)
    for t in ts:
        t.join(timeout=0.5)
    repeats = sum(len(s) - len(set(s)) for s in seen)
    acquires = sum(len(s) for s in seen)
    return acquires, repeats, frames


mcrfpy.current_scene = mcrfpy.Scene("issue_410")
ok = True
for name, w, h, g in (("greedy W=1 hold=2ms", 1, 0.002, 0),
                      ("polite W=8 hold=2ms gap=1ms", 8, 0.002, 0.001),
                      ("W=64 hold=0.2ms gap=1ms", 64, 0.0002, 0.001)):
    acq, rep, fr = run(w, h, g)
    print("%s: acquires=%d re-admissions=%d frames=%d" % (name, acq, rep, fr))
    if acq < 10:
        print("FAIL: %s made no progress" % name); ok = False
    if rep:
        print("FAIL: %s: %d acquires re-served in a window that already served the thread" % (name, rep)); ok = False
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
