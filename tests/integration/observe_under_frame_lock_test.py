"""Integration test: GridData.observe() inside mcrfpy.lock() is atomic w.r.t. the FRAME (req 2).

Mechanism (see design brief for GridData.observe() / mcrfpy.VisibilityMask):

Two entities `a` and `b` are kept at the same cell by a main-thread mcrfpy.Timer callback
that moves them one after the other, with a deliberate time.sleep() between the two
assignments. During that sleep the GIL is released and the world is momentarily
INCONSISTENT -- `a` has moved, `b` has not yet. A background reader that calls
gd.observe() at an arbitrary moment can catch that intermediate ("torn") state. A reader
that only calls observe() from inside `mcrfpy.lock()` cannot, because the #219 safe
window only opens at the end of a simulation frame, after the timer callback has already
returned and both entities have moved together.

There is deliberately NO C-level data race here: entity positions are mutated from
Python with the GIL held, and observe() holds the GIL for its entire duration, so each
individual C++ read is memory-safe with respect to Python mutation regardless of the
lock. What mcrfpy.lock() adds is *frame* coherence (no reader can observe a
half-completed frame), not memory safety -- and that is exactly what this test measures.

Per the reviewing standard ("a test that cannot fail is not a gate"), the interesting
number here is `unlocked_torn`: Phase B removes the lock and is expected to observe real
tearing, which is the mutation check proving `locked_torn == 0` is a property of the lock
and not a property of the test being unable to observe tearing at all. Section 3/4
guard against the two ways `locked_torn == 0` could be vacuously true: the timer never
firing (checked via distinct positions seen), and no frames actually elapsing during
Phase A (checked via the tick delta).

Two checks were added after the original draft, both closing holes a reviewer would
otherwise walk through:

  - **Phase A2, the cadence-matched control.** Phase A sleeps 1 ms between reads and
    Phase B does not, so "locked never tears, unlocked always tears" could in principle
    have been an artifact of the *cadence* rather than of the lock. Phase A2 repeats
    Phase A exactly -- same read count, same sleep -- with only `with mcrfpy.lock():`
    removed. It is the single-variable version of the mutation check.
  - **Phase C, the barrier instant (req 3).** Inside ONE lock block, several observe()
    calls must return the SAME tick: the tick is stamped at the barrier, and observe()
    must not itself drive a frame. That second half matters beyond tidiness -- the
    frame-lock condition variable has no timeout, so an observation API that drove a
    frame from inside the lock would self-deadlock the whole engine.

Run: ./mcrogueface --headless --exec ../tests/integration/observe_under_frame_lock_test.py
"""

import sys
import threading
import time

import mcrfpy

DEADLINE_SECONDS = 60.0
LOCKED_READS = 200
UNLOCKED_READS = 2000
CONTROL_READS = 200
OBSERVES_PER_LOCK = 8
LOCK_BLOCKS = 25

failures = []

scene = mcrfpy.Scene("observe_under_frame_lock")
mcrfpy.current_scene = scene
grid = mcrfpy.Grid(grid_size=(64, 4))
scene.children.append(grid)

for y in range(4):
    for x in range(64):
        pt = grid.at(x, y)
        pt.walkable = True
        pt.transparent = True

a = mcrfpy.Entity((0, 0), grid=grid)
a.name = "a"
b = mcrfpy.Entity((0, 0), grid=grid)
b.name = "b"

gd = grid.grid_data

_next_n = [0]


def timer_cb(timer, runtime):
    """Move a, sleep (GIL released, world inconsistent), then move b. Repeats forever,
    cycling n over 0..63 -- this is the ONLY thing that mutates a/b's positions."""
    n = _next_n[0] % 64
    _next_n[0] += 1
    a.cell_pos = (n, 0)
    time.sleep(0.002)
    b.cell_pos = (n, 0)


mover = mcrfpy.Timer("observe_lock_mover", timer_cb, 1)

reader_done = threading.Event()
worker_error = []
results = {}


def classify(snap, distinct_positions):
    """Returns True if this snapshot caught a and b disagreeing (a torn read)."""
    ents = {e["name"]: e["cell_pos"] for e in snap["entities"]}
    a_pos = ents.get("a")
    b_pos = ents.get("b")
    if a_pos is not None:
        distinct_positions.add(a_pos)
    if b_pos is not None:
        distinct_positions.add(b_pos)
    return a_pos != b_pos


