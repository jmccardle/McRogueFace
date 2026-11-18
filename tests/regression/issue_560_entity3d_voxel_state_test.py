"""#560: Entity3D keeps per-cell seen/discovered memory sized to ONE viewport grid; it must be reset when
the viewport or its grid_size changes, or it is indexed with the new width. canSee/hasDiscovered are not
exposed to Python, so this drives the only entry point (update_visibility) through every resize / move and
requires it to keep working (ASan flags any stale-size indexing)."""
import sys
import mcrfpy

fails = []
a = mcrfpy.Viewport3D(); a.set_grid_size(30, 30)
b = mcrfpy.Viewport3D(); b.set_grid_size(3, 3)
e = mcrfpy.Entity3D(pos=(10, 10))
a.entities.append(e)
e.update_visibility()
a.grid_size = (4, 4)               # shrink under a live entity
e.update_visibility()
a.grid_size = (200, 200)           # grow
e.update_visibility()
a.entities.remove(e)
b.entities.append(e)               # another viewport, much smaller grid
e.update_visibility()
b.grid_size = (500, 2)
e.update_visibility()
try:
    e.pos = (400, 1)
    e.update_visibility()
except (ValueError, IndexError):
    pass
print("FAIL: " + "; ".join(fails) if fails else "PASS")
sys.exit(1 if fails else 0)
