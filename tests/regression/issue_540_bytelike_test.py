"""#540 D (decided): bytes, bytearray, memoryview, range and str are sequences but not positions:
TypeError, with the same message as any other non-position (naming the argument when named)."""
import sys
import mcrfpy

fails = []
tile = mcrfpy.TileLayer("t", -1, mcrfpy.default_texture, (8, 8))
grid = mcrfpy.Grid(grid_size=(8, 8), texture=mcrfpy.default_texture)
frame = mcrfpy.Frame(pos=(0, 0), size=(10, 10))
hm = mcrfpy.HeightMap((8, 8))

nonpos = {
    "bytes": b"\x01\x02",
    "bytearray": bytearray(b"\x01\x02"),
    "memoryview": memoryview(b"\x01\x02"),
    "range": range(2),
    "str": "ab",
}
callers = {
    "int FromObjectInt (TileLayer.set)": lambda p: tile.set(p, 1),
    "int ParseInt (Grid.at)": lambda p: grid.at(p),
    "int ParseInt pos= (Grid.at)": lambda p: grid.at(pos=p),
    "named (fill_rect pos)": lambda p: tile.fill_rect(p, (1, 1), 1),
    "named (fill_rect size)": lambda p: tile.fill_rect((0, 0), p, 1),
    "float FromObject (Frame.move)": lambda p: frame.move(p),
    "float ParseFloat (HeightMap.get_interpolated)": lambda p: hm.get_interpolated(p),
}
for cl, fn in callers.items():
    for nl, p in nonpos.items():
        try:
            fn(p)
            fails.append(f"{cl}: {nl} accepted as a position")
        except TypeError as e:
            if cl.startswith("named") and "must be" not in str(e):
                fails.append(f"{cl}: {nl}: message {e} does not name the argument")
        except Exception as e:
            fails.append(f"{cl}: {nl}: raised {type(e).__name__}: {e}; want TypeError")

# real sequences still work
tile.set([1, 2], 3)
tile.set((1, 2), 3)
frame.move([1, 2])

for f in fails:
    print("FAIL:", f)
print("FAIL" if fails else "PASS")
sys.exit(1 if fails else 0)
