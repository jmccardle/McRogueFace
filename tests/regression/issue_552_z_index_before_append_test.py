"""#552: a z_index chosen before a drawable is appended (setter or constructor argument) is kept by
append / extend / insert, and a z_index change re-sorts a Frame's children as it does a scene's.

Every case draws two overlapping 100x100 frames, A (red, first) and B (blue, second, offset by 30, 30),
into its own cell of one scene; the pixel in the overlap says which one is on top. The expectation for
each case is the colour that must be there. This is a rendering test: the pixels are what is asserted."""
import os
import sys
import tempfile

import mcrfpy
from mcrfpy import automation

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # --exec does not
from _png import read_png  # noqa: E402

RED, BLUE = (255, 0, 0), (0, 0, 255)
fails = []


scene = mcrfpy.Scene("z552")
ui = scene.children
cases = []   # (label, (x, y) of the overlap, expected colour)


def cell():
    i = len(cases)
    return 20 + (i % 6) * 165, 20 + (i // 6) * 165


def fr(x, y, color, **kw):
    return mcrfpy.Frame(pos=(x, y), size=(100, 100), fill_color=color, outline=0, **kw)


def pair(label, expect, build):
    ox, oy = cell()
    build(ox, oy)
    cases.append((label, (ox + 60, oy + 60), expect))


def c_setter_before_append(ox, oy):
    a, b = fr(ox, oy, RED), fr(ox + 30, oy + 30, BLUE)
    b.z_index = -1
    ui.append(a); ui.append(b)

def c_kwarg(ox, oy):
    a, b = fr(ox, oy, RED), fr(ox + 30, oy + 30, BLUE, z_index=-1)
    ui.append(a); ui.append(b)

def c_default_order(ox, oy):
    ui.append(fr(ox, oy, RED)); ui.append(fr(ox + 30, oy + 30, BLUE))

def c_setter_after_append(ox, oy):
    a, b = fr(ox, oy, RED), fr(ox + 30, oy + 30, BLUE)
    ui.append(a); ui.append(b)
    b.z_index = -1

def c_explicit_zero(ox, oy):
    a, b = fr(ox, oy, RED), fr(ox + 30, oy + 30, BLUE, z_index=0)
    a.z_index = 5
    ui.append(a); ui.append(b)

def c_insert(ox, oy):
    a, b = fr(ox, oy, RED), fr(ox + 30, oy + 30, BLUE)
    b.z_index = -1
    ui.append(a); ui.insert(len(ui), b)

def c_extend(ox, oy):
    a, b = fr(ox, oy, RED), fr(ox + 30, oy + 30, BLUE)
    b.z_index = -1
    ui.extend([a, b])

def c_extend_mixed(ox, oy):
    # a default-z item after an explicit one still goes on top of it
    a, b = fr(ox, oy, RED, z_index=50), fr(ox + 30, oy + 30, BLUE)
    ui.extend([a, b])

def frame_children(setter_first):
    def build(ox, oy):
        parent = mcrfpy.Frame(pos=(ox, oy), size=(200, 200), fill_color=(0, 0, 0, 0), outline=0)
        a, b = fr(0, 0, RED), fr(30, 30, BLUE)
        if setter_first:
            b.z_index = -1
        parent.children.append(a); parent.children.append(b)
        if not setter_first:
            b.z_index = -1
        ui.append(parent)
    return build

def c_frame_kwarg(ox, oy):
    parent = mcrfpy.Frame(pos=(ox, oy), size=(200, 200), fill_color=(0, 0, 0, 0), outline=0)
    parent.children.extend([fr(0, 0, RED), fr(30, 30, BLUE, z_index=-1)])
    ui.append(parent)

pair("scene: z_index set before append", RED, c_setter_before_append)
pair("scene: z_index constructor argument", RED, c_kwarg)
pair("scene: no z_index, insertion order", BLUE, c_default_order)
pair("scene: z_index set after append", RED, c_setter_after_append)
pair("scene: explicit z_index=0 below an explicit 5", RED, c_explicit_zero)
pair("scene: insert keeps the z_index", RED, c_insert)
pair("scene: extend keeps the z_index", RED, c_extend)
pair("scene: extend, default after explicit goes on top", BLUE, c_extend_mixed)
pair("frame children: z_index set before append", RED, frame_children(True))
pair("frame children: z_index set after append", RED, frame_children(False))
pair("frame children: extend with a constructor z_index", RED, c_frame_kwarg)

mcrfpy.current_scene = scene
mcrfpy.step(0)
path = os.path.join(tempfile.mkdtemp(prefix="mcrf552_"), "shot.png")
automation.screenshot(path)
width, height, ch, px = read_png(path)
for label, (x, y), want in cases:
    o = (y * width + x) * ch
    got = tuple(px[o:o + 3])
    if got != want:
        fails.append(f"{label}: pixel at ({x}, {y}) is {got}, want {want}")

if fails:
    print("FAIL")
    for f in fails:
        print(" ", f)
    sys.exit(1)
print("PASS")
sys.exit(0)
