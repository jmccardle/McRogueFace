"""#552 follow-ups: stable z sort, scenes that are not current, the auto z_index after removals / setter
changes / extend, every constructor's z_index, and `[i] = x` / slice assignment honouring a chosen z_index.
Order is asserted from the collection after a render; the non-current scene cases also check pixels."""
import os
import sys
import tempfile

import mcrfpy
from mcrfpy import automation

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # --exec does not
from _png import read_png  # noqa: E402

RED, BLUE = (255, 0, 0), (0, 0, 255)
fails = []
tmp = tempfile.mkdtemp(prefix="mcrf552r_")


def check(cond, msg):
    if not cond:
        fails.append(msg)


def render():
    mcrfpy.step(0)                     # step() never draws: a screenshot does, and that is what sorts
    automation.screenshot(os.path.join(tmp, "r.png"))


def names(coll):
    return [e.name for e in coll]


def fr(x=0, y=0, color=RED, **kw):
    return mcrfpy.Frame(pos=(x, y), size=(100, 100), fill_color=color, outline=0, **kw)


def pixel(path, x, y):
    w, h, ch, px = read_png(path)
    o = (y * w + x) * ch
    return tuple(px[o:o + 3])


# ---- 1. equal z_index siblings keep their insertion order through a render -----------------------
N = 200
s1 = mcrfpy.Scene("stable_scene")
for i in range(N):
    s1.children.append(fr(name=f"n{i}", z_index=1 + i % 3))   # three z levels, many equal
mcrfpy.current_scene = s1
render(); render()
want = sorted(range(N), key=lambda i: (1 + i % 3, i))
check(names(s1.children) == [f"n{i}" for i in want], "scene: equal-z children were reordered by the sort")
parent = fr(name="p")
for i in range(N):
    parent.children.append(fr(name=f"c{i}", z_index=1 + i % 3))
s1.children.append(parent)
render(); render()
check(names(parent.children) == [f"c{i}" for i in want], "frame: equal-z children were reordered by the sort")
g = mcrfpy.Grid(grid_size=(4, 4), texture=mcrfpy.default_texture, size=(100, 100))
for i in range(N):
    g.children.append(fr(name=f"g{i}", z_index=1 + i % 3))
s1.children.append(g)
render(); render()
check(names(g.children) == [f"g{i}" for i in want], "grid: equal-z children were reordered by the sort")

# ---- 2. a scene that is not current -----------------------------------------------------------
def non_current(label, build):
    a = mcrfpy.Scene("nc_a_" + label)
    b = mcrfpy.Scene("nc_b_" + label)
    a.children.append(fr(0, 0, RED))
    mcrfpy.current_scene = a
    render(); render()                       # A is drawn (and sorted) once
    mcrfpy.current_scene = b
    render()
    build(a.children)                        # B is current while A changes
    mcrfpy.current_scene = a
    render()
    path = os.path.join(tmp, label + ".png")
    automation.screenshot(path)
    return pixel(path, 60, 60)

def nc_append(ui):
    ui.append(fr(30, 30, BLUE, z_index=-1))
def nc_setter(ui):
    f = fr(30, 30, BLUE); ui.append(f); f.z_index = -1
def nc_extend(ui):
    ui.extend([fr(30, 30, BLUE, z_index=-1)])
def nc_insert(ui):
    ui.insert(1, fr(30, 30, BLUE, z_index=-1))
for label, build in (("append", nc_append), ("setter", nc_setter), ("extend", nc_extend), ("insert", nc_insert)):
    got = non_current(label, build)
    check(got == RED, f"non-current scene, {label}: overlap pixel {got}, want {RED} (the chosen z_index lost)")

# ---- 3. the automatic z_index is the highest + 10, after any change --------------------------
def auto_checks(ui, label, make):
    def add():
        f = make(); ui.append(f); return f
    a, b, c = add(), add(), add()
    check([a.z_index, b.z_index, c.z_index] == [0, 10, 20], f"{label}: first three {[a.z_index, b.z_index, c.z_index]}")
    ui.remove(c)
    d = add()
    check(d.z_index == 20, f"{label}: after removing the top, append gave {d.z_index}, want 20")
    b.z_index = 100
    e = add()
    check(e.z_index == 110, f"{label}: after a z setter raised the top, append gave {e.z_index}, want 110")
    f_, g_ = make(), make()
    ui.extend([f_, g_])
    check([f_.z_index, g_.z_index] == [120, 130], f"{label}: extend gave {[f_.z_index, g_.z_index]}, want [120, 130]")
    g_.z_index = 3
    h = add()
    check(h.z_index == 130, f"{label}: after lowering the top, append gave {h.z_index}, want 130")
    ui.remove(h); ui.remove(f_)
    b.z_index = 50
    e.z_index = 40
    i = add()
    check(i.z_index == 60, f"{label}: after removals and a setter, append gave {i.z_index}, want 60")
    x = make(); x.z_index = 500
    ui.append(x)
    y = add()
    check(y.z_index == 510, f"{label}: after an explicit append, auto gave {y.z_index}, want 510")
    ui[0] = fr(z_index=1000)               # replaced by a chosen z_index
    z = add()
    check(z.z_index == 1010, f"{label}: after an item replaced with z 1000, auto gave {z.z_index}, want 1010")
    while len(ui):
        ui.pop()
    w = add()
    check(w.z_index == 0, f"{label}: first append into an emptied collection gave {w.z_index}, want 0")

