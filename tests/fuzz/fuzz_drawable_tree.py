"""Fuzz target: drawable membership, identity pins and GC ownership (0.3.0).

Attacks the semantics described in CLAUDE.md under "Identity pin" (#436,
#443), "Membership" (#442, #447, #438), "Render invalidation" (#427, #446)
and "GC ownership" (#441):

- A drawable has ONE parent (a drawable or a Scene); every add MOVES it.
  Cycles are refused with ValueError before anything is mutated; a slice
  assignment naming one object twice raises ValueError and commits nothing.
- While a C++ container owns an object, its live Python wrapper (plain or a
  Python subclass) is pinned: fetching it back from the container returns the
  same object, of the same type, with its Python attributes intact, even after
  every Python reference to it was dropped and gc.collect() ran.
- The GC may only traverse/clear callbacks of objects a wrapper owns
  exclusively; a closure on a contained object must survive collection.
- An entity belongs to one GridData; a layer to one GridData.

A small pool of Frames/Captions/Sprites/GridViews (and Python subclasses of
each, carrying an attribute and on_click closures that capture other pool
objects -- reference cycles through C++) is driven by byte-selected ops across
several parents and two scenes, with GridData shared between views, entity
moves, layer add/remove, cache_subtree toggling, animations and mcrfpy.step().

After every op the harness checks the membership/identity invariants. A
violation raises AssertionError, which is deliberately NOT in
EXPECTED_EXCEPTIONS. The C++ harness (fuzz_common.cpp) clears any Python
exception that escapes fuzz_one_input, so on AssertionError we print the
traceback and os.abort(): libFuzzer treats SIGABRT as a crash and writes the
input as an artifact. Set ABORT_ON_ASSERT = False (e.g. in a repro script) to
get a plain exception instead.

Identity is tracked through C++-side state only (the drawable's `name`), never
through Python references, so a dropped-and-refetched wrapper can be checked:
names starting with "s" belong to subclass instances, whose `tag` attribute
must equal their name and whose type must be the recorded subclass.
"""

import gc
import os
import sys
import traceback

import mcrfpy

from fuzz_common import ByteStream, EXPECTED_EXCEPTIONS


ABORT_ON_ASSERT = True

# Caps: keep each iteration small and fast under ASan + debug CPython.
MAX_DRAWABLES = 12
MAX_GRIDDATA = 3
MAX_ENTITIES = 8
MAX_LAYERS = 4
MAX_OPS = 40
MAX_GRID_DIM = 8
MAX_WALK = 96          # bound on nodes visited by the invariant walk
SCENE_NAMES = ("fuzz_dt_s0", "fuzz_dt_s1")


# --------------------------------------------------------------------------
# Python subclasses. `tag` lives in the instance __dict__, i.e. only on the
# wrapper: if the identity pin fails, a refetch yields a fresh base-type
# wrapper without it.
# --------------------------------------------------------------------------

class SubFrame(mcrfpy.Frame):
    pass


class SubCaption(mcrfpy.Caption):
    pass


class SubSprite(mcrfpy.Sprite):
    pass


class SubGridView(mcrfpy.GridView):
    pass


class SubEntity(mcrfpy.Entity):
    pass


SUBCLASSES = {
    "SubFrame": SubFrame,
    "SubCaption": SubCaption,
    "SubSprite": SubSprite,
    "SubGridView": SubGridView,
    "SubEntity": SubEntity,
}


class Pool:
    """All per-iteration state. Holds the ONLY Python references the harness
    keeps; dropping an entry from these lists is how we drop references."""

    def __init__(self):
        self.scenes = []
        self.drawables = []
        self.datas = []
        self.entities = []
        self.layers = []
        # name -> (subclass name or None, has_handler). Strings/bools only,
        # so this never keeps an object alive.
        self.meta = {}
        self.counter = 0
        # Scenes are name-keyed in the engine; after a same-name Scene() is
        # constructed, an old Scene object resolves to the new one, so
        # scene-membership assertions stop being meaningful (see op).
        self.scene_checks = True

    def next_name(self, sub):
        self.counter += 1
        return ("s%d" if sub else "d%d") % self.counter


