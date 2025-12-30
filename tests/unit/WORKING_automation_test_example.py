#!/usr/bin/env python3
"""Example of CORRECT test pattern using timer callbacks for automation"""
import mcrfpy
from mcrfpy import automation
from datetime import datetime

def run_automation_tests():
    """This runs AFTER the game loop has started and rendered frames"""
    print("\n=== Automation Test Running (1 second after start) ===")
    
    # NOW we can take screenshots that will show content!
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"WORKING_screenshot_{timestamp}.png"
    
    # Take screenshot - this should now show our red frame
    result = automation.screenshot(filename)
    print(f"Screenshot taken: {filename} - Result: {result}")
    
    # Test clicking on the frame
    automation.click(200, 200)  # Click in center of red frame
    
    # Test keyboard input
    automation.typewrite("Hello from timer callback!")
    
    # Take another screenshot to show any changes
    filename2 = f"WORKING_screenshot_after_click_{timestamp}.png"
    automation.screenshot(filename2)
    print(f"Second screenshot: {filename2}")
    
    print("Test completed successfully!")
    print("\nThis works because:")
    print("1. The game loop has been running for 1 second")
    print("2. The scene has been rendered multiple times")
    print("3. The RenderTexture now contains actual rendered content")
    
    # Cancel this timer so it doesn't repeat
    mcrfpy.delTimer("automation_test")
    
    # Optional: exit after a moment
    def exit_game():
        print("Exiting...")
        mcrfpy.exit()
    mcrfpy.setTimer("exit", exit_game, 500)  # Exit 500ms later

# This code runs during --exec script execution
print("=== Setting Up Test Scene ===")

# Create scene with visible content
mcrfpy.createScene("timer_test_scene")
mcrfpy.setScene("timer_test_scene")
ui = mcrfpy.sceneUI("timer_test_scene")

# Add a bright red frame that should be visible
frame = mcrfpy.Frame(pos=(100, 100), size=(400, 300),
                    fill_color=mcrfpy.Color(255, 0, 0),      # Bright red
                    outline_color=mcrfpy.Color(255, 255, 255), # White outline
                    outline=5.0)
ui.append(frame)

# Add text
caption = mcrfpy.Caption(pos=(150, 150),
                        text="TIMER TEST - SHOULD BE VISIBLE",
                        fill_color=mcrfpy.Color(255, 255, 255))
caption.font_size = 24
frame.children.append(caption)

# Add click handler to demonstrate interaction
def frame_clicked(x, y, button):
    print(f"Frame clicked at ({x}, {y}) with button {button}")

frame.on_click = frame_clicked

print("Scene setup complete. Setting timer for automation tests...")

# THIS IS THE KEY: Set timer to run AFTER the game loop starts
mcrfpy.setTimer("automation_test", run_automation_tests, 1000)

print("Timer set. Game loop will start after this script completes.")
print("Automation tests will run 1 second later when content is visible.")

# Script ends here - game loop starts next