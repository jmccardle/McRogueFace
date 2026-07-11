"""Regression test for #351 render early-out vs. the turn manager (grid.step()).

The #351 view render early-out re-blits a cached texture when
GridData.content_generation is unchanged. Entity movement driven by the
Python setters bumps content_generation, but the C++ turn manager
(grid.step()) mutated entity->cell_position / entity->position DIRECTLY,
never invalidating the view. Result: entities pathfinding via step() did not
visibly move on screen (the observed regression).

This test moves an entity with a WAYPOINT behavior via grid.step() and asserts
the rendered frame actually changes. It fails (identical before/after frames)
against the pre-fix build and passes once step() invalidates the view.

Headless screenshots are synchronous (#153) -- no Timer needed.
"""
import mcrfpy
from mcrfpy import automation
import sys
import os
import tempfile

TMPDIR = tempfile.mkdtemp(prefix="mcrf351step_")
_n = 0


def shot():
    global _n
    p = os.path.join(TMPDIR, "s%d.png" % _n)
    _n += 1
    automation.screenshot(p)
    with open(p, "rb") as f:
        return f.read()


def main():
    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    scene = mcrfpy.Scene("t351step")
    scene.activate()

    grid = mcrfpy.Grid(grid_size=(12, 12), pos=(10, 10), size=(384, 384),
                       texture=tex)
    scene.children.append(grid)

    # Open floor so pathfinding is trivial.
    for y in range(12):
        for x in range(12):
            grid.at(x, y).walkable = True
            grid.at(x, y).transparent = True

    ent = mcrfpy.Entity(grid_pos=(1, 1), texture=tex, sprite_index=84)
    grid.entities.append(ent)
    ent.move_speed = 0  # instant per-step move
    # WAYPOINT behavior: march across the grid, one cell per step().
    ent.set_behavior(mcrfpy.Behavior.WAYPOINT, waypoints=[(10, 10)], turns=1)

    # Render an initial frame so the early-out cache is primed.
    before = shot()
    start_cell = (ent.grid_pos.x, ent.grid_pos.y)

    # Drive the turn manager; entity should advance along the path.
    grid.step(n=1)
    after = shot()
    moved_cell = (ent.grid_pos.x, ent.grid_pos.y)

    assert moved_cell != start_cell, (
        "entity did not advance logically via step(): %r -> %r"
        % (start_cell, moved_cell))
    assert before != after, (
        "REGRESSION: grid.step() moved the entity logically (%r -> %r) but the "
        "rendered frame did not change -- #351 early-out served a stale cache."
        % (start_cell, moved_cell))

    # A second step should move again and re-render again.
    grid.step(n=1)
    after2 = shot()
    assert after != after2, "second step() did not re-render the moved entity"

    # And an idle (no-op) step must NOT falsely re-render differently: with the
    # entity still walking the path it will move, so instead assert the early-out
    # still works when nothing changes -- two back-to-back shots with no step.
    idle_a = shot()
    idle_b = shot()
    assert idle_a == idle_b, "idle frames differ; early-out not engaging"

    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
