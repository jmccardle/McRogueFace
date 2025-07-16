#!/usr/bin/env python3
"""Force Python to be non-interactive"""
import sys
import os

print("Attempting to force non-interactive mode...")

# Remove ps1/ps2 if they exist
if hasattr(sys, 'ps1'):
    delattr(sys, 'ps1')
if hasattr(sys, 'ps2'):
    delattr(sys, 'ps2')

# Set environment variable
os.environ['PYTHONSTARTUP'] = ''

# Try to set stdin to non-interactive
try:
    import fcntl
    import termios
    # Make stdin non-interactive by removing ICANON flag
    attrs = termios.tcgetattr(0)
    attrs[3] = attrs[3] & ~termios.ICANON
    termios.tcsetattr(0, termios.TCSANOW, attrs)
    print("Modified terminal attributes")
except:
    print("Could not modify terminal attributes")

print("Script complete")