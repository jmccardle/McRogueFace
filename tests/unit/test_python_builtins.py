#!/usr/bin/env python3
"""Test Python builtins to diagnose the SystemError

Regression coverage for the embedded CPython interpreter: range/len/iteration
and the builtins table itself must behave exactly as they do in stock Python.
(Historically these raised SystemError inside McRogueFace's interpreter.)
"""

import sys

failures = []

def check(name, condition, detail=""):
    """Record and report a single check."""
    if condition:
        print("  [PASS]", name)
    else:
        print("  [FAIL]", name, "-", detail)
        failures.append(name)

def check_no_raise(name, fn, expected):
    """Call fn(); it must not raise, and must return `expected`."""
    try:
        actual = fn()
    except Exception as e:
        check(name, False, "raised %s: %s" % (type(e).__name__, e))
        return
    check(name, actual == expected, "got %r, expected %r" % (actual, expected))

print("Python version:", sys.version)
print("=" * 50)

# Test 1: Simple range
print("Test 1: Simple range(5)")
r = range(5)
check("range(5) is a range", type(r) is range, "type was %r" % (type(r),))
check_no_raise("iterate range(5)", lambda: [i for i in r], [0, 1, 2, 3, 4])

print()

# Test 2: Range with start/stop
print("Test 2: range(1, 5)")
check_no_raise("iterate range(1, 5)", lambda: list(range(1, 5)), [1, 2, 3, 4])

print()

# Test 3: Range in list comprehension
print("Test 3: List comprehension with range")
check_no_raise("[x for x in range(3)]", lambda: [x for x in range(3)], [0, 1, 2])

print()

# Test 4: Range in for loop (the failing case)
print("Test 4: for x in range(3):")
def _for_loop():
    out = []
    for x in range(3):
        out.append(x)
    return out
check_no_raise("for x in range(3)", _for_loop, [0, 1, 2])

print()

# Test 5: len() on list
print("Test 5: len() on list")
check_no_raise("len([1, 2, 3])", lambda: len([1, 2, 3]), 3)

print()

# Test 6: len() on tuple
print("Test 6: len() on tuple")
check_no_raise("len((1, 2, 3))", lambda: len((1, 2, 3)), 3)

print()

# Test 7: Nested function calls (reproducing the error context)
print("Test 7: Nested context like in the failing code")
def _walls():
    walls = []
    for x in range(1, 8):
        walls.append((x, 1))
    return walls
check_no_raise("build wall list via range + append", _walls,
               [(1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1)])

print()

# Test 8: Check if builtins are intact
print("Test 8: Builtin integrity check")
import builtins
check("range is builtins.range", range is builtins.range)
check("len is builtins.len", len is builtins.len)
check("type(range) is type", type(range) is type, "was %r" % (type(range),))
check("len is a builtin_function_or_method",
      type(len).__name__ == "builtin_function_or_method",
      "was %r" % (type(len).__name__,))

print()
if failures:
    print("FAIL: %d check(s) failed: %s" % (len(failures), ", ".join(failures)))
    sys.exit(1)

print("PASS")
sys.exit(0)