def _fail(msg):
    raise AssertionError(msg)


def _is_drawable(x):
    return isinstance(x, mcrfpy.Drawable)


def _has_children(x):
    return isinstance(x, (mcrfpy.Frame, mcrfpy.GridView, mcrfpy.Scene))


def _containers(pool):
    """Every container in the pool (scenes + drawables with children)."""
    out = []
    if pool.scene_checks:
        out.extend(pool.scenes)
    out.extend(x for x in pool.drawables if _has_children(x))
    return out


def _snapshot(pool):
    """Identity snapshot of every pool container's children (holds refs)."""
    return [(c, list(c.children)) for c in _containers(pool)]


def _assert_unchanged(before, what):
    for c, kids in before:
        now = list(c.children)
        if len(now) != len(kids) or any(a is not b for a, b in zip(now, kids)):
            _fail("%s raised ValueError but mutated %r: %d -> %d children"
                  % (what, c, len(kids), len(now)))


def _check_wrapper(pool, x):
    """Subclass/type/attribute/handler checks keyed by C++-side name."""
    name = x.name
    info = pool.meta.get(name)
    if info is None:
        return
    sub, has_handler = info
    if sub is not None:
        cls = SUBCLASSES[sub]
        if type(x) is not cls:
            _fail("identity pin lost subclass: %s came back as %s, expected %s"
                  % (name, type(x).__name__, sub))
        if getattr(x, "tag", None) != name:
            _fail("subclass wrapper %s lost its instance attribute" % name)
    if has_handler and _is_drawable(x):
        if x.on_click is None:
            _fail("on_click handler of contained %s was cleared" % name)


def _check_invariants(pool):
    seen = {}            # id(child) -> container (also keeps refs alive)
    keep = []
    stack = list(_containers(pool))
    visited = 0
    visited_containers = set()
    while stack and visited < MAX_WALK:
        c = stack.pop()
        if id(c) in visited_containers:
            continue
        visited_containers.add(id(c))
        keep.append(c)
        kids = list(c.children)
        n = len(c.children)
        if n != len(kids):
            _fail("len(children)=%d but iteration gave %d" % (n, len(kids)))
        for i, k in enumerate(kids):
            visited += 1
            keep.append(k)
            if c.children[i] is not k:
                _fail("children[%d] is not the object iteration returned" % i)
            p1 = k.parent
            if p1 is not k.parent:
                _fail("x.parent is x.parent failed for %r" % (k,))
            if p1 is not c:
                _fail("child %r of %r reports parent %r" % (k, c, p1))
            if id(k) in seen:
                _fail("drawable %r appears in two child slots" % (k,))
            seen[id(k)] = c
            _check_wrapper(pool, k)
            if _has_children(k):
                stack.append(k)

    # Every pool drawable with a parent is in exactly that parent's children.
    for x in pool.drawables:
        p = x.parent
        if p is not x.parent:
            _fail("x.parent is x.parent failed for pool %r" % (x,))
        _check_wrapper(pool, x)
        if p is None:
            continue
        if isinstance(p, mcrfpy.Scene) and not pool.scene_checks:
            continue
        hits = sum(1 for k in p.children if k is x)
        if hits != 1:
            _fail("%r has parent %r but appears %d times in its children"
                  % (x, p, hits))

    # Entities: e.grid is the GridData whose entities contain it, once.
    datas = list(pool.datas)
    for v in pool.drawables:
        if isinstance(v, mcrfpy.GridView):
            gd = v.grid_data
            if gd is not v.grid_data:
                _fail("view.grid_data is view.grid_data failed")
            if gd is not None:
                datas.append(gd)
    ent_seen = {}
    data_seen = set()
    for d in datas:
        if id(d) in data_seen:
            continue
        data_seen.add(id(d))
        for e in d.entities:
            keep.append(e)
            g = e.grid
            if g is not d:
                _fail("entity %r in %r reports grid %r" % (e, d, g))
            if id(e) in ent_seen and ent_seen[id(e)] is not d:
                _fail("entity %r in two GridData" % (e,))
            if id(e) in ent_seen:
                _fail("entity %r twice in one GridData" % (e,))
            ent_seen[id(e)] = d
            _check_wrapper(pool, e)
    for e in pool.entities:
        g = e.grid
        if g is not e.grid:
            _fail("entity.grid is entity.grid failed")
        if g is not None:
            hits = sum(1 for k in g.entities if k is e)
            if hits != 1:
                _fail("entity %r has grid but appears %d times" % (e, hits))
    # Layers: attached iff listed.
    for L in pool.layers:
        g = L.grid
        if g is not None and not any(x is L for x in g.layers):
            _fail("layer %r reports grid %r that does not list it" % (L, g))


