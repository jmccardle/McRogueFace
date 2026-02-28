"""Test ping-pong easing functions.

Verifies that ping-pong easings oscillate (0 -> 1 -> 0) and that
complete()/stop() on ping-pong animations returns to the start value.
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


# --- Test 1: Ping-pong easing enum members exist ---
check("PING_PONG exists", hasattr(mcrfpy.Easing, "PING_PONG"))
check("PING_PONG_SMOOTH exists", hasattr(mcrfpy.Easing, "PING_PONG_SMOOTH"))
check("PING_PONG_EASE_IN exists", hasattr(mcrfpy.Easing, "PING_PONG_EASE_IN"))
check("PING_PONG_EASE_OUT exists", hasattr(mcrfpy.Easing, "PING_PONG_EASE_OUT"))
check("PING_PONG_EASE_IN_OUT exists", hasattr(mcrfpy.Easing, "PING_PONG_EASE_IN_OUT"))

# Check enum values are sequential from 31
check("PING_PONG value is 31", int(mcrfpy.Easing.PING_PONG) == 31)
check("PING_PONG_EASE_IN_OUT value is 35", int(mcrfpy.Easing.PING_PONG_EASE_IN_OUT) == 35)


# --- Test 2: Ping-pong animation reaches midpoint then returns ---
sprite = mcrfpy.Sprite(pos=(0, 0))
scene.children.append(sprite)
anim = sprite.animate("x", 100.0, 1.0, mcrfpy.Easing.PING_PONG)
check("ping-pong anim created", anim is not None)

# Step to midpoint (t=0.5)
for _ in range(5):
    mcrfpy.step(0.1)

midpoint_x = sprite.x
check(f"at midpoint x ({midpoint_x:.1f}) is near 100", midpoint_x > 80.0)

# Step to end (t=1.0)
for _ in range(5):
    mcrfpy.step(0.1)

final_x = sprite.x
check(f"at end x ({final_x:.1f}) returns near 0", final_x < 20.0)
check("ping-pong anim completes", anim.is_complete == True)


# --- Test 3: Ping-pong smooth animation oscillates ---
sprite2 = mcrfpy.Sprite(pos=(0, 0))
scene.children.append(sprite2)
anim2 = sprite2.animate("x", 200.0, 1.0, mcrfpy.Easing.PING_PONG_SMOOTH)

# Step to midpoint
for _ in range(5):
    mcrfpy.step(0.1)
mid_x2 = sprite2.x
check(f"smooth midpoint x ({mid_x2:.1f}) is near 200", mid_x2 > 150.0)

# Step to end
for _ in range(5):
    mcrfpy.step(0.1)
final_x2 = sprite2.x
check(f"smooth end x ({final_x2:.1f}) returns near 0", final_x2 < 20.0)


# --- Test 4: Ping-pong with loop=True cycles continuously ---
sprite3 = mcrfpy.Sprite(pos=(0, 0))
scene.children.append(sprite3)
anim3 = sprite3.animate("x", 100.0, 0.5, mcrfpy.Easing.PING_PONG, loop=True)
check("ping-pong loop is_looping", anim3.is_looping == True)

# Step through 2 full cycles
for _ in range(20):
    mcrfpy.step(0.1)

check("ping-pong loop doesn't complete", anim3.is_complete == False)
check("ping-pong loop has valid target", anim3.hasValidTarget() == True)


# --- Test 5: complete() on ping-pong returns to start value ---
sprite4 = mcrfpy.Sprite(pos=(50, 0))
scene.children.append(sprite4)
anim4 = sprite4.animate("x", 200.0, 1.0, mcrfpy.Easing.PING_PONG)

# Step partway through
for _ in range(3):
    mcrfpy.step(0.1)

# Now complete - should return to start (50), not go to target (200)
anim4.complete()
completed_x = sprite4.x
check(f"complete() returns to start ({completed_x:.1f})", abs(completed_x - 50.0) < 5.0)


# --- Test 6: stop() on ping-pong freezes at current value (no jump) ---
sprite5 = mcrfpy.Sprite(pos=(0, 0))
scene.children.append(sprite5)
anim5 = sprite5.animate("x", 100.0, 1.0, mcrfpy.Easing.PING_PONG_SMOOTH)

# Step to ~midpoint
for _ in range(5):
    mcrfpy.step(0.1)

pre_stop_x = sprite5.x
anim5.stop()

# Step more - value shouldn't change
for _ in range(5):
    mcrfpy.step(0.1)

post_stop_x = sprite5.x
check(f"stop() freezes value ({pre_stop_x:.1f} == {post_stop_x:.1f})",
      abs(pre_stop_x - post_stop_x) < 1.0)


# --- Test 7: Callback receives start value for ping-pong ---
callback_values = []
def on_complete(target, prop, value):
    callback_values.append(value)

sprite6 = mcrfpy.Sprite(pos=(10, 0))
scene.children.append(sprite6)
anim6 = sprite6.animate("x", 300.0, 0.5, mcrfpy.Easing.PING_PONG, callback=on_complete)

# Step to completion
for _ in range(10):
    mcrfpy.step(0.1)

check("callback was triggered", len(callback_values) == 1)
if callback_values:
    # Callback value should be near start value (10), not target (300)
    check(f"callback value ({callback_values[0]:.1f}) is near start (10)",
          abs(callback_values[0] - 10.0) < 5.0)


# --- Test 8: EaseInOut ping-pong (sin^2) is smooth at boundaries ---
sprite7 = mcrfpy.Sprite(pos=(0, 0))
scene.children.append(sprite7)
anim7 = sprite7.animate("x", 100.0, 1.0, mcrfpy.Easing.PING_PONG_EASE_IN_OUT)

# Capture values at several timesteps
values = []
for _ in range(10):
    mcrfpy.step(0.1)
    values.append(sprite7.x)

# First value should be small (accelerating from 0)
check(f"easeInOut starts slow ({values[0]:.1f} < 30)", values[0] < 30.0)
# Middle values should be larger
check(f"easeInOut peaks in middle ({max(values):.1f} > 70)", max(values) > 70.0)
# Last value should be near 0 again
check(f"easeInOut returns to start ({values[-1]:.1f} < 10)", values[-1] < 10.0)


# --- Test 9: Legacy string names work for ping-pong ---
sprite8 = mcrfpy.Sprite(pos=(0, 0))
scene.children.append(sprite8)
anim8 = sprite8.animate("x", 100.0, 0.5, "pingPong")
check("legacy string 'pingPong' works", anim8 is not None)

for _ in range(10):
    mcrfpy.step(0.1)
check("legacy string anim completes", anim8.is_complete == True)
check(f"legacy string returns to start ({sprite8.x:.1f})", abs(sprite8.x) < 5.0)


# --- Test 10: Standard easing complete() is unaffected (regression) ---
sprite9 = mcrfpy.Sprite(pos=(0, 0))
scene.children.append(sprite9)
anim9 = sprite9.animate("x", 500.0, 1.0, mcrfpy.Easing.EASE_IN_OUT)

# Step partway
for _ in range(3):
    mcrfpy.step(0.1)

anim9.complete()
check(f"standard easing complete() goes to target ({sprite9.x:.1f})",
      abs(sprite9.x - 500.0) < 5.0)


# --- Test 11: Animation constructor with ping-pong easing ---
anim10 = mcrfpy.Animation("x", 100.0, 1.0, mcrfpy.Easing.PING_PONG, loop=True)
check("Animation constructor with PING_PONG", anim10 is not None)
check("Animation constructor loop=True", anim10.is_looping == True)


# --- Summary ---
if PASS:
    print("PASS")
    sys.exit(0)
else:
    print("FAIL")
    sys.exit(1)
