"""fuzz_pathfinding_behavior - Wave 2 W9 target (#283).

Fuzzes the pathfinding + agent-behavior surface:
- grid.get_dijkstra_map(root, diagonal_cost, collide) with bad inputs
- DijkstraMap.distance / path_from / step_from / to_heightmap
- grid.step(n=, turn_order=) driving behavior callbacks that mutate the
  entity list mid-iteration (adjacent to #273 die-during-iteration)
- entity.step / turn_order / default_behavior / target_label /
  sight_radius / move_speed mutation

API verified against src/UIGridPathfinding.cpp and src/UIEntity.cpp:
- get_dijkstra_map signature: (root, diagonal_cost=1.41, collide=<label_str|None>)
  -- `collide` is a label STRING, not a set of coords.
- DijkstraMap.path_from returns an AStarPath (walk/peek/remaining), not list.
- step callback signature is `callback(trigger, data)` (two args).
- grid.step signature: (n=1, turn_order=<int filter|None>). turn_order is an
  integer filter (-1 = all), not a list of entities.
- set_default_behavior / set_turn_order / set_sight_radius accept any int
  without range validation, so they will NOT raise on negatives -- that's
  fine for fuzzing, we just exercise them.
- Entity constructor accepts `grid_pos=(x, y)` and `grid=<Grid>` kwargs.

Contract: define fuzz_one_input(data: bytes) -> None. The C++ harness
(tests/fuzz/fuzz_common.cpp) calls this for every libFuzzer iteration.
Wraps work in try/except EXPECTED_EXCEPTIONS so Python noise doesn't
pollute libFuzzer output -- only ASan/UBSan report real bugs.
"""

import mcrfpy

from fuzz_common import ByteStream, EXPECTED_EXCEPTIONS


# ---------------------------------------------------------------------------
# Step callbacks
#
# Signature is callback(trigger, data) -- verified against
# tests/unit/entity_step_callback_test.py and src/UIGridPyMethods.cpp:708
# (fireStepCallback uses PyObject_CallFunction(callback, "OO", ...)).
# ---------------------------------------------------------------------------


def _noop_step(trigger, data):
    pass


def _die_step(entity_ref):
    """Factory: returns a callback that calls entity.die() (targets #273)."""
    def cb(trigger, data):
        try:
            entity_ref.die()
        except Exception:
            pass
    return cb


def _move_step(entity_ref, tx, ty):
    """Factory: returns a callback that moves the entity to (tx, ty)."""
    def cb(trigger, data):
        try:
            entity_ref.grid_pos = (tx, ty)
        except Exception:
            pass
    return cb


def _spawn_step(grid_ref, tx, ty, sink):
    """Factory: returns a callback that creates another entity on the grid."""
    def cb(trigger, data):
        try:
            ne = mcrfpy.Entity(grid_pos=(tx, ty), grid=grid_ref)
            sink.append(ne)
        except Exception:
            pass
    return cb


# ---------------------------------------------------------------------------
# Helpers for consuming fuzz bytes into position tuples.
# ---------------------------------------------------------------------------


def _rand_coord(stream, w, h, oob_chance=True):
    """Return an (x, y) tuple. 1/8 chance of out-of-bounds when oob_chance."""
    if oob_chance and (stream.u8() & 0x07) == 0:
        # Occasionally OOB
        return (
            stream.int_in_range(-4, w + 4),
            stream.int_in_range(-4, h + 4),
        )
    return (stream.int_in_range(0, w - 1), stream.int_in_range(0, h - 1))


def _pick_entity(stream, entities):
    if not entities:
        return None
    return stream.pick_one(entities)


# ---------------------------------------------------------------------------
# Op dispatch
# ---------------------------------------------------------------------------


NUM_OPS = 17


