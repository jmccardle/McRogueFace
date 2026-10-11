"""Regression test for #442 - appending a drawable into its own descendant segfaulted.

    a = Frame(); b = Frame(); a.children.append(b); b.children.append(a)   # SIGSEGV

The children mutators accepted an ancestor (or the object itself), the parent chain
became a loop, and every upward walk -- markContentDirty, global position, alignment --
recursed forever. Now UIDrawable::canAdopt() refuses with ValueError, BEFORE anything is
mutated, on every path that sets a parent: append, insert, extend, __setitem__, slice
assignment, the parent= setter and constructor keyword, and Frame(children=). Frame and
GridView children alike.

Before the fix the first check below crashed the process, so a pre-fix run is a segfault.
"""
import sys

import mcrfpy

failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


def chain(n):
    """f[0] > f[1] > ... > f[n-1], each the only child of the one before."""
    f = [mcrfpy.Frame() for _ in range(n)]
    for p, c in zip(f, f[1:]):
        p.children.append(c)
    return f


def snapshot(frames):
    return [(f.parent, list(f.children)) for f in frames]


def refused(what, op, frames):
    before = snapshot(frames)
    try:
        op()
        check(False, "%s: must raise ValueError" % what)
    except ValueError as e:
        check(snapshot(frames) == before, "%s: ValueError (%s), nothing mutated" % (what, e))


a, b, c, d = chain(4)
F = [a, b, c, d]
refused("append itself", lambda: a.children.append(a), F)
refused("append the parent", lambda: b.children.append(a), F)
refused("append a deep ancestor", lambda: d.children.append(a), F)
refused("insert an ancestor", lambda: c.children.insert(0, a), F)
x = mcrfpy.Frame()
y = mcrfpy.Frame()
holder = mcrfpy.Frame()
holder.children.append(y)
refused("extend with an ancestor last", lambda: d.children.extend([x, y, b]), F + [x, y, holder])
check(x.parent is None and y.parent is holder, "extend: the valid items before it did not move")
d.children.append(mcrfpy.Frame())
refused("__setitem__ an ancestor", lambda: d.children.__setitem__(0, a), F)
refused("slice-assign an ancestor", lambda: d.children.__setitem__(slice(0, 1), [x, a]), F + [x])
refused("parent= setter to a descendant", lambda: setattr(a, "parent", d), F)
refused("parent= setter to itself", lambda: setattr(a, "parent", a), F)

# Constructor paths: Frame(children=[...], parent=...) and re-running __init__.
k = mcrfpy.Frame()
try:
    mcrfpy.Frame(children=[k], parent=k)
    check(False, "Frame(children=[k], parent=k) must raise ValueError")
except ValueError:
    check(len(k.children) == 0, "Frame(children=[k], parent=k): ValueError, k left without the frame")
# Re-running __init__ resets the frame's own state first; the ancestor is still refused.
try:
    d.__init__(children=[a])
    check(False, "__init__(children=[ancestor]) must raise ValueError")
except ValueError:
    check(a.parent is None and d.parent is c, "__init__(children=[ancestor]): ValueError, chain intact")

# GridView children, and loops that mix Frames and GridViews.
g = mcrfpy.Grid(grid_size=(4, 4), pos=(0, 0), size=(64, 64))
inner = mcrfpy.Frame()
g.children.append(inner)
outer = mcrfpy.Frame()
outer.children.append(g)
G = [outer, inner]
refused("grid overlay: append the grid's ancestor", lambda: g.children.append(outer), G)
refused("frame in a grid: append the grid", lambda: inner.children.append(g), G)
refused("grid.parent = its own overlay child", lambda: setattr(g, "parent", inner), G)
refused("grid appended to its own children", lambda: g.children.append(g), G)

# The upward walks still terminate (they would recurse forever on a loop).
check(d.global_position is not None, "global_position walks a sane chain")

# Legitimate moves are untouched.
p, q = mcrfpy.Frame(), mcrfpy.Frame()
p.children.append(q)
p.children.append(q)
check(list(p.children) == [q], "re-appending an existing child is fine")
r = mcrfpy.Frame()
r.children.append(q)
check(q.parent is r and len(p.children) == 0, "moving a child to a sibling parent is fine")
q.parent = p
check(q.parent is p and len(r.children) == 0, "the parent= setter moves it back")
scene = mcrfpy.Scene("t442")
scene.children.append(a)
check(a.parent is scene and a in list(scene.children), "a scene accepts any drawable")

# Frame(children=) now goes through extend(): a child is detached from its old parent
# (it used to stay in both collections) and any drawable type is accepted.
old = mcrfpy.Frame()
kid = mcrfpy.Frame()
old.children.append(kid)
line = mcrfpy.Line(start=(0, 0), end=(5, 5))
nf = mcrfpy.Frame(children=[kid, line])
check(kid.parent is nf and len(old.children) == 0,
      "Frame(children=[kid]) moves kid out of its old parent")
check(line.parent is nf and len(nf.children) == 2, "Frame(children=) accepts a Line")

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
