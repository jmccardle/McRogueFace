"""#560 D: PySequence_GetItem returns NULL for a list subclass whose __len__ lies; the 3D bindings
dereferenced it. Every coordinate-triple argument is hit with such a list: an exception is the
answer, a crash is the failure. Also E-adjacent: follow_path with a list shrunk by an element's __index__."""
import sys
import mcrfpy

class Liar(list):
    """claims 3 items, holds none: sq_item raises IndexError"""
    def __len__(self):
        return 3

fails = []
def attempt(label, fn):
    try:
        fn()
    except (TypeError, ValueError, IndexError, RuntimeError, OverflowError):
        return
    except BaseException as e:
        fails.append(f"{label}: {type(e).__name__}: {e}")
        return
    fails.append(label + ": a lying sequence was accepted")

liar = Liar()
vg = mcrfpy.VoxelGrid(size=(8, 8, 8))
vg.add_material("stone", color=(128, 128, 128))
attempt("VoxelGrid(size=liar)", lambda: mcrfpy.VoxelGrid(size=liar))
attempt("offset = liar", lambda: setattr(vg, "offset", liar))
attempt("fill_box", lambda: vg.fill_box(liar, (1, 1, 1), 1))
attempt("fill_box max", lambda: vg.fill_box((0, 0, 0), liar, 1))
attempt("fill_box_hollow", lambda: vg.fill_box_hollow(liar, (1, 1, 1), 1))
attempt("fill_sphere", lambda: vg.fill_sphere(liar, 2, 1))
attempt("fill_cylinder", lambda: vg.fill_cylinder(liar, 2, 2, 1))
attempt("fill_noise", lambda: vg.fill_noise(liar, (1, 1, 1), 1))
attempt("fill_noise max", lambda: vg.fill_noise((0, 0, 0), liar, 1))
attempt("copy_region", lambda: vg.copy_region(liar, (2, 2, 2)))
attempt("copy_region max", lambda: vg.copy_region((0, 0, 0), liar))
region = vg.copy_region((0, 0, 0), (2, 2, 2))
attempt("paste_region", lambda: vg.paste_region(region, liar))
vp = mcrfpy.Viewport3D()
attempt("camera_pos", lambda: setattr(vp, "camera_pos", liar))
attempt("camera_target", lambda: setattr(vp, "camera_target", liar))
attempt("Viewport3D(camera_pos=liar)", lambda: mcrfpy.Viewport3D(camera_pos=liar))

# follow_path: an element's __index__ empties the list the loop is walking
class Evil:
    def __index__(self):
        path.clear()
        return 1
path = [(Evil(), 1), (2, 2)]
vp.set_grid_size(8, 8)
e = mcrfpy.Entity3D(pos=(0, 0))
vp.entities.append(e)
try:
    e.follow_path(path)
except (TypeError, ValueError, IndexError, RuntimeError):
    pass
print("FAIL: " + "; ".join(fails) if fails else "PASS")
sys.exit(1 if fails else 0)
