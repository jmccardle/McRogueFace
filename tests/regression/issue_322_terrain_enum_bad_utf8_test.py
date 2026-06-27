"""
Regression test for issue #322 -- WangSet.terrain_enum pending-error abort.

terrain_enum() builds a Python IntEnum from parsed Wang color names but did not
check the return of PyDict_SetItemString / PyUnicode_FromString. A name carrying
invalid UTF-8 (trivially reachable from an untrusted .tsx import) makes those
calls fail and leave an exception pending; the code then called PyObject_Call
with that error set, tripping CPython's "_PyErr_Occurred" assertion / abort.

The fix checks every C-API return and propagates the real exception instead.
This test crafts a .tsx whose wangset and wangcolor names contain raw 0xFF/0xFE
bytes (rapidxml passes attribute bytes through verbatim), loads it, and asserts
terrain_enum() raises a clean catchable exception rather than aborting.

ASCII-only source. Prints PASS/FAIL and sys.exit(0/1).
"""

import mcrfpy
import sys
import os

failures = []


def check(label, cond):
    if not cond:
        failures.append(label)
    print(("  ok  " if cond else " FAIL ") + label)


TMP = os.environ.get("TMPDIR", "/tmp")
path = os.path.join(TMP, "issue_322_badwang_%d.tsx" % os.getpid())

# Well-formed XML; the wangset/wangcolor name attributes carry invalid UTF-8.
xml = (
    b'<?xml version="1.0" encoding="UTF-8"?>\n'
    b'<tileset version="1.10" tiledversion="1.10.2" name="t" '
    b'tilewidth="16" tileheight="16" tilecount="4" columns="2">\n'
    b' <image source="x.png" width="32" height="32"/>\n'
    b' <wangsets>\n'
    b'  <wangset name="ws_\xff\xfe" type="corner" tile="-1">\n'
    b'   <wangcolor name="C_\xff\xfe" color="#ff0000" tile="-1" probability="1"/>\n'
    b'  </wangset>\n'
    b' </wangsets>\n'
    b'</tileset>\n'
)
with open(path, "wb") as fh:
    fh.write(xml)

try:
    ts = mcrfpy.TileSetFile(path)
    sets = list(ts.wang_sets)
    check("malformed-name tileset loads and exposes its wangset", len(sets) >= 1)

    handled = 0
    for ws in sets:
        try:
            ws.terrain_enum()
            # A clean enum is acceptable too (some platforms may decode the
            # bytes); the bug was the abort, not the specific outcome.
            handled += 1
            check("terrain_enum() returned without crashing", True)
        except UnicodeDecodeError:
            handled += 1
            check("terrain_enum() raises a clean UnicodeDecodeError (no abort)", True)
        except (ValueError, TypeError) as e:
            handled += 1
            check("terrain_enum() raises clean %s (no abort)" % type(e).__name__, True)
        except SystemError as e:
            # "<built-in> returned a result with an exception set" is exactly the
            # pre-fix symptom of calling Python with a pending error.
            check("terrain_enum() leaked a pending error (SystemError): %s" % e, False)
    check("processed at least one wangset without process abort", handled >= 1)
finally:
    try:
        os.unlink(path)
    except OSError:
        pass


print("")
if failures:
    print("FAIL -- %d check(s) failed:" % len(failures))
    for f in failures:
        print("  - " + f)
    sys.exit(1)
print("PASS -- terrain_enum surfaces a clean exception for invalid-UTF-8 names.")
sys.exit(0)
