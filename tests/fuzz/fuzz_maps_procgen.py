"""fuzz_maps_procgen - Wave 2 target W7 (addresses #283).

HeightMap and DiscreteMap are the standardized abstract data containers that
every procgen system converts to/from. Fuzzing HeightMap/DiscreteMap methods
plus the one-directional conversions from NoiseSource/BSP into HeightMap
covers the entire procgen surface without having to fuzz each individual
procgen system.

No specific known-bug issues drive this target - it is new territory.

Contract: define fuzz_one_input(data: bytes) -> None. The C++ harness
(tests/fuzz/fuzz_common.cpp) calls this for every libFuzzer iteration.
Use ByteStream to consume bytes. Wrap work in try/except EXPECTED_EXCEPTIONS.
"""

import mcrfpy

from fuzz_common import ByteStream, EXPECTED_EXCEPTIONS

# Keep dimensions small: procgen ops are expensive and libFuzzer needs
# high iter/sec to find bugs. Bigger maps also blow up memory on every
# iteration for no coverage benefit.
MIN_DIM = 2
MAX_DIM = 32

ALGOS = ("simplex", "perlin", "wavelet")
NOISE_MODES = ("flat", "fbm", "turbulence")
BSP_SELECTS = ("leaves", "all", "internal")

MAX_HEIGHTMAPS = 3
MAX_DISCRETEMAPS = 3
MAX_NOISES = 2
MAX_BSPS = 2
MAX_OPS = 30


def _pick_size(stream):
    return (
        stream.int_in_range(MIN_DIM, MAX_DIM),
        stream.int_in_range(MIN_DIM, MAX_DIM),
    )


def _pick_small_float(stream, lo=-5.0, hi=5.0):
    return stream.float_in_range(lo, hi)


def _pick_u8(stream):
    return stream.u8()


def _pick_coord(stream, bound=MAX_DIM * 2):
    # Allow occasional OOB to exercise bounds checking.
    return stream.int_in_range(-2, bound)


def _pick_hm(stream, hms):
    if not hms:
        return None
    return hms[stream.int_in_range(0, len(hms) - 1)]


def _pick_dm(stream, dms):
    if not dms:
        return None
    return dms[stream.int_in_range(0, len(dms) - 1)]


def _pick_noise(stream, nss):
    if not nss:
        return None
    return nss[stream.int_in_range(0, len(nss) - 1)]


def _pick_bsp(stream, bsps):
    if not bsps:
        return None
    return bsps[stream.int_in_range(0, len(bsps) - 1)]


def _make_heightmap(stream, hms):
    if len(hms) >= MAX_HEIGHTMAPS:
        hms.pop(0)
    size = _pick_size(stream)
    fill = _pick_small_float(stream, -2.0, 2.0)
    hms.append(mcrfpy.HeightMap(size=size, fill=fill))


def _make_discretemap(stream, dms):
    if len(dms) >= MAX_DISCRETEMAPS:
        dms.pop(0)
    size = _pick_size(stream)
    fill = _pick_u8(stream)
    dms.append(mcrfpy.DiscreteMap(size=size, fill=fill))


def _make_noise(stream, nss):
    if len(nss) >= MAX_NOISES:
        nss.pop(0)
    algo = ALGOS[stream.int_in_range(0, len(ALGOS) - 1)]
    # sample() requires dimensions==2. Use 2D most of the time, sometimes
    # try 1/3/4 to exercise get()/fbm() dimension validation paths.
    dims_roll = stream.u8() & 0x07
    if dims_roll < 6:
        dims = 2
    else:
        dims = stream.int_in_range(1, 4)
    hurst = stream.float_in_range(0.0, 1.0)
    lacunarity = stream.float_in_range(1.0, 4.0)
    seed = stream.u32()
    nss.append(mcrfpy.NoiseSource(
        dimensions=dims,
        algorithm=algo,
        hurst=hurst,
        lacunarity=lacunarity,
        seed=seed,
    ))


