#!/usr/bin/env python3
import sys
import mcrfpy
print("1")
scene = mcrfpy.Scene("test")
print("2")
ui = scene.children
print("3")
print(f"children: {ui}")
print("4")
sys.exit(0)
