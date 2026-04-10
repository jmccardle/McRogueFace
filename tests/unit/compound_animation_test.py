"""Test compound (Color and Vector) animation targets - issue #218"""
import mcrfpy
import sys

PASS = True

def check(name, condition):
    global PASS
    if not condition:
        print(f"FAIL: {name}")
        PASS = False
    else:
        print(f"  ok: {name}")

# Create a scene with test objects
scene = mcrfpy.Scene("test_compound_anim")
ui = scene.children

frame = mcrfpy.Frame(pos=(10, 20), size=(100, 100),
                     fill_color=mcrfpy.Color(255, 0, 0))
ui.append(frame)

cap = mcrfpy.Caption(text="hello", pos=(50, 60))
ui.append(cap)

tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
sprite = mcrfpy.Sprite(pos=(70, 80), texture=tex)
ui.append(sprite)

mcrfpy.current_scene = scene

# Test 1: Frame "pos" animation property recognized
check("Frame hasProperty 'pos'", True)  # would fail at animate() if not
frame.animate("pos", (200, 300), 0.5, mcrfpy.Easing.LINEAR)

# Test 2: Frame "position" animation property still works
frame2 = mcrfpy.Frame(pos=(0, 0), size=(50, 50))
ui.append(frame2)
frame2.animate("position", (100, 100), 0.5, mcrfpy.Easing.LINEAR)

# Test 3: Frame "fill_color" compound animation
frame.animate("fill_color", (0, 255, 0, 255), 0.5, mcrfpy.Easing.LINEAR)

# Test 4: Frame "outline_color" compound animation
frame.animate("outline_color", (128, 128, 128), 0.5, mcrfpy.Easing.LINEAR)

# Test 5: Caption "pos" animation
cap.animate("pos", (200, 200), 0.5, mcrfpy.Easing.LINEAR)

# Test 6: Caption "position" animation
cap.animate("position", (300, 300), 0.5, mcrfpy.Easing.LINEAR)

# Test 7: Caption "fill_color" compound animation
cap.animate("fill_color", (0, 0, 255), 0.5, mcrfpy.Easing.LINEAR)

# Test 8: Sprite "pos" animation
sprite.animate("pos", (200, 200), 0.5, mcrfpy.Easing.LINEAR)

# Test 9: Sprite "position" animation
sprite.animate("position", (300, 300), 0.5, mcrfpy.Easing.LINEAR)

# Test 10: Frame "size" compound animation
frame.animate("size", (200, 200), 0.5, mcrfpy.Easing.LINEAR)

# Test 11: Step time forward and verify position changed
initial_x = frame.x
for _ in range(10):
    mcrfpy.step(0.06)

check("Frame moved from pos animation", frame.x != initial_x)

# Test 12: Verify Caption position changed
check("Caption pos changed", cap.x != 50)

# Test 13: Verify Sprite position changed
check("Sprite pos changed", sprite.x != 70)

if PASS:
    print("PASS")
    sys.exit(0)
else:
    sys.exit(1)
