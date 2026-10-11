"""#467: every NoiseSource leaked its random generator (18.9 KB): TCOD_noise_delete
frees the noise but not the TCOD_Random the engine made for it, and re-running
__init__ leaked another. Measured with glibc's mallinfo2() (C heap): bytes retained
per extra NoiseSource, from the slope between n and 4n."""
import ctypes
import gc
import sys

import mcrfpy


class MallInfo2(ctypes.Structure):
    _fields_ = [(name, ctypes.c_size_t) for name in (
        "arena", "ordblks", "smblks", "hblks", "hblkhd",
        "usmblks", "fsmblks", "uordblks", "fordblks", "keepcost")]


_libc = ctypes.CDLL(None)
_libc.mallinfo2.restype = MallInfo2


def bytes_after(fn, n):
    gc.collect()
    before = _libc.mallinfo2().uordblks
    for i in range(n):
        fn(i)
    gc.collect()
    return _libc.mallinfo2().uordblks - before


def leak_per_call(fn, n=20):
    fn(0)
    return (bytes_after(fn, 4 * n) - bytes_after(fn, n)) / (3 * n)


def create_and_drop(i):
    n = mcrfpy.NoiseSource(seed=i)
    n.get((0.5, 0.5))


reused = mcrfpy.NoiseSource(seed=1)


def reinit(i):
    reused.__init__(seed=i)


failures = 0
for label, fn in (("NoiseSource created and dropped", create_and_drop),
                  ("NoiseSource.__init__ re-run", reinit)):
    per = leak_per_call(fn)
    ok = per < 1024
    failures += not ok
    print(f"{'ok' if ok else 'FAIL'}: {label}: {per:.0f} bytes retained each (pre-fix: ~18900)")

if failures:
    sys.exit(1)
print("PASS")
sys.exit(0)
