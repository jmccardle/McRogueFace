"""#540: BSP.split_once raises ValueError for a position outside the node's extent, before any
state changes. Both children must be non-empty, so the position is strictly inside the extent:
x < position < x + w (vertical, horizontal=False) and y < position < y + h (horizontal=True)."""
import sys
import mcrfpy

fails = []


def snapshot(b):
    return (len(b), [(n.pos, n.size) for n in b.leaves()])


def check(label, horizontal, pos, size, position, valid):
    b = mcrfpy.BSP(pos=pos, size=size)
    b.split_recursive(depth=1, min_size=(2, 2), seed=1)   # existing children to preserve
    before = snapshot(b)
    root_before = b.root
    try:
        r = b.split_once(horizontal, position)
    except ValueError as e:
        if valid:
            fails.append(f"{label}: valid position {position} raised {e}")
            return
        lo = pos[1] if horizontal else pos[0]
        ext = size[1] if horizontal else size[0]
        if f"{lo + 1}..{lo + ext - 1}" not in str(e):
            fails.append(f"{label}: message {e!r} does not name the valid range")
        if snapshot(b) != before:
            fails.append(f"{label}: rejected split changed the tree")
        try:
            root_before.left
        except Exception as e2:
            fails.append(f"{label}: rejected split invalidated node references: {e2}")
        return
    except BaseException as e:
        fails.append(f"{label}: raised {type(e).__name__}: {e}")
        return
    if not valid:
        fails.append(f"{label}: position {position} accepted")
        return
    if r is not b or len(b) != 2:
        fails.append(f"{label}: valid split gave {len(b)} leaves")
    for n in b.leaves():
        if n.size[0] < 1 or n.size[1] < 1:
            fails.append(f"{label}: empty child {n.pos} {n.size}")


for horizontal, name in ((False, "vertical"), (True, "horizontal")):
    for origin in ((0, 0), (7, 11), (-5, -9)):
        size = (20, 16)
        lo = origin[1] if horizontal else origin[0]
        ext = size[1] if horizontal else size[0]
        tag = f"{name} origin={origin}"
        for position, valid in ((lo - 1, False), (lo, False), (lo + 1, True),
                                (lo + ext // 2, True), (lo + ext - 1, True),
                                (lo + ext, False), (lo + ext + 1, False)):
            check(f"{tag} position={position}", horizontal, origin, size, position, valid)

for f in fails:
    print("FAIL:", f)
if fails:
    sys.exit(1)
print("PASS")
sys.exit(0)
