"""The ordering contract of mcrfpy.lock(), in counts and happens-before -- #395, #535.

This replaces the wall-clock half of the old hold-budget test. That test asserted "a ms
held inside the lock costs the frame ~a ms" (slope in [0.6, 1.4]) and "overhead < 2 ms":
properties of the machine, which failed under CPU load. The properties it was really
protecting are about ORDER, and are checked here with no time budget:

  A. SERVED BY THE FRAME THAT FINDS IT WAITING. When a holder is blocked in lock()
     ('lock_waiting' == 1) and ONE frame runs, that frame's window admits it
     ('lock_admissions' +1, 'lock_windows' +1) and the holder has run its block and
     released before step() returns. Not "within N ms": within exactly one frame.
  B. THE MAIN THREAD IS PARKED EXACTLY WHILE A HOLDER IS INSIDE. The holder blocks inside
     its block until a helper thread lets it go; step() must not return before the block
     has exited. (A hold costs the frame its duration -- how long that is, is the
     benchmark's business: tests/benchmarks/frame_lock_hold_cost_bench.py.)
  C. WORK OUTSIDE THE LOCK DOES NOT PARK THE MAIN THREAD. The control arm: a thread busy
     outside the lock (blocked on an event the main thread has not set) while the main
     thread completes many frames. Frames advance, the thread is still unfinished.
  D. A HOLDER SEES A SETTLED FRAME. The frame number a holder reads inside its block
     strictly increases from holder to holder (one window per frame, in order, never
     repeated).
  E. THE WINDOW OPENS ONLY FOR WAITERS. Frames with nobody waiting open no window.

The wall clock appears only as HANG_SECONDS, a hang detector ("deadlock/hang"), never as
a performance bound.
"""
import sys
import threading
import time

import mcrfpy

HANG_SECONDS = 30.0
ROUNDS = 20
failures = []


def check(label, cond):
    if not cond:
        failures.append(label)
        print(f"  FAILURE: {label}")
    else:
        print(f"  ok  {label}")


def hang(what):
    print(f"FAIL: deadlock/hang: {what} (no progress for {HANG_SECONDS:.0f}s)")
    sys.exit(1)


def wait_until(pred, what):
    deadline = time.monotonic() + HANG_SECONDS
    while not pred():
        if time.monotonic() > deadline:
            hang(what)
        time.sleep(0.0005)


def metrics():
    return mcrfpy.get_metrics()


mcrfpy.current_scene = mcrfpy.Scene("hold_ordering")

# --- E: no waiter, no window --------------------------------------------------------
m0 = metrics()
for _ in range(10):
    mcrfpy.step(0.016)
m1 = metrics()
check("E: frames with no waiter open no window "
      f"(windows +{m1['lock_windows'] - m0['lock_windows']}, admissions "
      f"+{m1['lock_admissions'] - m0['lock_admissions']})",
      m1["lock_windows"] == m0["lock_windows"] and m1["lock_admissions"] == m0["lock_admissions"])

# --- A + B + D: one holder, one frame -----------------------------------------------
events = []            # appended by the holder in program order
holder_frames = []
go = threading.Event()
let_go = threading.Event()
stop = threading.Event()
in_block = threading.Event()


def holder():
    while True:
        go.wait()
        go.clear()
        if stop.is_set():
            return
        with mcrfpy.lock():
            holder_frames.append(metrics()["current_frame"])
            events.append("enter")
            in_block.set()
            # Stay inside until a helper (NOT the main thread: it is parked) lets go.
            if not let_go.wait(HANG_SECONDS):
                events.append("hang")
            events.append("exit")


def helper():
    # Releases the holder once it is verifiably inside its block. It measures nothing:
    # the main thread is parked in step() for however long this takes.
    while not stop.is_set():
        if in_block.wait(0.05):
            in_block.clear()
            time.sleep(0.005)   # gives a (mutated) non-parking step() room to return early
            let_go.set()


ht = threading.Thread(target=holder, daemon=True)
hl = threading.Thread(target=helper, daemon=True)
ht.start()
hl.start()

served_in_one_frame = 0
adm_ok = 0
for rnd in range(ROUNDS):
    events.clear()
    let_go.clear()
    go.set()
    wait_until(lambda: metrics()["lock_waiting"] == 1, f"holder never blocked in lock() (round {rnd})")
    before = metrics()
    mcrfpy.step(0.016)
    after = metrics()
    snapshot = list(events)       # what had happened by the time step() returned
    if snapshot == ["enter", "exit"]:
        served_in_one_frame += 1
    if (after["lock_admissions"] - before["lock_admissions"] == 1
            and after["lock_windows"] - before["lock_windows"] == 1):
        adm_ok += 1
    wait_until(lambda: metrics()["lock_waiting"] == 0, "holder still counted as waiting")

check(f"A+B: one frame admitted the waiting holder AND parked until it exited, "
      f"{served_in_one_frame}/{ROUNDS} rounds", served_in_one_frame == ROUNDS)
check(f"A: that frame was exactly one window and one admission, {adm_ok}/{ROUNDS} rounds",
      adm_ok == ROUNDS)
check("D: each holder read a distinct, strictly increasing frame number "
      f"({len(holder_frames)} samples)",
      len(holder_frames) == ROUNDS
      and all(b > a for a, b in zip(holder_frames, holder_frames[1:])))

stop.set()
go.set()
let_go.set()
in_block.set()
ht.join(HANG_SECONDS)
hl.join(HANG_SECONDS)
check("the holder and helper threads shut down", not ht.is_alive() and not hl.is_alive())

# --- C: work outside the lock does not park the main thread -------------------------
release_outside = threading.Event()
finished_outside = threading.Event()


def outside_worker():
    release_outside.wait(HANG_SECONDS)    # "busy outside the lock", until main says otherwise
    with mcrfpy.lock():
        pass
    finished_outside.set()


ot = threading.Thread(target=outside_worker, daemon=True)
ot.start()
f0 = metrics()["current_frame"]
for _ in range(200):
    mcrfpy.step(0.016)
f1 = metrics()["current_frame"]
check(f"C: 200 frames completed while a thread worked outside the lock (current_frame +{f1 - f0})",
      f1 - f0 == 200)
check("C: and that thread, never having entered the lock, is still unfinished",
      not finished_outside.is_set())
release_outside.set()
wait_until(lambda: metrics()["lock_waiting"] == 1, "outside worker never reached lock()")
a0 = metrics()["lock_admissions"]
mcrfpy.step(0.016)
check("C: once it asks, the very next frame admits it", metrics()["lock_admissions"] == a0 + 1)
wait_until(finished_outside.is_set, "outside worker admitted but never finished")
ot.join(HANG_SECONDS)

if failures:
    print(f"\n{len(failures)} FAILURE(S):")
    for f in failures:
        print(f"  FAILURE: {f}")
    sys.exit(1)
print("\nPASS")
sys.exit(0)
