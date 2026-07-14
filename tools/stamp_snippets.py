#!/usr/bin/env python3
"""
stamp_snippets.py -- run every docs snippet and stamp what actually happened.

Plain python3, standard library only. Run from the project root:

    python3 tools/stamp_snippets.py            # run, restamp headers in place
    python3 tools/stamp_snippets.py --check    # verify stamps are current; touch nothing

Each snippet in tests/snippets/ carries a machine-readable provenance header:

    # mcrf: objects=[Caption,Color,Grid,Scene] verified=0.2.8@a7ba486 status=ok

The docs site reads that header to build its snippet index -- the object tags become
cross-links, and `status` renders as a badge next to the sample.

Until now every field was hand-typed. `status=ok` was a CLAIM, asserted by whoever last
touched the file, and 130 of them said "ok" while nothing had ever executed them. This
script makes the header a MEASUREMENT:

  * `status`   comes from actually running the snippet through tests/snippets/_harness.py
  * `verified` comes from the engine that ran it (the release version, out of
               api/manifest.json) -- a stable "0.2.8-dev" during a cycle, "0.2.9" at a tag
  * `objects`  is derived from the source, intersected with the objects the engine
               actually exports -- so a snippet that starts using a new type gets tagged
               for it without anyone remembering to.

--check is the CI gate: it fails if any stamp disagrees with a fresh run, which is what
stops the corpus from quietly drifting back into decoration.
"""

import argparse
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNIPPET_DIR = os.path.join(ROOT, "tests", "snippets")
HARNESS = os.path.join(SNIPPET_DIR, "_harness.py")
MANIFEST = os.path.join(ROOT, "api", "manifest.json")
BUILD_DIR = os.path.join(ROOT, "build")
MCROGUEFACE = os.path.join(BUILD_DIR, "mcrogueface")

HEADER_RE = re.compile(r"^#\s*mcrf:\s*(.*)$")
TIMEOUT = 30


def load_manifest():
    with open(MANIFEST, encoding="utf-8") as f:
        m = json.load(f)
    version = m.get("version", "unknown")
    commit = m.get("commit", "unknown")
    objects = set(m.get("objects", {}).keys())
    if not objects:
        sys.exit("manifest has no objects -- regenerate api/manifest.json first")
    return version, commit, objects


def snippet_paths():
    names = sorted(
        n for n in os.listdir(SNIPPET_DIR)
        if n.endswith(".py") and not n.startswith("_")
    )
    return [os.path.join(SNIPPET_DIR, n) for n in names]


def run_snippet(path):
    """Run one snippet through the harness. Returns (status, detail)."""
    env = os.environ.copy()
    lib = os.path.join(BUILD_DIR, "lib")
    env["LD_LIBRARY_PATH"] = os.pathsep.join(
        p for p in (lib, env.get("LD_LIBRARY_PATH", "")) if p
    )
    try:
        proc = subprocess.run(
            [MCROGUEFACE, "--headless", "--exec", path, "--exec", HARNESS],
            capture_output=True, text=True, timeout=TIMEOUT, cwd=BUILD_DIR, env=env,
        )
    except subprocess.TimeoutExpired:
        return "fail", "timeout"

    out = proc.stdout + proc.stderr
    if "Traceback (most recent call last)" in out:
        last = [l for l in out.strip().splitlines() if l.strip()]
        return "fail", last[-1][:120] if last else "traceback"
    if "SNIPPET_FAIL" in out:
        line = next((l for l in out.splitlines() if "SNIPPET_FAIL" in l), "")
        return "fail", line.split("SNIPPET_FAIL:", 1)[-1].strip()[:120]
    if proc.returncode != 0:
        return "fail", f"exit {proc.returncode}"
    if "SNIPPET_OK" not in out:
        return "fail", "harness did not report SNIPPET_OK"
    return "ok", ""


def parse_header(source):
    """Read the existing `# mcrf:` claims back out of a snippet."""
    for line in source.splitlines()[:5]:
        m = HEADER_RE.match(line.rstrip("\n"))
        if not m:
            continue
        payload = m.group(1)
        out = {}
        objs = re.search(r"objects=\[([^\]]*)\]", payload)
        out["objects"] = ([o.strip() for o in objs.group(1).split(",") if o.strip()]
                          if objs else [])
        st = re.search(r"status=(\S+)", payload)
        out["status"] = st.group(1) if st else None
        ver = re.search(r"verified=(\S+)", payload)
        out["verified"] = ver.group(1) if ver else None
        return out
    return {"objects": [], "status": None, "verified": None}


def derive_objects(source, known):
    """Which engine objects does this snippet actually touch?"""
    used = set(re.findall(r"\bmcrfpy\.([A-Z]\w*)", source))
    return sorted(used & known)


def build_header(objects, version, status):
    # `verified` is the release version, NOT version@commit. A commit hash would churn
    # every one of these headers on every commit for zero signal git history doesn't
    # already carry -- and `--check` ignores `verified` anyway. During a dev cycle the
    # version is a stable "0.2.8-dev"; at a tagged release it becomes "0.2.9", which is
    # the marker that freezes a version into the docs site's history.
    return (f"# mcrf: objects=[{','.join(objects)}] "
            f"verified={version} status={status}")


def restamp(source, header):
    """Replace the leading `# mcrf:` line, or insert one at the top."""
    lines = source.splitlines(keepends=True)
    for i, line in enumerate(lines[:5]):
        if HEADER_RE.match(line.rstrip("\n")):
            lines[i] = header + "\n"
            return "".join(lines)
    return header + "\n" + "".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="fail if any stamp is out of date; write nothing")
    args = ap.parse_args()

    if not os.path.exists(MCROGUEFACE):
        sys.exit(f"{MCROGUEFACE} not found -- run `make` first")

    version, commit, known = load_manifest()
    paths = snippet_paths()
    print(f"stamping {len(paths)} snippets against {version}@{commit}\n")

    failed, stale = [], []
    for path in paths:
        name = os.path.basename(path)
        with open(path, encoding="utf-8") as f:
            source = f.read()

        status, detail = run_snippet(path)
        objects = derive_objects(source, known)

        if status == "fail":
            failed.append((name, detail))
            print(f"  FAIL {name}: {detail}")

        if args.check:
            # Compare only the CLAIMS -- status and objects. Deliberately NOT `verified`:
            # that field records the engine a snippet was last confirmed against, which
            # is provenance, not a freshness assertion. If --check demanded it equal
            # HEAD, every commit would invalidate all 130 stamps and the gate would cry
            # wolf until people stopped listening. `verified` is refreshed at release
            # time by `make stamp-snippets`.
            old = parse_header(source)
            if old.get("status") != status:
                stale.append(f"{name}: header says status={old.get('status')!r}, "
                             f"actual run is {status!r}")
            elif old.get("objects") != objects:
                stale.append(f"{name}: header objects {old.get('objects')} "
                             f"!= actual {objects}")
            continue

        updated = restamp(source, build_header(objects, version, status))
        if updated != source:
            with open(path, "w", encoding="utf-8") as f:
                f.write(updated)

    print(f"\n{len(paths) - len(failed)}/{len(paths)} snippets ok")

    if args.check and stale:
        print(f"\n{len(stale)} snippet(s) have a stale `# mcrf:` stamp:")
        for line in stale:
            print(f"  - {line}")
        print("\nRun: python3 tools/stamp_snippets.py")
        return 1

    if failed:
        print(f"\n{len(failed)} snippet(s) failed:")
        for name, detail in failed:
            print(f"  - {name}: {detail}")
        return 1

    if not args.check:
        print("headers restamped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
