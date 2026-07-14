#!/usr/bin/env python3
"""
Issue #378: the embedded interpreter's filesystem encoding must be UTF-8.

init_python_with_config() -- the path main.cpp actually uses -- did no
pre-initialization at all, so PyPreConfig.utf8_mode was never enabled and the
filesystem encoding fell back to ASCII. sys.getdefaultencoding() said utf-8 and the
locale said UTF-8; only the filesystem encoding disagreed. (init_python(), the other
init path, had always set utf8_mode = 1 correctly.)

open() with no explicit encoding= defaults to the filesystem encoding, so it could not
read a UTF-8 file -- a degree sign was enough:

    UnicodeDecodeError: 'ascii' codec can't decode byte 0xc2 ...

In any normal CPython 3, open() defaults to UTF-8. This broke any script reading a data
file, a save file, or its own source.

NOT affected, despite the folklore that "--exec scripts must be ASCII-only": --exec on
a source file containing non-ASCII characters always worked. The C++ side reads the
file and hands the bytes to Python, which parses them as UTF-8 per PEP 3120. The
folklore was pointing at open(), via harnesses that read scripts themselves.

This file contains non-ASCII characters and reads itself back with a bare open(), so it
exercises both halves.
"""

import sys

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print(f"FAIL: {msg}")
    else:
        print(f"  ok: {msg}")


# Non-ASCII in a comment -- rotate the camera 90 degrees clockwise
# The characters that broke the docs snippets: degree, bullet
DEGREE = "\N{DEGREE SIGN}"
BULLET = "\N{BULLET}"


def test_filesystem_encoding():
    enc = sys.getfilesystemencoding()
    check(enc.lower().replace("-", "") == "utf8",
          f"sys.getfilesystemencoding() is utf-8 (got {enc!r})")
    check(sys.getdefaultencoding().lower().replace("-", "") == "utf8",
          "sys.getdefaultencoding() is utf-8")


def test_source_literals_survived_the_parse():
    """If the loader had used ASCII, this file would not have parsed at all."""
    check(DEGREE == "°", "a degree sign round-trips through the source")
    check(BULLET == "•", "a bullet round-trips through the source")


def test_open_defaults_to_utf8():
    """open() with no encoding= must read UTF-8, like any other Python 3."""
    path = __file__
    with open(path) as f:
        text = f.read()
    check("DEGREE SIGN" in text,
          "open() with no encoding= read this file back without a UnicodeDecodeError")


def main():
    test_filesystem_encoding()
    test_source_literals_survived_the_parse()
    test_open_defaults_to_utf8()

    if failures:
        print(f"\nFAILED ({len(failures)} checks)")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print("\nPASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
