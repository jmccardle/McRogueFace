"""Fuzz target: EntityCollection operations across multiple differently-sized grids.

Hunts the bug family from issues #258-#263, #273, #274:

- #258-#263: UIEntity::gridstate heap overflows when an entity transfers between
  grids of different sizes. The bug showed up in every mutation path
  (append/extend/insert/setitem/slice assignment/set_grid).
- #273: entity.die() during iteration over grid.entities invalidated the C++
  list iterator. The fix now raises RuntimeError; we still want the fuzzer to
  exercise the raise path and any neighbour that could miss the guard.
- #274: set_grid(None) and set_grid(other_grid) needed to update the spatial
  hash; a missing remove/insert causes use-after-free.

The fuzz loop keeps a small pool of grids of varying sizes and a pool of
entities, then dispatches a sequence of byte-driven operations against them:
create/destroy, append/insert/extend, remove/pop, __setitem__, slice
assignment, del, direct grid reassignment, and iteration with mid-loop
mutation. libFuzzer's coverage feedback drives the state exploration in
UIEntityCollection.cpp and UIEntity::set_grid.

The C++ harness (tests/fuzz/fuzz_common.cpp) invokes fuzz_one_input(data) for
every libFuzzer iteration and calls fuzz_common.safe_reset() before each call.
We still catch expected Python exceptions so one bad op does not abort the
whole iteration, which would hide later coverage from libFuzzer.
"""

import mcrfpy

from fuzz_common import ByteStream, EXPECTED_EXCEPTIONS


# Caps chosen to keep each iteration fast and avoid address-space exhaustion
# under ASan. Grids up to 32x32 = 1024 cells means gridstate vectors stay
# small; 16 entities is enough to exercise slice-assignment boundaries.
MAX_GRIDS = 4
MAX_ENTITIES = 16
MAX_OPS = 48
MAX_GRID_DIM = 32


def _pick_grid(stream, grids):
    """Pick a random grid from the pool, or None if pool empty."""
    if not grids:
        return None
    return grids[stream.int_in_range(0, len(grids) - 1)]


def _pick_entity(stream, entities):
    """Pick a random entity from the pool, or None if pool empty."""
    if not entities:
        return None
    return entities[stream.int_in_range(0, len(entities) - 1)]


def _make_entity(stream, grids, attach=True):
    """Create a fresh entity, optionally attached to a random grid."""
    x = stream.int_in_range(0, MAX_GRID_DIM - 1)
    y = stream.int_in_range(0, MAX_GRID_DIM - 1)
    grid = _pick_grid(stream, grids) if attach else None
    if grid is not None:
        return mcrfpy.Entity(grid_pos=(x, y), grid=grid)
    return mcrfpy.Entity(grid_pos=(x, y))


def _make_grid(stream):
    """Create a grid with a random small size."""
    w = stream.int_in_range(1, MAX_GRID_DIM)
    h = stream.int_in_range(1, MAX_GRID_DIM)
    return mcrfpy.Grid(grid_size=(w, h))


def _safe_index(stream, collection_len):
    """Pick an index in [0, collection_len-1], or 0 when empty."""
    if collection_len <= 0:
        return 0
    return stream.int_in_range(0, collection_len - 1)


def _op_new_grid(stream, grids, entities):
    if len(grids) >= MAX_GRIDS:
        # Drop a random grid first so we exercise grid destruction paths too.
        idx = stream.int_in_range(0, len(grids) - 1)
        grids.pop(idx)
    grids.append(_make_grid(stream))


def _op_new_entity(stream, grids, entities):
    if len(entities) >= MAX_ENTITIES:
        idx = stream.int_in_range(0, len(entities) - 1)
        entities.pop(idx)
    entities.append(_make_entity(stream, grids, attach=bool(stream.int_in_range(0, 1))))


def _op_append(stream, grids, entities):
    grid = _pick_grid(stream, grids)
    if grid is None:
        return
    # Half the time append a fresh entity, half the time append an existing one
    # from the pool to exercise the cross-grid transfer path in append().
    if entities and stream.int_in_range(0, 1):
        ent = _pick_entity(stream, entities)
    else:
        ent = _make_entity(stream, grids, attach=False)
        if len(entities) < MAX_ENTITIES:
            entities.append(ent)
    grid.entities.append(ent)