def _make_bsp(stream, bsps):
    if len(bsps) >= MAX_BSPS:
        bsps.pop(0)
    # BSP with (0,0) or (1,1) size may degenerate - guard via MIN_DIM.
    w = stream.int_in_range(MIN_DIM, MAX_DIM)
    h = stream.int_in_range(MIN_DIM, MAX_DIM)
    bsps.append(mcrfpy.BSP(pos=(0, 0), size=(w, h)))


# =============================================================================
# Dispatch ops
# =============================================================================

def _op_hm_scalar(stream, hms):
    hm = _pick_hm(stream, hms)
    if hm is None:
        return
    which = stream.u8() % 7
    if which == 0:
        hm.fill(_pick_small_float(stream))
    elif which == 1:
        hm.clear()
    elif which == 2:
        hm.add_constant(_pick_small_float(stream))
    elif which == 3:
        hm.scale(_pick_small_float(stream))
    elif which == 4:
        lo = _pick_small_float(stream)
        hi = _pick_small_float(stream)
        if lo > hi:
            lo, hi = hi, lo
        hm.clamp(lo, hi)
    elif which == 5:
        lo = _pick_small_float(stream)
        hi = _pick_small_float(stream)
        if lo > hi:
            lo, hi = hi, lo
        hm.normalize(lo, hi)
    elif which == 6:
        hm.inverse()


def _op_hm_terrain(stream, hms):
    hm = _pick_hm(stream, hms)
    if hm is None:
        return
    which = stream.u8() % 4
    if which == 0:
        cx = stream.int_in_range(-2, MAX_DIM + 2)
        cy = stream.int_in_range(-2, MAX_DIM + 2)
        radius = stream.float_in_range(0.1, 10.0)
        height = _pick_small_float(stream)
        hm.add_hill((cx, cy), radius, height)
    elif which == 1:
        cx = stream.int_in_range(-2, MAX_DIM + 2)
        cy = stream.int_in_range(-2, MAX_DIM + 2)
        radius = stream.float_in_range(0.1, 10.0)
        target = _pick_small_float(stream)
        hm.dig_hill((cx, cy), radius, target)
    elif which == 2:
        n_points = stream.int_in_range(1, 16)
        seed = stream.u32()
        hm.add_voronoi(n_points, seed=seed)
    elif which == 3:
        roughness = stream.float_in_range(0.0, 1.0)
        seed = stream.u32()
        hm.mid_point_displacement(roughness=roughness, seed=seed)


def _op_hm_smooth_erosion(stream, hms):
    hm = _pick_hm(stream, hms)
    if hm is None:
        return
    if stream.bool():
        iterations = stream.int_in_range(1, 4)
        hm.smooth(iterations=iterations)
    else:
        # Keep drop count small - rain_erosion is O(drops * steps).
        drops = stream.int_in_range(1, 32)
        erosion = stream.float_in_range(0.0, 0.5)
        sedim = stream.float_in_range(0.0, 0.5)
        seed = stream.u32()
        hm.rain_erosion(drops, erosion=erosion, sedimentation=sedim, seed=seed)


def _op_hm_binary(stream, hms):
    # Intentionally allow mismatched sizes. These must raise, not crash.
    if len(hms) < 2:
        return
    a = hms[stream.int_in_range(0, len(hms) - 1)]
    b = hms[stream.int_in_range(0, len(hms) - 1)]
    which = stream.u8() % 7
    if which == 0:
        a.add(b)
    elif which == 1:
        a.subtract(b)
    elif which == 2:
        a.multiply(b)
    elif which == 3:
        t = stream.float_in_range(0.0, 1.0)
        a.lerp(b, t)
    elif which == 4:
        a.copy_from(b)
    elif which == 5:
        a.max(b)
    elif which == 6:
        a.min(b)


