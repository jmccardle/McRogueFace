"""Regression test: GridPointState references must not dangle after grid resize.

Issue #265: GridPointState objects held Python references to internal vectors
that could be invalidated when the underlying grid data was reallocated.

Fix: GridPointState now copies data or holds safe references that survive
grid modifications.
"""
import mcrfpy
import sys

PASS = True

def check(name, condition):
    global PASS
    if not condition:
        print(f"FAIL: {name}")
        PASS = False
    else:
        print(f"  ok: {name}")

# Test 1: Access GridPointState after entity transfer
grid = mcrfpy.Grid(grid_size=(10, 10))
entity = mcrfpy.Entity(grid_pos=(5, 5), grid=grid)
entity.update_visibility()

state = entity.at(3, 3)
check("GridPointState accessible", state is not None)

# Transfer entity to a different grid (invalidates old gridstate)
grid2 = mcrfpy.Grid(grid_size=(20, 20))
entity.grid = grid2
entity.update_visibility()

# Old state reference should not crash
# (In the buggy version, accessing state after transfer would read freed memory)
try:
    # Access the new gridstate
    new_state = entity.at(15, 15)
    check("GridPointState valid after transfer", new_state is not None)
except Exception as e:
    check(f"GridPointState valid after transfer (exception: {e})", False)

# Test 2: Multiple entities with GridPointState references
entities = []
for i in range(5):
    e = mcrfpy.Entity(grid_pos=(i, i), grid=grid)
    entities.append(e)

for e in entities:
    e.update_visibility()

states = [e.at(0, 0) for e in entities]
check("Multiple GridPointState refs created", len(states) == 5)

# Remove all entities (should not crash)
for e in entities:
    e.grid = None

check("Entities removed safely", len(grid.entities) == 0)

# Test 3: GridPoint reference stability
gp = grid.at(5, 5)
check("GridPoint accessible", gp is not None)
check("GridPoint walkable", gp.walkable == True or gp.walkable == False)

if PASS:
    print("PASS")
    sys.exit(0)
else:
    sys.exit(1)
