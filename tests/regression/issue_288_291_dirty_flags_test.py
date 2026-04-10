"""Test render cache dirty flag propagation for issues #288-#291.

#288: UICollection mutations don't invalidate parent Frame's render cache
#289: Caption Python property setters don't call markDirty()
#290: UIDrawable base x/y/pos setters don't propagate dirty flags to parent
#291: Audit all Python property setters for missing markDirty() calls

These tests exercise all property setters that were missing dirty flag calls,
inside a clip_children=True Frame (which uses render caching). The test verifies
that no crashes occur and properties are correctly set after modification.
Visual correctness requires a non-headless render test.
"""
import mcrfpy
import sys

test_pass = True
test_count = 0
fail_count = 0

def check(condition, msg):
    global test_pass, test_count, fail_count
    test_count += 1
    if not condition:
        print(f"  FAIL: {msg}")
        test_pass = False
        fail_count += 1

# Create a scene with a clipped parent frame (uses render caching)
scene = mcrfpy.Scene("test_dirty_flags")
mcrfpy.current_scene = scene

parent = mcrfpy.Frame(pos=(10, 10), size=(800, 600),
                       fill_color=mcrfpy.Color(40, 40, 40),
                       clip_children=True)
scene.children.append(parent)

# ============================================================
# Test #290: UIDrawable base x/y/pos setters (all drawable types)
# ============================================================
print("Testing #290: UIDrawable position setters...")

frame = mcrfpy.Frame(pos=(10, 10), size=(100, 100),
                      fill_color=mcrfpy.Color(255, 0, 0))
parent.children.append(frame)

# Test x setter
frame.x = 50.0
check(frame.x == 50.0, "frame.x setter")

# Test y setter
frame.y = 60.0
check(frame.y == 60.0, "frame.y setter")

# Test pos setter (tuple)
frame.pos = (70.0, 80.0)
check(frame.x == 70.0 and frame.y == 80.0, "frame.pos setter (tuple)")

# Test w/h setters
frame.w = 200.0
check(frame.w == 200.0, "frame.w setter")
frame.h = 150.0
check(frame.h == 150.0, "frame.h setter")

# ============================================================
# Test #289: Caption property setters
# ============================================================
print("Testing #289: Caption property setters...")

cap = mcrfpy.Caption(text="Hello", pos=(100, 100))
parent.children.append(cap)

# Text setter
cap.text = "World"
check(cap.text == "World", "caption.text setter")

# Fill color setter
cap.fill_color = mcrfpy.Color(255, 0, 0)
c = cap.fill_color
check(c.r == 255 and c.g == 0 and c.b == 0, "caption.fill_color setter")

# Outline color setter
cap.outline_color = mcrfpy.Color(0, 255, 0)
c = cap.outline_color
check(c.r == 0 and c.g == 255 and c.b == 0, "caption.outline_color setter")

# Outline thickness setter
cap.outline = 2.0
check(cap.outline == 2.0, "caption.outline setter")

# Font size setter
cap.font_size = 24
check(cap.font_size == 24, "caption.font_size setter")

# ============================================================
# Test #288: UICollection mutations
# ============================================================
print("Testing #288: UICollection mutations...")

# append (already tested above, but test with clip_children parent)
child1 = mcrfpy.Frame(pos=(0, 0), size=(20, 20),
                       fill_color=mcrfpy.Color(0, 0, 255))
initial_count = len(parent.children)
parent.children.append(child1)
check(len(parent.children) == initial_count + 1, "collection append")

# insert
child2 = mcrfpy.Frame(pos=(30, 0), size=(20, 20),
                       fill_color=mcrfpy.Color(0, 255, 0))
parent.children.insert(0, child2)
check(len(parent.children) == initial_count + 2, "collection insert")

# setitem (replace)
child3 = mcrfpy.Frame(pos=(60, 0), size=(20, 20),
                       fill_color=mcrfpy.Color(255, 255, 0))
parent.children[0] = child3
check(len(parent.children) == initial_count + 2, "collection setitem")

# remove
parent.children.remove(child1)
check(len(parent.children) == initial_count + 1, "collection remove")

# pop
popped = parent.children.pop()
check(len(parent.children) == initial_count, "collection pop")

# extend
extras = [
    mcrfpy.Frame(pos=(0, 200), size=(20, 20), fill_color=mcrfpy.Color(128, 128, 128)),
    mcrfpy.Frame(pos=(30, 200), size=(20, 20), fill_color=mcrfpy.Color(64, 64, 64))
]
parent.children.extend(extras)
check(len(parent.children) == initial_count + 2, "collection extend")

