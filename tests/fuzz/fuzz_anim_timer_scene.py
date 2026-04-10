"""fuzz_anim_timer_scene - stub. Wave 2 agent W6 will implement.

Target bugs: #269 (PythonObjectCache race), #270 (GridLayer dangling),
#275 (UIEntity missing tp_dealloc), #277 (GridChunk dangling). Random
animation create/step/callback, timer start/stop/pause/resume/restart,
Frame nesting and reparenting, scene swap mid-callback.

Contract: define fuzz_one_input(data: bytes) -> None.
"""

import mcrfpy

from fuzz_common import ByteStream, EXPECTED_EXCEPTIONS


def fuzz_one_input(data):
    stream = ByteStream(data)
    try:
        mcrfpy.Scene("anim_stub")
    except EXPECTED_EXCEPTIONS:
        pass
