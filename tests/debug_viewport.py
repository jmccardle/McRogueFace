import mcrfpy
import sys

vp = mcrfpy.Viewport3D(pos=(0,0), size=(100,100))
vp.set_grid_size(16, 16)
e = mcrfpy.Entity3D(pos=(5,5), scale=1.0)
vp.entities.append(e)

# Check viewport
v = e.viewport
print("viewport:", v, file=sys.stderr, flush=True)

sys.exit(0)
