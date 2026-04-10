"""fuzz_property_types - stub. Wave 2 agent W5 will implement.

Target bugs: #267 (PyObject_GetAttrString reference leaks), #268
(sfVector2f_to_PyObject NULL deref), #272 (UniformCollection unchecked
weak_ptr). Random property get/set with type confusion across all UI types.

Contract: define fuzz_one_input(data: bytes) -> None.
"""

import mcrfpy

from fuzz_common import ByteStream, EXPECTED_EXCEPTIONS


def fuzz_one_input(data):
    stream = ByteStream(data)
    try:
        mcrfpy.Frame(pos=(0, 0), size=(10, 10))
    except EXPECTED_EXCEPTIONS:
        pass
