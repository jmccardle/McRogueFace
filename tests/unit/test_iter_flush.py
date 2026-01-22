#!/usr/bin/env python3
import sys
import mcrfpy
print("1 - Creating scene", flush=True)
scene = mcrfpy.Scene("test")
print("2 - Getting children", flush=True)
ui = scene.children
print("3 - Creating frame", flush=True)
frame = mcrfpy.Frame(pos=(0,0), size=(50,50))
print("4 - Appending frame", flush=True)
ui.append(frame)
print("5 - Starting iteration", flush=True)
for item in ui:
    print(f"Item: {item}", flush=True)
print("6 - Iteration done", flush=True)
sys.exit(0)
