#!/usr/bin/env python3
"""Standalone runner for the interactive procedural generation demo system.

Run with: ./mcrogueface ../tests/run_procgen_interactive.py

Or from the build directory:
    ./mcrogueface --exec ../tests/run_procgen_interactive.py
"""

import sys
import os

# Add the tests directory to path
tests_dir = os.path.dirname(os.path.abspath(__file__))
if tests_dir not in sys.path:
    sys.path.insert(0, tests_dir)

# Import and run the demo system
from procgen_interactive.main import main

main()
