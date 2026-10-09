"""Background-thread networking smoke test (#219 frame lock + shipped network stdlib).

The thing being gated here is the engine's obligation to an embedder that runs a message
bus -- NATS, MQTT, a plain TCP feed -- on a background thread inside the engine process
while the main thread keeps running frames. That obligation has two halves:

  1. The interpreter we ship can do sockets, TLS, selectors and asyncio FROM A THREAD
     THAT IS NOT THE MAIN THREAD. (`asyncio` in particular is not automatically fine off
     the main thread -- signal-handler installation is main-thread-only, so a naive
     event-loop setup raises there and nowhere else.)
  2. Blocking in that thread does not stall the engine, and the thread can hand its
     results back to the world under `mcrfpy.lock()` without the main thread losing time.

Both halves are asserted against observable engine state rather than being assumed.

What makes this test non-vacuous, in order of importance:

  * Phase 1 measures frames completed by the main thread DURING a window in which the
    worker is provably parked inside a `selectors.select()` syscall. If that syscall did
    not release the GIL, the main thread would complete ~zero frames in that window, so
    the `>= MIN_FRAMES_DURING_BLOCK` assertion is a real discriminator, not a tautology.

  * Phase 2 asserts the simulation clock advanced by EXACTLY one step per step() call
    (`n * STEP_MS`), even though several hundred milliseconds of wall time passed while
    the worker did real I/O. Frame time must never feed back into world advancement; a
    world clock driven by elapsed wall time would fail this by a wide margin.

  * The worker mutates the scene ONLY inside `with mcrfpy.lock():`, and the main thread
    asserts the mutation landed. Before the fix in this commit, that acquire blocked
    forever under a headless step()-driven loop, because the #219 safe window was opened
    only from the render path -- so this assertion also gates that regression.

Deliberately NOT done here, because the spec forbids it and because it would stall the
engine: no I/O, no await, and no blocking wait inside the `mcrfpy.lock()` block. The
worker does all of its waiting outside the lock and enters it only to assign.

Run: ./mcrogueface --headless --exec ../tests/integration/background_thread_network_test.py
"""

import asyncio
import selectors
import socket
import ssl
import sys
import threading
import time

import mcrfpy

# One simulated frame. STEP_MS must equal STEP_SECONDS * 1000 exactly, because the
# clock assertion in phase 2 is an equality: mcrfpy.step() converts seconds to whole
# milliseconds, and 0.016 -> 16 is exact.
STEP_SECONDS = 0.016
STEP_MS = 16

# How long the worker parks inside selectors.select() with nothing to read.
BLOCK_SECONDS = 0.25

# Frames the main thread must complete while the worker is parked in that syscall.
# The engine reaches ~10^6 headless frames/second, so this threshold is ~4 orders of
# magnitude below the expected value; it is set low only to stay meaningful on a loaded
# CI box. The failure mode it catches -- a worker holding the GIL across its blocking
# call -- produces a number near zero, not near this bound.
MIN_FRAMES_DURING_BLOCK = 100

# Wall-clock ceilings. Exceeding one means the worker wedged; the test fails rather
# than hanging until the runner's timeout.
PHASE1_DEADLINE = 3.0
PHASE2_DEADLINE = 5.0

SENTINEL_X = 1234.0

failures = []


def check(condition, message):
    if not condition:
        failures.append(message)
    return condition


# --- scene under test -------------------------------------------------------------
scene = mcrfpy.Scene("bg_thread_net")
target = mcrfpy.Frame(pos=(0, 0), size=(10, 10))
scene.children.append(target)
mcrfpy.current_scene = scene

# --- worker <-> main handshakes ---------------------------------------------------
blocking_started = threading.Event()   # worker is about to park in select()
blocking_ended = threading.Event()     # worker came back out of select()
proceed = threading.Event()            # main thread releases the worker into phase 2
done = threading.Event()               # worker finished (successfully or not)

worker_error = []
worker_notes = {}


