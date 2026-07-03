# API Stability Policy (1.0 Contract)

This document records the compatibility promises that freeze at McRogueFace 1.0.
Each item below is a **semantic decision that cannot be changed compatibly after
1.0** and was ratified in the 2026-07-02 pre-1.0 memory-model review. Additive,
opt-in APIs may still be introduced after 1.0; the guarantees here constrain
what those additions may assume.

The public `mcrfpy` surface (types, methods, properties, enum members,
functions, singletons, and each property's inferred type / read-only flag) is
guarded against accidental drift by
`tests/unit/api_surface_snapshot_test.py`, which diffs the live module against
a committed golden file. That test is the mechanical enforcement of this policy;
any intentional change to the surface must be a reviewed re-baseline of the
golden file.

## Value semantics for Color and Vector (#326)

`mcrfpy.Color` and `mcrfpy.Vector` are **value types, forever.** They store
their data inline (no shared references), and every property that returns a
Color or Vector returns a **fresh copy**. This matches how `sf::Color` /
`sf::Vector2f` behave in C++ and carries zero implementation risk. Write-through
proxy views were considered and rejected: they would freeze dangling-parent
lifetime and identity questions into the contract.

The direct consequence is that mutating a component of a color/vector obtained
from a property does **not** affect the original — it mutates a throwaway copy:

```python
frame.fill_color.r = 255   # NO-OP: mutates a temporary copy, then discards it
```

The two supported idioms are:

```python
# 1. Read-modify-writeback
c = frame.fill_color       # copy
c.r = 255                  # mutate the copy
frame.fill_color = c       # write the whole value back

# 2. Whole-value assignment
frame.fill_color = mcrfpy.Color(255, 0, 0)
```

This behavior is stated normatively in the `Color` and `Vector` class
docstrings and will not change in the 1.x series.

## Bulk-edit convention for writable views (#328)

Future zero-copy **writable** views over cell/buffer data (numpy / buffer
protocol) are exposed **only** through an `edit()` context manager:

```python
with layer.edit() as view:
    view[...] = ...        # write freely
# on __exit__, the affected state is conservatively invalidated
# (whole-layer markDirty / full TCOD resync + generation bump as applicable)
```

Forgetting to synchronize is impossible by construction, which applies the
project's fail-early principle to the API surface. The engine performs **no
automatic change detection**; invalidation is triggered unconditionally on
`__exit__`.

- **Read-only** zero-copy views (for example `DiscreteMap.mask()`) may still be
  exposed directly, with no `edit()` ceremony, because they cannot violate
  engine invariants.
- **No always-writable raw view + `mark_dirty()` primitives will be shipped.**
  If a genuine need for persistent writable views emerges after 1.0, such
  primitives can be added additively without breaking the `edit()` idiom.

This convention is the pattern that the buffer-protocol work must follow:
ColorLayer/TileLayer buffers (#335), related view APIs (#334), and any future
`grid.walkable` array view (which depends on the GridData SoA refactor, #332).

## Subinterpreters are out of scope for 1.x (#330)

Running mcrfpy in a Python subinterpreter is unsupported in 1.x; the module
declares `m_size = -1` and will refuse or misbehave. See #220.

The module uses single-phase initialization with global state (static
`PyTypeObject`s, cached enum singletons, and global engine pointers), so it
cannot be safely instantiated per-subinterpreter. Excluding subinterpreters from
the 1.0 promise leaves the later refactor (#220: heap types, multi-phase init,
per-interpreter module state) unconstrained. Heap-type conversion does not change
Python-visible behavior, so nothing else needs to be reserved for it.

## Related

- [Threading model](threading-model.md) — the `mcrfpy.lock()` off-main-thread
  contract, which likewise freezes at 1.0.
- `tests/unit/api_surface_snapshot_test.py` — enforcement mechanism for the
  public API surface.
