"""#540 F: the argument name in the helper's errors is a plain parameter, not hidden state.
An outer NAMED parse whose __index__ runs an inner UNNAMED parse and an inner differently-named
parse (both failing) must keep every name right, and leave no stale name behind."""
import sys
import mcrfpy

fails = []
BIG = 2**70
tile = mcrfpy.TileLayer("t", -1, mcrfpy.default_texture, (8, 8))
grid = mcrfpy.Grid(grid_size=(8, 8), texture=mcrfpy.default_texture)
seen = {}


class Idx:
    def __index__(self):
        for label, fn in (
            ("inner unnamed", lambda: grid.at((BIG, 0))),
            ("inner named pos", lambda: tile.fill_rect((BIG, 0), (1, 1), 1)),
            ("inner named size", lambda: tile.fill_rect((0, 0), (1, BIG), 1)),
        ):
            try:
                fn()
            except OverflowError as e:
                seen[label] = str(e)
        return 1


# outer parse is "size"; its x converts via the re-entrant __index__, its y is bad
try:
    tile.fill_rect((0, 0), [Idx(), BIG], 1)
    fails.append("outer: did not raise")
except OverflowError as e:
    if not str(e).startswith("size:"):
        fails.append(f"outer error lost its name: {e}")

if not seen.get("inner unnamed", "").startswith("position component"):
    fails.append(f"inner unnamed parse got a name: {seen.get('inner unnamed')!r}")
if not seen.get("inner named pos", "").startswith("pos:"):
    fails.append(f"inner named pos wrong: {seen.get('inner named pos')!r}")
if not seen.get("inner named size", "").startswith("size:"):
    fails.append(f"inner named size wrong: {seen.get('inner named size')!r}")

# nothing stale afterwards: an unnamed parse is still unnamed, a named one still named
try:
    grid.at((BIG, 0))
except OverflowError as e:
    if not str(e).startswith("position component"):
        fails.append(f"stale name on a later unnamed parse: {e}")
try:
    tile.fill_rect((BIG, 0), (1, 1), 1)
except OverflowError as e:
    if not str(e).startswith("pos:"):
        fails.append(f"later named parse wrong: {e}")

# and the same through a user __len__ (generic sequence)
class LenReenters:
    def __len__(self):
        try:
            grid.at((BIG, 0))
        except OverflowError as e:
            seen["len unnamed"] = str(e)
        return 2
    def __getitem__(self, i): return (BIG, 0)[i]

try:
    tile.fill_rect(LenReenters(), (1, 1), 1)
except OverflowError as e:
    if not str(e).startswith("pos:"):
        fails.append(f"outer pos error lost its name after nested __len__ parse: {e}")
if not seen.get("len unnamed", "").startswith("position component"):
    fails.append(f"nested unnamed parse inside __len__: {seen.get('len unnamed')!r}")

for f in fails:
    print("FAIL:", f)
print("FAIL" if fails else "PASS")
sys.exit(1 if fails else 0)