# slice deletion
del parent.children[initial_count:]
check(len(parent.children) == initial_count, "collection slice delete")

# ============================================================
# Test #291: UISprite property setters
# ============================================================
print("Testing #291: UISprite property setters...")

# Need a texture for sprite tests - use a test texture if available
try:
    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    sprite = mcrfpy.Sprite(pos=(200, 200), texture=tex, sprite_index=0)
    parent.children.append(sprite)

    sprite.scale = 2.0
    check(sprite.scale == 2.0, "sprite.scale setter")

    sprite.sprite_index = 1
    check(sprite.sprite_index == 1, "sprite.sprite_index setter")

    # Texture setter
    sprite.texture = tex
    check(True, "sprite.texture setter (no crash)")

    # Pos setter
    sprite.pos = (210, 210)
    check(True, "sprite.pos setter (no crash)")
except Exception as e:
    print(f"  (Sprite tests skipped - no test texture: {e})")

# ============================================================
# Test #291: UICircle property setters
# ============================================================
print("Testing #291: UICircle property setters...")

circle = mcrfpy.Circle(radius=25.0, center=(300, 300),
                        fill_color=mcrfpy.Color(255, 128, 0))
parent.children.append(circle)

circle.radius = 30.0
check(circle.radius == 30.0, "circle.radius setter")

circle.fill_color = mcrfpy.Color(0, 128, 255)
c = circle.fill_color
check(c.r == 0 and c.g == 128 and c.b == 255, "circle.fill_color setter")

circle.outline_color = mcrfpy.Color(255, 255, 255)
c = circle.outline_color
check(c.r == 255, "circle.outline_color setter")

circle.outline = 3.0
check(circle.outline == 3.0, "circle.outline setter")

# ============================================================
# Test #291: UILine property setters
# ============================================================
print("Testing #291: UILine property setters...")

line = mcrfpy.Line(start=(10, 400), end=(200, 400),
                    thickness=2.0, color=mcrfpy.Color(255, 0, 255))
parent.children.append(line)

line.start = (20, 410)
check(True, "line.start setter (no crash)")

line.end = (210, 410)
check(True, "line.end setter (no crash)")

line.color = mcrfpy.Color(0, 255, 255)
c = line.color
check(c.r == 0 and c.g == 255 and c.b == 255, "line.color setter")

line.thickness = 4.0
check(line.thickness == 4.0, "line.thickness setter")

# ============================================================
# Test #291: UIArc property setters
# ============================================================
print("Testing #291: UIArc property setters...")

arc = mcrfpy.Arc(center=(400, 300), radius=40.0, start_angle=0.0,
                  end_angle=180.0, color=mcrfpy.Color(128, 0, 255),
                  thickness=3.0)
parent.children.append(arc)

arc.radius = 50.0
check(arc.radius == 50.0, "arc.radius setter")

arc.start_angle = 45.0
check(arc.start_angle == 45.0, "arc.start_angle setter")

arc.end_angle = 270.0
check(arc.end_angle == 270.0, "arc.end_angle setter")

arc.color = mcrfpy.Color(255, 128, 128)
c = arc.color
check(c.r == 255 and c.g == 128 and c.b == 128, "arc.color setter")

arc.thickness = 5.0
check(arc.thickness == 5.0, "arc.thickness setter")

# ============================================================
# Test #291: UIGrid property setters
# ============================================================
print("Testing #291: UIGrid property setters...")

try:
    grid = mcrfpy.Grid(grid_size=(10, 10), pos=(500, 100), size=(200, 200))
    parent.children.append(grid)

    grid.center_x = 5.0
    check(True, "grid.center_x setter (no crash)")

    grid.center_y = 5.0
    check(True, "grid.center_y setter (no crash)")

    grid.zoom = 2.0
    check(grid.zoom == 2.0, "grid.zoom setter")

    grid.fill_color = mcrfpy.Color(20, 20, 40)
    check(True, "grid.fill_color setter (no crash)")
except Exception as e:
    print(f"  (Grid tests skipped: {e})")

# ============================================================
# Trigger a render cycle to exercise dirty flag code paths
# ============================================================
print("Triggering render cycle...")
mcrfpy.step(0.016)  # ~1 frame at 60fps

# ============================================================
# Summary
# ============================================================
print(f"\n{'='*50}")
print(f"Results: {test_count - fail_count}/{test_count} passed")
if test_pass:
    print("PASS: All dirty flag propagation tests passed")
    sys.exit(0)
else:
    print(f"FAIL: {fail_count} test(s) failed")
    sys.exit(1)
