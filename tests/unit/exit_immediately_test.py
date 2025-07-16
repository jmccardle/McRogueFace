#!/usr/bin/env python3
"""Test if calling mcrfpy.exit() prevents the >>> prompt"""
import mcrfpy

print("Calling mcrfpy.exit() immediately...")
mcrfpy.exit()
print("This should not print if exit worked")