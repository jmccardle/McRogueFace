"""#560 E: EntityCollection3D iteration under mutation. The iterator used to hold a std::list iterator:
a remove+append kept the size (the guard passed) and left it on an erased node (ASan: use-after-free).
It is index-based over a vector now. Assertions: no crash, and every yielded entity is a live member."""
import sys
import mcrfpy

fails = []
def check(c, m):
    if not c: fails.append(m)

vp = mcrfpy.Viewport3D()
vp.set_grid_size(8, 8)
ents = [mcrfpy.Entity3D(pos=(i, 0)) for i in range(4)]
for e in ents:
    vp.entities.append(e)

# same-size mutation mid-iteration: remove one, append one
it = iter(vp.entities)
seen = [next(it)]
vp.entities.remove(ents[1])
newcomer = mcrfpy.Entity3D(pos=(5, 5))
vp.entities.append(newcomer)
try:
    while True:
        seen.append(next(it))
except StopIteration:
    pass
except RuntimeError:
    pass                                   # "modified during iteration" is an accepted answer too
live = list(vp.entities)
check(all(any(s is m for m in live) or s is ents[0] for s in seen), "every yielded entity is a live member")
check(len(live) == 4 and newcomer in live and ents[1] not in live, "membership is as mutated")

# plain iteration still yields every entity, in order, once
vp3 = mcrfpy.Viewport3D()
vp3.set_grid_size(4, 4)
es = [mcrfpy.Entity3D(pos=(i % 4, 0)) for i in range(40)]
for e in es:
    vp3.entities.append(e)
got = list(vp3.entities)
check(len(got) == 40 and all(a is b for a, b in zip(got, es)), "iteration yields every entity in order")
# growing/shrinking during iteration raises, it does not read freed memory
it = iter(vp3.entities); next(it)
vp3.entities.pop(0)
try:
    next(it); fails.append("size change during iteration did not raise")
except RuntimeError:
    pass
# clear() mid-iteration
it = iter(vp3.entities); next(it)
vp3.entities.clear()
try:
    next(it); fails.append("clear() during iteration did not raise")
except RuntimeError:
    pass
print("FAIL: " + "; ".join(fails) if fails else "PASS")
sys.exit(1 if fails else 0)
