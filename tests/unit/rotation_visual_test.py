#!/usr/bin/env python3
"""Visual test for rotation support - uses direct screenshot"""
import mcrfpy
from mcrfpy import automation
import sys

# Create test scene
test_scene = mcrfpy.Scene("rotation_test")
ui = test_scene.children

# Create background
bg = mcrfpy.Frame(pos=(0, 0), size=(800, 600), fill_color=mcrfpy.Color(40, 40, 50))
ui.append(bg)

# Row 1: Frames with different rotations
# Frame at 0 degrees
frame1 = mcrfpy.Frame(pos=(100, 100), size=(60, 60), fill_color=mcrfpy.Color(200, 50, 50))
frame1.rotation = 0.0
frame1.origin = (30, 30)  # Center origin
ui.append(frame1)

# Frame at 45 degrees
frame2 = mcrfpy.Frame(pos=(250, 100), size=(60, 60), fill_color=mcrfpy.Color(50, 200, 50))
frame2.rotation = 45.0
frame2.origin = (30, 30)
ui.append(frame2)

# Frame at 90 degrees
frame3 = mcrfpy.Frame(pos=(400, 100), size=(60, 60), fill_color=mcrfpy.Color(50, 50, 200))
frame3.rotation = 90.0
frame3.origin = (30, 30)
ui.append(frame3)

# Label for row 1
label1 = mcrfpy.Caption(text="Frames: 0, 45, 90 degrees", pos=(100, 50))
ui.append(label1)

# Row 2: Captions with rotation
caption1 = mcrfpy.Caption(text="Rotated Text", pos=(100, 250))
caption1.rotation = 0.0
ui.append(caption1)

caption2 = mcrfpy.Caption(text="Rotated Text", pos=(300, 250))
caption2.rotation = -15.0
ui.append(caption2)

caption3 = mcrfpy.Caption(text="Rotated Text", pos=(500, 250))
caption3.rotation = 30.0
ui.append(caption3)

# Label for row 2
label2 = mcrfpy.Caption(text="Captions: 0, -15, 30 degrees", pos=(100, 200))
ui.append(label2)

# Row 3: Circles (rotation with offset origin causes orbiting)
circle1 = mcrfpy.Circle(center=(100, 400), radius=25, fill_color=mcrfpy.Color(200, 200, 50))
circle1.rotation = 0.0
ui.append(circle1)

circle2 = mcrfpy.Circle(center=(250, 400), radius=25, fill_color=mcrfpy.Color(200, 50, 200))
circle2.rotation = 45.0
circle2.origin = (20, 0)  # Offset origin to show orbiting effect
ui.append(circle2)

circle3 = mcrfpy.Circle(center=(400, 400), radius=25, fill_color=mcrfpy.Color(50, 200, 200))
circle3.rotation = 90.0
circle3.origin = (20, 0)  # Same offset
ui.append(circle3)

# Label for row 3
label3 = mcrfpy.Caption(text="Circles with offset origin: 0, 45, 90 degrees", pos=(100, 350))
ui.append(label3)

# Row 4: Lines with rotation
line1 = mcrfpy.Line(start=(100, 500), end=(150, 500), thickness=3, color=mcrfpy.Color(255, 255, 255))
line1.rotation = 0.0
ui.append(line1)

line2 = mcrfpy.Line(start=(250, 500), end=(300, 500), thickness=3, color=mcrfpy.Color(255, 200, 200))
line2.rotation = 45.0
line2.origin = (125, 500)  # Rotate around line center
ui.append(line2)

line3 = mcrfpy.Line(start=(400, 500), end=(450, 500), thickness=3, color=mcrfpy.Color(200, 255, 200))
line3.rotation = -45.0
line3.origin = (200, 500)
ui.append(line3)

# Label for row 4
label4 = mcrfpy.Caption(text="Lines: 0, 45, -45 degrees", pos=(100, 470))
ui.append(label4)

# Arcs with rotation
arc1 = mcrfpy.Arc(center=(600, 100), radius=40, start_angle=0, end_angle=90, thickness=5)
arc1.rotation = 0.0
ui.append(arc1)

arc2 = mcrfpy.Arc(center=(700, 100), radius=40, start_angle=0, end_angle=90, thickness=5)
arc2.rotation = 45.0
ui.append(arc2)

# Label for arcs
label5 = mcrfpy.Caption(text="Arcs: 0, 45 degrees", pos=(550, 50))
ui.append(label5)

# Activate scene
mcrfpy.current_scene = test_scene

# Advance the game loop to render, then take screenshot
mcrfpy.step(0.1)
automation.screenshot("rotation_visual_test.png")
print("Screenshot saved as rotation_visual_test.png")
print("PASS")
sys.exit(0)