def _op_insert(stream, grids, entities):
    grid = _pick_grid(stream, grids)
    if grid is None:
        return
    idx = stream.int_in_range(0, max(0, len(grid.entities)))
    if entities and stream.int_in_range(0, 1):
        ent = _pick_entity(stream, entities)
    else:
        ent = _make_entity(stream, grids, attach=False)
        if len(entities) < MAX_ENTITIES:
            entities.append(ent)
    grid.entities.insert(idx, ent)


def _op_extend(stream, grids, entities):
    grid = _pick_grid(stream, grids)
    if grid is None:
        return
    count = stream.int_in_range(0, 3)
    batch = []
    for _ in range(count):
        if entities and stream.int_in_range(0, 1):
            batch.append(_pick_entity(stream, entities))
        else:
            ent = _make_entity(stream, grids, attach=False)
            if len(entities) < MAX_ENTITIES:
                entities.append(ent)
            batch.append(ent)
    grid.entities.extend(batch)


def _op_remove(stream, grids, entities):
    grid = _pick_grid(stream, grids)
    if grid is None or len(grid.entities) == 0:
        return
    idx = _safe_index(stream, len(grid.entities))
    target = grid.entities[idx]
    grid.entities.remove(target)


def _op_pop(stream, grids, entities):
    grid = _pick_grid(stream, grids)
    if grid is None or len(grid.entities) == 0:
        return
    if stream.int_in_range(0, 1):
        grid.entities.pop()
    else:
        idx = _safe_index(stream, len(grid.entities))
        grid.entities.pop(idx)


def _op_setitem(stream, grids, entities):
    """Replace entities[i] with an entity possibly from a different grid.

    This is the critical path for gridstate resize (#258-#263): when the
    replacement entity was previously attached to a differently-sized grid,
    its gridstate must be resized to match the new grid.
    """
    grid = _pick_grid(stream, grids)
    if grid is None or len(grid.entities) == 0:
        return
    idx = _safe_index(stream, len(grid.entities))
    if entities and stream.int_in_range(0, 1):
        ent = _pick_entity(stream, entities)
    else:
        ent = _make_entity(stream, grids, attach=True)
        if len(entities) < MAX_ENTITIES:
            entities.append(ent)
    grid.entities[idx] = ent


