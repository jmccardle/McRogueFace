#!/usr/bin/env python3
"""
snippet_run.py -- a private working directory for each engine run (#541).

The engine resolves assets/ and scripts/ relative to its cwd and WRITES into it (a `save/`
directory, imgui.ini). Several agents running the snippet tools against one shared build
directory would write into, and race on, that directory. scratch_cwd() builds a per-process
directory that symlinks everything the build directory has (so assets, scripts and lib
resolve exactly as before) and is otherwise empty, so whatever the engine writes lands there
and is deleted at exit.
"""
import atexit
import os
import shutil
import tempfile


def scratch_cwd(build_dir, prefix="mcrf-snippet-"):
    if not os.path.isdir(build_dir):
        raise SystemExit(f"build directory not found: {build_dir} (set MCRF_BUILD_DIR to a built engine)")
    scratch = tempfile.mkdtemp(prefix=prefix)
    atexit.register(shutil.rmtree, scratch, ignore_errors=True)
    for name in os.listdir(build_dir):
        # What the engine writes at run time stays out: it must go to the scratch directory.
        if name in ("save", "imgui.ini"):
            continue
        os.symlink(os.path.join(build_dir, name), os.path.join(scratch, name))
    return scratch
