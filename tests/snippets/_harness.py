#!/usr/bin/env python3
"""
Snippet harness -- chained as a SECOND --exec after a documentation snippet.

    ./mcrogueface --headless --exec tests/snippets/042_foo.py --exec tests/snippets/_harness.py

The snippets under this directory are the code published on mcrogueface.github.io.
They are display scripts: each builds a scene and stops. They deliberately do NOT
call sys.exit(), because they must stay copy-pasteable -- a reader who pastes one
into their own game should get a running scene, not an interpreter that quits.

That is exactly what makes them un-runnable on their own: since #350, a headless
--exec script that never exits is an error, because step() is the only headless
clock. So the harness supplies the ending the snippet must not have. It runs in the
same interpreter and against the same engine state, so the scene the snippet built is
still there to inspect.

Chaining --exec (rather than exec()-ing the snippet's source from a parent script) is
deliberate on two counts: the snippet travels the same code path a real user's script
travels, and nothing has to read the file -- which is how the first version of this
harness tripped over #378 and mistook three healthy snippets for broken ones.

A snippet PASSES if it runs clean AND leaves something behind. Merely not raising is
not enough: a snippet whose body silently no-ops still renders as a code sample on the
docs site, and would still be wrong.
"""

import sys

import mcrfpy

FAIL = "SNIPPET_FAIL"
OK = "SNIPPET_OK"


def fail(msg):
    print(f"{FAIL}: {msg}")
    sys.exit(1)


# Advance one full simulation frame (#350): scene update, timers, Python
# Scene.update(), animations, transitions. If the snippet registered a timer or an
# animation, this is what proves it can actually tick without raising.
try:
    mcrfpy.step(0.016)
except Exception as exc:  # noqa: BLE001 -- any raise here is a real failure
    import traceback
    traceback.print_exc()
    fail(f"step() raised {type(exc).__name__}: {exc}")

scene = mcrfpy.current_scene
if scene is None:
    fail("snippet left no active scene (mcrfpy.current_scene is None)")

n = len(scene.children)
if n == 0:
    fail(f"snippet activated scene {scene.name!r} but added nothing to it")

print(f"{OK}: scene={scene.name!r} children={n}")
sys.exit(0)
