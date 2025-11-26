#!/usr/bin/env python3
"""Test Grid.children collection - Issue #132"""
import mcrfpy
from mcrfpy import automation
import sys

def take_screenshot(runtime):
    """Take screenshot after render completes"""
    mcrfpy.delTimer("screenshot")
    automation.screenshot("test_grid_children_result.png")

    print("Screenshot saved to test_grid_children_result.png")
    print("PASS - Grid.children test completed")
    sys.exit(0)

def run_test(runtime):
    """Main test - runs after scene is set up"""
    mcrfpy.delTimer("test")

    # Get the scene UI
    ui = mcrfpy.sceneUI("test")

    # Create a grid without texture (uses default 16x16 cells)
    print("Test 1: Creating Grid with children...")
    grid = mcrfpy.Grid(grid_size=(20, 15), pos=(50, 50), size=(320, 240))
    grid.fill_color = mcrfpy.Color(30, 30, 60)
    ui.append(grid)

    # Verify entities and children properties exist
    print(f"  grid.entities = {grid.entities}")
    print(f"  grid.children = {grid.children}")

    # Test 2: Add UIDrawable children to the grid
    print("\nTest 2: Adding UIDrawable children...")

    # Speech bubble style caption - positioned in grid-world pixels
    # At cell (5, 3) which is 5*16=80, 3*16=48 in pixels
    caption = mcrfpy.Caption(text="Hello!", pos=(80, 48))
    caption.fill_color = mcrfpy.Color(255, 255, 200)
    caption.outline = 1
    caption.outline_color = mcrfpy.Color(0, 0, 0)
    grid.children.append(caption)
    print(f"  Added caption at (80, 48)")

    # A highlight circle around cell (10, 7) = (160, 112)
    # Circle needs center, not pos
    circle = mcrfpy.Circle(center=(168, 120), radius=20,
                           fill_color=mcrfpy.Color(255, 255, 0, 100),
                           outline_color=mcrfpy.Color(255, 255, 0),
                           outline=2)
    grid.children.append(circle)
    print(f"  Added highlight circle at (168, 120)")

    # A line indicating a path from (2,2) to (8,6)
    # In pixels: (32, 32) to (128, 96)
    line = mcrfpy.Line(start=(32, 32), end=(128, 96),
                       color=mcrfpy.Color(0, 255, 0), thickness=3)
    grid.children.append(line)
    print(f"  Added path line from (32,32) to (128,96)")

    # An arc for range indicator at (15, 10) = (240, 160)
    arc = mcrfpy.Arc(center=(240, 160), radius=40, start_angle=0, end_angle=270,
                     color=mcrfpy.Color(255, 0, 255), thickness=4)
    grid.children.append(arc)
    print(f"  Added range arc at (240, 160)")

    # Test 3: Verify children count
    print(f"\nTest 3: Verifying children count...")
    print(f"  grid.children count = {len(grid.children)}")
    assert len(grid.children) == 4, f"Expected 4 children, got {len(grid.children)}"

    # Test 4: Children should be accessible by index
    print("\nTest 4: Accessing children by index...")
    child0 = grid.children[0]
    print(f"  grid.children[0] = {child0}")
    child1 = grid.children[1]
    print(f"  grid.children[1] = {child1}")

    # Test 5: Modify a child's position (should update in grid)
    print("\nTest 5: Modifying child position...")
    original_pos = (caption.pos.x, caption.pos.y)
    caption.pos = mcrfpy.Vector(90, 58)
    new_pos = (caption.pos.x, caption.pos.y)
    print(f"  Moved caption from {original_pos} to {new_pos}")

    # Test 6: Test z_index for children
    print("\nTest 6: Testing z_index ordering...")
    # Add overlapping elements with different z_index
    frame1 = mcrfpy.Frame(pos=(150, 80), size=(40, 40))
    frame1.fill_color = mcrfpy.Color(255, 0, 0, 200)
    frame1.z_index = 10
    grid.children.append(frame1)

    frame2 = mcrfpy.Frame(pos=(160, 90), size=(40, 40))
    frame2.fill_color = mcrfpy.Color(0, 255, 0, 200)
    frame2.z_index = 5  # Lower z_index, rendered first (behind)
    grid.children.append(frame2)
    print(f"  Added overlapping frames: red z=10, green z=5")

    # Test 7: Test visibility
    print("\nTest 7: Testing child visibility...")
    frame3 = mcrfpy.Frame(pos=(50, 150), size=(30, 30))
    frame3.fill_color = mcrfpy.Color(0, 0, 255)
    frame3.visible = False
    grid.children.append(frame3)
    print(f"  Added invisible blue frame (should not appear)")

    # Test 8: Pan the grid and verify children move with it
    print("\nTest 8: Testing pan (children should follow grid camera)...")
    # Center the view on cell (10, 7.5) - default was grid center
    grid.center = (160, 120)  # Center on pixel (160, 120)
    print(f"  Centered grid on (160, 120)")

    # Test 9: Test zoom
    print("\nTest 9: Testing zoom...")
    grid.zoom = 1.5
    print(f"  Set zoom to 1.5")

    print(f"\nFinal children count: {len(grid.children)}")

    # Schedule screenshot for next frame
    mcrfpy.setTimer("screenshot", take_screenshot, 100)

# Create a test scene
mcrfpy.createScene("test")
mcrfpy.setScene("test")

# Schedule test to run after game loop starts
mcrfpy.setTimer("test", run_test, 50)