auto_checks(mcrfpy.Scene("auto_scene").children, "scene", fr)
auto_checks(fr().children, "frame", fr)
fa, fb = fr(), fr()
for i in range(20):                        # interleaved collections do not disturb each other's answer
    p, q = fr(), fr()
    fa.children.append(p); fb.children.append(q)
    fb.children.append(fr())
check([c.z_index for c in fa.children] == [10 * i for i in range(20)], "interleaved: first collection's z_index run")
check([c.z_index for c in fb.children] == [10 * i for i in range(40)], "interleaved: second collection's z_index run")
big = fr()
for i in range(2000):
    big.children.append(fr())
check(big.children[1999].z_index == 19990, "2000 appends: last auto z_index")

# ---- 4. every constructor honours z_index (keyword, and positional where there is a position) ----
tex = mcrfpy.default_texture
ctors = {
    "Frame": lambda **k: mcrfpy.Frame(**k),
    "Caption": lambda **k: mcrfpy.Caption(text="x", **k),
    "Sprite": lambda **k: mcrfpy.Sprite(texture=tex, **k),
    "Line": lambda **k: mcrfpy.Line(start=(0, 0), end=(5, 5), **k),
    "Circle": lambda **k: mcrfpy.Circle(radius=3, **k),
    "Arc": lambda **k: mcrfpy.Arc(radius=3, **k),
    "Grid": lambda **k: mcrfpy.Grid(grid_size=(2, 2), texture=tex, **k),
}
if hasattr(mcrfpy, "Viewport3D"):
    ctors["Viewport3D"] = lambda **k: mcrfpy.Viewport3D(**k)
for kind, make in ctors.items():
    ui = mcrfpy.Scene("ctor_" + kind).children
    ui.append(fr()); ui.append(fr())
    neg = make(z_index=-1)
    zero = make(z_index=0)
    plain = make()
    ui.append(neg); ui.append(zero); ui.append(plain)
    check(neg.z_index == -1, f"{kind}(z_index=-1) appended after two frames has z_index {neg.z_index}")
    check(zero.z_index == 0, f"{kind}(z_index=0) appended after two frames has z_index {zero.z_index}")
    check(plain.z_index == 20, f"{kind}() appended after a chosen z_index has {plain.z_index}, want 20")

# ---- 5. [i] = x and slice assignment ----------------------------------------------------------
def replace_checks(label, ui):
    for i in range(4):
        ui.append(fr(name=f"r{i}"))                       # z 0, 10, 20, 30
    x = fr(name="x", z_index=-7)
    ui[1] = x
    check(x.z_index == -7, f"{label}: [i] = x overwrote a chosen z_index with {x.z_index}")
    y = fr(name="y")
    ui[2] = y
    check(y.z_index == 20, f"{label}: [i] = y (no chosen z) took {y.z_index}, want the slot's 20")
    s1_, s2_ = fr(name="s1", z_index=-9), fr(name="s2")
    ui[0:2] = [s1_, s2_]
    check(s1_.z_index == -9, f"{label}: slice kept {s1_.z_index} for a chosen -9")
    check(s2_.z_index == -7, f"{label}: slice gave {s2_.z_index} to an unchosen item, want the slot's -7")
    render(); render()
    check([e.z_index for e in ui] == sorted(e.z_index for e in ui), f"{label}: not sorted after render {[e.z_index for e in ui]}")

sc = mcrfpy.Scene("repl_scene")
mcrfpy.current_scene = sc
replace_checks("scene", sc.children)
rp = fr(name="rp")
sc.children.append(rp)
replace_checks("frame", rp.children)

if fails:
    print("FAIL")
    for f in fails:
        print(" ", f)
    sys.exit(1)
print("PASS")
sys.exit(0)
