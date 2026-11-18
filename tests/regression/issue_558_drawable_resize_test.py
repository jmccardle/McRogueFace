"""#558: Drawable.resize on a Grid goes through the same camera check as size= (ValueError, not applied)."""
import sys
import mcrfpy

fails = []
g = mcrfpy.Grid(grid_size=(4, 4), texture=mcrfpy.default_texture, size=(40, 40))
g.zoom = 1e-6
before = (g.size.x, g.size.y, g.zoom)
for name, call in (("Drawable.resize(w, h)", lambda: mcrfpy.Drawable.resize(g, 1e7, 1e7)),
                   ("Drawable.resize((w, h))", lambda: mcrfpy.Drawable.resize(g, (1e7, 1e7))),
                   ("size=", lambda: setattr(g, "size", (1e7, 1e7)))):
    try:
        call()
        fails.append(f"{name} accepted an invalid size")
    except ValueError:
        pass
    if (g.size.x, g.size.y, g.zoom) != before:
        fails.append(f"{name} changed the view: {(g.size.x, g.size.y, g.zoom)}")
mcrfpy.Drawable.resize(g, 50, 50)
if (g.size.x, g.size.y) != (50, 50):
    fails.append("a valid Drawable.resize was not applied")
if fails:
    print("FAIL"); [print(" ", f) for f in fails]; sys.exit(1)
print("PASS"); sys.exit(0)
