"""Shared helpers for McRogueFace native libFuzzer fuzz targets (#283).

Every fuzz target imports from this module. Stable contract:
- ByteStream: deterministically consume fuzzer bytes into typed values
- safe_reset(): clear mcrfpy global state between iterations
- EXPECTED_EXCEPTIONS: tuple of Python-level exceptions to swallow

The C++ harness (tests/fuzz/fuzz_common.cpp) calls safe_reset() before
each target invocation and catches any exception that escapes. Targets
should wrap their work in `try: ... except EXPECTED_EXCEPTIONS: pass`
so Python noise doesn't pollute the libFuzzer output.
"""

import mcrfpy

EXPECTED_EXCEPTIONS = (
    TypeError,
    ValueError,
    AttributeError,
    IndexError,
    KeyError,
    OverflowError,
    RuntimeError,
    NotImplementedError,
    StopIteration,
)


class ByteStream:
    """Deterministic byte-to-value converter.

    Replaces atheris.FuzzedDataProvider for our native libFuzzer harness.
    Running out of bytes is silently tolerated: consumers get 0/empty/False,
    so a short input still produces a valid (if shallow) iteration.
    """

    __slots__ = ("_buf", "_pos")

    def __init__(self, data):
        self._buf = data
        self._pos = 0

    @property
    def remaining(self):
        return max(0, len(self._buf) - self._pos)

    def take(self, n):
        if self._pos >= len(self._buf) or n <= 0:
            return b""
        end = min(len(self._buf), self._pos + n)
        out = self._buf[self._pos:end]
        self._pos = end
        return out

    def u8(self):
        b = self.take(1)
        return b[0] if b else 0

    def u16(self):
        b = self.take(2)
        return int.from_bytes(b.ljust(2, b"\x00"), "little", signed=False)

    def u32(self):
        b = self.take(4)
        return int.from_bytes(b.ljust(4, b"\x00"), "little", signed=False)

    def int_in_range(self, lo, hi):
        if hi <= lo:
            return lo
        span = hi - lo + 1
        if span <= 256:
            return lo + (self.u8() % span)
        if span <= 65536:
            return lo + (self.u16() % span)
        return lo + (self.u32() % span)

    def float_in_range(self, lo, hi):
        f = self.u32() / 4294967296.0
        return lo + f * (hi - lo)

    def bool(self):
        return (self.u8() & 1) == 1

    def pick_one(self, seq):
        if not seq:
            return None
        return seq[self.int_in_range(0, len(seq) - 1)]

    def ascii_str(self, max_len=16):
        n = self.int_in_range(0, max_len)
        raw = self.take(n)
        return "".join(chr(c) for c in raw if 32 <= c < 127)


def safe_reset():
    """Reset mcrfpy global state between fuzz iterations.

    Stops all timers (they hold callback refs and can fire mid-mutation)
    and installs a fresh empty scene so the prior iteration's UI tree is
    released. Failures here are tolerated — the C++ harness catches them.
    """
    try:
        timers = list(mcrfpy.timers) if hasattr(mcrfpy, "timers") else []
        for t in timers:
            try:
                t.stop()
            except Exception:
                pass
    except Exception:
        pass
    try:
        mcrfpy.current_scene = mcrfpy.Scene("fuzz_reset")
    except Exception:
        pass
