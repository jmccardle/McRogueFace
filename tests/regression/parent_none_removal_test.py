"""Test that setting .parent = None removes child from parent's children.

Verifies consistency between:
- Frame.children.remove(child)
- child.parent = None
- Entity.grid = None
"""
import mcrfpy
from mcrfpy import automation
import sys

PASS = True
results = []

def check(name, condition):
    global PASS
    if not condition:
        PASS = False
        results.append(f"  FAIL: {name}")
    else:
        results.append(f"  pass: {name}")

# ============================================================
# Test 1: child.parent = None removes from Frame.children
# ============================================================

scene = mcrfpy.Scene("test")
mcrfpy.current_scene = scene

box = mcrfpy.Frame(pos=(10,10), size=(200,200),
                    fill_color=mcrfpy.Color(40,40,40))
scene.children.append(box)

cap1 = mcrfpy.Caption(text="child1", pos=(5,5))
cap2 = mcrfpy.Caption(text="child2", pos=(5,25))
cap3 = mcrfpy.Caption(text="child3", pos=(5,45))
box.children.append(cap1)
box.children.append(cap2)
box.children.append(cap3)

check("1a: initial count is 3", len(box.children) == 3)
check("1b: cap2 parent is box", cap2.parent is not None)

# Remove via parent = None
cap2.parent = None
check("1c: count after cap2.parent=None is 2", len(box.children) == 2)
check("1d: cap2.parent is now None", cap2.parent is None)
check("1e: remaining children are cap1,cap3",
      box.children[0].text == "child1" and box.children[1].text == "child3")

# ============================================================
# Test 2: child.parent = None on Frame child (not Caption)
# ============================================================

inner = mcrfpy.Frame(pos=(10,100), size=(50,50),
                      fill_color=mcrfpy.Color(255,0,0))
box.children.append(inner)
check("2a: count after adding inner frame is 3", len(box.children) == 3)

inner.parent = None
check("2b: count after inner.parent=None is 2", len(box.children) == 2)
check("2c: inner.parent is None", inner.parent is None)

# ============================================================
# Test 3: child.parent = None on scene-level element
# ============================================================

top_frame = mcrfpy.Frame(pos=(300,10), size=(100,100),
                          fill_color=mcrfpy.Color(0,255,0))
scene.children.append(top_frame)
initial_scene_count = len(scene.children)
check("3a: top_frame added to scene", initial_scene_count >= 2)

top_frame.parent = None
check("3b: scene count decreased", len(scene.children) == initial_scene_count - 1)
check("3c: top_frame.parent is None", top_frame.parent is None)

# ============================================================
# Test 4: while-loop clearing via parent = None
# ============================================================

container = mcrfpy.Frame(pos=(10,10), size=(200,200))
scene.children.append(container)

for i in range(5):
    container.children.append(
        mcrfpy.Caption(text=f"item{i}", pos=(0, i*20)))
check("4a: container has 5 children", len(container.children) == 5)

# Clear by setting parent = None on each child
while len(container.children):
    container.children[0].parent = None
check("4b: container cleared via parent=None loop", len(container.children) == 0)

# ============================================================
# Test 5: Entity.grid = None removes from grid
# ============================================================

tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
grid = mcrfpy.Grid(grid_size=(10,10), texture=tex,
                    pos=(0,0), size=(200,200))
scene.children.append(grid)

e1 = mcrfpy.Entity(grid_pos=(1,1), texture=tex, sprite_index=0)
e2 = mcrfpy.Entity(grid_pos=(2,2), texture=tex, sprite_index=1)
e3 = mcrfpy.Entity(grid_pos=(3,3), texture=tex, sprite_index=2)
grid.entities.append(e1)
grid.entities.append(e2)
grid.entities.append(e3)

check("5a: grid has 3 entities", len(grid.entities) == 3)

e2.grid = None
check("5b: grid has 2 entities after e2.grid=None", len(grid.entities) == 2)
check("5c: e2.grid is None", e2.grid is None)

# ============================================================
# Test 6: Grid.children (overlay drawables) - parent = None
# ============================================================

overlay_cap = mcrfpy.Caption(text="overlay", pos=(5,5))
grid.children.append(overlay_cap)
check("6a: grid.children has 1 overlay", len(grid.children) == 1)

overlay_cap.parent = None
check("6b: grid.children empty after parent=None", len(grid.children) == 0)

# ============================================================
# Test 7: Visual verification with screenshots
# ============================================================

scene2 = mcrfpy.Scene("visual")
parent = mcrfpy.Frame(pos=(10,10), size=(400,300),
                       fill_color=mcrfpy.Color(40,40,40))
scene2.children.append(parent)

red = mcrfpy.Frame(pos=(10,10), size=(80,80),
                    fill_color=mcrfpy.Color(255,0,0))
green = mcrfpy.Frame(pos=(100,10), size=(80,80),
                      fill_color=mcrfpy.Color(0,255,0))
blue = mcrfpy.Frame(pos=(190,10), size=(80,80),
                     fill_color=mcrfpy.Color(0,0,255))

parent.children.append(red)
parent.children.append(green)
parent.children.append(blue)

mcrfpy.current_scene = scene2
mcrfpy.step(0.05)
automation.screenshot("parent_none_7a_before.png")

# Remove green via parent = None
green.parent = None
mcrfpy.step(0.05)
automation.screenshot("parent_none_7b_after.png")

check("7a: visual - green removed from children", len(parent.children) == 2)

# ============================================================
# Report
# ============================================================

print("=" * 50)
print("parent=None removal test results:")
for r in results:
    print(r)
print("=" * 50)
if PASS:
    print("PASS")
else:
    print("FAIL")
sys.exit(0 if PASS else 1)
