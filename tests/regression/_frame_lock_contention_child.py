"""Child process for issue_412_frame_lock_gil_inversion_test.py.

N background threads hammer `with mcrfpy.lock():` while the main thread drives frames.
Pre-fix, N >= 2 wedges the whole interpreter (see the parent's docstring), so this
child produces NO output at all and the parent's subprocess timeout is what reports
it. Post-fix it prints one RESULT line and exits 0.

Deliberately kept to nothing but the barrier: no grid, no entities, no rendering, no
audio. If this hangs, `mcrfpy.lock()` is the only thing it can be.

Env:
  MCRF_LOCK_THREADS     number of background threads (default 4)
  MCRF_LOCK_ITERATIONS  acquires per thread (default 200)
"""

import json
import os
import sys
import threading
import time

import mcrfpy

N = int(os.environ.get("MCRF_LOCK_THREADS", "4"))
M = int(os.environ.get("MCRF_LOCK_ITERATIONS", "200"))
WALL_DEADLINE = 20.0

scene = mcrfpy.Scene("lock_contention")
mcrfpy.current_scene = scene

counts = [0] * N
errors = []
stop = threading.Event()


def worker(i):
    try:
        for _ in range(M):
            if stop.is_set():
                return
            with mcrfpy.lock():
                counts[i] += 1
    except BaseException as exc:  # noqa: BLE001 -- reported through the RESULT line
        errors.append(f"worker {i}: {exc!r}")


threads = [threading.Thread(target=worker, args=(i,), name=f"lk{i}", daemon=True)
           for i in range(N)]
for t in threads:
    t.start()

frames = 0
end = time.monotonic() + WALL_DEADLINE
while any(t.is_alive() for t in threads) and time.monotonic() < end:
    mcrfpy.step(0.016)
    frames += 1
stop.set()
for t in threads:
    t.join(timeout=1.0)

alive = sum(1 for t in threads if t.is_alive())
# JSON on one line: the fields are lists, so a space-separated k=v line cannot be
# parsed unambiguously by the parent.
print("RESULT " + json.dumps({
    "threads": N, "iterations": M, "counts": counts,
    "frames": frames, "alive": alive, "errors": errors,
}))
sys.stdout.flush()
sys.exit(0)
