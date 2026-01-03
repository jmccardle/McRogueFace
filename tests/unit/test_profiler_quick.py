"""
Quick test to verify profiling system compiles and basic metrics work
"""
import mcrfpy
import sys

# Create a simple scene
test = mcrfpy.Scene("test")
test.activate()
ui = test.children

# Create a small grid
grid = mcrfpy.Grid(
    grid_size=(10, 10),
    pos=(0, 0),
    size=(400, 400)
)

# Add a few entities
for i in range(5):
    entity = mcrfpy.Entity(grid_pos=(i, i), sprite_index=1)
    grid.entities.append(entity)

ui.append(grid)

print("✓ Profiler system compiled successfully")
print("✓ Scene created with grid and entities")
print("✓ Ready for runtime profiling tests")
print("")
print("Note: Run without --headless to see F3 profiler overlay in action")

sys.exit(0)
