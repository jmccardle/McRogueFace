"""
Regression test for issue #369.

Every path that hands a C++ drawable back to Python must return the *same* wrapper
object, or `child.parent is parent` silently answers False and Python subclasses
reached through those paths lose their identity.

Broken paths this locks down:
  - UIDrawable::get_parent          (.parent)
  - find_in_collection              (mcrfpy.find / find_all)
  - UIEntityCollection concat/slice (entities + [...], entities[a:b])
"""
import mcrfpy
import sys

failures = []


def check(label, condition):
    if condition:
        print(f"  PASS: {label}")
    else:
        print(f"  FAIL: {label}")
        failures.append(label)


scene = mcrfpy.Scene("issue369")
ui = scene.children

# ---------------------------------------------------------------- .parent identity
print("1. .parent returns a stable, identical wrapper")
parent = mcrfpy.Frame(pos=(0, 0), size=(100, 100), name="parent_frame")
kid = mcrfpy.Frame(pos=(1, 1), size=(10, 10), name="kid_frame")
ui.append(parent)
parent.children.append(kid)

check("kid.parent is parent", kid.parent is parent)
check("repeated reads are identical", kid.parent is kid.parent)
check("id() is stable across reads", id(kid.parent) == id(kid.parent))

# .parent must be usable as a dict key / set member
seen = {kid.parent: "found"}
check(".parent works as a dict key", seen.get(parent) == "found")
check(".parent works in a set", len({kid.parent, kid.parent, parent}) == 1)

# ------------------------------------------------------- subclass survives .parent
print("2. Python subclass identity survives .parent")


class MyFrame(mcrfpy.Frame):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.custom_state = "preserved"


sub_parent = MyFrame(pos=(0, 0), size=(200, 200), name="sub_parent")
sub_kid = mcrfpy.Caption(pos=(5, 5), text="inner", name="sub_kid")
ui.append(sub_parent)
sub_parent.children.append(sub_kid)

check("sub_kid.parent is sub_parent", sub_kid.parent is sub_parent)
check("subclass type preserved", isinstance(sub_kid.parent, MyFrame))
check("subclass attributes preserved",
      getattr(sub_kid.parent, "custom_state", None) == "preserved")

# ------------------------------------------------- .parent covers all drawable types
print("3. .parent resolves non-Frame/Caption/Sprite/Grid parents (was None)")
# Line/Circle/Arc/Viewport3D had no switch arm and fell through to Py_RETURN_NONE.
# They aren't containers, so verify the *child-of-grid* case instead: a GridView
# parent must come back identical, and every type must at least round-trip via find().
grid = mcrfpy.Grid(grid_size=(10, 10), pos=(0, 0), size=(100, 100), name="the_grid")
ui.append(grid)
overlay = mcrfpy.Frame(pos=(0, 0), size=(10, 10), name="overlay_child")
grid.children.append(overlay)
check("overlay.parent is grid", overlay.parent is grid)

# ------------------------------------------------------------- find() identity
print("4. find() / find_all() return existing wrappers")
found = mcrfpy.find("parent_frame", "issue369")
check("find() returns the same object", found is parent)

found_sub = mcrfpy.find("sub_parent", "issue369")
check("find() preserves subclass", found_sub is sub_parent)
check("find() subclass attrs intact",
      getattr(found_sub, "custom_state", None) == "preserved")

all_found = mcrfpy.find_all("*_frame", "issue369")
by_id = {id(o) for o in all_found}
check("find_all() returns live wrappers",
      id(parent) in by_id and id(kid) in by_id)

# ---------------------------------------------------------- entity collection paths
print("5. EntityCollection slice / concat preserve entity identity")


class MyEntity(mcrfpy.Entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tag = "mine"


e0 = MyEntity(grid_pos=(1, 1))
e1 = mcrfpy.Entity(grid_pos=(2, 2))
e2 = mcrfpy.Entity(grid_pos=(3, 3))
for e in (e0, e1, e2):
    grid.entities.append(e)

check("entities[0] is e0", grid.entities[0] is e0)

sliced = grid.entities[0:2]
check("slice returns the same wrappers", sliced[0] is e0 and sliced[1] is e1)
check("slice preserves subclass", isinstance(sliced[0], MyEntity))
check("slice preserves subclass attrs", getattr(sliced[0], "tag", None) == "mine")

concat = grid.entities + []
check("concat returns the same wrappers", concat[0] is e0)
check("concat preserves subclass", isinstance(concat[0], MyEntity))

# The #266 identity ref must survive a duplicate-wrapper round trip: before the fix,
# the temporary wrapper's dealloc cleared UIEntity::pyobject on the shared C++ object.
del sliced, concat
import gc
gc.collect()
check("entity identity survives temp wrappers", grid.entities[0] is e0)
check("subclass attrs survive temp wrappers",
      getattr(grid.entities[0], "tag", None) == "mine")

print()
if failures:
    print(f"FAIL - {len(failures)} check(s) failed:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)

print("PASS")
sys.exit(0)
