"""#533: fill_rect pos/size accept a tuple, list or Vector (like set()); bad types raise."""
import sys
import mcrfpy

fails = []

def check(cond, msg):
    if not cond:
        fails.append(msg)

shapes = {
    "tuple": lambda a, b: (a, b),
    "list": lambda a, b: [a, b],
    "Vector": lambda a, b: mcrfpy.Vector(a, b),
}

def make(kind):
    if kind == "TileLayer":
        return mcrfpy.TileLayer("t", -1, mcrfpy.default_texture, (6, 6)), 5, (lambda l, p: l.at(p))
    return mcrfpy.ColorLayer("c", -1, (6, 6)), mcrfpy.Color(10, 20, 30, 255), (lambda l, p: l.at(p))

for kind in ("TileLayer", "ColorLayer"):
    for pn, pf in shapes.items():
        for sn, sf in shapes.items():
            layer, val, get = make(kind)
            try:
                layer.fill_rect(pf(1, 2), sf(2, 3), val)
            except Exception as e:
                fails.append(f"{kind} pos={pn} size={sn}: {type(e).__name__}: {e}")
                continue
            inside = get(layer, (1, 2))
            outside = get(layer, (0, 0))
            check(inside == val, f"{kind} pos={pn} size={sn}: inside {inside!r} != {val!r}")
            check(outside != val, f"{kind} pos={pn} size={sn}: outside was filled")
            check(get(layer, (2, 4)) == val, f"{kind} pos={pn} size={sn}: last cell not filled")
            check(get(layer, (3, 2)) != val, f"{kind} pos={pn} size={sn}: spilled past width")
    layer, val, _ = make(kind)
    for bad_pos, bad_size in (("ab", (1, 1)), ((0, 0), 3), ((0, 0, 0), (1, 1)), ((0, 0), None)):
        try:
            layer.fill_rect(bad_pos, bad_size, val)
            fails.append(f"{kind}: fill_rect({bad_pos!r}, {bad_size!r}) did not raise")
        except (TypeError, ValueError):
            pass

# Error messages name the argument that was bad, and the exception type is exact.
for kind in ("TileLayer", "ColorLayer"):
    layer, val, _ = make(kind)
    for name, exc, call in (
        ("size", ValueError, lambda: layer.fill_rect((0, 0), mcrfpy.Vector(float("nan"), 1), val)),
        ("size", TypeError, lambda: layer.fill_rect((0, 0), "ab", val)),
        ("size", TypeError, lambda: layer.fill_rect([0, 0], [1], val)),
        ("size", OverflowError, lambda: layer.fill_rect((0, 0), mcrfpy.Vector(1e30, 1), val)),
        ("size", OverflowError, lambda: layer.fill_rect((0, 0), (2**70, 1), val)),
        ("pos", ValueError, lambda: layer.fill_rect(mcrfpy.Vector(float("inf"), 0), (1, 1), val)),
        ("pos", TypeError, lambda: layer.fill_rect(None, (1, 1), val)),
        ("pos", OverflowError, lambda: layer.fill_rect((2**31, 0), (1, 1), val)),
    ):
        try:
            call()
            fails.append(f"{kind}: bad {name} did not raise")
        except Exception as e:
            check(type(e) is exc, f"{kind}: bad {name} raised {type(e).__name__}, want {exc.__name__}")
            check(str(e).startswith(name + ":"), f"{kind}: error for bad {name} is {e!r}")

for f in fails:
    print("FAIL:", f)
print("FAIL" if fails else "PASS")
sys.exit(1 if fails else 0)
