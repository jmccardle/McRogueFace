"""Test automation module with new position parsing and Vector returns"""
import mcrfpy
from mcrfpy import automation
import sys

# Track test results
passed = 0
failed = 0

def test(name, condition):
    global passed, failed
    if condition:
        print(f"  PASS: {name}")
        passed += 1
    else:
        print(f"  FAIL: {name}")
        failed += 1

print("Testing automation module updates...")
print()

# Test 1: position() returns Vector
print("1. Testing position() returns Vector...")
pos = automation.position()
test("position() returns Vector type", type(pos).__name__ == "Vector")
test("position has x attribute", hasattr(pos, 'x'))
test("position has y attribute", hasattr(pos, 'y'))
print()

# Test 2: size() returns Vector
print("2. Testing size() returns Vector...")
sz = automation.size()
test("size() returns Vector type", type(sz).__name__ == "Vector")
test("size has x attribute", hasattr(sz, 'x'))
test("size has y attribute", hasattr(sz, 'y'))
test("size.x > 0", sz.x > 0)
test("size.y > 0", sz.y > 0)
print()

# Test 3: onScreen() accepts various position formats
print("3. Testing onScreen() with various position formats...")
# Move mouse to a known position first
automation.moveTo((100, 100))
test("onScreen((100, 100)) with tuple", automation.onScreen((100, 100)) == True)
test("onScreen([50, 50]) with list", automation.onScreen([50, 50]) == True)
test("onScreen(mcrfpy.Vector(200, 200)) with Vector", automation.onScreen(mcrfpy.Vector(200, 200)) == True)
# Should be off-screen (negative)
test("onScreen((-10, -10)) returns False", automation.onScreen((-10, -10)) == False)
print()

# Test 4: moveTo() accepts position as grouped argument
print("4. Testing moveTo() with grouped position...")
automation.moveTo((150, 150))
pos = automation.position()
test("moveTo((150, 150)) moves to correct x", int(pos.x) == 150)
test("moveTo((150, 150)) moves to correct y", int(pos.y) == 150)

automation.moveTo([200, 200])
pos = automation.position()
test("moveTo([200, 200]) with list", int(pos.x) == 200 and int(pos.y) == 200)

automation.moveTo(mcrfpy.Vector(250, 250))
pos = automation.position()
test("moveTo(Vector(250, 250)) with Vector", int(pos.x) == 250 and int(pos.y) == 250)
print()

# Test 5: moveRel() accepts offset as grouped argument
print("5. Testing moveRel() with grouped offset...")
automation.moveTo((100, 100))  # Start position
automation.moveRel((50, 50))   # Relative move
pos = automation.position()
test("moveRel((50, 50)) from (100, 100)", int(pos.x) == 150 and int(pos.y) == 150)
print()

# Test 6: click() accepts optional position as grouped argument
print("6. Testing click() with grouped position...")
# Click at current position (no args should work)
try:
    automation.click()
    test("click() with no args (current position)", True)
except:
    test("click() with no args (current position)", False)

try:
    automation.click((200, 200))
    test("click((200, 200)) with tuple", True)
except:
    test("click((200, 200)) with tuple", False)

try:
    automation.click([300, 300], clicks=2)
    test("click([300, 300], clicks=2) with list", True)
except:
    test("click([300, 300], clicks=2) with list", False)
print()

# Test 7: scroll() accepts position as second grouped argument
print("7. Testing scroll() with grouped position...")
try:
    automation.scroll(3)  # No position - use current
    test("scroll(3) without position", True)
except:
    test("scroll(3) without position", False)

try:
    automation.scroll(3, (100, 100))
    test("scroll(3, (100, 100)) with tuple", True)
except:
    test("scroll(3, (100, 100)) with tuple", False)
print()

# Test 8: mouseDown/mouseUp with grouped position
print("8. Testing mouseDown/mouseUp with grouped position...")
try:
    automation.mouseDown((100, 100))
    automation.mouseUp((100, 100))
    test("mouseDown/mouseUp((100, 100)) with tuple", True)
except:
    test("mouseDown/mouseUp((100, 100)) with tuple", False)
print()

# Test 9: dragTo() with grouped position
print("9. Testing dragTo() with grouped position...")
automation.moveTo((100, 100))
try:
    automation.dragTo((200, 200))
    test("dragTo((200, 200)) with tuple", True)
except Exception as e:
    print(f"    Error: {e}")
    test("dragTo((200, 200)) with tuple", False)
print()

# Test 10: dragRel() with grouped offset
print("10. Testing dragRel() with grouped offset...")
automation.moveTo((100, 100))
try:
    automation.dragRel((50, 50))
    test("dragRel((50, 50)) with tuple", True)
except Exception as e:
    print(f"    Error: {e}")
    test("dragRel((50, 50)) with tuple", False)
print()

# Summary
print("=" * 40)
print(f"Results: {passed} passed, {failed} failed")
if failed == 0:
    print("All tests passed!")
    sys.exit(0)
else:
    print("Some tests failed")
    sys.exit(1)