# --------------------------------------------------------------------------
# Construction
# --------------------------------------------------------------------------

def _pick(stream, seq):
    if not seq:
        return None
    return seq[stream.int_in_range(0, len(seq) - 1)]


def _cap_append(stream, lst, obj, cap):
    if len(lst) >= cap:
        lst.pop(stream.int_in_range(0, len(lst) - 1))
    lst.append(obj)


def _new_data(stream, pool):
    w = stream.int_in_range(1, MAX_GRID_DIM)
    h = stream.int_in_range(1, MAX_GRID_DIM)
    d = mcrfpy.GridData(grid_size=(w, h))
    _cap_append(stream, pool.datas, d, MAX_GRIDDATA)
    return d


def _new_drawable(stream, pool):
    kind = stream.u8() % 10
    sub = kind >= 6
    name = pool.next_name(sub)
    pos = (stream.int_in_range(0, 64), stream.int_in_range(0, 64))
    base = kind % 6 if not sub else kind - 6   # sub: 0..3
    if base == 0:
        cls = SubFrame if sub else mcrfpy.Frame
        x = cls(pos=pos, size=(stream.int_in_range(0, 64),
                                stream.int_in_range(0, 64)), name=name)
    elif base == 1:
        cls = SubCaption if sub else mcrfpy.Caption
        x = cls(text=name, pos=pos, name=name)
    elif base == 2:
        cls = SubSprite if sub else mcrfpy.Sprite
        x = cls(pos=pos, name=name)
    elif base == 3:
        cls = SubGridView if sub else mcrfpy.GridView
        if pool.datas and stream.bool():
            x = cls(grid=_pick(stream, pool.datas), pos=pos, size=(32, 32),
                    name=name)
        else:
            x = cls(grid_size=(stream.int_in_range(1, MAX_GRID_DIM),
                               stream.int_in_range(1, MAX_GRID_DIM)),
                    pos=pos, size=(32, 32), name=name)
    elif base == 4:
        x = mcrfpy.Line(start=pos, end=(0, 0), name=name)
    else:
        x = mcrfpy.Circle(center=pos, radius=4, name=name)
    if sub:
        x.tag = name
        pool.meta[name] = (type(x).__name__, False)
    _cap_append(stream, pool.drawables, x, MAX_DRAWABLES)
    return x


def _new_entity(stream, pool):
    sub = stream.bool()
    name = pool.next_name(sub)
    cls = SubEntity if sub else mcrfpy.Entity
    e = cls(grid_pos=(stream.int_in_range(0, MAX_GRID_DIM - 1),
                      stream.int_in_range(0, MAX_GRID_DIM - 1)), name=name)
    if sub:
        e.tag = name
        pool.meta[name] = ("SubEntity", False)
    _cap_append(stream, pool.entities, e, MAX_ENTITIES)
    return e


