"""
Regression test for issue #350.

Headless mcrfpy.step() advanced animations and timers only. It never called
McRFPy_API::updatePythonScenes(), which lives solely in doFrame() -- so under step():

  * Scene.update(dt) overrides NEVER fired (the filed bug)
  * the C++ scene update never ran
  * scene transitions never progressed or completed
  * current_frame never advanced

Any game with per-frame logic in update() was untestable headless.

step() is now a full SIMULATION frame: everything doFrame() does except render and
input. Rendering stays deliberately off the clock -- it costs zero simulation time
(see issue_341 test), so step() must still render nothing.
"""
import mcrfpy
import sys

failures = []


def check(label, condition, detail=""):
    if condition:
        print(f"  PASS: {label}")
    else:
        print(f"  FAIL: {label} {detail}")
        failures.append(label)


# ------------------------------------------------------- Scene.update under step()
print("1. Scene.update(dt) fires under step() (the filed bug)")


class CountingScene(mcrfpy.Scene):
    def __init__(self, name):
        super().__init__(name)
        self.update_count = 0
        self.dt_total = 0.0

    def update(self, dt):
        self.update_count += 1
        self.dt_total += dt


scene = CountingScene("issue350")
mcrfpy.current_scene = scene

for _ in range(5):
    mcrfpy.step(0.016)

check("update() fired once per step()", scene.update_count == 5,
      f"got {scene.update_count}")
check("update() received the dt", abs(scene.dt_total - 5 * 0.016) < 1e-4,
      f"got {scene.dt_total}")

# ------------------------------------------------------------ current_frame advances
print("2. current_frame advances under step()")
before = mcrfpy.get_metrics()["current_frame"]
for _ in range(3):
    mcrfpy.step(0.016)
after = mcrfpy.get_metrics()["current_frame"]
check("current_frame advanced by 3", after - before == 3, f"{before} -> {after}")

# ------------------------------------------------------------------- timers still fire
print("3. Timers still fire under step() (unchanged behavior)")
fired = []
mcrfpy.Timer("t350", lambda timer, rt: fired.append(rt), 50)
for _ in range(4):
    mcrfpy.step(0.02)
check("timer fired", len(fired) > 0, f"got {len(fired)} fires")

# ----------------------------------------------------------- step() must not render
print("4. step() still renders nothing (render is off the clock)")
m = mcrfpy.get_metrics()
check("draw_calls == 0 after step()-only", m["draw_calls"] == 0,
      f"got {m['draw_calls']}")

print()
if failures:
    print(f"FAIL - {len(failures)} check(s) failed:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)

print("PASS")
sys.exit(0)
