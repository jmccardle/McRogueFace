"""#460: get_metrics()['fps'] came from static_cast<int>(1000 / avg_frame_ms). A tiny
step(dt) pushed that past INT_MAX: undefined behaviour (UBSan in the fuzz build), and
an arbitrary value on Release. It now saturates at INT_MAX."""
import sys

import mcrfpy

INT_MAX = 2**31 - 1

for _ in range(60):          # fill the whole frame-time history with tiny frames
    mcrfpy.step(1e-12)
fps = mcrfpy.get_metrics()["fps"]
if fps != INT_MAX:
    print(f"FAIL: fps after tiny steps is {fps}, expected saturation at {INT_MAX}")
    sys.exit(1)

for _ in range(60):
    mcrfpy.step(0.016)
fps = mcrfpy.get_metrics()["fps"]
if not 50 <= fps <= 70:
    print(f"FAIL: fps after 16 ms steps is {fps}")
    sys.exit(1)

print("PASS")
sys.exit(0)
