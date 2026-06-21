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

# --- A grid created without an explicit texture still gets the engine default
# texture, so its view's texture is also non-None (the getter's None branch is
# defensive-only -- no public API produces a textureless grid). -------------
bare_grid = mcrfpy.Grid(grid_size=(8, 8))
bare_view = mcrfpy.GridView(grid=bare_grid, pos=(0, 0), size=(80, 80))
check("default-textured grid's view exposes a Texture (not None)",
      isinstance(bare_view.texture, mcrfpy.Texture))
check("view texture matches its grid's texture source",
      bare_view.texture.source == bare_grid.texture.source)

# --- property is read-only (NULL setter) -----------------------------------
try:
    view.texture = texture
    check("GridView.texture is read-only (assignment raises)", False)
except AttributeError:
    check("GridView.texture is read-only (assignment raises)", True)
except Exception as e:
    check("GridView.texture is read-only (raised %s)" % type(e).__name__, False)


print("")
if failures:
    print("FAIL -- %d check(s) failed:" % len(failures))
    for f in failures:
        print("  - " + f)
    sys.exit(1)
print("PASS -- GridView.texture returns the tile Texture (or None when absent).")
sys.exit(0)
