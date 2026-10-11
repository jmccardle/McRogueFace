"""Regression test for #427 - grid layer edits never appeared inside Frame(cache_subtree=True).

Entity and cell changes reach the view through GridData::markDirty(), which bumps
content_generation AND marks every registered view dirty, so the view's parent chain
learns its subtree changed (#368's unconditional walk). Layer edits only bumped
content_generation: the view's own early-out (#351) noticed when asked to render, but a
caching ancestor never asked -- it kept blitting its cached texture.

Every layer mutation below must change the screenshot under a caching Frame, and (as a
control) without one.
"""
import mcrfpy
from mcrfpy import automation
import sys, os, tempfile

TMPDIR = tempfile.mkdtemp(prefix="mcrf427_")
_n = 0
failures = []


def shot():
    global _n
    p = os.path.join(TMPDIR, "s%d.png" % _n)
    _n += 1
    automation.screenshot(p)
    with open(p, "rb") as f:
        return f.read()


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
RED = mcrfpy.Color(255, 0, 0)
BLUE = mcrfpy.Color(0, 0, 255)


def color_edit(g, cl, tl):
    with cl.edit() as view:
        for y in range(4):
            for x in range(4):
                view[y, x, 1] = 255
                view[y, x, 3] = 255


def tile_edit(g, cl, tl):
    with tl.edit() as view:
        for y in range(4):
            for x in range(4):
                view[y, x] = 5


def add_layer(g, cl, tl):
    extra = mcrfpy.ColorLayer(name="extra", z_index=5)
    g.add_layer(extra)
    extra.fill(BLUE)


MUTATIONS = [
    ("ColorLayer.set", lambda g, cl, tl: cl.set((2, 2), RED)),
    ("ColorLayer.fill", lambda g, cl, tl: cl.fill(RED)),
    ("ColorLayer.fill_rect", lambda g, cl, tl: cl.fill_rect((1, 1), (3, 3), BLUE)),
    ("ColorLayer.edit", color_edit),
    ("TileLayer.set", lambda g, cl, tl: tl.set((2, 2), 7)),
    ("TileLayer.fill", lambda g, cl, tl: tl.fill(9)),
    ("TileLayer.edit", tile_edit),
    ("ColorLayer.visible", lambda g, cl, tl: setattr(cl, "visible", False)),
    ("ColorLayer.z_index", lambda g, cl, tl: setattr(cl, "z_index", -5)),
    ("TileLayer.visible", lambda g, cl, tl: setattr(tl, "visible", False)),
    ("add_layer", add_layer),
    ("remove_layer", lambda g, cl, tl: g.remove_layer(cl)),
]


def build(scene, cache):
    holder = mcrfpy.Frame(pos=(0, 0), size=(300, 300), cache_subtree=cache)
    cl = mcrfpy.ColorLayer(name="fog", z_index=1)
    tl = mcrfpy.TileLayer(name="terrain", z_index=-1, texture=tex)
    g = mcrfpy.Grid(grid_size=(8, 8), pos=(10, 10), size=(256, 256),
                    texture=tex, layers=[tl, cl])
    tl.fill(1)
    cl.fill(mcrfpy.Color(0, 0, 0, 128))
    holder.children.append(g)
    scene.children.append(holder)
    return holder, g, cl, tl


scene = mcrfpy.Scene("t427")
scene.activate()
for cache in (True, False):
    for name, mutate in MUTATIONS:
        holder, g, cl, tl = build(scene, cache)
        before = shot()
        check(shot() == before, "cache_subtree=%s %s: idle frames identical" % (cache, name))
        mutate(g, cl, tl)
        check(shot() != before, "cache_subtree=%s: %s repaints" % (cache, name))
        scene.children.remove(holder)

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