def _dispatch(op, stream, state):
    grid = state["grid"]
    entities = state["entities"]
    w = state["w"]
    h = state["h"]

    if op == 0:
        # Op 0: create an entity at a random position, cap at 8
        if len(entities) >= 8:
            return
        pos = _rand_coord(stream, w, h, oob_chance=False)
        e = mcrfpy.Entity(grid_pos=pos, grid=grid)
        entities.append(e)

    elif op == 1:
        # Op 1: set entity.step = noop
        e = _pick_entity(stream, entities)
        if e is not None:
            e.step = _noop_step

    elif op == 2:
        # Op 2: set entity.step = die()-callback (iteration-safety stress)
        e = _pick_entity(stream, entities)
        if e is not None:
            e.step = _die_step(e)

    elif op == 3:
        # Op 3: set entity.step = move callback
        e = _pick_entity(stream, entities)
        if e is not None:
            tx, ty = _rand_coord(stream, w, h, oob_chance=True)
            e.step = _move_step(e, tx, ty)

    elif op == 4:
        # Op 4: set entity.step = spawn callback (grows entity list in-callback)
        e = _pick_entity(stream, entities)
        if e is not None:
            tx, ty = _rand_coord(stream, w, h, oob_chance=False)
            e.step = _spawn_step(grid, tx, ty, entities)

    elif op == 5:
        # Op 5: mutate turn_order (including 0 = skip, negatives)
        e = _pick_entity(stream, entities)
        if e is not None:
            e.turn_order = stream.int_in_range(-5, 10)

    elif op == 6:
        # Op 6: mutate default_behavior (including out-of-range)
        e = _pick_entity(stream, entities)
        if e is not None:
            e.default_behavior = stream.int_in_range(-2, 15)

    elif op == 7:
        # Op 7: mutate target_label (ascii or None)
        e = _pick_entity(stream, entities)
        if e is not None:
            if stream.bool():
                e.target_label = None
            else:
                e.target_label = stream.ascii_str(max_len=8)

    elif op == 8:
        # Op 8: mutate sight_radius (including negative, huge)
        e = _pick_entity(stream, entities)
        if e is not None:
            e.sight_radius = stream.int_in_range(-5, 100)

    elif op == 9:
        # Op 9: mutate move_speed (0 = instant, nonsense floats)
        e = _pick_entity(stream, entities)
        if e is not None:
            e.move_speed = stream.float_in_range(-1.0, 5.0)

    elif op == 10:
        # Op 10: get_dijkstra_map with coord root (in-bounds usually, OOB occasionally)
        root = _rand_coord(stream, w, h, oob_chance=True)
        state["djm"] = grid.get_dijkstra_map(root=root)

    elif op == 11:
        # Op 11: get_dijkstra_map with entity root
        e = _pick_entity(stream, entities)
        if e is not None:
            state["djm"] = grid.get_dijkstra_map(root=e)

    elif op == 12:
        # Op 12: get_dijkstra_map with a diagonal_cost (negative/huge/nonsense)
        root = _rand_coord(stream, w, h, oob_chance=False)
        dc = stream.float_in_range(-2.0, 10.0)
        state["djm"] = grid.get_dijkstra_map(root=root, diagonal_cost=dc)

    elif op == 13:
        # Op 13: get_dijkstra_map with a collide label (string or None)
        root = _rand_coord(stream, w, h, oob_chance=False)
        if stream.bool():
            label = None
        else:
            label = stream.ascii_str(max_len=6)
        state["djm"] = grid.get_dijkstra_map(root=root, collide=label)

    elif op == 14:
        # Op 14: query djm.distance(pos) including OOB
        djm = state["djm"]
        if djm is not None:
            q = _rand_coord(stream, w, h, oob_chance=True)
            djm.distance(q)

    elif op == 15:
        # Op 15: query djm.path_from(pos) -- returns AStarPath, exercise it
        djm = state["djm"]
        if djm is not None:
            q = _rand_coord(stream, w, h, oob_chance=True)
            path = djm.path_from(q)
            # Exercise AStarPath properties
            if path is not None:
                try:
                    _ = path.remaining
                except EXPECTED_EXCEPTIONS:
                    pass
                try:
                    _ = path.origin
                except EXPECTED_EXCEPTIONS:
                    pass
                try:
                    _ = path.destination
                except EXPECTED_EXCEPTIONS:
                    pass
                # Walk a few steps if available
                for _ in range(stream.int_in_range(0, 4)):
                    try:
                        path.walk()
                    except EXPECTED_EXCEPTIONS:
                        break

    elif op == 16:
        # Op 16: query djm.step_from(pos) and djm.to_heightmap()
        djm = state["djm"]
        if djm is not None:
            q = _rand_coord(stream, w, h, oob_chance=True)
            djm.step_from(q)
            hm = djm.to_heightmap()
            if hm is not None:
                # Read a few cells from the heightmap
                for _ in range(stream.int_in_range(0, 3)):
                    try:
                        hx = stream.int_in_range(0, w - 1)
                        hy = stream.int_in_range(0, h - 1)
                        _ = hm[hx, hy]
                    except EXPECTED_EXCEPTIONS:
                        break


def _dispatch_step(stream, state):
    """Fire grid.step() with random n / turn_order filter. Separate op so
    we can mix it with regular ops in the main loop."""
    grid = state["grid"]
    mode = stream.u8() & 0x03
    if mode == 0:
        grid.step()
    elif mode == 1:
        grid.step(n=stream.int_in_range(0, 5))
    elif mode == 2:
        grid.step(turn_order=stream.int_in_range(-2, 5))
    else:
        grid.step(n=stream.int_in_range(0, 3),
                  turn_order=stream.int_in_range(-1, 5))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def fuzz_one_input(data):
    stream = ByteStream(data)
    try:
        w = stream.int_in_range(2, 16)
        h = stream.int_in_range(2, 16)
        grid = mcrfpy.Grid(grid_size=(w, h))

        # Attach grid to a scene so behavior callbacks have a consistent world.
        try:
            scene = mcrfpy.Scene("fuzz_pb")
            mcrfpy.current_scene = scene
            scene.children.append(grid)
        except EXPECTED_EXCEPTIONS:
            pass

        state = {
            "grid": grid,
            "entities": [],
            "djm": None,
            "w": w,
            "h": h,
        }

        n_ops = stream.int_in_range(1, 30)
        for _ in range(n_ops):
            if stream.remaining < 1:
                break

            # Occasionally fire grid.step() to drive callbacks that mutate state.
            # This sits BEFORE the dispatch so callbacks still run even when we
            # run out of ops.
            if (stream.u8() & 0x0f) == 0:
                try:
                    _dispatch_step(stream, state)
                except EXPECTED_EXCEPTIONS:
                    pass
                continue

            op = stream.u8() % NUM_OPS
            try:
                _dispatch(op, stream, state)
            except EXPECTED_EXCEPTIONS:
                pass

        # Op 17 per plan: rapid iteration -- fire grid.step() several times
        # at the end with callbacks still installed, each call may mutate the
        # entity list (spawn, die, move). Use the remaining bytes to decide
        # how many rounds.
        if stream.remaining >= 1:
            rounds = stream.int_in_range(0, 10)
            for _ in range(rounds):
                try:
                    grid.step()
                except EXPECTED_EXCEPTIONS:
                    pass

    except EXPECTED_EXCEPTIONS:
        pass
