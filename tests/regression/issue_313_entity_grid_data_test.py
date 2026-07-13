# Regression test for #313: UIEntity::grid -> shared_ptr<GridData> + entity.texture
#
# Guards the invariants that must survive the #313 refactor:
#   (a) entity.texture getter returns the entity's real Texture (never crashes)
#   (b) setter accepts Texture only (TypeError otherwise), reflected on read-back,
#       and preserves sprite_index
#   (c) entity pixel position (x/y/pos) is derived from the GRID's cell size,
#       NOT the entity's own texture -- setting a different-sized texture on the
#       entity must not move it
#   (d) entity.grid returns the same GridData object across step/FOV cycles
#       (PythonObjectCache identity). #361 changed WHAT it returns -- the map, not
#       a view -- but the identity guarantee this test exists for is unchanged.
#   (e) find_path() and at() still work, and constructing their temporary internal
#       grid wrappers does not destroy the grid's cell callbacks (#251 guard)
#   (f) a GridPoint obtained from entity.at() outlives the entity and the grid
#       reference without crashing (aliasing shared_ptr keeps the grid alive)
import mcrfpy
import gc
import sys

failures = []

def check(cond, label):
    status = "ok" if cond else "FAIL"
    print("  %s: %s" % (status, label))
    if not cond:
        failures.append(label)