def reader():
    try:
        # Phase A -- locked. Each read is atomic with respect to the frame: observe()
        # can only run once the #219 safe window is open, i.e. between frames, never
        # while the timer callback is mid-sleep.
        locked_torn = 0
        locked_distinct = set()
        first_tick = None
        last_tick = None
        for _ in range(LOCKED_READS):
            with mcrfpy.lock():
                snap = gd.observe()
            if first_tick is None:
                first_tick = snap["tick"]
            last_tick = snap["tick"]
            if classify(snap, locked_distinct):
                locked_torn += 1
            # FrameLock's safe window is a single wake-all per frame, not a per-acquire
            # turnstile (src/GameEngine.cpp: openWindow()/closeWindow()): a background
            # loop that re-acquires faster than the main thread's step() loop gets
            # scheduled can complete many lock/release cycles inside ONE open window,
            # before closeWindow() ever observes waiting==0 and lets current_frame
            # advance. That is expected engine behavior, not a bug -- but it would make
            # this measurement (assertion 4) racy against Python's GIL scheduling. This
            # sleep just yields between iterations so the main thread's step() loop gets
            # a turn; it does not change what is measured (locked_torn is still real).
            time.sleep(0.001)
        results["locked_reads"] = LOCKED_READS
        results["locked_torn"] = locked_torn
        results["locked_distinct_positions"] = len(locked_distinct)
        results["locked_tick_delta"] = last_tick - first_tick

        # Phase B -- unlocked. Mutation check: remove the lock, same read, same world,
        # and show tearing actually happens when nothing prevents it.
        unlocked_torn = 0
        unlocked_distinct = set()
        for _ in range(UNLOCKED_READS):
            snap = gd.observe()
            if classify(snap, unlocked_distinct):
                unlocked_torn += 1
        results["unlocked_reads"] = UNLOCKED_READS
        results["unlocked_torn"] = unlocked_torn

        # Phase A2 -- the cadence-matched control. IDENTICAL to phase A in every respect
        # (same read count, same 1 ms sleep between reads, same world, same mover) except
        # that `with mcrfpy.lock():` is gone. This is the single-variable form of the
        # phase-B mutation check: phase B changes both the lock and the cadence, so on its
        # own it cannot distinguish "the lock prevents tearing" from "sleeping between
        # reads prevents tearing."
        control_torn = 0
        control_distinct = set()
        for _ in range(CONTROL_READS):
            snap = gd.observe()
            if classify(snap, control_distinct):
                control_torn += 1
            time.sleep(0.001)
        results["control_reads"] = CONTROL_READS
        results["control_torn"] = control_torn
        results["control_distinct_positions"] = len(control_distinct)

        # Phase C -- the barrier instant (req 3). Several observe() calls inside ONE lock
        # block must all report the SAME tick: the tick is stamped at the barrier, the
        # barrier is one instant, and observe() must not drive a frame from inside it.
        # Across blocks the tick must strictly increase, or the "instant" would just be a
        # frozen clock.
        #
        # Each block also checks the tick's IDENTITY with the engine's own counter, read
        # from inside the same lock block: the barrier opens before current_frame++ in both
        # frame paths, so a locked observation stamps the frame whose work has just
        # settled, and get_metrics()['current_frame'] read at that same instant must agree
        # exactly. A delta cannot establish this -- any constant offset survives one.
        block_ticks = []
        ticks_per_block_unique = []
        tick_is_current_frame = 0
        for _ in range(LOCK_BLOCKS):
            with mcrfpy.lock():
                seen = [gd.observe()["tick"] for _ in range(OBSERVES_PER_LOCK)]
                frame_at_barrier = mcrfpy.get_metrics()["current_frame"]
            if seen[0] == frame_at_barrier:
                tick_is_current_frame += 1
            ticks_per_block_unique.append(len(set(seen)))
            block_ticks.append(seen[0])
            time.sleep(0.001)
        results["tick_is_current_frame"] = tick_is_current_frame
        results["lock_blocks"] = LOCK_BLOCKS
        results["observes_per_lock"] = OBSERVES_PER_LOCK
        results["blocks_with_one_tick"] = sum(1 for n in ticks_per_block_unique if n == 1)
        results["block_ticks_strictly_increasing"] = all(
            b > a for a, b in zip(block_ticks, block_ticks[1:]))
        results["block_tick_span"] = block_ticks[-1] - block_ticks[0]
    except BaseException as exc:  # noqa: BLE001 -- reported on the main thread
        worker_error.append(exc)
    finally:
        reader_done.set()


thread = threading.Thread(target=reader, name="observe-reader", daemon=True)
thread.start()

# Main thread drives the headless clock: timers (including the mover) only fire from
# step(), and the frame-lock safe window only opens inside a simulation frame.
deadline = time.monotonic() + DEADLINE_SECONDS
steps = 0
while not reader_done.is_set() and time.monotonic() < deadline:
    mcrfpy.step(1.0)
    steps += 1

mover.stop()
thread.join(timeout=2.0)

if worker_error:
    failures.append(f"background reader raised {worker_error[0]!r}")

if not reader_done.is_set():
    failures.append(
        f"reader did not finish within {DEADLINE_SECONDS}s deadline after {steps} "
        f"mcrfpy.step() calls -- partial results: {results!r}")

if thread.is_alive():
    failures.append("background reader thread is still running after join(timeout=2.0)")

