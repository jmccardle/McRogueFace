"""
Regression test for issue #356.

mcrfpy's dynamic module attributes (current_scene, scenes, timers, ...) used to be a
PEP-562 module __getattr__. getattr/hasattr worked, but they were absent from
dir(mcrfpy) -- and every doc/stub/manifest generator discovers module symbols via
dir(), so the single most common idiom in the engine appeared in no generated docs.

They are now real getset descriptors on type(mcrfpy), plus a __dir__ override
(CPython's module.__dir__ reports only __dict__ keys, so descriptors alone are not
enough -- that is the trap this test exists to catch).
"""
import mcrfpy
import sys
import types

DYNAMIC = [
    "current_scene",
    "scenes",
    "timers",
    "animations",
    "default_transition",
    "default_transition_duration",
    "save_dir",
]
READONLY = ["scenes", "timers", "animations", "save_dir"]

failures = []


def check(label, condition):
    if condition:
        print(f"  PASS: {label}")
    else:
        print(f"  FAIL: {label}")
        failures.append(label)


print("1. All dynamic attributes are in dir(mcrfpy)")
names = dir(mcrfpy)
for attr in DYNAMIC:
    check(f"'{attr}' in dir(mcrfpy)", attr in names)

print("2. dir() still contains normal module symbols")
check("classes still listed", "Frame" in names and "Scene" in names)
check("functions still listed", "find" in names and "step" in names)

print("3. They are real descriptors carrying docstrings")
modtype = type(mcrfpy)
for attr in DYNAMIC:
    descr = getattr(modtype, attr, None)
    check(f"'{attr}' is a getset descriptor",
          isinstance(descr, types.GetSetDescriptorType))
    check(f"'{attr}' has a docstring", bool(descr and descr.__doc__))

print("4. Access still works (behavior preserved)")
scene = mcrfpy.Scene("issue356")
mcrfpy.current_scene = scene
check("current_scene round-trips", mcrfpy.current_scene is not None)
check("scenes is a tuple", isinstance(mcrfpy.scenes, tuple))
check("timers is a tuple", isinstance(mcrfpy.timers, tuple))
check("animations is a tuple", isinstance(mcrfpy.animations, tuple))
check("save_dir is a str", isinstance(mcrfpy.save_dir, str))
check("default_transition_duration is a float",
      isinstance(mcrfpy.default_transition_duration, float))

mcrfpy.default_transition_duration = 0.25
check("default_transition_duration is writable",
      abs(mcrfpy.default_transition_duration - 0.25) < 1e-6)

print("5. Read-only attributes still reject assignment")
for attr in READONLY:
    try:
        setattr(mcrfpy, attr, ())
        check(f"assigning '{attr}' raises AttributeError", False)
    except AttributeError:
        check(f"assigning '{attr}' raises AttributeError", True)

print("6. Validation preserved on the writable ones")
try:
    mcrfpy.default_transition_duration = -1.0
    check("negative duration raises ValueError", False)
except ValueError:
    check("negative duration raises ValueError", True)

try:
    mcrfpy.default_transition_duration = "not a number"
    check("non-numeric duration raises TypeError", False)
except TypeError:
    check("non-numeric duration raises TypeError", True)

print("7. Unknown attributes still raise AttributeError")
try:
    mcrfpy.definitely_not_an_attribute
    check("unknown attribute raises AttributeError", False)
except AttributeError:
    check("unknown attribute raises AttributeError", True)

print()
if failures:
    print(f"FAIL - {len(failures)} check(s) failed:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)

print("PASS")
sys.exit(0)
