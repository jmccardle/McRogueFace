"""fuzz_texture_factory - Texture byte-ingestion + pixel-transform fuzzing
(#312, Tier B).

Raw byte ingestion and pixel transforms are classic memory-safety surfaces.
Drives the three Texture factory/transform entry points (verified against
src/PyTexture.cpp):

    Texture.from_bytes(data:y*, width, height, sprite_w, sprite_h, name='')  [classmethod]
    Texture.composite(layers:list, sprite_w, sprite_h, name='')             [classmethod]
    texture.hsl_shift(hue, sat=0.0, lit=0.0)                                 [instance]

from_bytes validates len(data) == width*height*4 (PyTexture.cpp:283) but does
NOT bound width/height to be positive, so zero dimensions and mismatched
lengths are stressed here. composite checks list/element types and equal layer
dimensions (PyTexture.cpp:315-360); empty lists, None/non-Texture elements, and
mismatched sizes are all exercised.

NOTE: the width*height*4 multiplication-overflow path (huge dimensions paired
with a coincidentally-matching tiny buffer, PyTexture.cpp:283) is intentionally
NOT probed here -- forcing it would trigger a multi-GB sf::Image allocation and
OOM the fuzzer rather than produce a clean crash. Dimensions are bounded so the
length check rejects oversized inputs before any allocation. That overflow case
warrants a separate, manual ASan check.

Creating sf::Texture needs a GL context; the fuzz build is SFML-backed (not
headless) and already loads default_texture at startup, so creation works.

Contract: fuzz_one_input(data: bytes) -> None.
"""

import mcrfpy

from fuzz_common import ByteStream, EXPECTED_EXCEPTIONS, safe_reset

MAX_OPS = 24


def weird_float(stream):
    sel = stream.u8() % 6
    if sel == 0:
        return float("inf")
    if sel == 1:
        return float("-inf")
    if sel == 2:
        return float("nan")
    if sel == 3:
        return stream.float_in_range(-720.0, 720.0)
    if sel == 4:
        return stream.float_in_range(-5.0, 5.0)
    return 0.0


def _default_texture():
    try:
        return getattr(mcrfpy, "default_texture", None)
    except Exception:
        return None


def make_valid_texture(stream):
    """Construct a small, valid Texture via from_bytes (matched length)."""
    w = stream.int_in_range(1, 16)
    h = stream.int_in_range(1, 16)
    need = w * h * 4
    raw = stream.take(need)
    if len(raw) < need:
        raw = raw + bytes(need - len(raw))
    sw = stream.int_in_range(1, w)
    sh = stream.int_in_range(1, h)
    return mcrfpy.Texture.from_bytes(raw, w, h, sw, sh)


def fuzz_from_bytes_mismatch(stream):
    """Deliberately mismatched dims/length/zero dims -> error paths."""
    n = stream.int_in_range(0, 1024)
    raw = stream.take(n)
    w = stream.int_in_range(-2, 64)
    h = stream.int_in_range(-2, 64)
    sw = stream.int_in_range(-2, 64)
    sh = stream.int_in_range(-2, 64)
    try:
        mcrfpy.Texture.from_bytes(raw, w, h, sw, sh)
    except EXPECTED_EXCEPTIONS:
        pass
    except MemoryError:
        pass


def fuzz_composite(stream, pool):
    """Composite a list mixing valid textures, None, non-textures, mismatches."""
    layers = []
    count = stream.int_in_range(0, 5)
    for _ in range(count):
        sel = stream.u8() % 5
        if sel == 0 and pool:
            layers.append(pool[stream.int_in_range(0, len(pool) - 1)])
        elif sel == 1:
            layers.append(None)
        elif sel == 2:
            layers.append("not a texture")
        elif sel == 3:
            dt = _default_texture()
            layers.append(dt)
        else:
            try:
                layers.append(make_valid_texture(stream))
            except EXPECTED_EXCEPTIONS:
                pass
            except MemoryError:
                pass
    sw = stream.int_in_range(-2, 32)
    sh = stream.int_in_range(-2, 32)
    # Sometimes pass a non-list to hit the PyList_Check path.
    arg = layers if stream.bool() else tuple(layers)
    try:
        mcrfpy.Texture.composite(arg, sw, sh)
    except EXPECTED_EXCEPTIONS:
        pass
    except MemoryError:
        pass


def fuzz_hsl_shift(stream, pool):
    tex = None
    if pool and stream.bool():
        tex = pool[stream.int_in_range(0, len(pool) - 1)]
    else:
        tex = _default_texture()
    if tex is None:
        return
    try:
        tex.hsl_shift(weird_float(stream), weird_float(stream), weird_float(stream))
    except EXPECTED_EXCEPTIONS:
        pass
    except MemoryError:
        pass


def fuzz_one_input(data):
    stream = ByteStream(data)
    pool = []
    try:
        n = stream.int_in_range(1, MAX_OPS)
        for _ in range(n):
            if stream.remaining < 1:
                break
            choice = stream.u8() % 4
            if choice == 0:
                try:
                    tex = make_valid_texture(stream)
                    if len(pool) < 6:
                        pool.append(tex)
                except EXPECTED_EXCEPTIONS:
                    pass
                except MemoryError:
                    pass
            elif choice == 1:
                fuzz_from_bytes_mismatch(stream)
            elif choice == 2:
                fuzz_composite(stream, pool)
            else:
                fuzz_hsl_shift(stream, pool)
    except EXPECTED_EXCEPTIONS:
        pass
