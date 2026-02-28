"""Test Entity.animate() with list of int frame indices.

Verifies that Entity supports sprite frame list animation,
including with loop=True.
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

# Create a grid with an entity
tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
grid = mcrfpy.Grid(grid_size=(10, 10), texture=tex, pos=(0, 0), size=(320, 320))
scene.children.append(grid)

entity = mcrfpy.Entity(grid_pos=(1, 1), texture=tex, sprite_index=0)
grid.entities.append(entity)


# --- Test 1: Entity.animate with list target ---
anim = entity.animate("sprite_index", [0, 1, 2, 3], 0.4)
check("entity animate with list returns Animation", anim is not None)
check("entity frame list anim has valid target", anim.hasValidTarget() == True)

# Step to complete
for _ in range(10):
    mcrfpy.step(0.1)

check("entity frame list anim completes", anim.is_complete == True)


# --- Test 2: Entity.animate with list + loop=True ---
entity2 = mcrfpy.Entity(grid_pos=(2, 2), texture=tex, sprite_index=0)
grid.entities.append(entity2)

anim2 = entity2.animate("sprite_index", [10, 11, 12, 13], 0.4, loop=True)
check("entity loop frame list is_looping", anim2.is_looping == True)

# Step well past duration
for _ in range(20):
    mcrfpy.step(0.1)

check("entity loop frame list doesn't complete", anim2.is_complete == False)

# The sprite_index should be one of the frame values
idx = entity2.sprite_index
check(f"entity sprite_index is valid frame ({idx})", idx in [10, 11, 12, 13])


# --- Test 3: Invalid list items raise TypeError ---
try:
    entity.animate("sprite_index", [1, 2, "bad", 4], 0.5)
    check("invalid list item raises TypeError", False)
except TypeError:
    check("invalid list item raises TypeError", True)


# --- Test 4: Entity.animate with int still works (no regression) ---
entity3 = mcrfpy.Entity(grid_pos=(3, 3), texture=tex, sprite_index=0)
grid.entities.append(entity3)

anim3 = entity3.animate("sprite_index", 5, 0.2)
check("entity animate with int still works", anim3 is not None)

for _ in range(5):
    mcrfpy.step(0.1)

check("entity int anim completes", anim3.is_complete == True)
check("entity sprite_index set to target", entity3.sprite_index == 5)


# --- Test 5: Entity.animate with float still works (no regression) ---
entity4 = mcrfpy.Entity(grid_pos=(4, 4), texture=tex, sprite_index=0)
grid.entities.append(entity4)

anim4 = entity4.animate("draw_x", 5.0, 0.3)
check("entity animate with float still works", anim4 is not None)

for _ in range(10):
    mcrfpy.step(0.1)

check("entity float anim completes", anim4.is_complete == True)


# --- Summary ---
if PASS:
    print("PASS")
    sys.exit(0)
else:
    print("FAIL")
    sys.exit(1)