def _op_hm_subscript(stream, hms):
    hm = _pick_hm(stream, hms)
    if hm is None:
        return
    x = _pick_coord(stream)
    y = _pick_coord(stream)
    if stream.bool():
        # Read
        _ = hm[x, y]
    else:
        # Write
        hm[x, y] = _pick_small_float(stream)


def _op_hm_query(stream, hms):
    hm = _pick_hm(stream, hms)
    if hm is None:
        return
    which = stream.u8() % 5
    if which == 0:
        hm.min_max()
    elif which == 1:
        lo = _pick_small_float(stream)
        hi = _pick_small_float(stream)
        if lo > hi:
            lo, hi = hi, lo
        hm.count_in_range((lo, hi))
    elif which == 2:
        x = _pick_coord(stream)
        y = _pick_coord(stream)
        hm.get(x, y)
    elif which == 3:
        x = stream.float_in_range(-2.0, MAX_DIM + 2.0)
        y = stream.float_in_range(-2.0, MAX_DIM + 2.0)
        hm.get_interpolated(x, y)
    elif which == 4:
        lo = _pick_small_float(stream)
        hi = _pick_small_float(stream)
        if lo > hi:
            lo, hi = hi, lo
        hm.threshold((lo, hi))


def _op_dm_scalar(stream, dms):
    dm = _pick_dm(stream, dms)
    if dm is None:
        return
    which = stream.u8() % 3
    if which == 0:
        dm.fill(_pick_u8(stream))
    elif which == 1:
        dm.clear()
    elif which == 2:
        dm.invert()


def _op_dm_get_set(stream, dms):
    dm = _pick_dm(stream, dms)
    if dm is None:
        return
    x = _pick_coord(stream)
    y = _pick_coord(stream)
    if stream.bool():
        _ = dm[x, y]
    else:
        dm[x, y] = _pick_u8(stream)


def _op_dm_query(stream, dms):
    dm = _pick_dm(stream, dms)
    if dm is None:
        return
    which = stream.u8() % 4
    if which == 0:
        dm.count(_pick_u8(stream))
    elif which == 1:
        lo = _pick_u8(stream)
        hi = _pick_u8(stream)
        if lo > hi:
            lo, hi = hi, lo
        dm.count_range(lo, hi)
    elif which == 2:
        dm.min_max()
    elif which == 3:
        dm.histogram()


def _op_dm_bitwise(stream, dms):
    if len(dms) < 2:
        return
    a = dms[stream.int_in_range(0, len(dms) - 1)]
    b = dms[stream.int_in_range(0, len(dms) - 1)]
    which = stream.u8() % 3
    if which == 0:
        a.bitwise_and(b)
    elif which == 1:
        a.bitwise_or(b)
    elif which == 2:
        a.bitwise_xor(b)


def _op_dm_to_bool(stream, dms):
    dm = _pick_dm(stream, dms)
    if dm is None:
        return
    which = stream.u8() % 3
    if which == 0:
        dm.bool(_pick_u8(stream))
    elif which == 1:
        # Random small set of ints
        n = stream.int_in_range(1, 4)
        values = set()
        for _ in range(n):
            values.add(_pick_u8(stream))
        dm.bool(values)
    elif which == 2:
        threshold = _pick_u8(stream)
        dm.bool(lambda v, t=threshold: v > t)


def _op_dm_copy_from(stream, dms):
    # Intentionally allow mismatched sizes - must raise not crash.
    if len(dms) < 2:
        return
    a = dms[stream.int_in_range(0, len(dms) - 1)]
    b = dms[stream.int_in_range(0, len(dms) - 1)]
    which = stream.u8() % 3
    if which == 0:
        a.copy_from(b)
    elif which == 1:
        a.max(b)
    elif which == 2:
        a.min(b)


def _op_hm_add_noise(stream, hms, nss):
    hm = _pick_hm(stream, hms)
    ns = _pick_noise(stream, nss)
    if hm is None or ns is None:
        return
    mode = NOISE_MODES[stream.int_in_range(0, len(NOISE_MODES) - 1)]
    octaves = stream.int_in_range(1, 6)
    scale = stream.float_in_range(-2.0, 2.0)
    if stream.bool():
        hm.add_noise(ns, mode=mode, octaves=octaves, scale=scale)
    else:
        hm.multiply_noise(ns, mode=mode, octaves=octaves, scale=scale)


