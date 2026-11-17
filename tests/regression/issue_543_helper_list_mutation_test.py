"""#543: the position helper must not read freed memory when converting x runs user code that
mutates the container being parsed. It takes references to both items before any conversion.

Under ASan (make asan) the old code is a SEGV in extract_int / extract_number; in a normal
build the freed slot is often still readable, so the assertions below also pin the semantics:
the pair is snapshotted, i.e. y is the object that was in the list when parsing began."""
import sys
import mcrfpy

fails = []


class Y:
    def __init__(self, v): self.v = v
    def __index__(self): return self.v


def make_x(pair, action):
    class X:
        def __index__(self):
            action(pair)
            return 1
    return X()


def clear(pair): pair.clear()
def replace_y(pair): pair[1] = Y(6)       # drops the list's reference to the original y
def pop_y(pair): pair.pop()
def grow(pair): pair.extend(range(50))    # reallocates the list's item array


tile = mcrfpy.TileLayer("t", -1, mcrfpy.default_texture, (8, 8))

for name, action in (("clear", clear), ("replace_y", replace_y), ("pop_y", pop_y), ("grow", grow)):
    # integer path: TileLayer.set((x, y), v) -> cell (1, 3)
    tile.fill(-1)
    pair = [None, Y(3)]
    pair[0] = make_x(pair, action)
    try:
        tile.set(pair, 5)
    except Exception as e:
        fails.append(f"int path/{name}: raised {type(e).__name__}: {e}")
    else:
        if tile.at((1, 3)) != 5:
            fails.append(f"int path/{name}: cell (1, 3) is {tile.at((1, 3))}, want 5 (y snapshotted)")

    # float path: Frame.move([dx, dy]) -> moved by (1, 3)
    f = mcrfpy.Frame(pos=(0, 0), size=(10, 10))
    pair = [None, Y(3)]
    pair[0] = make_x(pair, action)
    try:
        f.move(pair)
    except Exception as e:
        fails.append(f"float path/{name}: raised {type(e).__name__}: {e}")
    else:
        if (f.x, f.y) != (1.0, 3.0):
            fails.append(f"float path/{name}: frame at {(f.x, f.y)}, want (1.0, 3.0)")

# ParseInt / ParseFloat entry points with a list argument

shared = [None, Y(2)]
shared[0] = make_x(shared, clear)
grid = mcrfpy.Grid(grid_size=(5, 5), texture=mcrfpy.default_texture)
try:
    grid.at(shared)
except Exception as e:
    fails.append(f"ParseInt/Grid.at: raised {type(e).__name__}: {e}")

for f in fails:
    print("FAIL:", f)
print("FAIL" if fails else "PASS")
sys.exit(1 if fails else 0)