def _pick_container(stream, pool):
    conts = [x for x in pool.drawables if _has_children(x)]
    conts.extend(pool.scenes)
    return _pick(stream, conts)


def _pick_child(stream, pool):
    """Mostly an existing pool drawable; sometimes something already contained
    (possibly with no Python reference anywhere but its container)."""
    if pool.drawables and stream.u8() % 4 != 0:
        return _pick(stream, pool.drawables)
    c = _pick_container(stream, pool)
    if c is not None and len(c.children):
        return c.children[stream.int_in_range(0, len(c.children) - 1)]
    return _new_drawable(stream, pool)


def _expect_parent(pool, child, parent):
    if isinstance(parent, mcrfpy.Scene) and not pool.scene_checks:
        return
    p = child.parent
    if p is not parent:
        _fail("after add, %r.parent is %r, expected %r" % (child, p, parent))
    hits = [i for i, k in enumerate(parent.children) if k is child]
    if len(hits) != 1:
        _fail("after add, %r appears %d times in parent" % (child, len(hits)))
    got = parent.children[hits[0]]
    if got is not child or type(got) is not type(child):
        _fail("refetched child is not the appended object")


# --------------------------------------------------------------------------
# Ops
# --------------------------------------------------------------------------

def _guarded_add(pool, what, fn, child, parent):
    """Run an add-type op. On ValueError nothing may have changed."""
    before = _snapshot(pool)
    try:
        fn()
    except ValueError:
        _assert_unchanged(before, what)
        return
    if child is not None and parent is not None:
        _expect_parent(pool, child, parent)


def _op_new(stream, pool):
    if stream.u8() % 4 == 0:
        _new_data(stream, pool)
    else:
        _new_drawable(stream, pool)


def _op_append(stream, pool):
    p = _pick_container(stream, pool)
    x = _pick_child(stream, pool)
    if p is None or x is None:
        return
    _guarded_add(pool, "append", lambda: p.children.append(x), x, p)


def _op_insert(stream, pool):
    p = _pick_container(stream, pool)
    x = _pick_child(stream, pool)
    if p is None or x is None:
        return
    i = stream.int_in_range(-2, len(p.children) + 1)
    _guarded_add(pool, "insert", lambda: p.children.insert(i, x), x, p)


def _op_extend(stream, pool):
    p = _pick_container(stream, pool)
    if p is None:
        return
    batch = [_pick_child(stream, pool) for _ in range(stream.int_in_range(0, 3))]
    _guarded_add(pool, "extend", lambda: p.children.extend(batch), None, None)
    if not pool.scene_checks and isinstance(p, mcrfpy.Scene):
        return
    for x in batch:
        if x.parent is not p and any(x is k for k in p.children):
            _fail("extended %r is in %r but reports parent %r" % (x, p, x.parent))


def _op_setitem(stream, pool):
    p = _pick_container(stream, pool)
    x = _pick_child(stream, pool)
    if p is None or x is None or len(p.children) == 0:
        return
    i = stream.int_in_range(-len(p.children), len(p.children) - 1)

    def go():
        p.children[i] = x
    _guarded_add(pool, "setitem", go, x, p)


def _op_slice_assign(stream, pool):
    p = _pick_container(stream, pool)
    if p is None:
        return
    n = len(p.children)
    a = stream.int_in_range(0, n)
    b = stream.int_in_range(a, n)
    batch = [_pick_child(stream, pool) for _ in range(stream.int_in_range(0, 3))]
    dup = bool(batch) and stream.u8() % 3 == 0
    if dup:
        batch.insert(stream.int_in_range(0, len(batch)), _pick(stream, batch))
    extended = stream.bool() and a < b
    step = stream.int_in_range(1, 3) if extended else 1
    if extended:
        want = (b - a + step - 1) // step
        while len(batch) > want:
            batch.pop()
    before = _snapshot(pool)

    def go():
        if extended:
            p.children[a:b:step] = batch
        else:
            p.children[a:b] = batch
    has_dup = len({id(o) for o in batch}) != len(batch)
    try:
        go()
    except ValueError:
        _assert_unchanged(before, "slice assignment")
        return
    if has_dup:
        _fail("slice assignment naming one drawable twice did not raise")
    for x in batch:
        _expect_parent(pool, x, p)