def _op_hm_add_bsp(stream, hms, bsps):
    hm = _pick_hm(stream, hms)
    bsp = _pick_bsp(stream, bsps)
    if hm is None or bsp is None:
        return
    select = BSP_SELECTS[stream.int_in_range(0, len(BSP_SELECTS) - 1)]
    shrink = stream.int_in_range(0, 3)
    value = _pick_small_float(stream)
    if stream.bool():
        hm.add_bsp(bsp, select=select, shrink=shrink, value=value)
    else:
        hm.multiply_bsp(bsp, select=select, shrink=shrink, value=value)


def _op_noise_sample(stream, nss, hms):
    ns = _pick_noise(stream, nss)
    if ns is None:
        return
    size = _pick_size(stream)
    mode = NOISE_MODES[stream.int_in_range(0, len(NOISE_MODES) - 1)]
    octaves = stream.int_in_range(1, 6)
    # sample() requires dimensions==2; other dims will raise ValueError.
    sampled = ns.sample(size=size, mode=mode, octaves=octaves)
    if len(hms) >= MAX_HEIGHTMAPS:
        hms.pop(0)
    hms.append(sampled)


def _op_bsp_to_heightmap(stream, bsps, hms):
    bsp = _pick_bsp(stream, bsps)
    if bsp is None:
        return
    select = BSP_SELECTS[stream.int_in_range(0, len(BSP_SELECTS) - 1)]
    shrink = stream.int_in_range(0, 3)
    value = _pick_small_float(stream)
    hm = bsp.to_heightmap(select=select, shrink=shrink, value=value)
    if len(hms) >= MAX_HEIGHTMAPS:
        hms.pop(0)
    hms.append(hm)


def _op_dm_from_heightmap(stream, hms, dms):
    hm = _pick_hm(stream, hms)
    if hm is None:
        return
    # Build a random mapping. Occasionally produce malformed mappings to
    # exercise error paths.
    malformed = (stream.u8() & 0x0f) == 0
    if malformed:
        mapping = [("not", "a", "tuple"), 42]
    else:
        n_bands = stream.int_in_range(1, 5)
        mapping = []
        for _ in range(n_bands):
            lo = _pick_small_float(stream)
            hi = _pick_small_float(stream)
            if lo > hi:
                lo, hi = hi, lo
            val = _pick_u8(stream)
            mapping.append(((lo, hi), val))
    dm = mcrfpy.DiscreteMap.from_heightmap(hm, mapping)
    if len(dms) >= MAX_DISCRETEMAPS:
        dms.pop(0)
    dms.append(dm)


def _op_dm_to_heightmap(stream, dms, hms):
    dm = _pick_dm(stream, dms)
    if dm is None:
        return
    if stream.bool():
        # No mapping: direct uint8->float cast.
        hm = dm.to_heightmap()
    else:
        n = stream.int_in_range(1, 6)
        mapping = {}
        for _ in range(n):
            key = _pick_u8(stream)
            mapping[key] = _pick_small_float(stream)
        hm = dm.to_heightmap(mapping)
    if len(hms) >= MAX_HEIGHTMAPS:
        hms.pop(0)
    hms.append(hm)


def _op_bsp_split(stream, bsps):
    bsp = _pick_bsp(stream, bsps)
    if bsp is None:
        return
    which = stream.u8() % 3
    if which == 0:
        depth = stream.int_in_range(1, 6)
        min_w = stream.int_in_range(1, 8)
        min_h = stream.int_in_range(1, 8)
        max_ratio = stream.float_in_range(1.0, 4.0)
        seed = stream.u32()
        bsp.split_recursive(
            depth=depth,
            min_size=(min_w, min_h),
            max_ratio=max_ratio,
            seed=seed,
        )
    elif which == 1:
        horizontal = stream.bool()
        position = stream.int_in_range(0, MAX_DIM)
        bsp.split_once(horizontal=horizontal, position=position)
    elif which == 2:
        bsp.clear()


