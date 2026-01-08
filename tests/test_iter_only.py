#!/usr/bin/env python3
import sys
import mcrfpy
print("1 - Creating scene")
scene = mcrfpy.Scene("test")
print("2 - Getting children")
ui = scene.children
print("3 - Creating frame")
frame = mcrfpy.Frame(pos=(0,0), size=(50,50))
print("4 - Appending frame")
ui.append(frame)
print("5 - Starting iteration")
for item in ui:
    print(f"Item: {item}")
print("6 - Iteration done")
sys.exit(0)
