#!/usr/bin/env python3
"""Very simple callback test"""
import mcrfpy
import sys

def cb(a, t):
    print("CB")

test = mcrfpy.Scene("test")
test.activate() 
e = mcrfpy.Entity((0, 0), texture=None, sprite_index=0)
a = mcrfpy.Animation("x", 1.0, 0.1, "linear", callback=cb)
a.start(e)
mcrfpy.setTimer("exit", lambda r: sys.exit(0), 200)