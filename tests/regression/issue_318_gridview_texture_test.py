"""
Regression test for issue #318 -- GridView.texture always returned None.

Root cause: the getter had a `TODO: return texture wrapper` and fell through to
Py_RETURN_NONE even when self->data->ptex was non-null. The fix returns a
Texture wrapper sharing the underlying shared_ptr<PyTexture>, mirroring
UIGrid.texture.

Needs an asset; run via run_tests.py (cwd=build/) or from build/ so that
assets/kenney_tinydungeon.png resolves. ASCII-only. Prints PASS/FAIL + exit.
"""

import mcrfpy
import sys

failures = []


def check(label, cond):
    if not cond:
        failures.append(label)
    print(("  ok  " if cond else " FAIL ") + label)


texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)

# --- GridView over a textured grid: texture must now be returned -----------
grid = mcrfpy.Grid(grid_size=(10, 10), texture=texture)
view = mcrfpy.GridView(grid=grid, pos=(0, 0), size=(160, 160))

t = view.texture
check("GridView.texture is not None when the view has a texture", t is not None)
check("GridView.texture is a Texture", isinstance(t, mcrfpy.Texture))
if isinstance(t, mcrfpy.Texture):
    # Wrapper should describe the same underlying sheet as the source.
    check("sprite_width matches source (16)", t.sprite_width == 16)
    check("sprite_height matches source (16)", t.sprite_height == 16)
    check("matches grid.texture sprite dims",
          grid.texture is not None
          and t.sprite_width == grid.texture.sprite_width
          and t.sprite_height == grid.texture.sprite_height)

# --- #453: a grid created without a texture has none until it's first drawn, and
# a view reports its GridData's texture (it has none of its own yet, #454). ----
bare_grid = mcrfpy.Grid(grid_size=(8, 8))
bare_view = mcrfpy.GridView(grid=bare_grid, pos=(0, 0), size=(80, 80))
check("a grid made without a texture has none (not yet drawn)", bare_view.texture is None)

# --- #453: assigning passes through to the GridData --------------------------
bare_view.texture = texture
check("view.texture = t sets the GridData's texture",
      bare_grid.grid_data.texture is texture and bare_view.texture is texture)


print("")
if failures:
    print("FAIL -- %d check(s) failed:" % len(failures))
    for f in failures:
        print("  - " + f)
    sys.exit(1)
print("PASS -- GridView.texture is its GridData's tile Texture (or None).")
sys.exit(0)