def _op_delete(stream, pool):
    p = _pick_container(stream, pool)
    if p is None or len(p.children) == 0:
        return
    n = len(p.children)
    m = stream.u8() % 4
    if m == 0:
        del p.children[stream.int_in_range(0, n - 1)]
    elif m == 1:
        a = stream.int_in_range(0, n)
        del p.children[a:stream.int_in_range(a, n):stream.int_in_range(1, 2)]
    elif m == 2:
        x = p.children[stream.int_in_range(0, n - 1)]
        p.children.remove(x)
        if x.parent is not None:
            _fail("removed %r still reports parent %r" % (x, x.parent))
    else:
        x = p.children.pop(stream.int_in_range(-n, n - 1)) if stream.bool() \
            else p.children.pop()
        if x.parent is not None:
            _fail("popped %r still reports parent %r" % (x, x.parent))


def _op_cycle(stream, pool):
    """Add an ancestor (or self) into a descendant: must raise, not mutate."""
    xs = [x for x in pool.drawables if _has_children(x)]
    x = _pick(stream, xs)
    if x is None:
        return
    chain = [x]
    p = x.parent
    while _is_drawable(p) and len(chain) < 16:
        chain.append(p)
        p = p.parent
    anc = _pick(stream, chain)
    before = _snapshot(pool)
    mode = stream.u8() % 4
    try:
        if mode == 0:
            x.children.append(anc)
        elif mode == 1:
            x.children.insert(0, anc)
        elif mode == 2:
            x.children[0:0] = [anc]
        else:
            anc.parent = x
    except ValueError:
        _assert_unchanged(before, "cycle attempt")
        return
    _fail("adding ancestor %r into %r did not raise" % (anc, x))


def _op_parent_assign(stream, pool):
    x = _pick_child(stream, pool)
    if x is None:
        return
    m = stream.u8() % 3
    if m == 0:
        target = None
    elif m == 1:
        target = _pick(stream, pool.scenes)
    else:
        target = _pick_container(stream, pool)
    _guarded_add(pool, "parent=", lambda: setattr(x, "parent", target), x, target)
    if target is None and x.parent is not None:
        _fail("parent = None left %r with parent %r" % (x, x.parent))


def _make_handler(captured):
    def handler(pos, button, action):
        total = 0
        for o in captured:
            if _is_drawable(o):
                _ = o.parent
                if _has_children(o):
                    total += len(o.children)
            elif isinstance(o, mcrfpy.Entity):
                _ = o.grid
        return total
    return handler


def _op_set_click(stream, pool):
    x = _pick_child(stream, pool)
    if x is None or not hasattr(x, "on_click"):
        return
    captured = [x] if stream.bool() else []
    for _ in range(stream.int_in_range(0, 3)):
        o = _pick(stream, pool.drawables + pool.entities)
        if o is not None:
            captured.append(o)
    x.on_click = _make_handler(captured)
    info = pool.meta.get(x.name)
    pool.meta[x.name] = (info[0] if info else None, True)


def _op_drop_refs(stream, pool):
    """Drop Python references to random pool objects, then collect."""
    for _ in range(stream.int_in_range(1, 4)):
        lst = _pick(stream, [pool.drawables, pool.drawables, pool.entities,
                             pool.datas, pool.layers])
        if lst:
            lst.pop(stream.int_in_range(0, len(lst) - 1))
    gc.collect()
    _op_walk(stream, pool)


