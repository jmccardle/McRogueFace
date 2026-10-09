"""mcrfpy must refuse to load in any subinterpreter (Python 3.14+/3.15).

mcrfpy is backed by process-global engine state (the GameEngine, static
PyTypeObjects, PythonObjectCache), so a second interpreter importing it would
share -- and could corrupt -- the main interpreter's objects. Both the default
'isolated' config and the 'legacy' config must raise ImportError rather than
hand back a module.
"""
import sys
import mcrfpy

try:
    import _interpreters
except ImportError:
    print("SKIP: no _interpreters module")
    sys.exit(0)

PROBE = (
    "try:\n"
    "    import mcrfpy\n"
    "    result = 'imported'\n"
    "except ImportError as e:\n"
    "    result = 'ImportError: ' + str(e)\n"
)

failures = []
for config in ("isolated", "legacy"):
    try:
        interp = _interpreters.create(config)
    except Exception as e:  # e.g. legacy unsupported on this build
        print(f"  {config}: cannot create ({type(e).__name__}: {e}) -- skipped")
        continue
    try:
        # exec() returns None on success, or an excinfo snapshot if the
        # subinterpreter raised -- so assert inside it to report the outcome.
        excinfo = _interpreters.exec(interp,
            PROBE + "assert result != 'imported', result\n")
        if excinfo is not None:
            failures.append(f"{config}: subinterpreter imported mcrfpy ({excinfo.msg})")
        else:
            print(f"  {config}: import refused")
    finally:
        _interpreters.destroy(interp)

# The main interpreter's module must be unaffected
assert mcrfpy.Frame is not None

if failures:
    for f in failures:
        print("FAIL:", f)
    sys.exit(1)
print("PASS")
sys.exit(0)