def _op_bsp_walk(stream, bsps):
    bsp = _pick_bsp(stream, bsps)
    if bsp is None:
        return
    # Shallow access on leaves - exercises BSPNode property getters and
    # the center() method (targets 1044-1051 in PyBSP.cpp).
    count = 0
    max_walk = stream.int_in_range(1, 8)
    try:
        for leaf in bsp.leaves():
            _ = leaf.pos
            _ = leaf.size
            _ = leaf.bounds
            _ = leaf.is_leaf
            _ = leaf.level
            leaf.center()
            count += 1
            if count >= max_walk:
                break
    except EXPECTED_EXCEPTIONS:
        pass


def _dispatch(op, stream, hms, dms, nss, bsps):
    # 23 distinct operations covering all four surfaces plus conversions.
    if op == 0:
        _make_heightmap(stream, hms)
    elif op == 1:
        _make_discretemap(stream, dms)
    elif op == 2:
        _make_noise(stream, nss)
    elif op == 3:
        _make_bsp(stream, bsps)
    elif op == 4:
        _op_hm_scalar(stream, hms)
    elif op == 5:
        _op_hm_terrain(stream, hms)
    elif op == 6:
        _op_hm_smooth_erosion(stream, hms)
    elif op == 7:
        _op_hm_binary(stream, hms)
    elif op == 8:
        _op_hm_subscript(stream, hms)
    elif op == 9:
        _op_hm_query(stream, hms)
    elif op == 10:
        _op_dm_scalar(stream, dms)
    elif op == 11:
        _op_dm_get_set(stream, dms)
    elif op == 12:
        _op_dm_query(stream, dms)
    elif op == 13:
        _op_dm_bitwise(stream, dms)
    elif op == 14:
        _op_dm_to_bool(stream, dms)
    elif op == 15:
        _op_dm_copy_from(stream, dms)
    elif op == 16:
        _op_hm_add_noise(stream, hms, nss)
    elif op == 17:
        _op_hm_add_bsp(stream, hms, bsps)
    elif op == 18:
        _op_noise_sample(stream, nss, hms)
    elif op == 19:
        _op_bsp_to_heightmap(stream, bsps, hms)
    elif op == 20:
        _op_dm_from_heightmap(stream, hms, dms)
    elif op == 21:
        _op_dm_to_heightmap(stream, dms, hms)
    elif op == 22:
        _op_bsp_split(stream, bsps)
    elif op == 23:
        _op_bsp_walk(stream, bsps)


_NUM_OPS = 24


def fuzz_one_input(data):
    stream = ByteStream(data)
    hms = []
    dms = []
    nss = []
    bsps = []
    try:
        # Prime each container with at least one object so the very first
        # iteration exercises conversions and binary ops, not just empty
        # noops. All these can still raise on pathological sizes, which
        # is fine.
        try:
            _make_heightmap(stream, hms)
        except EXPECTED_EXCEPTIONS:
            pass
        try:
            _make_discretemap(stream, dms)
        except EXPECTED_EXCEPTIONS:
            pass
        try:
            _make_noise(stream, nss)
        except EXPECTED_EXCEPTIONS:
            pass
        try:
            _make_bsp(stream, bsps)
        except EXPECTED_EXCEPTIONS:
            pass

        n_ops = stream.int_in_range(1, MAX_OPS)
        for _ in range(n_ops):
            if stream.remaining < 1:
                break
            op = stream.u8() % _NUM_OPS
            try:
                _dispatch(op, stream, hms, dms, nss, bsps)
            except EXPECTED_EXCEPTIONS:
                pass
    except EXPECTED_EXCEPTIONS:
        pass
