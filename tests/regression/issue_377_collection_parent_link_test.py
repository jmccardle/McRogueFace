#!/usr/bin/env python3
"""
Issue #377: every UICollection mutator must maintain the parent link.

`x in collection` and `x.parent is <collection owner>` are supposed to be two views of
the same fact (#122/#183). Only append() maintained it. The rest got it wrong two ways:

  * insert/extend/setitem called setParent(owner.lock()) unconditionally. A SCENE
    collection has no owner drawable, so that resolved to null -- and setParent(nullptr)
    also clears parent_scene. The drawable landed in the scene's UI vector, rendered
    fine, and reported .parent of None.

  * The slice arms never touched the link at all: a slice-delete left the removed child
    pointing at a parent that no longer contained it, and a slice-assign never parented
    the incoming items nor unparented the ones they displaced.

Two adjacent traps in the same functions are also covered here: `collection[-1]` on an
EMPTY collection hung the engine forever (`while (index < 0) index += size()` adds zero
each pass), and getitem's `index > size() - 1` bounds check underflowed to SIZE_MAX when
size() was 0, so it went on to index an empty vector.

This invariant is what #373's identity pin hangs off, so it has to hold for every path.
"""

import sys

import mcrfpy

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print(f"FAIL: {msg}")
    else:
        print(f"  ok: {msg}")


def frame(n=10):
    return mcrfpy.Frame(pos=(0, 0), size=(n, n))


def check_linked(child, owner, collection, label):
    """The two views of membership must agree."""
    check(child in collection, f"{label}: child is in the collection")
    check(child.parent is owner, f"{label}: child.parent is the owner (got {child.parent!r})")


def check_unlinked(child, collection, label):
    check(child not in collection, f"{label}: child is NOT in the collection")
    check(child.parent is None, f"{label}: child.parent is None (got {child.parent!r})")


def test_scene_collection_mutators():
    """A scene collection parents via parent_scene; only append used to do it."""
    scene = mcrfpy.Scene("link_scene")

    a, b, c, d = frame(), frame(), frame(), frame()

    scene.children.append(a)
    check_linked(a, scene, scene.children, "scene append")

    scene.children.insert(0, b)
    check_linked(b, scene, scene.children, "scene insert")

    scene.children.extend([c])
    check_linked(c, scene, scene.children, "scene extend")

    scene.children[0] = d
    check_linked(d, scene, scene.children, "scene setitem")


def test_frame_collection_mutators():
    scene = mcrfpy.Scene("link_frame")
    owner = mcrfpy.Frame(pos=(0, 0), size=(200, 200))
    scene.children.append(owner)

    a, b, c, d = frame(), frame(), frame(), frame()

    owner.children.append(a)
    check_linked(a, owner, owner.children, "frame append")

    owner.children.insert(0, b)
    check_linked(b, owner, owner.children, "frame insert")

    owner.children.extend([c])
    check_linked(c, owner, owner.children, "frame extend")

    replaced = owner.children[0]
    owner.children[0] = d
    check_linked(d, owner, owner.children, "frame setitem")
    check_unlinked(replaced, owner.children, "frame setitem (displaced element)")


def test_removal_mutators_unlink():
    scene = mcrfpy.Scene("link_remove")
    owner = mcrfpy.Frame(pos=(0, 0), size=(200, 200))
    scene.children.append(owner)

    a, b, c = frame(), frame(), frame()
    owner.children.extend([a, b, c])

    owner.children.remove(a)
    check_unlinked(a, owner.children, "frame remove()")

    popped = owner.children.pop(0)
    check_unlinked(popped, owner.children, "frame pop()")

    del owner.children[0]
    check_unlinked(c, owner.children, "frame __delitem__")
    check(len(owner.children) == 0, "the collection is empty after removing everything")


