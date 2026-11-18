# mcrf: objects=[Color,Frame,Scene] verified=0.3.6 status=ok
import mcrfpy

scene = mcrfpy.Scene("test")
scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(100, 100),
                                  fill_color=mcrfpy.Color(40, 120, 220)))
mcrfpy.current_scene = scene

# region: step
import mcrfpy

# Advance by specific duration (seconds)
dt = mcrfpy.step(0.1)  # Advance 100ms
print(f"Advanced by {dt} seconds")

# Advance by integer (converts to float)
dt = mcrfpy.step(1)  # Advance 1 second

# Advance to next scheduled event (timer or animation)
dt = mcrfpy.step(None)  # or mcrfpy.step()
print(f"Advanced {dt} seconds to next event")
# endregion

# region: advance
mcrfpy.advance(2500)   # int MILLISECONDS (step() takes float seconds)
print(mcrfpy.get_metrics()["simulation_time_ms"])  # simulated ms; "runtime" is wall-clock seconds
# endregion

# region: seed
mcrfpy.set_random_seed(1234)    # unsigned 32-bit int
print(mcrfpy.get_random_seed())  # 1234; record this to replay an unseeded run
# endregion
