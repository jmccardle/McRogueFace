"""Full-loop profiling workload: textured grid + moving entities + animated
nested UI, with forced real renders each frame (screenshot flushes the render
target in headless mode). Exercises render + update + animation together so
Callgrind/perf surface where the ENGINE actually spends time -- not a microbench.

NOTE: forcing renders via automation.screenshot() means ~96% of instructions go
to PNG encoding (libsfml stbi_zlib_compress). See docs/profiling.md "screenshot/
PNG trap": profile update/animation with step()-only, or subtract stbi_* symbols.
This workload found #348 (get_grid alloc churn).

Usage:
  ./build-profile/mcrogueface --headless --exec tests/benchmarks/profile_workload.py
  # or under Callgrind:
  make callgrind SCRIPT=tests/benchmarks/profile_workload.py
"""
import mcrfpy
from mcrfpy import automation
import sys
import os
import tempfile

GRID_W, GRID_H = 60, 60
ENTITY_COUNT = 80
FRAMES = 40
UI_FRAMES = 30  # nested animated frames


def build():
    scene = mcrfpy.Scene("profile")
    ui = scene.children

    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)

    color_layer = mcrfpy.ColorLayer(z_index=-1, name="color")
    grid = mcrfpy.Grid(grid_size=(GRID_W, GRID_H), pos=(0, 0), size=(960, 720),
                       texture=tex, layers=[color_layer])
    for x in range(GRID_W):
        for y in range(GRID_H):
            c = grid.at(x, y)
            c.walkable = True
            c.transparent = True
            color_layer.set((x, y), mcrfpy.Color(30, 30, 40, 255))
    ui.append(grid)

    entities = []
    vels = []
    for i in range(ENTITY_COUNT):
        e = mcrfpy.Entity((i % GRID_W, (i * 7) % GRID_H),
                          sprite_index=(i % 12) + 10, grid=grid)
        entities.append(e)
        vels.append((0.3 if i % 2 else -0.3, -0.2 if i % 3 else 0.2))

    # Nested animated UI hierarchy
    frames = []
    for i in range(UI_FRAMES):
        f = mcrfpy.Frame(pos=(10 + i * 5, 10 + i * 3), size=(120, 60),
                         fill_color=mcrfpy.Color(80, 40, 40, 200))
        cap = mcrfpy.Caption(text=f"f{i}", pos=(4, 4))
        f.children.append(cap)
        ui.append(f)
        # animate several properties -> exercises the per-frame animation path
        f.animate("x", 400.0 + i, 3.0, mcrfpy.Easing.EASE_IN_OUT)
        f.animate("opacity", 0.4, 3.0, mcrfpy.Easing.LINEAR)
        frames.append(f)

    return scene, grid, entities, vels, frames


def main():
    scene, grid, entities, vels, frames = build()
    mcrfpy.current_scene = scene

    with tempfile.TemporaryDirectory(prefix="mcrf_prof_") as tmp:
        # warmup (build chunk caches etc.)
        for _ in range(3):
            automation.screenshot(os.path.join(tmp, "w.png"))

        for frame in range(FRAMES):
            # move entities (dirties grid) via cell position
            for e, (vx, vy) in zip(entities, vels):
                p = e.cell_pos
                nx = (p.x + vx) % GRID_W
                ny = (p.y + vy) % GRID_H
                e.cell_pos = (nx, ny)
            mcrfpy.step(0.016)
            automation.screenshot(os.path.join(tmp, "f.png"))

    print(f"profile workload done: {FRAMES} frames, {ENTITY_COUNT} entities, "
          f"{UI_FRAMES} animated frames, grid {GRID_W}x{GRID_H}")


if __name__ == "__main__":
    main()
    sys.exit(0)
