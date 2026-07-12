#!/usr/bin/env python3
"""
Direct-execution test for the API manifest generator (tools/generate_api_manifest.py).

Verifies:
  - the generator runs inside the engine and writes api/manifest.json
  - the manifest carries the expected schema keys and structure
  - output is deterministic across two consecutive runs

Run:
    cd build && ./mcrogueface --headless --exec ../tests/unit/api_manifest_test.py
"""

import os
import sys
import json
import importlib.util
import subprocess


def fail(msg):
    print("FAIL: " + msg)
    sys.exit(1)


def find_repo_root():
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=os.getcwd(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.decode("utf-8").strip()
    except Exception:
        pass
    # Fallback: two levels up from this test file (tests/unit/ -> repo).
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_generator(repo):
    gen_path = os.path.join(repo, "tools", "generate_api_manifest.py")
    if not os.path.exists(gen_path):
        fail("generator not found at " + gen_path)
    spec = importlib.util.spec_from_file_location("gen_api_manifest", gen_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    repo = find_repo_root()
    manifest_path = os.path.join(repo, "api", "manifest.json")
    full_path = os.path.join(repo, "docs", "generated", "api_full.json")

    gen = load_generator(repo)

    # First run.
    gen.main()
    if not os.path.exists(manifest_path):
        fail("manifest.json not written")
    if not os.path.exists(full_path):
        fail("api_full.json not written")
    with open(manifest_path, "rb") as f:
        run1 = f.read()
    with open(full_path, "rb") as f:
        run1_full = f.read()

    # Second run -- must be byte-identical (deterministic).
    gen.main()
    with open(manifest_path, "rb") as f:
        run2 = f.read()
    with open(full_path, "rb") as f:
        run2_full = f.read()

    if run1 != run2:
        fail("manifest.json is not deterministic across two runs")
    if run1_full != run2_full:
        fail("api_full.json is not deterministic across two runs")

    # Schema / structure checks.
    manifest = json.loads(run1.decode("utf-8"))
    required = ["schema", "version", "commit", "dirty", "seeded", "objects", "functions"]
    for key in required:
        if key not in manifest:
            fail("manifest missing top-level key: " + key)

    if manifest["schema"] != 1:
        fail("schema is not 1")
    if not isinstance(manifest["objects"], dict) or not manifest["objects"]:
        fail("objects is empty or not a dict")
    if not isinstance(manifest["functions"], dict) or not manifest["functions"]:
        fail("functions is empty or not a dict")
    if not isinstance(manifest["dirty"], bool):
        fail("dirty is not a bool")
    if not isinstance(manifest["seeded"], bool):
        fail("seeded is not a bool")

    # A known object with expected member/lifecycle structure.
    if "Grid" not in manifest["objects"]:
        fail("expected object 'Grid' missing")
    grid = manifest["objects"]["Grid"]
    for key in ["kind", "doc_sha", "lifecycle", "members"]:
        if key not in grid:
            fail("Grid missing key: " + key)
    if grid["kind"] != "class":
        fail("Grid kind is not 'class'")
    if "since" not in grid["lifecycle"]:
        fail("Grid lifecycle missing 'since'")
    if len(grid["doc_sha"]) != 16:
        fail("doc_sha is not 16 hex chars")

    # Every member carries the required fields and a valid kind.
    valid_kinds = {"method", "classmethod", "staticmethod", "property"}
    for oname, obj in manifest["objects"].items():
        for mname, member in obj["members"].items():
            for key in ["kind", "signature", "doc_sha", "lifecycle"]:
                if key not in member:
                    fail("%s.%s missing key: %s" % (oname, mname, key))
            if member["kind"] not in valid_kinds:
                fail("%s.%s has invalid kind: %s" % (oname, mname, member["kind"]))
            if len(member["doc_sha"]) != 16:
                fail("%s.%s doc_sha not 16 hex" % (oname, mname))

    # Functions carry required fields.
    for fname, fn in manifest["functions"].items():
        for key in ["kind", "signature", "doc_sha", "lifecycle"]:
            if key not in fn:
                fail("function %s missing key: %s" % (fname, key))
        if fn["kind"] != "function":
            fail("function %s kind is not 'function'" % fname)

    print("PASS: manifest deterministic, schema valid, %d objects / %d functions"
          % (len(manifest["objects"]), len(manifest["functions"])))
    sys.exit(0)


if __name__ == "__main__":
    main()
