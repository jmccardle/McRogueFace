import mcrfpy
from mcrfpy import automation
import runpy, sys, pathlib

OUT = sys.argv[1] if len(sys.argv) > 1 else "image00.png"

demo_path = (pathlib.Path(__file__).resolve().parent.parent /
             "tests" / "demo" / "audio_synth_demo.py")
runpy.run_path(str(demo_path), run_name="__demo__")

def shot(timer, runtime):
    automation.screenshot(OUT)
    print(f"Wrote {OUT}")
    sys.exit(0)

mcrfpy.Timer("header_shot", shot, 150)
