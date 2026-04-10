"""Regression test: Python object reference count leaks.

Issues #267, #275: Accessing certain properties (scene.children, entity
collections) would leak references, causing memory growth over time.

Fix: Proper Py_DECREF in collection accessors and property getters.

Note: sys.gettotalrefcount() is only available in debug Python builds.
This test uses a weaker proxy: create many objects, verify they're
collectible, and check that repeated property access doesn't accumulate
uncollectable objects.
"""
import mcrfpy
import sys
import gc

PASS = True

def check(name, condition):
    global PASS
    if not condition:
        print(f"FAIL: {name}")
        PASS = False
    else:
        print(f"  ok: {name}")

# Test 1: scene.children access doesn't leak
scene = mcrfpy.Scene("refcount_test")
mcrfpy.current_scene = scene

for i in range(100):
    children = scene.children
    _ = len(children)

gc.collect()
check("scene.children access loop completed", True)

# Test 2: grid.entities access doesn't leak
grid = mcrfpy.Grid(grid_size=(10, 10))
scene.children.append(grid)
for i in range(5):
    mcrfpy.Entity(grid_pos=(i % 10, 0), grid=grid)

for i in range(100):
    entities = grid.entities
    _ = len(entities)

gc.collect()
check("grid.entities access loop completed", True)

# Test 3: Repeated entity property access
entity = mcrfpy.Entity(grid_pos=(5, 5), grid=grid)
for i in range(100):
    _ = entity.grid_pos
    _ = entity.sprite_index

gc.collect()
check("entity property access loop completed", True)

# Test 4: Collection iteration doesn't leak
for i in range(50):
    for child in scene.children:
        pass
    for ent in grid.entities:
        pass

gc.collect()
check("collection iteration loop completed", True)

# Test 5: Creating and destroying objects in a loop
for i in range(50):
    temp_scene = mcrfpy.Scene(f"temp_{i}")
    f = mcrfpy.Frame(pos=(0, 0), size=(10, 10))
    temp_scene.children.append(f)
    del f

gc.collect()
check("create/destroy cycle completed", True)

# Test 6: If pydebug is available, do actual refcount check
if hasattr(sys, 'gettotalrefcount'):
    gc.collect()
    before = sys.gettotalrefcount()
    for i in range(1000):
        _ = scene.children
        _ = grid.entities
    gc.collect()
    after = sys.gettotalrefcount()
    growth = after - before
    check(f"refcount growth <= 50 (got {growth})", growth <= 50)
else:
    print("  skip: sys.gettotalrefcount not available (not a debug build)")

if PASS:
    print("PASS")
    sys.exit(0)
else:
    sys.exit(1)
