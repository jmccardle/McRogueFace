#!/usr/bin/env python3
"""
Semantics test for issue #329: grid.entities backed by std::vector.

Pins the observable behavior of the EntityCollection sequence after the
container swap from std::list to std::vector:

  * indexing (positive and negative)
  * out-of-range IndexError
  * slicing returns a plain list
  * iteration yields every element in order
  * mutation during iteration raises RuntimeError (size-guard / generation
    check) -- iteration is index-based, so this is well-defined and can
    never corrupt memory even in the remove+add "same size" case
  * grid.step() turn processing is immune to entity death mid-step
    (it snapshots into a vector internally)

These behaviors match the pre-#329 std::list implementation; the swap is a
purely internal container change.
"""

import mcrfpy
import sys

results = []


def check(name, cond):
    results.append((name, bool(cond)))
    print(("  ok  " if cond else " FAIL") + " : " + name)


def make_grid(name, count):
    scene = mcrfpy.Scene(name)
    grid = mcrfpy.Grid(grid_size=(50, 50), pos=(0, 0), size=(400, 400))
    scene.children.append(grid)
    ents = grid.entities
    made = []
    for i in range(count):
        e = mcrfpy.Entity((i, i))
        ents.append(e)
        made.append(e)
    return grid, ents, made


def test_indexing():
    grid, ents, made = make_grid("m_idx", 5)
    check("len == 5", len(ents) == 5)
    check("positive index [0] is first", ents[0] is not None)
    # identity is preserved through the cache: the same Entity comes back
    check("index preserves identity", ents[2] is made[2])
    check("negative index [-1] == [4]", ents[-1] is made[4])
    check("negative index [-5] == [0]", ents[-5] is made[0])


def test_out_of_range():
    grid, ents, made = make_grid("m_oob", 3)
    got = False
    try:
        _ = ents[3]
    except IndexError:
        got = True
    check("index 3 raises IndexError", got)

    got = False
    try:
        _ = ents[-4]
    except IndexError:
        got = True
    check("index -4 raises IndexError", got)


def _same_entity(a, b):
    # Slicing returns fresh Entity wrappers (it does not consult the identity
    # cache), so compare the underlying entity by its distinguishing position
    # rather than Python object identity. Each entity i was created at (i, i).
    return a.pos.x == b.pos.x and a.pos.y == b.pos.y


def test_slicing():
    grid, ents, made = make_grid("m_slice", 6)
    sl = ents[1:4]
    check("slice returns list", isinstance(sl, list))
    check("slice length correct", len(sl) == 3)
    check("slice contents in order",
          _same_entity(sl[0], made[1]) and _same_entity(sl[1], made[2])
          and _same_entity(sl[2], made[3]))

    sl2 = ents[::2]
    check("extended slice length", len(sl2) == 3)
    check("extended slice contents",
          _same_entity(sl2[0], made[0]) and _same_entity(sl2[1], made[2])
          and _same_entity(sl2[2], made[4]))

    sl3 = ents[-2:]
    check("negative slice contents",
          len(sl3) == 2 and _same_entity(sl3[0], made[4])
          and _same_entity(sl3[1], made[5]))


def test_iteration_order():
    grid, ents, made = make_grid("m_iter", 5)
    seen = [e for e in ents]
    check("iteration visits all", len(seen) == 5)
    check("iteration in order",
          all(seen[i] is made[i] for i in range(5)))


def test_mutation_during_iteration():
    grid, ents, made = make_grid("m_mut", 5)
    # Removing during iteration changes size -> well-defined RuntimeError.
    raised = False
    try:
        for e in ents:
            ents.remove(e)
    except RuntimeError:
        raised = True
    check("remove during iteration raises RuntimeError", raised)

    # append during iteration also raises (size changed).
    grid2, ents2, made2 = make_grid("m_mut2", 3)
    raised = False
    try:
        for e in ents2:
            ents2.append(mcrfpy.Entity((30, 30)))
            break_now = len(ents2) > 6  # guard against infinite loop if no raise
            if break_now:
                break
    except RuntimeError:
        raised = True
    check("append during iteration raises RuntimeError", raised)


def test_step_immune_to_death():
    # grid.step() must snapshot internally so an entity dying mid-step
    # (removing itself from the collection) cannot invalidate the loop.
    scene = mcrfpy.Scene("m_step")
    grid = mcrfpy.Grid(grid_size=(20, 20), pos=(0, 0), size=(200, 200))
    scene.children.append(grid)
    ents = grid.entities

    removed = []
    for i in range(5):
        e = mcrfpy.Entity((i, 0))
        e.turn_order = 1
        # PATH behavior with an empty path resolves to DONE on the first
        # step, which fires the `step` callback deterministically.
        e.set_behavior(int(mcrfpy.Behavior.PATH))

        def on_step(trigger, data, _e=e):
            # On its turn, remove itself from the grid mid-step.
            try:
                grid.entities.remove(_e)
                removed.append(_e)
            except ValueError:
                pass

        e.step = on_step
        ents.append(e)

    before = len(ents)
    # Must not crash even though each callback mutates the live collection
    # while step() is iterating its internal snapshot.
    grid.step(1)
    after = len(ents)
    check("grid.step() survived mid-step self-removal (len %d -> %d, "
          "%d removed)" % (before, after, len(removed)), True)
    # If callbacks fired (expected), entities were actually removed.
    check("mid-step removals took effect", after == before - len(removed))


def main():
    test_indexing()
    test_out_of_range()
    test_slicing()
    test_iteration_order()
    test_mutation_during_iteration()
    test_step_immune_to_death()

    failed = [n for n, ok in results if not ok]
    if failed:
        print("\nFAIL: %d checks failed: %s" % (len(failed), ", ".join(failed)))
        return False
    print("\nPASS: all %d checks passed" % len(results))
    return True


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
