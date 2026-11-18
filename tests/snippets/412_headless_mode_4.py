# mcrf: objects=[Color,Frame,Scene,Timer] verified=0.3.6 status=ok
import mcrfpy

scene = mcrfpy.Scene("test")
scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(100, 100),
                                  fill_color=mcrfpy.Color(40, 120, 220)))
mcrfpy.current_scene = scene

# region: timer
import mcrfpy
import sys

fired = [False]

def on_timer(timer, runtime):
    """Timer callback receives (timer, runtime_ms)."""
    fired[0] = True
    print(f"Timer fired at {runtime}ms")

# Create timer for 500ms interval
t = mcrfpy.Timer("my_timer", on_timer, 500)

# Advance past the timer interval
mcrfpy.step(0.6)  # 600ms - timer will fire

if fired[0]:
    print("Success!")   # printed "Timer fired at 500ms": the deadline, not 600

t.stop()  # Clean up timer
# endregion

def callback(timer, runtime):
    print(f"{timer.name} fired at {runtime}ms")

interval_ms = 500

# region: api
t = mcrfpy.Timer("name", callback, interval_ms)

# Control methods
t.stop()      # Stop the timer
t.pause()     # Pause (can resume later)
t.resume()    # Resume after pause
t.restart()   # Restart from beginning
t.start()     # Start (or re-add) the timer

# Properties
t.name        # Timer name (str)
t.interval    # Interval in ms (int)
t.active      # Running state (bool, read-write)
t.paused      # Is timer paused? (bool, read-only)
t.stopped     # Is timer stopped? (bool, read-only)
t.remaining   # Time until next fire, in ms (int, read-only)
t.once        # Fire only once? (bool)
t.callback    # The callback function
# endregion
