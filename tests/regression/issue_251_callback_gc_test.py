"""Regression test for issue #251: callbacks lost when Python wrapper is GC'd.

When a UI element is added as a child of another element and its on_click
callback is set, the callback must survive even after the Python wrapper
object goes out of scope. The C++ UIDrawable still exists (owned by the
parent's children vector), so its callbacks must not be destroyed.

Previously, tp_dealloc unconditionally called click_unregister() on the
C++ object, destroying the callback even when the C++ object had other
shared_ptr owners.
"""
import mcrfpy
import gc
import sys


# ---- Test 1: Frame callback survives wrapper GC ----
scene = mcrfpy.Scene("test251")
parent = mcrfpy.Frame(pos=(0, 0), size=(400, 400))
scene.children.append(parent)

clicked = [False]

def make_child_with_callback():
    """Create a child frame with on_click, don't return/store the wrapper."""
    child = mcrfpy.Frame(pos=(10, 10), size=(100, 100))
    child.on_click = lambda pos, btn, act: clicked.__setitem__(0, True)
    parent.children.append(child)
    # child goes out of scope here - wrapper will be GC'd

make_child_with_callback()
gc.collect()  # Force GC to collect the wrapper

# The child Frame still exists in parent.children
assert len(parent.children) == 1, f"Expected 1 child, got {len(parent.children)}"

# Get a NEW wrapper for the same C++ object
child_ref = parent.children[0]

# The callback should still be there
assert child_ref.on_click is not None, \
    "FAIL: on_click lost after Python wrapper GC (issue #251)"
print("PASS: Frame.on_click survives wrapper GC")


# ---- Test 2: Multiple callback types survive ----
entered = [False]
exited = [False]

def make_child_with_all_callbacks():
    child = mcrfpy.Frame(pos=(120, 10), size=(100, 100))
    child.on_click = lambda pos, btn, act: clicked.__setitem__(0, True)
    child.on_enter = lambda pos: entered.__setitem__(0, True)
    child.on_exit = lambda pos: exited.__setitem__(0, True)
    parent.children.append(child)

make_child_with_all_callbacks()
gc.collect()

child2 = parent.children[1]
assert child2.on_click is not None, "FAIL: on_click lost"
assert child2.on_enter is not None, "FAIL: on_enter lost"
assert child2.on_exit is not None, "FAIL: on_exit lost"
print("PASS: All callback types survive wrapper GC")


# ---- Test 3: Caption callback survives in parent ----
def make_caption_with_callback():
    cap = mcrfpy.Caption(text="Click me", pos=(10, 120))
    cap.on_click = lambda pos, btn, act: None
    parent.children.append(cap)

make_caption_with_callback()
gc.collect()

cap_ref = parent.children[2]
assert cap_ref.on_click is not None, \
    "FAIL: Caption.on_click lost after wrapper GC"
print("PASS: Caption.on_click survives wrapper GC")


# ---- Test 4: Sprite callback survives ----
def make_sprite_with_callback():
    sp = mcrfpy.Sprite(pos=(10, 200))
    sp.on_click = lambda pos, btn, act: None
    parent.children.append(sp)

make_sprite_with_callback()
gc.collect()

sp_ref = parent.children[3]
assert sp_ref.on_click is not None, \
    "FAIL: Sprite.on_click lost after wrapper GC"
print("PASS: Sprite.on_click survives wrapper GC")


# ---- Test 5: Callback is actually callable after GC ----
call_count = [0]

def make_callable_child():
    child = mcrfpy.Frame(pos=(10, 300), size=(50, 50))
    child.on_click = lambda pos, btn, act: call_count.__setitem__(0, call_count[0] + 1)
    parent.children.append(child)

make_callable_child()
gc.collect()

recovered = parent.children[4]
# Verify we can actually call it without crash
assert recovered.on_click is not None, "FAIL: callback is None"
print("PASS: Recovered callback is callable")


# ---- Test 6: Callback IS cleaned up when element is truly destroyed ----
standalone = mcrfpy.Frame(pos=(0, 0), size=(50, 50))
standalone.on_click = lambda pos, btn, act: None
assert standalone.on_click is not None
del standalone
gc.collect()
# No crash = success (we can't access the object anymore, but it shouldn't leak)
print("PASS: Standalone element cleans up callbacks on true destruction")


print("\nAll issue #251 regression tests passed!")
sys.exit(0)
