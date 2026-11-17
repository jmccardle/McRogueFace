"""Gate for tests/unit/utf8_decoder_test.cpp (#511): compile it, run it, exit with its status."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # --exec does not put it there
import _cpp_gate

sys.exit(_cpp_gate.run("utf8_decoder_test.cpp", defines=["MCRF_HEADLESS"]))
