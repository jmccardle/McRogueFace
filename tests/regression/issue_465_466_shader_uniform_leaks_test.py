"""#465: every Shader assigned to a drawable leaked (set_shader INCREF'd it and its
deleter never DECREF'd). #466: reading .uniforms leaked the drawable's allocation
(the collection wrapper's weak_ptr was never destroyed, keeping the make_shared
control block alive).

#465 is checked with exact reference counts. #466 leaks C++ heap that
sys.getallocatedblocks() can't see, so it is measured with glibc's mallinfo2():
bytes retained per extra call, from the slope between n and 4n calls.
"""
import ctypes
import gc
import sys

import mcrfpy

FRAG = "uniform float u; void main(){ gl_FragColor = vec4(u, 0.0, 0.0, 1.0); }"
failures = []


def check(cond, msg):
    print(("ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


class MallInfo2(ctypes.Structure):
    _fields_ = [(name, ctypes.c_size_t) for name in (
        "arena", "ordblks", "smblks", "hblks", "hblkhd",
        "usmblks", "fsmblks", "uordblks", "fordblks", "keepcost")]


_libc = ctypes.CDLL(None)
_libc.mallinfo2.restype = MallInfo2


def heap_bytes():
    return _libc.mallinfo2().uordblks


def bytes_after(fn, n):
    gc.collect()
    before = heap_bytes()
    for _ in range(n):
        fn()
    gc.collect()
    return heap_bytes() - before


def leak_per_call(fn, n=200):
    fn()
    return (bytes_after(fn, 4 * n) - bytes_after(fn, n)) / (3 * n)


# #465: the drawable releases its shader
for label, make in (("Frame", lambda: mcrfpy.Frame(pos=(0, 0), size=(10, 10))),
                    ("Sprite", lambda: mcrfpy.Sprite(pos=(0, 0))),
                    ("Entity", lambda: mcrfpy.Entity())):
    shader = mcrfpy.Shader(FRAG)
    before = sys.getrefcount(shader)
    for _ in range(100):
        d = make()
        d.shader = shader
        del d
    gc.collect()
    check(sys.getrefcount(shader) == before,
          f"{label}.shader: refcount +{sys.getrefcount(shader) - before} after 100 drawables dropped")

shader = mcrfpy.Shader(FRAG)
f = mcrfpy.Frame(pos=(0, 0), size=(10, 10))
before = sys.getrefcount(shader)
f.shader = shader
check(sys.getrefcount(shader) == before + 1, "an assigned shader is held exactly once")
check(f.shader is shader, "frame.shader returns the assigned Shader")
f.shader = None
check(sys.getrefcount(shader) == before, "shader = None releases it")


# #466: reading .uniforms doesn't keep the drawable's memory
def frame_with_uniform():
    f = mcrfpy.Frame(pos=(0, 0), size=(10, 10))
    f.uniforms["u"] = 1.0


def entity_with_uniform():
    e = mcrfpy.Entity()
    e.uniforms["u"] = 1.0


for label, fn in (("Frame.uniforms", frame_with_uniform),
                  ("Entity.uniforms", entity_with_uniform)):
    per_call = leak_per_call(fn)
    check(per_call < 64, f"{label}: {per_call:.0f} bytes retained per drawable (pre-fix: ~950)")

if failures:
    print(f"FAIL: {len(failures)} check(s)")
    sys.exit(1)
print("PASS")
sys.exit(0)
