# navigation_screenshot.py - Take screenshot of navigation demo
import mcrfpy
from mcrfpy import automation
import os

# Change to the correct directory for the demo
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Run the navigation demo
exec(open('navigation_demo.py').read())

# Take a screenshot after a brief delay
def take_shot(rt):
    automation.screenshot('../screenshots/navigation_demo.png')
    print('Screenshot saved!')
    mcrfpy.exit()

timer = mcrfpy.Timer('screenshot', take_shot, 500)
