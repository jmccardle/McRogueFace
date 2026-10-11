"""Frame repr labels its height h= (it printed the height as a second w=)."""
import mcrfpy
import sys

r = repr(mcrfpy.Frame(pos=(1, 2), size=(30, 40)))
if "w=30, h=40" not in r:
    print(f"FAIL: {r}")
    sys.exit(1)
print("PASS")
sys.exit(0)
