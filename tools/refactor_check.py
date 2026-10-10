#!/usr/bin/env python3
"""
refactor_check.py - fast per-edit check for binding-lint migrations (#430).

    .venv-audit/bin/python3 tools/refactor_check.py src/UIArc.cpp \
        --site "from-arg-owner|src/UIArc.cpp|UIArc::set_center|vec = PyVector::from_arg(...) never released"

1. Compiles FILE alone with -fsyntax-only, using its flags from
   build/compile_commands.json (`cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=ON` in build/).
   Writes nothing, so parallel agents never contend for the build directory.
   A header is checked through every .cpp in the database that includes it.
2. Lints FILE and reports:
     - whether the target --site key is gone (pass the key exactly as the baseline
       or `lint_bindings.py --json` prints it, without the leading count);
     - any finding in FILE beyond what the baseline allows (a regression).

Exit 0 only if all of it holds. Prints one line per problem.
"""
import argparse
import json
import shlex
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lint_bindings as lb  # noqa: E402

ROOT = lb.ROOT
DB = ROOT / "build" / "compile_commands.json"


def syntax_check(path: Path) -> list[str]:
    if not DB.exists():
        return [f"missing {DB.relative_to(ROOT)}: run cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=ON .. in build/"]
    entries = json.loads(DB.read_text())
    if path.suffix in (".h", ".hpp"):
        name = path.name
        units = [e for e in entries
                 if f'#include "{name}"' in Path(e["file"]).read_text(errors="replace")][:3]
        if not units:
            return []  # header included nowhere we compile
    else:
        units = [e for e in entries if Path(e["file"]).resolve() == path]
        if not units:
            return [f"{path} is not in the compile database (new file? re-run cmake)"]
    problems = []
    for e in units:
        args = e["arguments"] if "arguments" in e else shlex.split(e["command"])
        out, skip = [], False
        for a in args:
            if skip:
                skip = False
                continue
            if a == "-o":
                skip = True
                continue
            if a == "-c":
                continue
            out.append(a)
        out.append("-fsyntax-only")
        r = subprocess.run(out, cwd=e["directory"], capture_output=True, text=True)
        if r.returncode != 0:
            errs = [ln for ln in r.stderr.splitlines() if "error" in ln][:15]
            problems.append(f"COMPILE FAILED ({Path(e['file']).name}):\n  " + "\n  ".join(errs))
    return problems


def lint_check(path: Path, sites: list[str]) -> list[str]:
    rel = path.relative_to(ROOT).as_posix()
    findings = lb.lint_file(path)
    current = Counter(f.key for f in findings)
    allowed = Counter({k: n for k, n in lb.load_baseline().items() if k.split("|")[1] == rel})
    problems = []
    for site in sites:
        if current[site] > 0:
            lines = [str(f.line) for f in findings if f.key == site]
            problems.append(f"SITE STILL PRESENT (line {', '.join(lines)}): {site}")
    for k, n in (current - allowed).items():
        lines = [str(f.line) for f in findings if f.key == k]
        problems.append(f"NEW FINDING x{n} (line {', '.join(lines)}): {k}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--site", action="append", default=[], help="baseline key this edit must remove (repeatable)")
    ap.add_argument("--no-compile", action="store_true")
    a = ap.parse_args()
    path = Path(a.file).resolve()
    problems = [] if a.no_compile else syntax_check(path)
    problems += lint_check(path, a.site)
    for p in problems:
        print(p)
    print("REFACTOR CHECK: " + ("FAIL" if problems else "PASS"))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
