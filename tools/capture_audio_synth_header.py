import mcrfpy
from mcrfpy import automation
import runpy, sys, pathlib

OUT = sys.argv[1] if len(sys.argv) > 1 else "image00.png"

demo_path = (pathlib.Path(__file__).resolve().parent.parent /
             "tests" / "demo" / "audio_synth_demo.py")
runpy.run_path(str(demo_path), run_name="__demo__")

# In headless --exec mode timers never fire; use step() to advance the loop.
for _ in range(30):
    mcrfpy.step(0.01)

automation.screenshot(OUT)
print(f"Wrote {OUT}")
sys.exit(0)