def test_slice_delete_unlinks():
    scene = mcrfpy.Scene("link_slicedel")
    owner = mcrfpy.Frame(pos=(0, 0), size=(200, 200))
    scene.children.append(owner)

    a, b, c, d = frame(), frame(), frame(), frame()
    owner.children.extend([a, b, c, d])

    del owner.children[0:2]              # contiguous
    check(len(owner.children) == 2, "contiguous slice-delete removed two elements")
    check_unlinked(a, owner.children, "contiguous slice-delete (a)")
    check_unlinked(b, owner.children, "contiguous slice-delete (b)")
    check_linked(c, owner, owner.children, "contiguous slice-delete (survivor c)")

    e, f = frame(), frame()
    owner.children.extend([e, f])        # now: c, d, e, f
    del owner.children[0::2]             # extended slice: removes c and e
    check_unlinked(c, owner.children, "extended slice-delete (c)")
    check_unlinked(e, owner.children, "extended slice-delete (e)")
    check_linked(d, owner, owner.children, "extended slice-delete (survivor d)")
    check_linked(f, owner, owner.children, "extended slice-delete (survivor f)")


def test_slice_assign_links():
    scene = mcrfpy.Scene("link_sliceassign")
    owner = mcrfpy.Frame(pos=(0, 0), size=(200, 200))
    scene.children.append(owner)

    a, b = frame(), frame()
    owner.children.extend([a, b])

    c, d = frame(), frame()
    owner.children[0:1] = [c, d]         # resizing contiguous assign
    check_linked(c, owner, owner.children, "slice-assign (new element c)")
    check_linked(d, owner, owner.children, "slice-assign (new element d)")
    check_unlinked(a, owner.children, "slice-assign (displaced element a)")
    check_linked(b, owner, owner.children, "slice-assign (untouched element b)")

    e = frame()
    owner.children[0:1] = [e]            # same-size contiguous assign
    check_linked(e, owner, owner.children, "same-size slice-assign (new element)")
    check_unlinked(c, owner.children, "same-size slice-assign (displaced element)")

    # Extended slice assign
    g, h = frame(), frame()
    owner.children[0::2] = [g, h]
    check_linked(g, owner, owner.children, "extended slice-assign (g)")
    check_linked(h, owner, owner.children, "extended slice-assign (h)")


def test_slice_assign_on_scene():
    """Slice-assign into a scene collection must parent to the SCENE."""
    scene = mcrfpy.Scene("link_slicescene")
    a, b = frame(), frame()
    scene.children.extend([a, b])

    c = frame()
    scene.children[0:1] = [c]
    check_linked(c, scene, scene.children, "scene slice-assign")
    check_unlinked(a, scene.children, "scene slice-assign (displaced)")


def test_reparent_between_owners():
    """Appending to a new owner must remove from the old one, not leave it in both."""
    scene = mcrfpy.Scene("link_reparent")
    one = mcrfpy.Frame(pos=(0, 0), size=(100, 100))
    two = mcrfpy.Frame(pos=(0, 0), size=(100, 100))
    scene.children.extend([one, two])

    x = frame()
    one.children.append(x)
    check_linked(x, one, one.children, "child starts in owner one")

    two.children.append(x)
    check(x not in one.children, "reparenting removed the child from its old owner")
    check_linked(x, two, two.children, "reparenting linked the child to its new owner")


def test_empty_collection_negative_index():
    """`collection[-1]` on an empty collection used to hang the engine forever."""
    scene = mcrfpy.Scene("link_empty")

    try:
        scene.children[-1]
        check(False, "getitem[-1] on an empty collection raises IndexError")
    except IndexError:
        check(True, "getitem[-1] on an empty collection raises IndexError")

    try:
        scene.children[-1] = frame()
        check(False, "setitem[-1] on an empty collection raises IndexError")
    except IndexError:
        check(True, "setitem[-1] on an empty collection raises IndexError")

    # Negative indexing still works when there IS something to index.
    a, b = frame(), frame()
    scene.children.extend([a, b])
    check(scene.children[-1] is b, "negative indexing resolves from the end")
    check(scene.children[-2] is a, "negative indexing reaches the first element")
    try:
        scene.children[-3]
        check(False, "an out-of-range negative index raises IndexError")
    except IndexError:
        check(True, "an out-of-range negative index raises IndexError")


def main():
    test_scene_collection_mutators()
    test_frame_collection_mutators()
    test_removal_mutators_unlink()
    test_slice_delete_unlinks()
    test_slice_assign_links()
    test_slice_assign_on_scene()
    test_reparent_between_owners()
    test_empty_collection_negative_index()

    if failures:
        print(f"\nFAILED ({len(failures)} checks)")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print("\nPASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
