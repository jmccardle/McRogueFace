"""#464: a drawable's scene parent was the scene's NAME. Constructing another Scene with
that name re-pointed the old scene's children at the new one: `f.parent` named the new
scene, detaching `f` searched the new scene's list and missed, and `f` could end up in
two collections at once. The old Scene object's `.children` also showed the new list.

Now the link is the scene itself. Giving a name to a new scene leaves the old scene's
children with the old scene (which is unregistered and can be registered again)."""
import gc
import sys

import mcrfpy

failures = []


def check(cond, msg):
    print(("ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


def contains(coll, obj):
    return sum(1 for k in coll if k is obj)


# The fuzz-found sequence
s = mcrfpy.Scene("dup")
f = mcrfpy.Frame(name="f")
s.children.append(f)
s2 = mcrfpy.Scene("dup")
check(f.parent is s, "after a new Scene takes the name, f.parent is still the old scene")
check(contains(s.children, f) == 1, "the old scene's children still hold f")
check(len(s2.children) == 0, "the new scene starts empty")
check(not s.registered and s2.registered, "the name moved: old unregistered, new registered")

p = mcrfpy.Frame(name="p")
p.children.append(f)
check(contains(s.children, f) == 0, "moving f to a Frame removes it from the old scene")
check(f.parent is p, "f.parent is the Frame")

s2.unregister()
s.register()
check(contains(s.children, f) + contains(p.children, f) == 1, "f is in exactly one collection")

# Re-registering the old scene brings its children back with it
s3 = mcrfpy.Scene("keep")
c = mcrfpy.Caption(text="kept")
s3.children.append(c)
mcrfpy.Scene("keep")
s3.register()
check(contains(s3.children, c) == 1 and c.parent is s3, "an old scene keeps its children through re-registration")

# parent = scene uses that scene, registered or not
old = mcrfpy.Scene("pp")
mcrfpy.Scene("pp")
g = mcrfpy.Frame()
g.parent = old
check(g.parent is old and contains(old.children, g) == 1, "drawable.parent = unregistered scene adds it there")

# Replacing the CURRENT scene's name: the new scene is shown (it used to fall back to
# whichever scene sorted first, or none), with on_exit / on_enter as for activate()
events = []


class Tracked(mcrfpy.Scene):
    def __init__(self, name, tag):
        self.tag = tag  # before the base __init__, which can already call on_enter
        super().__init__(name)

    def on_enter(self):
        events.append(("enter", self.tag))

    def on_exit(self):
        events.append(("exit", self.tag))


cur = Tracked("current_dup", "old")
cur.children.append(mcrfpy.Frame())
mcrfpy.current_scene = cur
events.clear()
new = Tracked("current_dup", "new")
mcrfpy.step(0.016)
check(mcrfpy.current_scene is new, "the scene shown is the one that now has the name")
check(len(cur.children) == 1, "the replaced current scene keeps its children")
check(events == [("exit", "old"), ("enter", "new")], f"on_exit(old) then on_enter(new): {events}")

# Re-registering the old one takes the name (and the screen) back
cur.register()
check(mcrfpy.current_scene is cur and not new.registered, "register() takes the name back")

# A dropped old scene frees its tree, and its children forget it
d = mcrfpy.Scene("drop")
h = mcrfpy.Frame()
d.children.append(h)
mcrfpy.Scene("drop")
del d
gc.collect()
check(h.parent is None, "a child of a freed scene has no parent")

if failures:
    sys.exit(1)
print("PASS")
sys.exit(0)
