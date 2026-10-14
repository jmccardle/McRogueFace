"""#493: mcrfpy.default_fov must be consumed by new grids and validated on assignment."""
import sys
import mcrfpy

assert mcrfpy.default_fov is mcrfpy.FOV.BASIC, mcrfpy.default_fov
g0 = mcrfpy.Grid(grid_size=(4, 4))
assert g0.fov is mcrfpy.FOV.BASIC

mcrfpy.default_fov = mcrfpy.FOV.SHADOW
assert mcrfpy.default_fov is mcrfpy.FOV.SHADOW
g1 = mcrfpy.Grid(grid_size=(4, 4))
assert g1.fov is mcrfpy.FOV.SHADOW, g1.fov
assert g0.fov is mcrfpy.FOV.BASIC, "existing grids must not change"

# GridData construction path too
assert mcrfpy.GridData(grid_size=(3, 3)).fov is mcrfpy.FOV.SHADOW

# the value really drives FOV: a grid's own setting still overrides
g1.fov = mcrfpy.FOV.PERMISSIVE_2
assert g1.fov is mcrfpy.FOV.PERMISSIVE_2

# validation: nothing changes on a bad assignment
for bad, exc in (("nonsense", TypeError), (None, TypeError), (999, ValueError), (-1, ValueError)):
    try:
        mcrfpy.default_fov = bad
    except exc:
        pass
    else:
        raise AssertionError(f"default_fov = {bad!r} should raise {exc.__name__}")
    assert mcrfpy.default_fov is mcrfpy.FOV.SHADOW

try:
    del mcrfpy.default_fov
except (AttributeError, TypeError):
    pass
else:
    raise AssertionError("delete should raise")

mcrfpy.default_fov = mcrfpy.FOV.BASIC
print("PASS")
sys.exit(0)
