#!/usr/bin/env python3
"""Test for automation click methods - Related to issue #78 (Middle click sends 'C')"""
import mcrfpy
from datetime import datetime

# Try to import automation, but handle if it doesn't exist
try:
    from mcrfpy import automation
    HAS_AUTOMATION = True
    print("SUCCESS: mcrfpy.automation module imported successfully")
except (ImportError, AttributeError) as e:
    HAS_AUTOMATION = False
    print(f"WARNING: mcrfpy.automation module not available - {e}")
    print("The automation module may not be implemented yet")

# Track events
click_events = []
key_events = []

def click_handler(x, y, button):
    """Track click events"""
    click_events.append((x, y, button))
    print(f"Click received: ({x}, {y}, button={button})")

def key_handler(key, scancode=None):
    """Track keyboard events"""
    key_events.append(key)
    print(f"Key received: {key} (scancode: {scancode})")

def test_clicks():
    """Test various click types, especially middle click (Issue #78)"""
    if not HAS_AUTOMATION:
        print("SKIP - automation module not available")
        print("The automation module may not be implemented yet")
        return
    
    # Create test scene
    mcrfpy.createScene("click_test")
    mcrfpy.setScene("click_test")
    ui = mcrfpy.sceneUI("click_test")
    
    # Set up keyboard handler to detect Issue #78
    mcrfpy.keypressScene(key_handler)
    
    # Create clickable frame
    frame = mcrfpy.Frame(50, 50, 300, 200,
                        fill_color=mcrfpy.Color(100, 100, 200),
                        outline_color=mcrfpy.Color(255, 255, 255),
                        outline=2.0)
    frame.click = click_handler
    ui.append(frame)
    
    caption = mcrfpy.Caption(mcrfpy.Vector(60, 60),
                            text="Click Test Area",
                            fill_color=mcrfpy.Color(255, 255, 255))
    frame.children.append(caption)
    
    # Test different click types
    print("Testing click types...")
    
    # Left click
    try:
        automation.click(200, 150)
        print("✓ Left click sent")
    except Exception as e:
        print(f"✗ Left click failed: {e}")
    
    # Right click
    try:
        automation.rightClick(200, 150)
        print("✓ Right click sent")
    except Exception as e:
        print(f"✗ Right click failed: {e}")
    
    # Middle click - This is Issue #78
    try:
        automation.middleClick(200, 150)
        print("✓ Middle click sent")
    except Exception as e:
        print(f"✗ Middle click failed: {e}")
    
    # Double click
    try:
        automation.doubleClick(200, 150)
        print("✓ Double click sent")
    except Exception as e:
        print(f"✗ Double click failed: {e}")
    
    # Triple click
    try:
        automation.tripleClick(200, 150)
        print("✓ Triple click sent")
    except Exception as e:
        print(f"✗ Triple click failed: {e}")
    
    # Click with specific button parameter
    try:
        automation.click(200, 150, button='middle')
        print("✓ Click with button='middle' sent")
    except Exception as e:
        print(f"✗ Click with button parameter failed: {e}")
    
    # Check results after a delay
    def check_results(runtime):
        print(f"\nClick events received: {len(click_events)}")
        print(f"Keyboard events received: {len(key_events)}")
        
        # Check for Issue #78
        if any('C' in str(event) or ord('C') == event for event in key_events):
            print("✗ ISSUE #78 CONFIRMED: Middle click sent 'C' keyboard event!")
        else:
            print("✓ No spurious 'C' keyboard events detected")
        
        # Analyze click events
        for event in click_events:
            print(f"  Click: {event}")
        
        # Take screenshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_clicks_issue78_{timestamp}.png"
        automation.screenshot(filename)
        print(f"Screenshot saved: {filename}")
        
        if len(click_events) > 0:
            print("PASS - Clicks detected")
        else:
            print("FAIL - No clicks detected (may be headless limitation)")
        
        mcrfpy.delTimer("check_results")
    
    mcrfpy.setTimer("check_results", check_results, 2000)

# Set up timer to run test
print("Setting up test timer...")
mcrfpy.setTimer("test", test_clicks, 1000)

# Cancel timer after running once
def cleanup():
    mcrfpy.delTimer("test")
    mcrfpy.delTimer("cleanup")
    
mcrfpy.setTimer("cleanup", cleanup, 1100)

# Exit after test completes
def exit_test():
    print("\nTest completed - exiting")
    import sys
    sys.exit(0)
    
mcrfpy.setTimer("exit", exit_test, 5000)

print("Test script initialized, waiting for timers...")