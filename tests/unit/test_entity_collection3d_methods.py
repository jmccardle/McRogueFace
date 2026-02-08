"""Test EntityCollection3D pop/find/extend (issue #243)"""
import mcrfpy
import sys

errors = []

vp = mcrfpy.Viewport3D(pos=(0,0), size=(100,100))
vp.set_grid_size(16, 16)

# Setup: add 5 named entities
for i in range(5):
    e = mcrfpy.Entity3D(pos=(i, i), scale=1.0)
    e.name = f"entity_{i}"
    vp.entities.append(e)

# Test find - existing
found = vp.entities.find("entity_2")
if found is None:
    errors.append("find('entity_2') returned None")
elif found.name != "entity_2":
    errors.append(f"find returned wrong entity: {found.name}")

# Test find - missing
missing = vp.entities.find("nonexistent")
if missing is not None:
    errors.append("find('nonexistent') should return None")

# Test pop() - default (last element)
count_before = len(vp.entities)
popped = vp.entities.pop()
if popped.name != "entity_4":
    errors.append(f"pop() should return last, got {popped.name}")
if len(vp.entities) != count_before - 1:
    errors.append(f"Length should decrease after pop")

# Test pop(0) - first element
popped0 = vp.entities.pop(0)
if popped0.name != "entity_0":
    errors.append(f"pop(0) should return first, got {popped0.name}")

# Test pop(1) - middle element
popped1 = vp.entities.pop(1)
if popped1.name != "entity_2":
    errors.append(f"pop(1) should return index 1, got {popped1.name}")

# Current state: [entity_1, entity_3]
if len(vp.entities) != 2:
    errors.append(f"Expected 2 remaining, got {len(vp.entities)}")

# Test pop - out of range
try:
    vp.entities.pop(99)
    errors.append("pop(99) should raise IndexError")
except IndexError:
    pass

# Test extend
new_entities = []
for i in range(3):
    e = mcrfpy.Entity3D(pos=(10+i, 10+i), scale=1.0)
    e.name = f"new_{i}"
    new_entities.append(e)
vp.entities.extend(new_entities)
if len(vp.entities) != 5:
    errors.append(f"After extend, expected 5, got {len(vp.entities)}")

# Verify extended entities are findable
if vp.entities.find("new_1") is None:
    errors.append("Extended entity not findable")

# Test extend with invalid type
try:
    vp.entities.extend([42])
    errors.append("extend with non-Entity3D should raise TypeError")
except TypeError:
    pass

# Test extend with non-iterable
try:
    vp.entities.extend(42)
    errors.append("extend with non-iterable should raise TypeError")
except TypeError:
    pass

# Test name property
e_named = mcrfpy.Entity3D(pos=(0,0), scale=1.0)
e_named.name = "test_name"
if e_named.name != "test_name":
    errors.append(f"name property: expected 'test_name', got '{e_named.name}'")

if errors:
    for err in errors:
        print(f"FAIL: {err}", file=sys.stderr)
    sys.exit(1)
else:
    print("PASS: EntityCollection3D pop/find/extend (issue #243)", file=sys.stderr)
    sys.exit(0)
