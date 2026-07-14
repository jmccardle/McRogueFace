#!/usr/bin/env python3
"""
Issue #373: a GC'd Python subclass wrapper must not resurrect as its base type.

PythonObjectCache holds only weakrefs, so #369 (route every C++ -> Python conversion
through the cache) preserved object identity only while Python still held a reference
to the wrapper. If the user dropped their last reference while C++ still owned the
object, the wrapper was collected, the next lookup missed the cache, and a fresh
BASE-type wrapper was allocated -- silently downgrading the subclass and losing every
attribute set on it.

The fix is an owner-held strong ref ("pin"): a subclassed drawable's wrapper is kept
alive for exactly as long as the drawable is a member of a children collection. That
boundary is the parent link, so the pin is taken in setParent()/setParentScene() and
released on every path out -- including an owner destroyed while it still holds
children, which is the leak this test also guards.
"""

import gc
import sys
import weakref

import mcrfpy

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print(f"FAIL: {msg}")
    else:
        print(f"  ok: {msg}")


class MyFrame(mcrfpy.Frame):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.hp = 100


class MyCaption(mcrfpy.Caption):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tag = "captioned"


def test_parent_survives_gc():
    """The scenario from the issue: reach a GC'd subclass parent through .parent."""
    scene = mcrfpy.Scene("gc_parent")

    parent = MyFrame(pos=(0, 0), size=(100, 100))
    scene.children.append(parent)
    kid = mcrfpy.Frame(pos=(1, 1), size=(10, 10))
    parent.children.append(kid)

    del parent          # C++ still owns it via the scene's collection
    gc.collect()

    recovered = kid.parent
    check(type(recovered) is MyFrame,
          f"kid.parent is still a MyFrame after gc (got {type(recovered).__name__})")
    check(getattr(recovered, "hp", None) == 100,
          "the subclass attribute set in __init__ survived")
    check(kid.parent is kid.parent,
          "repeated .parent reads return the same object")
    check(kid.parent is recovered,
          "the pinned wrapper is the one handed back, not a new one")


def test_collection_indexing_survives_gc():
    """Reaching the same object by indexing the collection, not via .parent."""
    scene = mcrfpy.Scene("gc_index")
    sub = MyCaption(text="hello", pos=(5, 5))
    scene.children.append(sub)

    ref = weakref.ref(sub)
    del sub
    gc.collect()

    check(ref() is not None,
          "a subclassed drawable in a scene keeps its wrapper alive")
    got = scene.children[0]
    check(type(got) is MyCaption,
          f"scene.children[0] is still a MyCaption (got {type(got).__name__})")
    check(got.tag == "captioned", "its subclass attribute survived")
    check(got is ref(), "it is the original wrapper, not a copy")


def test_pin_released_on_removal():
    """Leaving the collection must drop the pin, or every subclass leaks forever."""
    scene = mcrfpy.Scene("gc_release")
    sub = MyFrame(pos=(0, 0), size=(10, 10))
    scene.children.append(sub)

    ref = weakref.ref(sub)
    scene.children.remove(sub)
    del sub
    gc.collect()

    check(ref() is None,
          "the wrapper is freed once the drawable leaves the collection")


def test_pin_released_when_owner_dies():
    """An owner destroyed while still holding children must drop their pins.

    Nothing calls setParent(nullptr) on this path -- the children vector simply dies --
    so without an explicit release in ~UIFrame the wrapper <-> drawable cycle would
    strand the whole subtree in memory.
    """
    scene = mcrfpy.Scene("gc_owner")
    holder = mcrfpy.Frame(pos=(0, 0), size=(50, 50))
    scene.children.append(holder)

    inner = MyFrame(pos=(1, 1), size=(5, 5))
    holder.children.append(inner)
    ref = weakref.ref(inner)
    del inner
    gc.collect()
    check(ref() is not None, "a nested subclass is pinned while its owner holds it")

    scene.children.remove(holder)
    del holder
    gc.collect()
    check(ref() is None,
          "the nested wrapper is freed when its owner is destroyed (no leak)")


def test_reparenting_preserves_identity():
    """Moving between collections must not drop the subclass on the floor.

    Reparenting unlinks then relinks; if the unlink released the last reference, the
    re-pin would find nothing in the cache and the subclass would be gone.
    """
    scene = mcrfpy.Scene("gc_reparent")
    a = mcrfpy.Frame(pos=(0, 0), size=(80, 80))
    b = mcrfpy.Frame(pos=(0, 0), size=(80, 80))
    scene.children.append(a)
    scene.children.append(b)

    sub = MyFrame(pos=(2, 2), size=(8, 8))
    sub.hp = 55
    a.children.append(sub)
    ref = weakref.ref(sub)
    del sub
    gc.collect()

    moved = a.children[0]
    b.children.append(moved)          # reparent a -> b
    del moved
    gc.collect()

    check(len(a.children) == 0, "the drawable left its old parent")
    check(len(b.children) == 1, "the drawable joined its new parent")
    check(ref() is not None, "it is still pinned by its new owner")
    got = b.children[0]
    check(type(got) is MyFrame,
          f"it is still a MyFrame after reparenting (got {type(got).__name__})")
    check(got.hp == 55, "and kept the attribute that was set on it")


def test_base_type_is_not_pinned():
    """Only subclasses are pinned. A base wrapper carries no state, so re-creating it
    is unobservable -- and pinning it would cost memory for nothing."""
    scene = mcrfpy.Scene("gc_base")
    plain = mcrfpy.Frame(pos=(0, 0), size=(10, 10))
    scene.children.append(plain)

    ref = weakref.ref(plain)
    del plain
    gc.collect()

    check(ref() is None, "a base-type wrapper is not pinned")
    got = scene.children[0]
    check(type(got) is mcrfpy.Frame, "it still round-trips as a Frame")
    check(got.w == 10, "and its C++ state is intact")


def main():
    test_parent_survives_gc()
    test_collection_indexing_survives_gc()
    test_pin_released_on_removal()
    test_pin_released_when_owner_dies()
    test_reparenting_preserves_identity()
    test_base_type_is_not_pinned()

    if failures:
        print(f"\nFAILED ({len(failures)} checks)")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print("\nPASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
