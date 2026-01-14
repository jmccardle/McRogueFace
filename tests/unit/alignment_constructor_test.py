#!/usr/bin/env python3
"""Test alignment constructor arguments work correctly."""

import mcrfpy
import sys

# Test that alignment args work in constructors

print("Test 1: Frame with align constructor arg...")
parent = mcrfpy.Frame(pos=(0, 0), size=(400, 300))
child = mcrfpy.Frame(size=(100, 50), align=mcrfpy.Alignment.CENTER)
parent.children.append(child)
# Expected: (400-100)/2=150, (300-50)/2=125
if abs(child.x - 150) < 0.1 and abs(child.y - 125) < 0.1:
    print("  PASS: Frame align constructor arg works")
else:
    print(f"  FAIL: Expected (150, 125), got ({child.x}, {child.y})")
    sys.exit(1)

print("Test 2: Frame with align and margin constructor args...")
parent2 = mcrfpy.Frame(pos=(0, 0), size=(400, 300))
child2 = mcrfpy.Frame(size=(50, 50), align=mcrfpy.Alignment.TOP_LEFT, margin=10)
parent2.children.append(child2)
if abs(child2.x - 10) < 0.1 and abs(child2.y - 10) < 0.1:
    print("  PASS: Frame margin constructor arg works")
else:
    print(f"  FAIL: Expected (10, 10), got ({child2.x}, {child2.y})")
    sys.exit(1)

print("Test 3: Caption with align constructor arg...")
parent3 = mcrfpy.Frame(pos=(0, 0), size=(400, 300))
cap = mcrfpy.Caption(text="Test", align=mcrfpy.Alignment.TOP_CENTER, margin=20)
parent3.children.append(cap)
# Should be centered horizontally, 20px from top
if abs(cap.y - 20) < 0.1:
    print("  PASS: Caption align constructor arg works")
else:
    print(f"  FAIL: Expected y=20, got y={cap.y}")
    sys.exit(1)

print("Test 4: Sprite with align constructor arg...")
parent4 = mcrfpy.Frame(pos=(0, 0), size=(400, 300))
spr = mcrfpy.Sprite(align=mcrfpy.Alignment.BOTTOM_LEFT, margin=5)
parent4.children.append(spr)
if abs(spr.x - 5) < 0.1:
    print("  PASS: Sprite align constructor arg works")
else:
    print(f"  FAIL: Expected x=5, got x={spr.x}")
    sys.exit(1)

print("Test 5: Grid with align constructor arg...")
parent5 = mcrfpy.Frame(pos=(0, 0), size=(400, 300))
grid = mcrfpy.Grid(grid_size=(10, 10), size=(200, 200), align=mcrfpy.Alignment.CENTER_RIGHT, margin=15)
parent5.children.append(grid)
# Expected x: 400-200-15=185
if abs(grid.x - 185) < 0.1:
    print("  PASS: Grid align constructor arg works")
else:
    print(f"  FAIL: Expected x=185, got x={grid.x}")
    sys.exit(1)

print("Test 6: Line with align constructor arg...")
parent6 = mcrfpy.Frame(pos=(0, 0), size=(400, 300))
line = mcrfpy.Line(start=(0, 0), end=(50, 0), align=mcrfpy.Alignment.TOP_LEFT, margin=25)
parent6.children.append(line)
# Line's position (pos) should be at margin
if abs(line.pos.x - 25) < 0.1 and abs(line.pos.y - 25) < 0.1:
    print("  PASS: Line align constructor arg works")
else:
    print(f"  FAIL: Expected pos at (25, 25), got ({line.pos.x}, {line.pos.y})")
    sys.exit(1)

print("Test 7: Circle with align constructor arg...")
parent7 = mcrfpy.Frame(pos=(0, 0), size=(400, 300))
circ = mcrfpy.Circle(radius=30, align=mcrfpy.Alignment.CENTER)
parent7.children.append(circ)
# Circle is centered, center.x should be at parent center (400/2=200), center.y at (300/2=150)
if abs(circ.center.x - 200) < 0.1 and abs(circ.center.y - 150) < 0.1:
    print("  PASS: Circle align constructor arg works")
else:
    print(f"  FAIL: Expected center at (200, 150), got ({circ.center.x}, {circ.center.y})")
    sys.exit(1)

print("Test 8: Arc with align constructor arg...")
parent8 = mcrfpy.Frame(pos=(0, 0), size=(400, 300))
arc = mcrfpy.Arc(radius=40, align=mcrfpy.Alignment.BOTTOM_CENTER, vert_margin=10)
parent8.children.append(arc)
# Arc is BOTTOM_CENTER aligned with 10px vert_margin
# Arc bounds: width=2*radius=80, height=2*radius=80
# center.x should be 400/2=200 (centered)
# For bottom alignment: bottom of arc = 300-10 = 290, so center.y = 290 - 40 = 250
if abs(arc.center.x - 200) < 1.0 and abs(arc.center.y - 250) < 1.0:
    print("  PASS: Arc align constructor arg works")
else:
    print(f"  FAIL: Expected center at (200, 250), got ({arc.center.x}, {arc.center.y})")
    sys.exit(1)

print("Test 9: Testing horiz_margin and vert_margin separately...")
parent9 = mcrfpy.Frame(pos=(0, 0), size=(400, 300))
frame9 = mcrfpy.Frame(size=(100, 50), align=mcrfpy.Alignment.TOP_RIGHT, horiz_margin=30, vert_margin=20)
parent9.children.append(frame9)
# Expected: x = 400-100-30=270, y = 20
if abs(frame9.x - 270) < 0.1 and abs(frame9.y - 20) < 0.1:
    print("  PASS: horiz_margin and vert_margin constructor args work")
else:
    print(f"  FAIL: Expected (270, 20), got ({frame9.x}, {frame9.y})")
    sys.exit(1)

print("Test 10: Nested children with alignment in constructor list...")
outer = mcrfpy.Frame(
    pos=(100, 100),
    size=(400, 300),
    children=[
        mcrfpy.Frame(size=(200, 100), align=mcrfpy.Alignment.CENTER),
        mcrfpy.Caption(text="Title", align=mcrfpy.Alignment.TOP_CENTER, margin=10),
    ]
)
# Check inner frame is centered
inner = outer.children[0]
# (400-200)/2=100, (300-100)/2=100
if abs(inner.x - 100) < 0.1 and abs(inner.y - 100) < 0.1:
    print("  PASS: Nested children alignment works in constructor list")
else:
    print(f"  FAIL: Expected inner at (100, 100), got ({inner.x}, {inner.y})")
    sys.exit(1)

print()
print("=" * 50)
print("All alignment constructor tests PASSED!")
print("=" * 50)
sys.exit(0)
