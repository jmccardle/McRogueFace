#!/usr/bin/env python3
"""Trace interactive mode by monkey-patching"""
import sys
import mcrfpy

# Monkey-patch to detect interactive mode
original_ps1 = None
if hasattr(sys, 'ps1'):
    original_ps1 = sys.ps1
    
class PS1Detector:
    def __repr__(self):
        import traceback
        print("\n!!! sys.ps1 accessed! Stack trace:")
        traceback.print_stack()
        return ">>> "
        
# Set our detector
sys.ps1 = PS1Detector()

print("Trace script loaded, ps1 detector installed")

# Do nothing else - let the game run