locked_reads = results.get("locked_reads")
locked_torn = results.get("locked_torn")
locked_distinct_positions = results.get("locked_distinct_positions")
locked_tick_delta = results.get("locked_tick_delta")
unlocked_reads = results.get("unlocked_reads")
unlocked_torn = results.get("unlocked_torn")
control_reads = results.get("control_reads")
control_torn = results.get("control_torn")
control_distinct_positions = results.get("control_distinct_positions")
blocks_with_one_tick = results.get("blocks_with_one_tick")
block_ticks_increasing = results.get("block_ticks_strictly_increasing")
block_tick_span = results.get("block_tick_span")

print()
print("measured                              | value")
print("--------------------------------------+-------")
print(f"steps (main-thread step())            | {steps}")
print(f"A  locked_reads                       | {locked_reads}")
print(f"A  locked_torn                        | {locked_torn}")
print(f"A  locked_distinct_positions          | {locked_distinct_positions}")
print(f"A  locked_tick_delta                  | {locked_tick_delta}")
print(f"B  unlocked_reads (no lock, no sleep) | {unlocked_reads}")
print(f"B  unlocked_torn                      | {unlocked_torn}")
print(f"A2 control_reads (no lock, SAME sleep)| {control_reads}")
print(f"A2 control_torn                       | {control_torn}")
print(f"A2 control_distinct_positions         | {control_distinct_positions}")
print(f"C  lock blocks x observes             | {results.get('lock_blocks')} x {results.get('observes_per_lock')}")
print(f"C  blocks reporting exactly one tick  | {blocks_with_one_tick}")
print(f"C  block ticks strictly increasing    | {block_ticks_increasing}")
print(f"C  block tick span                    | {block_tick_span}")
print(f"C  blocks where tick == current_frame | {results.get('tick_is_current_frame')}")
print()

if unlocked_torn is not None:
    print(f"the interesting number is unlocked_torn = {unlocked_torn} "
          f"(out of {unlocked_reads}) -- it should be large, and it is."
          if unlocked_torn > 0 else
          f"the interesting number is unlocked_torn = {unlocked_torn} -- it is NOT "
          "large, which undermines the whole test (see failures below).")

# Only evaluate the four required assertions if the reader actually finished --
# otherwise `results` is partial and these would be comparing against None.
if reader_done.is_set() and not worker_error:
    if locked_torn != 0:
        failures.append(f"locked_torn should be exactly 0, got {locked_torn}")

    if not (unlocked_torn > 0):
        failures.append(
            f"unlocked_torn should be > 0 (mutation check for assertion 1), got {unlocked_torn}")

    if locked_reads != LOCKED_READS:
        failures.append(f"locked_reads should be exactly {LOCKED_READS}, got {locked_reads}")
    if not (locked_distinct_positions > 1):
        failures.append(
            "locked_distinct_positions should be > 1 (non-vacuity: the mover timer must "
            f"actually have fired more than once during phase A), got {locked_distinct_positions}")

    if not (locked_tick_delta > 0):
        failures.append(
            "locked_tick_delta should be > 0 (frames must actually have advanced during "
            f"phase A), got {locked_tick_delta}")

    # Phase A2 -- the cadence-matched control. If this were 0 the phase-A result would
    # be explained by the sleep rather than by the lock, and assertion 1 would prove
    # nothing at all.
    if not (control_torn > 0):
        failures.append(
            "control_torn should be > 0 -- phase A2 is phase A with ONLY the lock removed, "
            "so a 0 here would mean phase A's locked_torn == 0 is attributable to the read "
            f"cadence rather than to mcrfpy.lock(); got {control_torn}")
    if not (control_distinct_positions > 1):
        failures.append(
            "control_distinct_positions should be > 1 (the mover must have been running "
            f"during phase A2 too), got {control_distinct_positions}")

    # Phase C -- the barrier instant (req 3).
    if blocks_with_one_tick != LOCK_BLOCKS:
        failures.append(
            f"all {LOCK_BLOCKS} lock blocks should report exactly one distinct tick across "
            f"their {OBSERVES_PER_LOCK} observe() calls (the tick is stamped at the barrier, "
            f"and observe() must not drive a frame), got {blocks_with_one_tick}")
    if not block_ticks_increasing:
        failures.append(
            "ticks across successive lock blocks should be strictly increasing -- otherwise "
            "the per-block agreement above is a stopped clock, not a barrier instant")
    if results.get("tick_is_current_frame") != LOCK_BLOCKS:
        failures.append(
            f"in all {LOCK_BLOCKS} lock blocks the observed tick must EQUAL "
            "get_metrics()['current_frame'] read at the same barrier -- freeze v1 §4 says "
            "world_tick IS current_frame, and a delta cannot establish that; got "
            f"{results.get('tick_is_current_frame')}")
    if not (block_tick_span >= LOCK_BLOCKS - 1):
        failures.append(
            f"block_tick_span should be at least {LOCK_BLOCKS - 1} (one frame per block "
            f"minimum), got {block_tick_span}")

if failures:
    for f in failures:
        print(f"FAIL: {f}")
    print("FAIL")
    sys.exit(1)

print("PASS")
sys.exit(0)