def main():
    tex16 = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(10, 10), texture=tex16, pos=(0, 0), size=(160, 160))
    for y in range(10):
        for x in range(10):
            p = grid.at(x, y)
            p.walkable = True
            p.transparent = True

    entity = mcrfpy.Entity(grid_pos=(2, 2), texture=tex16, sprite_index=5, grid=grid)

    # --- (a) getter returns the real texture ---
    t = entity.texture
    check(t is not None, "(a) entity.texture is not None")
    check(isinstance(t, mcrfpy.Texture), "(a) entity.texture is a Texture")
    check(t.sprite_width == 16 and t.sprite_height == 16,
          "(a) entity.texture has the constructor texture's sprite dims")
    check(t.source == tex16.source, "(a) entity.texture.source matches constructor texture")

    # --- (c) pixel position comes from the grid's cell size, not the entity texture ---
    x_before, y_before = entity.x, entity.y
    check(x_before == 2 * 16 and y_before == 2 * 16,
          "(c) pixel pos = grid_pos * grid cell size before texture change")

    # an 8x8 texture with 8x8 sprites (single red sprite)
    tex8 = mcrfpy.Texture.from_bytes(bytes([255, 0, 0, 255] * 64), 8, 8, 8, 8,
                                     name="<issue313-8x8>")

    # --- (b) setter semantics ---
    entity.texture = tex8
    check(entity.texture.sprite_width == 8 and entity.texture.sprite_height == 8,
          "(b) texture set is reflected on read-back")
    check(entity.sprite_index == 5, "(b) sprite_index preserved across texture set")
    try:
        entity.texture = 42
        check(False, "(b) non-Texture assignment raises TypeError")
    except TypeError:
        check(True, "(b) non-Texture assignment raises TypeError")
    try:
        entity.texture = None
        check(False, "(b) None assignment raises TypeError")
    except TypeError:
        check(True, "(b) None assignment raises TypeError")
    try:
        del entity.texture
        check(False, "(b) attribute deletion raises TypeError")
    except TypeError:
        check(True, "(b) attribute deletion raises TypeError")

    # --- (c) continued: position unchanged after the 8x8 texture swap ---
    check(entity.x == x_before and entity.y == y_before,
          "(c) pixel pos unchanged after setting a different-sized entity texture")

    # --- (d) entity.grid identity across a step/FOV cycle ---
    # #361: entity.grid is the GridData (the map), not the Grid (a camera onto it).
    # An entity can be on a map with no view at all, or with several; "the grid an
    # entity is in" is not a camera. It is still one stable object, which is what
    # the PythonObjectCache identity guarantee here is about.
    check(entity.grid is grid.grid_data, "(d) entity.grid is the map this Grid views")
    check(isinstance(entity.grid, mcrfpy.GridData), "(d) entity.grid is a GridData")
    grid.compute_fov((2, 2), radius=5)
    grid.step(1)
    check(entity.grid is grid.grid_data, "(d) entity.grid identity survives step + compute_fov")

    # --- (e) find_path / at() work; cell callbacks survive temp grid wrappers ---
    grid.on_cell_click = lambda pos, btn, action: None
    path = entity.find_path((5, 5))
    check(path is not None, "(e) find_path returns a result on an open grid")
    check(grid.on_cell_click is not None,
          "(e) grid.on_cell_click survives find_path's temporary grid wrapper (#251)")

    entity.update_visibility()
    gp = entity.at(2, 2)
    check(gp is not None, "(e) entity.at(own cell) returns a GridPoint when visible")
    check(gp.walkable is True, "(e) GridPoint from entity.at() reads cell data")
    check(grid.on_cell_click is not None,
          "(e) grid.on_cell_click survives entity.at()'s grid wrapper (#251)")

    # --- (g) hardening guards from the #313 adversarial review ---
    # Null-data Texture (Texture.__new__ without __init__) must be rejected,
    # not crash (same ValueError guard as UISprite.texture).
    null_tex = mcrfpy.Texture.__new__(mcrfpy.Texture)
    try:
        entity.texture = null_tex
        check(False, "(g) null-data Texture assignment raises ValueError")
    except ValueError:
        check(True, "(g) null-data Texture assignment raises ValueError")
    # An object whose __class__ raises must not crash isinstance handling.
    class EvilMeta:
        @property
        def __class__(self):
            raise RuntimeError("no class for you")
    try:
        entity.texture = EvilMeta()
        check(False, "(g) isinstance-error during assignment raises, no crash")
    except (TypeError, RuntimeError):
        check(True, "(g) isinstance-error during assignment raises, no crash")
    # Uninitialized Entity wrapper (Entity.__new__ without __init__) must
    # raise RuntimeError on texture access, not segfault.
    uninit = mcrfpy.Entity.__new__(mcrfpy.Entity)
    try:
        _ = uninit.texture
        check(False, "(g) uninitialized Entity texture get raises RuntimeError")
    except RuntimeError:
        check(True, "(g) uninitialized Entity texture get raises RuntimeError")
    try:
        uninit.texture = tex16
        check(False, "(g) uninitialized Entity texture set raises RuntimeError")
    except RuntimeError:
        check(True, "(g) uninitialized Entity texture set raises RuntimeError")

    # --- (h) entity.grid survives GC of the view's Python wrapper ---
    # The canonical idiom: append the Grid to a scene, drop the Python reference.
    # The C++ view lives on in the scene graph; the entity's map must stay valid
    # and identical. (#361: entity.grid is the GridData, so this no longer depends
    # on a view existing at all -- but the wrapper-GC hazard is the same one.)
    scene = mcrfpy.Scene("issue313_ov")
    g2 = mcrfpy.Grid(grid_size=(4, 4), texture=tex16, pos=(0, 0), size=(64, 64))
    e2 = mcrfpy.Entity(grid_pos=(1, 1), texture=tex16, grid=g2)
    data2 = g2.grid_data
    scene.children.append(g2)
    del g2
    gc.collect()
    check(e2.grid is data2,
          "(h) entity.grid is the same GridData after the view wrapper is GC'd")
    check(e2.grid.at(1, 1) is not None,
          "(h) that GridData is still usable after the view wrapper is GC'd")

    # --- (f) GridPoint outlives entity + grid references ---
    entity.die()
    del entity
    del grid
    gc.collect()
    check(gp.walkable is True, "(f) GridPoint usable after entity.die() and grid release")
    check(tuple(gp.grid_pos) == (2, 2), "(f) GridPoint position intact after teardown")
    del gp
    gc.collect()

    if failures:
        print("FAIL: %d check(s) failed" % len(failures))
        sys.exit(1)
    print("PASS")
    sys.exit(0)

if __name__ == "__main__":
    main()