def _op_slice_assign(stream, grids, entities):
    """Slice assignment - covers both contiguous and extended slices."""
    grid = _pick_grid(stream, grids)
    if grid is None:
        return
    n = len(grid.entities)
    a = stream.int_in_range(0, max(0, n))
    b = stream.int_in_range(a, max(a, n))
    extended = bool(stream.int_in_range(0, 1)) and a < b
    count = stream.int_in_range(0, 3)
    batch = []
    for _ in range(count):
        if entities and stream.int_in_range(0, 1):
            batch.append(_pick_entity(stream, entities))
        else:
            ent = _make_entity(stream, grids, attach=False)
            if len(entities) < MAX_ENTITIES:
                entities.append(ent)
            batch.append(ent)
    if extended:
        step = stream.int_in_range(1, 3)
        # Extended slice assignment requires matched lengths
        target_len = max(0, (b - a + step - 1) // step)
        if target_len == len(batch):
            grid.entities[a:b:step] = batch
    else:
        grid.entities[a:b] = batch


def _op_del_index(stream, grids, entities):
    """del grid.entities[i] or del grid.entities[a:b]."""
    grid = _pick_grid(stream, grids)
    if grid is None or len(grid.entities) == 0:
        return
    if stream.int_in_range(0, 1):
        idx = _safe_index(stream, len(grid.entities))
        del grid.entities[idx]
    else:
        n = len(grid.entities)
        a = stream.int_in_range(0, n)
        b = stream.int_in_range(a, n)
        del grid.entities[a:b]


def _op_transfer(stream, grids, entities):
    """e.grid = other_grid - THE critical gridstate-overflow path (#258-#263).

    Prefers picking a source and target grid of *different* sizes so every
    transfer stresses ensureGridstate's resize logic.
    """
    if len(grids) < 2 or not entities:
        return
    ent = _pick_entity(stream, entities)
    # Try to pick a grid whose size differs from entity's current grid
    target = _pick_grid(stream, grids)
    if target is None:
        return
    try:
        ent.grid = target
    except EXPECTED_EXCEPTIONS:
        pass


def _op_set_grid_none(stream, grids, entities):
    """Detach an entity from its grid - exercises #274 spatial hash removal."""
    ent = _pick_entity(stream, entities)
    if ent is None:
        return
    try:
        ent.grid = None
    except EXPECTED_EXCEPTIONS:
        pass


def _op_die(stream, grids, entities):
    """Call e.die() outside iteration - plain lifecycle path."""
    ent = _pick_entity(stream, entities)
    if ent is None:
        return
    try:
        ent.die()
    except EXPECTED_EXCEPTIONS:
        pass
    # Don't remove from entities list - let the pool hold a dead reference;
    # the next op that touches it should hit defensive paths.


def _op_iterate_and_mutate(stream, grids, entities):
    """Iterate grid.entities and mid-loop call die() or reassign grid.

    Targets #273 directly: the iterator must raise RuntimeError rather than
    UB. We swallow the RuntimeError because it's the correct behaviour.
    We also exercise a safe pattern (collect-then-die) in the other branch.
    """
    grid = _pick_grid(stream, grids)
    if grid is None or len(grid.entities) == 0:
        return
    mode = stream.int_in_range(0, 2)
    if mode == 0:
        # Unsafe: mutate mid-iter. Should raise RuntimeError.
        try:
            for ent in grid.entities:
                if stream.remaining < 1:
                    break
                if stream.int_in_range(0, 1):
                    ent.die()
                else:
                    # Reassign to a different grid mid-iter.
                    other = _pick_grid(stream, grids)
                    if other is not None and other is not grid:
                        ent.grid = other
        except EXPECTED_EXCEPTIONS:
            pass
    elif mode == 1:
        # Safe: collect then mutate.
        snapshot = list(grid.entities)
        for ent in snapshot:
            if stream.remaining < 1:
                break
            if stream.int_in_range(0, 3) == 0:
                try:
                    ent.die()
                except EXPECTED_EXCEPTIONS:
                    pass
    else:
        # Read-only iteration with incidental queries
        total = 0
        for ent in grid.entities:
            total += 1
            if total > 64:
                break


# Dispatch table - each op is (min_bytes, callable)
_OPS = [
    _op_new_grid,               # 0
    _op_new_entity,             # 1
    _op_append,                 # 2
    _op_insert,                 # 3
    _op_extend,                 # 4
    _op_remove,                 # 5
    _op_pop,                    # 6
    _op_setitem,                # 7
    _op_slice_assign,           # 8
    _op_del_index,              # 9
    _op_transfer,               # 10
    _op_set_grid_none,          # 11
    _op_die,                    # 12
    _op_iterate_and_mutate,     # 13
]


def fuzz_one_input(data):
    """libFuzzer entry point.

    Called by the C++ harness for every iteration. fuzz_common.safe_reset() is
    invoked BEFORE this function, so mcrfpy.current_scene is clear. We rebuild
    our local state from scratch each call so inputs are independent and
    reproducible from a crashing seed.
    """
    stream = ByteStream(data)
    if stream.remaining < 2:
        return

    try:
        # Seed the pool: one grid, zero entities. Ops will grow both pools.
        initial_grids = stream.int_in_range(1, MAX_GRIDS)
        grids = []
        for _ in range(initial_grids):
            try:
                grids.append(_make_grid(stream))
            except EXPECTED_EXCEPTIONS:
                pass
        entities = []

        n_ops = stream.int_in_range(1, MAX_OPS)
        for _ in range(n_ops):
            if stream.remaining < 2:
                break
            op_idx = stream.int_in_range(0, len(_OPS) - 1)
            try:
                _OPS[op_idx](stream, grids, entities)
            except EXPECTED_EXCEPTIONS:
                # One failing op must not abort the rest of the iteration.
                # libFuzzer needs to see coverage from subsequent ops.
                pass
    except EXPECTED_EXCEPTIONS:
        pass
    finally:
        # Drop local references so the next safe_reset() can fully clean up.
        # Entities retained in `entities` keep their C++ UIEntity alive, which
        # is fine - safe_reset only clears current_scene/timers.
        grids = None
        entities = None