def worker():
    """Runs entirely off the main thread. Real sockets, real syscalls."""
    try:
        check(threading.current_thread() is not threading.main_thread(),
              "worker did not run on a background thread")

        # A real listening socket on an ephemeral loopback port.
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        worker_notes["address"] = listener.getsockname()

        sel = selectors.DefaultSelector()
        sel.register(listener, selectors.EVENT_READ)

        # --- phase 1: park in a syscall with nothing to read ----------------------
        # Nobody has connected yet, so this blocks for the full timeout. The main
        # thread counts frames across exactly this window.
        blocking_started.set()
        t0 = time.monotonic()
        idle_events = sel.select(timeout=BLOCK_SECONDS)
        worker_notes["blocked_seconds"] = time.monotonic() - t0
        blocking_ended.set()

        check(idle_events == [],
              "selectors.select() reported readiness on an idle listener")
        check(worker_notes["blocked_seconds"] >= BLOCK_SECONDS * 0.8,
              "selectors.select() returned early -- it did not actually block "
              f"(blocked {worker_notes['blocked_seconds']:.3f}s, "
              f"expected ~{BLOCK_SECONDS}s)")

        proceed.wait(PHASE2_DEADLINE)

        # --- phase 2: a real connection and a real byte exchange ------------------
        # connect() to our own listener completes out of the accept backlog, so a
        # single thread can drive both ends without a second thread.
        client = socket.create_connection(listener.getsockname(), timeout=2.0)
        conn, _peer = listener.accept()

        # Watch the accepted connection, so select() is genuinely reporting readable
        # data rather than timing out on an idle listener.
        sel.unregister(listener)
        sel.register(conn, selectors.EVENT_READ)

        client.sendall(b"ping")
        ready = sel.select(timeout=2.0)
        check([key.fileobj for key, _mask in ready] == [conn],
              f"selectors.select() did not report the connection readable: {ready!r}")

        conn.settimeout(2.0)
        payload = conn.recv(4)
        check(payload == b"ping",
              f"loopback socket exchange returned {payload!r}, expected b'ping'")
        conn.sendall(b"pong")
        client.settimeout(2.0)
        check(client.recv(4) == b"pong", "reverse loopback exchange failed")

        # TLS machinery must load off the main thread too (_ssl + its default store).
        context = ssl.create_default_context()
        check(context.protocol is not None, "ssl.create_default_context() gave no protocol")
        worker_notes["openssl"] = ssl.OPENSSL_VERSION

        # asyncio on a NON-main thread. This is the case that actually breaks in
        # embedded interpreters: a fresh loop must be created and installed by hand,
        # because there is no implicit loop and no signal handling off the main thread.
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)

            async def roundtrip():
                await asyncio.sleep(0.01)
                return "asyncio-ok"

            worker_notes["asyncio"] = loop.run_until_complete(roundtrip())
        finally:
            asyncio.set_event_loop(None)
            loop.close()
        check(worker_notes.get("asyncio") == "asyncio-ok",
              "asyncio event loop did not run to completion off the main thread")

        for sock in (conn, client, listener):
            sock.close()
        sel.close()

        # Only now touch the world, and only to assign. The main thread is parked
        # for the duration of this block, so it must contain no I/O and no waiting.
        with mcrfpy.lock():
            target.x = SENTINEL_X

    except BaseException as exc:  # noqa: BLE001 - recorded and re-reported on main
        worker_error.append(exc)
    finally:
        # Always signal, so a worker failure surfaces as an assertion rather than
        # as the main thread spinning until its deadline.
        blocking_started.set()
        blocking_ended.set()
        done.set()


thread = threading.Thread(target=worker, name="bus-thread", daemon=True)
thread.start()

# --- phase 1 measurement ----------------------------------------------------------
check(blocking_started.wait(PHASE1_DEADLINE), "worker never reached its blocking call")

frames_before_block = mcrfpy.get_metrics()["current_frame"]
frames_during_block = 0
deadline = time.monotonic() + PHASE1_DEADLINE
while not blocking_ended.is_set() and time.monotonic() < deadline:
    mcrfpy.step(STEP_SECONDS)
    frames_during_block += 1

check(blocking_ended.is_set(),
      "worker never returned from selectors.select() within the deadline")
check(frames_during_block >= MIN_FRAMES_DURING_BLOCK,
      f"main thread completed only {frames_during_block} frames while the worker was "
      f"blocked in a syscall (expected >= {MIN_FRAMES_DURING_BLOCK}); the background "
      "thread appears to have held the GIL across its blocking call")

metrics_after_block = mcrfpy.get_metrics()
check(metrics_after_block["current_frame"] - frames_before_block == frames_during_block,
      "current_frame did not advance once per step() during the blocking window")

# --- phase 2 measurement ----------------------------------------------------------
sim_before = metrics_after_block["simulation_time_ms"]
frames_before = metrics_after_block["current_frame"]
wall_before = time.monotonic()

proceed.set()

steps_taken = 0
deadline = time.monotonic() + PHASE2_DEADLINE
while not done.is_set() and time.monotonic() < deadline:
    mcrfpy.step(STEP_SECONDS)
    steps_taken += 1

check(done.is_set(), "worker did not finish within the deadline")

wall_elapsed = time.monotonic() - wall_before
metrics_end = mcrfpy.get_metrics()
sim_delta = metrics_end["simulation_time_ms"] - sim_before
frame_delta = metrics_end["current_frame"] - frames_before

if worker_error:
    failures.append(f"background thread raised {worker_error[0]!r}")

# The world clock is driven by the caller, never by how long the frame took in the
# real world. Several hundred milliseconds of wall time elapsed above; the simulated
# clock must still show exactly one STEP_MS per step() call.
check(sim_delta == steps_taken * STEP_MS,
      f"simulation clock advanced {sim_delta}ms over {steps_taken} steps; expected "
      f"exactly {steps_taken * STEP_MS}ms -- wall time is leaking into world time")
check(frame_delta == steps_taken,
      f"current_frame advanced {frame_delta} over {steps_taken} step() calls")

# The worker's hand-back landed. Before the frame-lock window was opened in the
# headless frame path, this acquire blocked forever and this assertion could not pass.
check(target.x == SENTINEL_X,
      f"background thread's locked mutation did not land (target.x == {target.x}, "
      f"expected {SENTINEL_X})")

thread.join(timeout=2.0)
check(not thread.is_alive(), "background thread did not exit")

# --- report -----------------------------------------------------------------------
print(f"worker socket           : {worker_notes.get('address')}")
print(f"worker blocked in select: {worker_notes.get('blocked_seconds', float('nan')):.3f}s")
print(f"frames during that block: {frames_during_block}")
print(f"asyncio off main thread : {worker_notes.get('asyncio')}")
print(f"ssl                     : {worker_notes.get('openssl')}")
print(f"phase 2 wall elapsed    : {wall_elapsed:.3f}s")
print(f"phase 2 steps / sim ms  : {steps_taken} steps -> {sim_delta} ms simulated")
print(f"locked mutation         : target.x == {target.x}")

if failures:
    for message in failures:
        print(f"FAIL: {message}")
    sys.exit(1)

print("PASS")
sys.exit(0)