def _op_walk(stream, pool):
    """Exercise survivors: walk trees, call stored closures."""
    stack = list(pool.scenes) + list(pool.drawables)
    n = 0
    vec = mcrfpy.Vector(0, 0)
    while stack and n < MAX_WALK:
        o = stack.pop()
        n += 1
        cb = getattr(o, "on_click", None)
        if cb is not None:
            cb(vec, mcrfpy.MouseButton.LEFT, mcrfpy.InputState.PRESSED)
        if _has_children(o):
            stack.extend(o.children)
        if isinstance(o, mcrfpy.GridView):
            for e in o.entities:
                _ = e.grid


def _pick_data(stream, pool):
    ds = list(pool.datas)
    ds.extend(v.grid_data for v in pool.drawables
              if isinstance(v, mcrfpy.GridView))
    return _pick(stream, ds)


def _op_entities(stream, pool):
    m = stream.u8() % 6
    if m == 0 or not pool.entities:
        _new_entity(stream, pool)
        return
    e = _pick(stream, pool.entities)
    # Target either a GridData or a view (whose .entities delegates).
    views = [v for v in pool.drawables if isinstance(v, mcrfpy.GridView)]
    tgt = _pick(stream, views) if (views and stream.bool()) else _pick_data(stream, pool)
    if tgt is None:
        return
    d = tgt if isinstance(tgt, mcrfpy.GridData) else tgt.grid_data
    if m == 1:
        tgt.entities.append(e)
    elif m == 2:
        tgt.entities.insert(stream.int_in_range(0, len(tgt.entities)), e)
    elif m == 3:
        e.grid = tgt if stream.bool() else None
        return
    elif m == 4:
        batch = [_pick(stream, pool.entities)
                 for _ in range(stream.int_in_range(0, 3))]
        n = len(tgt.entities)
        a = stream.int_in_range(0, n)
        has_dup = len({id(o) for o in batch}) != len(batch)
        try:
            tgt.entities[a:stream.int_in_range(a, n)] = batch
        except ValueError:
            return
        if has_dup:
            _fail("entity slice assignment with a duplicate did not raise")
        for o in batch:
            if o.grid is not d:
                _fail("entity slice-assigned into %r reports %r" % (d, o.grid))
        return
    else:
        if len(tgt.entities):
            if stream.bool():
                tgt.entities.pop()
            else:
                tgt.entities.remove(tgt.entities[0])
        return
    if e.grid is not d:
        _fail("entity added to %r reports grid %r" % (d, e.grid))


def _op_layers(stream, pool):
    m = stream.u8() % 4
    d = _pick_data(stream, pool)
    if m == 0 or not pool.layers:
        name = "L%d" % stream.u8()
        L = (mcrfpy.ColorLayer(name=name, z_index=stream.int_in_range(-2, 2))
             if stream.bool() else
             mcrfpy.TileLayer(name=name, z_index=stream.int_in_range(-2, 2)))
        _cap_append(stream, pool.layers, L, MAX_LAYERS)
        if d is not None and stream.bool():
            d.add_layer(L)
        return
    L = _pick(stream, pool.layers)
    if d is None:
        return
    if m == 1:
        d.add_layer(L)
    elif m == 2:
        g = L.grid
        if g is not None:
            g.remove_layer(L if stream.bool() else L.name)
        else:
            d.remove_layer(L)
    else:
        L.z_index = stream.int_in_range(-3, 3)
        L.visible = stream.bool()


def _op_cache_dirty(stream, pool):
    xs = [x for x in pool.drawables if isinstance(x, mcrfpy.Frame)]
    x = _pick(stream, xs)
    if x is not None:
        x.cache_subtree = stream.bool()
    y = _pick(stream, pool.drawables)
    if y is None:
        return
    m = stream.u8() % 4
    if m == 0:
        y.x = stream.float_in_range(-10, 100)
    elif m == 1:
        y.visible = stream.bool()
    elif m == 2 and isinstance(y, mcrfpy.GridView):
        y.center = (stream.float_in_range(0, 64), stream.float_in_range(0, 64))
        y.zoom = stream.float_in_range(0.25, 4.0)
    elif m == 3 and hasattr(y, "fill_color"):
        y.fill_color = (stream.u8(), stream.u8(), stream.u8())


