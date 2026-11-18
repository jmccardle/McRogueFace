"""#552: Grid.step acts entities with an equal turn_order in collection order (a stable sort)."""
import sys
import mcrfpy

N = 60
g = mcrfpy.Grid(grid_size=(N, 2), texture=mcrfpy.default_texture)
acted = []
ents = []
for i in range(N):
    e = mcrfpy.Entity(grid_pos=(i, 0), grid=g)
    e.turn_order = 1 + (i % 2)               # two levels, many equal
    e.set_behavior(mcrfpy.Behavior.WAYPOINT, waypoints=[(i, 1)], turns=1)
    e.step = (lambda k: (lambda trigger, data: acted.append(k)))(i)
    ents.append(e)
g.step(n=1)
want = sorted(range(N), key=lambda i: (1 + i % 2, i))
fails = []
if sorted(acted) != list(range(N)):
    fails.append(f"every entity should have acted once, got {len(acted)} callbacks")
elif acted != want:
    fails.append(f"turn order {acted[:12]}..., want {want[:12]}...")
if fails:
    print("FAIL", fails); sys.exit(1)
print("PASS"); sys.exit(0)
