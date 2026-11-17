#!/usr/bin/env python3
"""
snippet_regions.py -- named regions inside a docs snippet (#541).

A snippet is one runnable file. A page of the docs site often shows only a FRAGMENT of
it (the function, not the scene around it). Rather than keep a second copy of the
fragment on the page -- which is how pages and samples drifted apart -- the snippet marks
the fragment, and the site injects exactly those lines:

    # region: shake
    def shake(frame, intensity=5):
        ...
    # endregion

Rules (all violations are errors, reported as file:line; nothing is skipped):

  * a marker is a whole line: optional indentation, `# region: NAME` or `# endregion`
  * NAME is [A-Za-z][A-Za-z0-9_-]*
  * regions do not nest: opening one while another is open is an error
  * a name appears once per file
  * every region is closed, and `# endregion` closes something
  * a region contains at least one line

The marker lines are comments, so the snippet still runs and stays copy-pasteable. The
injector strips them from published text (strip_markers).

Plain python3, standard library only. As a script it validates the files it is given:

    python3 tools/snippet_regions.py tests/snippets/076_effect_screen_shake.py
"""

import re
import sys
import textwrap

REGION_RE = re.compile(r"^\s*#\s*region\s*:\s*(.*?)\s*$")
ENDREGION_RE = re.compile(r"^\s*#\s*endregion\s*$")
# A line that looks like a marker but is not one of the two exact forms: an error, not
# silently ordinary text ("# region foo", "# end region", "#endregion foo").
NEAR_MISS_RE = re.compile(r"^\s*#\s*(region|end\s*region)\b", re.IGNORECASE)
NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")


class RegionError(Exception):
    """One or more region problems; .problems is a list of (line, message)."""

    def __init__(self, problems):
        self.problems = problems
        super().__init__("; ".join(f"line {n}: {m}" for n, m in problems))


def is_marker(line):
    stripped = line.rstrip("\n")
    return bool(REGION_RE.match(stripped) or ENDREGION_RE.match(stripped))


def parse(source):
    """Return {name: (first_body_line, last_body_line)}, 1-based inclusive.

    Raises RegionError listing every problem found."""
    regions = {}
    problems = []
    open_name = None
    open_line = None
    lines = source.splitlines()
    for i, line in enumerate(lines, start=1):
        m = REGION_RE.match(line)
        if m:
            name = m.group(1)
            if not NAME_RE.match(name):
                problems.append((i, f"bad region name {name!r} (want [A-Za-z][A-Za-z0-9_-]*)"))
                continue
            if open_name is not None:
                problems.append((i, f"region {name!r} opened inside region {open_name!r} "
                                    f"(opened line {open_line}); regions do not nest"))
                continue
            if name in regions:
                problems.append((i, f"duplicate region name {name!r}"))
                continue
            open_name, open_line = name, i
            continue
        if ENDREGION_RE.match(line):
            if open_name is None:
                problems.append((i, "# endregion with no open region"))
                continue
            if i - open_line - 1 < 1:
                problems.append((open_line, f"region {open_name!r} is empty"))
            regions[open_name] = (open_line + 1, i - 1)
            open_name = None
            continue
        if NEAR_MISS_RE.match(line):
            problems.append((i, "looks like a region marker but is not exactly "
                                "'# region: NAME' / '# endregion'"))
    if open_name is not None:
        problems.append((open_line, f"region {open_name!r} is never closed"))
    if problems:
        raise RegionError(sorted(problems))
    return regions


def strip_markers(text):
    """Remove region marker lines (and nothing else) from `text`."""
    keep = [l for l in text.splitlines(keepends=True)
            if not is_marker(l.rstrip("\r\n"))]
    return "".join(keep)


def region_text(source, name):
    """The dedented body of region `name`, marker lines excluded.

    KeyError (naming the regions that do exist) when there is no such region."""
    regions = parse(source)
    if name not in regions:
        have = ", ".join(sorted(regions)) or "none"
        raise KeyError(f"no region {name!r} (regions: {have})")
    first, last = regions[name]
    body = source.splitlines()[first - 1:last]
    return textwrap.dedent("\n".join(body)) + "\n"


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    bad = 0
    for path in argv:
        with open(path, encoding="utf-8") as f:
            src = f.read()
        try:
            regions = parse(src)
        except RegionError as e:
            bad += 1
            for n, msg in e.problems:
                print(f"{path}:{n}: {msg}")
            continue
        print(f"{path}: ok ({len(regions)} region(s): {', '.join(regions) or '-'})")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
