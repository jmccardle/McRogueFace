#!/usr/bin/env python3
"""
Object identity for the Window singleton and engine Timers (#430, Phase 2).

- mcrfpy.window and Window.get() used to be two different objects: the module built
  its own wrapper with tp_alloc while Window.get() lazily built another.
- mcrfpy.timers rebuilt a wrapper by hand (createTimerWrapper) for any timer whose
  wrapper was not live; it now goes through PyTimer::pyobject_for (cached_wrapper),
  so a Timer the user built comes back as itself, every time.
"""
import gc
import sys

import mcrfpy

failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


def same(label, get):
    try:
        a, b = get(), get()
    except Exception as exc:  # an accessor that raises is a failure, not a skip
        check(False, f"{label}: raised {type(exc).__name__}: {exc}")
        return
    check(a is not None and a is b, f"{label} is stable")


def window():
    print("window")
    same("Window.get()", lambda: mcrfpy.Window.get())
    check(mcrfpy.window is mcrfpy.Window.get(), "mcrfpy.window is Window.get()")
    try:
        mcrfpy.Window()
        check(False, "Window() is still not user-constructible")
    except TypeError:
        check(True, "Window() is still not user-constructible")


def find_timer(name):
    for t in mcrfpy.timers:
        if t.name == name:
            return t
    return None


def timers():
    print("timers")
    fired = []

    def cb(timer, runtime):
        fired.append(timer)

    t = mcrfpy.Timer("issue430_timer", cb, 10)
    same("mcrfpy.timers", lambda: find_timer("issue430_timer"))
    check(find_timer("issue430_timer") is t, "mcrfpy.timers returns the user's Timer")

    # Drop the user's reference: the running timer keeps its wrapper alive (#251),
    # so the listing must still hand back that same object, not a rebuilt one.
    tid = id(t)
    del t
    gc.collect()
    again = find_timer("issue430_timer")
    check(again is not None and id(again) == tid,
          "running timer keeps its wrapper after the user drops it")

    for _ in range(5):
        mcrfpy.step(0.02)
    check(len(fired) > 0, "timer fired under step()")
    check(all(x is again for x in fired), "callback receives the same Timer object")

    again.stop()
    del again
    gc.collect()


def main():
    for t in (window, timers):
        t()
        gc.collect()
    if failures:
        print(f"FAIL: {len(failures)} check(s) failed")
        sys.exit(1)
    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