def _op_step(stream, pool):
    m = stream.u8() % 3
    if m == 0:
        y = _pick(stream, pool.drawables)
        if y is not None:
            cap = [_pick(stream, pool.drawables)]
            y.animate("x", stream.float_in_range(0, 50),
                      stream.float_in_range(0.0, 0.05),
                      callback=lambda t, p, v: [o.parent for o in cap if o])
    elif m == 1 and pool.scenes:
        mcrfpy.current_scene = _pick(stream, pool.scenes)
    mcrfpy.step(stream.float_in_range(0.0, 0.05))


def _op_scene_replace(stream, pool):
    """Construct a Scene with a name already in use. Scenes are name-keyed:
    the old Scene object then resolves to the new one, so scene-membership
    checks are disabled for the rest of this iteration. That is #464: re-enable
    them when it's fixed."""
    if not pool.scenes or stream.u8() % 4 != 0:
        return
    i = stream.int_in_range(0, len(pool.scenes) - 1)
    pool.scene_checks = False
    pool.scenes[i] = mcrfpy.Scene(SCENE_NAMES[i])


_OPS = [
    _op_new,             # 0
    _op_append,          # 1
    _op_insert,          # 2
    _op_extend,          # 3
    _op_setitem,         # 4
    _op_slice_assign,    # 5
    _op_delete,          # 6
    _op_cycle,           # 7
    _op_parent_assign,   # 8
    _op_set_click,       # 9
    _op_drop_refs,       # 10
    _op_walk,            # 11
    _op_entities,        # 12
    _op_layers,          # 13
    _op_cache_dirty,     # 14
    _op_step,            # 15
    _op_new,             # 16 (weight construction up)
    _op_append,          # 17 (weight membership up)
    _op_scene_replace,   # 18
]


def _run(stream):
    pool = Pool()
    try:
        pool.scenes = [mcrfpy.Scene(n) for n in SCENE_NAMES]
        for _ in range(stream.int_in_range(1, 6)):
            try:
                _new_drawable(stream, pool)
            except EXPECTED_EXCEPTIONS:
                pass
        n_ops = stream.int_in_range(1, MAX_OPS)
        for _ in range(n_ops):
            if stream.remaining < 2:
                break
            op = _OPS[stream.int_in_range(0, len(_OPS) - 1)]
            try:
                op(stream, pool)
            except EXPECTED_EXCEPTIONS:
                pass
            _check_invariants(pool)
        # Final pass: drop everything but the scenes, collect, re-check what
        # the scenes still own (pins must keep subclass wrappers alive).
        pool.drawables = []
        pool.entities = []
        pool.datas = []
        pool.layers = []
        gc.collect()
        _check_invariants(pool)
        try:
            _op_walk(stream, pool)
        except EXPECTED_EXCEPTIONS:
            pass
    finally:
        for sc in pool.scenes:
            try:
                sc.children.clear()
            except Exception:
                pass
        pool = None
        gc.collect()


# Everything that exists at import time (stdlib, mcrfpy, this module) is
# immortal for our purposes. Freezing it moves it out of the collector's
# view, so the gc.collect() calls above only walk this iteration's objects:
# ~3x more iterations per second, with identical collection semantics for
# everything the harness creates.
gc.freeze()


def fuzz_one_input(data):
    """libFuzzer entry point (see module docstring for AssertionError)."""
    stream = ByteStream(data)
    if stream.remaining < 2:
        return
    try:
        _run(stream)
    except EXPECTED_EXCEPTIONS:
        pass
    except AssertionError:
        if not ABORT_ON_ASSERT:
            raise
        traceback.print_exc()
        sys.stderr.flush()
        sys.stdout.flush()
        os.abort()
