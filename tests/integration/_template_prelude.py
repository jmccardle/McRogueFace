"""First --exec of a template run: put the template's directory on sys.path.

--exec does not do this (only scripts/game.py does, #452), and the templates
import their sibling modules. The directory comes from MCRF_TEMPLATE_DIR.
"""
import os
import sys

sys.path.insert(0, os.environ["MCRF_TEMPLATE_DIR"])
