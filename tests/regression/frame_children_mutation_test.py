"""Test Frame.children mutation behaviors reported as potential bugs.

Three failure modes reported:
1. remove() on child doesn't visually update
2. Property mutation on stored references doesn't render
3. Clearing children via while-loop doesn't work

This test validates the data model. Visual screenshots require
a timer-based approach with mcrfpy.step() in headless mode.
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
# Test 1: remove() actually modifies the children collection
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

check("1a: initial children count is 3", len(box.children) == 3)

# Remove middle child
box.children.remove(cap2)
check("1b: children count after remove is 2", len(box.children) == 2)
check("1c: first child is still cap1", box.children[0].text == "child1")
check("1d: second child is now cap3", box.children[1].text == "child3")

# ============================================================
# Test 2: Property mutation on stored references
# ============================================================

stored_ref = box.children[0]
check("2a: stored ref text matches", stored_ref.text == "child1")
stored_ref.text = "MUTATED"
check("2b: mutation via stored ref visible via children[0]",
      box.children[0].text == "MUTATED")

# Verify identity: stored ref should point to same C++ object
check("2c: stored ref identity (same text after re-read)",
      stored_ref.text == box.children[0].text)

# ============================================================
# Test 3: fill_color mutation on child persists
# ============================================================

cap_direct = box.children[1]
original_color = cap_direct.fill_color
cap_direct.fill_color = mcrfpy.Color(255, 0, 0, 255)
reread_color = box.children[1].fill_color
check("3a: fill_color mutation persists (r)",
      reread_color.r == 255)
check("3b: fill_color mutation persists (g)",
      reread_color.g == 0)

# ============================================================
# Test 4: Mutation via iteration
# ============================================================

for child in box.children:
    child.text = "ITER_" + child.text

check("4a: mutation via iteration on child 0",
      box.children[0].text == "ITER_MUTATED")
check("4b: mutation via iteration on child 1",
      box.children[1].text == "ITER_child3")

# ============================================================
# Test 5: pop() works
# ============================================================

popped = box.children.pop()
check("5a: pop() reduces count", len(box.children) == 1)
check("5b: popped element has correct text", popped.text == "ITER_child3")

# ============================================================
# Test 6: while-loop clearing
# ============================================================

box.children.append(mcrfpy.Caption(text="a", pos=(0,0)))
box.children.append(mcrfpy.Caption(text="b", pos=(0,0)))
box.children.append(mcrfpy.Caption(text="c", pos=(0,0)))
check("6a: re-added children", len(box.children) == 4)

while len(box.children):
    box.children.pop()
check("6b: while-loop clearing empties children", len(box.children) == 0)

# ============================================================
# Test 7: Visual rendering via screenshots
# ============================================================

scene2 = mcrfpy.Scene("visual")
parent = mcrfpy.Frame(pos=(10,10), size=(400,300),
                       fill_color=mcrfpy.Color(40,40,40))
scene2.children.append(parent)

red_box = mcrfpy.Frame(pos=(10,10), size=(80,80),
                        fill_color=mcrfpy.Color(255,0,0))
green_box = mcrfpy.Frame(pos=(100,10), size=(80,80),
                          fill_color=mcrfpy.Color(0,255,0))
blue_box = mcrfpy.Frame(pos=(190,10), size=(80,80),
                         fill_color=mcrfpy.Color(0,0,255))

parent.children.append(red_box)
parent.children.append(green_box)
parent.children.append(blue_box)

mcrfpy.current_scene = scene2

# Render a frame, take screenshot with all 3
mcrfpy.step(0.05)
automation.screenshot("frame_children_7a_all3.png")

# Remove green box
parent.children.remove(green_box)
check("7a: remove green_box reduces count to 2", len(parent.children) == 2)

mcrfpy.step(0.05)
automation.screenshot("frame_children_7b_no_green.png")

# Mutate red to yellow via stored reference
red_box.fill_color = mcrfpy.Color(255, 255, 0)
mcrfpy.step(0.05)
automation.screenshot("frame_children_7c_yellow.png")

# Mutate via indexed access
parent.children[0].fill_color = mcrfpy.Color(255, 0, 255)  # magenta
mcrfpy.step(0.05)
automation.screenshot("frame_children_7d_magenta.png")

# Clear all
while len(parent.children):
    parent.children.pop()
check("7b: all children cleared", len(parent.children) == 0)

mcrfpy.step(0.05)
automation.screenshot("frame_children_7e_cleared.png")

# ============================================================
# Report
# ============================================================

print("=" * 50)
print("Frame.children mutation test results:")
for r in results:
    print(r)
print("=" * 50)
if PASS:
    print("PASS")
else:
    print("FAIL")
sys.exit(0 if PASS else 1)
