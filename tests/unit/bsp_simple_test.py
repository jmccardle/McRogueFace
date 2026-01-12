"""Simple BSP test to identify crash."""
import sys
import mcrfpy

print("Step 1: Import complete")

print("Step 2: Creating BSP...")
bsp = mcrfpy.BSP(pos=(0, 0), size=(100, 80))
print("Step 2: BSP created:", bsp)

print("Step 3: Getting bounds...")
bounds = bsp.bounds
print("Step 3: Bounds:", bounds)

print("Step 4: Getting root...")
root = bsp.root
print("Step 4: Root:", root)

print("Step 5: Split once...")
bsp.split_once(horizontal=True, position=40)
print("Step 5: Split complete")

print("Step 6: Get leaves...")
leaves = list(bsp.leaves())
print("Step 6: Leaves count:", len(leaves))

print("PASS")
sys.exit(0)
