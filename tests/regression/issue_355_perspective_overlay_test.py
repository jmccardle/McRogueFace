#!/usr/bin/env python3
"""Regression test for #355 - grid.perspective actually renders fog-of-war.

After the #252 Grid/GridView split, mcrfpy.Grid IS a UIGridView and the FOV
overlay is drawn by UIGridView::render(). But `grid.perspective = entity` fell
through getattro delegation to the internal _GridData and wrote UIGrid's copy of
the perspective state, which render() never reads -- the view gated the overlay
on its OWN perspective_enabled member, which nothing ever set. Result:
perspective_map computed correctly, grid.perspective_enabled read True, and not
a single fog pixel was drawn.

The state now lives on the view (single owner). This test asserts on PIXELS, not
on the property round-trip -- the property round-trip is exactly what lied.
"""
import sys
import os
import tempfile

import mcrfpy
from mcrfpy import automation

TMPDIR = tempfile.mkdtemp(prefix="mcrf355persp_")
_counter = 0


def shot():
    """Headless screenshot is synchronous (#153): render + capture inline."""
    global _counter
    path = os.path.join(TMPDIR, "p%d.png" % _counter)
    _counter += 1
    automation.screenshot(path)
    with open(path, "rb") as f:
        return f.read()


def main():
    texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)

    scene = mcrfpy.Scene("persp355")
    scene.activate()

    grid = mcrfpy.Grid(grid_size=(10, 10), pos=(0, 0), size=(160, 160), texture=texture)
    scene.children.append(grid)

    tiles = mcrfpy.TileLayer(name="terrain", z_index=-2, texture=texture)
    grid.add_layer(tiles)
    tiles.fill(5)

    # Opaque everywhere except the entity's own cell -> FOV is a tiny island, so
    # the vast majority of the map must be covered by the unknown/black overlay.
    for x in range(10):
        for y in range(10):
            grid.at(x, y).transparent = False

    e = mcrfpy.Entity((1, 1), grid=grid)
    e.sprite_index = 5

    omniscient = shot()

    grid.perspective = e
    e.update_visibility()

    assert grid.perspective is e, "grid.perspective did not round-trip the entity"
    assert grid.perspective_enabled is True, "assigning perspective must enable it"

    visible = sum(1 for x in range(10) for y in range(10)
                  if e.perspective_map[x, y] == mcrfpy.Perspective.VISIBLE)
    assert 0 < visible < 100, "test setup: expected a partial FOV, got %d visible" % visible

    fogged = shot()
    assert fogged != omniscient, (
        "grid.perspective is set and perspective_map has %d/100 visible cells, but the "
        "rendered frame is byte-identical to the omniscient one -- the FOV overlay is "
        "not being drawn (view's perspective state never set)" % visible
    )

    # Turning perspective back off must restore the omniscient image exactly.
    grid.perspective = None
    assert grid.perspective_enabled is False, "perspective=None must disable the overlay"
    cleared = shot()
    assert cleared == omniscient, (
        "clearing grid.perspective did not restore the un-fogged render"
    )

    # perspective_enabled toggles the overlay without clearing the entity.
    grid.perspective = e
    assert shot() != omniscient, "re-enabling perspective did not re-draw the overlay"
    grid.perspective_enabled = False
    assert grid.perspective is e, "perspective_enabled=False must not clear the entity"
    assert shot() == omniscient, "perspective_enabled=False did not remove the overlay"

    print("PASS")


if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except Exception as e:
        print("\nTEST FAILED: %s" % e)
        import traceback
        traceback.print_exc()
        sys.exit(1)
