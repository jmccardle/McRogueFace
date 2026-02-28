"""Test Animation loop parameter.

Verifies that loop=True causes animations to cycle instead of completing.
"""
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


# --- Setup ---
scene = mcrfpy.Scene("test")
mcrfpy.current_scene = scene

# --- Test 1: Default loop=False, animation completes ---
sprite = mcrfpy.Sprite(pos=(0, 0))
scene.children.append(sprite)
anim = sprite.animate("x", 100.0, 1.0)
check("default loop is False", anim.is_looping == False)

# Step past duration
for _ in range(15):
    mcrfpy.step(0.1)

check("non-loop animation completes", anim.is_complete == True)


# --- Test 2: loop=True, animation does NOT complete ---
sprite2 = mcrfpy.Sprite(pos=(0, 0))
scene.children.append(sprite2)
anim2 = sprite2.animate("x", 100.0, 0.5, loop=True)
check("loop=True sets is_looping", anim2.is_looping == True)

# Step well past duration
for _ in range(20):
    mcrfpy.step(0.1)

check("looping animation never completes", anim2.is_complete == False)
check("looping animation has valid target", anim2.hasValidTarget() == True)


# --- Test 3: Sprite frame list with loop ---
sprite3 = mcrfpy.Sprite(pos=(0, 0))
scene.children.append(sprite3)
anim3 = sprite3.animate("sprite_index", [0, 1, 2, 3], 0.4, loop=True)
check("frame list loop is_looping", anim3.is_looping == True)

# Step through multiple cycles
for _ in range(20):
    mcrfpy.step(0.1)

check("frame list loop doesn't complete", anim3.is_complete == False)


# --- Test 4: Loop animation can be stopped ---
sprite4 = mcrfpy.Sprite(pos=(0, 0))
scene.children.append(sprite4)
anim4 = sprite4.animate("x", 200.0, 0.5, loop=True)

for _ in range(10):
    mcrfpy.step(0.1)

check("loop animation running before stop", anim4.is_complete == False)
anim4.stop()
check("loop animation stopped", anim4.is_complete == True)


# --- Test 5: Loop animation can be replaced ---
sprite5 = mcrfpy.Sprite(pos=(0, 0))
scene.children.append(sprite5)
anim5a = sprite5.animate("x", 100.0, 0.5, loop=True)

for _ in range(5):
    mcrfpy.step(0.1)

# Replace with non-looping
anim5b = sprite5.animate("x", 200.0, 0.5)
check("replacement anim is not looping", anim5b.is_looping == False)

for _ in range(10):
    mcrfpy.step(0.1)

check("replacement anim completes", anim5b.is_complete == True)


# --- Test 6: Animation object created with loop=True via constructor ---
anim6 = mcrfpy.Animation("x", 100.0, 1.0, loop=True)
check("Animation constructor loop=True", anim6.is_looping == True)

anim7 = mcrfpy.Animation("x", 100.0, 1.0)
check("Animation constructor default loop=False", anim7.is_looping == False)


# --- Summary ---
if PASS:
    print("PASS")
    sys.exit(0)
else:
    print("FAIL")
    sys.exit(1)
