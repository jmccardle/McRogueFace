"""#552: the highest z_index of a collection is kept by its owner (scene, Frame, Grid) so that the z_index
a drawable without one gets is O(1). Every writer of a member's z_index or of the membership must keep that
maximum true. After each operation, appending a drawable without a chosen z_index must give exactly
(the true highest z_index now in the collection) + 10, or 0 for an empty one. Probes stay in the collection
(removing one would invalidate the cache and hide a stale value from the next check)."""
import gc
import sys

import mcrfpy

fails = []


def fr(**kw):
    return mcrfpy.Frame(pos=(0, 0), size=(5, 5), **kw)


def probe(ui, label):
    want = max((e.z_index for e in ui), default=-10) + 10
    p = fr()
    ui.append(p)
    if p.z_index != want:
        fails.append(f"{label}: auto z_index {p.z_index}, want {want}")


def tops(ui):
    return max(ui, key=lambda e: e.z_index)


def scenario(label, make, parent_reinit_factory=None):
    ui = make()
    other = make()
    parent_reinit = parent_reinit_factory() if parent_reinit_factory else None
    for _ in range(5):
        ui.append(fr())
    probe(ui, f"{label}: after appends")

    # z changed by animation, by the base descriptor, by the subclass setter
    f = ui[2]
    f.animate("z_index", 500, 0.1)
    for _ in range(4):
        mcrfpy.step(0.1)
    if f.z_index != 500:
        fails.append(f"{label}: animation left z_index {f.z_index}")
    probe(ui, f"{label}: after an animated rise")
    mcrfpy.Drawable.z_index.__set__(f, 700)
    probe(ui, f"{label}: after the base descriptor raised the top")
    f.z_index = -5
    probe(ui, f"{label}: after the setter lowered the top")
    f.z_index = 900
    probe(ui, f"{label}: raised again")
    f.animate("z_index", 3, 0.1)
    for _ in range(4):
        mcrfpy.step(0.1)
    probe(ui, f"{label}: after an animated fall of the top")

    # a member's __init__ re-run
    f.__init__(pos=(0, 0), size=(5, 5), z_index=2000)
    probe(ui, f"{label}: member __init__ with a higher z_index")
    f.__init__(pos=(0, 0), size=(5, 5), z_index=-40)
    probe(ui, f"{label}: member __init__ with a lower z_index")
    f.__init__(pos=(0, 0), size=(5, 5))
    probe(ui, f"{label}: member __init__ without z_index")

    # the parent's __init__ re-run
    if parent_reinit:
        parent_reinit()
        probe(parent_reinit.ui(), f"{label}: parent __init__ re-run")

    # removals
    ui = parent_reinit.ui() if parent_reinit else ui
    ui.pop()
    probe(ui, f"{label}: pop")
    ui.remove(tops(ui))
    probe(ui, f"{label}: remove of the top")
    del ui[0]
    probe(ui, f"{label}: del ui[0]")
    del ui[1:3]
    probe(ui, f"{label}: slice delete")

    # a member moved to another collection, and one inserted from another collection
    other.append(fr(z_index=300))
    probe(other, f"{label}: other, a chosen z_index")
    t = tops(ui)
    other.append(t)
    probe(ui, f"{label}: source after its top moved away")
    probe(other, f"{label}: destination after the move")
    h = fr(z_index=5000)
    other.append(h)
    ui.insert(0, h)
    probe(ui, f"{label}: after inserting a high z_index from another collection")
    probe(other, f"{label}: source of the insert")

    # [i] = x and slice assignment, with higher and lower explicit z_index
    ui[1] = fr(z_index=9000)
    probe(ui, f"{label}: [i] = higher explicit")
    ui[1] = fr(z_index=-9000)
    probe(ui, f"{label}: [i] = lower explicit over the old top")
    ui[0] = fr()
    probe(ui, f"{label}: [i] = unchosen (takes the slot's z_index)")
    ui[0:2] = [fr(z_index=12000), fr()]
    probe(ui, f"{label}: slice with a higher explicit")
    ui[0:2] = [fr(z_index=-1), fr(z_index=-2)]
    probe(ui, f"{label}: slice with lower explicit over the top")
    ui.extend([fr(z_index=20000), fr(), fr(z_index=7)])
    probe(ui, f"{label}: extend")

    # a wrapper dropped while its drawable stays in the collection
    def add_and_drop():
        x = fr(z_index=30000)
        ui.append(x)
    add_and_drop()
    gc.collect()
    probe(ui, f"{label}: after a wrapper was dropped")
    gc.collect()
    tops(ui).z_index = 1
    probe(ui, f"{label}: top lowered through a fresh wrapper")

    # clear
    while len(ui):
        ui.pop()
    probe(ui, f"{label}: emptied")
    if ui[0].z_index != 0:
        fails.append(f"{label}: first append into an emptied collection gave {ui[0].z_index}, want 0")


keep = []   # the owners must outlive their collections


def keeping(make_owner):
    def make():
        owner = make_owner()
        keep.append(owner)
        return owner.children
    return make


scenario("scene", keeping(lambda: mcrfpy.Scene("zmax_%d" % len(keep))))

class ReinitFrame:
    def __init__(self, parent):
        self.parent = parent
    def __call__(self):
        self.parent.__init__(pos=(1, 1), size=(9, 9), name="parent")
    def ui(self):
        return self.parent.children


scenario("frame", keeping(lambda: fr(name="parent")), lambda: ReinitFrame(keep[-2]))
scenario("grid", keeping(lambda: mcrfpy.Grid(grid_size=(2, 2), texture=mcrfpy.default_texture, size=(10, 10))))

if fails:
    print("FAIL")
    for f in fails:
        print(" ", f)
    sys.exit(1)
print("PASS")
sys.exit(0)
