"""
#394 -- mcrfpy.set_random_seed() / mcrfpy.get_random_seed().

In-process properties of the seed surface itself. The cross-process replay claim
lives in tests/integration/random_seed_replay_test.py; this file covers what a
single process can see:

  * the seed echoes, and reading it does not disturb it;
  * an unset seed still answers, with a value that is stable for the process;
  * set_random_seed RESETS the streams rather than merely recording a number --
    the difference is invisible unless you run the same scenario twice without
    reseeding in between and check that it does NOT repeat;
  * argument validation is strict, because a silently truncated 2**32 would make
    two different seeds produce identical runs with nothing reporting it.
"""

import sys

import mcrfpy

failures = []


def check(condition, message):
    if not condition:
        failures.append(message)
    return condition


# --------------------------------------------------------------------------- #
# The scenario. Asymmetric on purpose: 13 x 9 (not square), a wall down column
# x == 6 with a doorway at y == 2 (not mirror-symmetric in y), four entities at
# unmirrored starts. A square grid with mirrored contents cannot detect a
# transposed index by construction.
# --------------------------------------------------------------------------- #
GRID_W, GRID_H = 13, 9
TURNS = 30
STARTS = [
    (2, 1, mcrfpy.Behavior.NOISE4),
    (3, 6, mcrfpy.Behavior.NOISE8),
    (9, 2, mcrfpy.Behavior.NOISE4),
    (11, 7, mcrfpy.Behavior.NOISE8),
]


def run_scenario(turns=TURNS):
    grid = mcrfpy.GridData(grid_size=(GRID_W, GRID_H))
    for y in range(GRID_H):
        for x in range(GRID_W):
            point = grid.at(x, y)
            border = (x == 0 or x == GRID_W - 1 or y == 0 or y == GRID_H - 1)
            wall = (x == 6 and y != 2)
            point.walkable = not (border or wall)
            point.transparent = point.walkable
    entities = []
    for (x, y, behavior) in STARTS:
        entity = mcrfpy.Entity((x, y), grid=grid)
        entity.set_behavior(behavior)
        entity.move_speed = 0
        entities.append(entity)
    trace = []
    for _ in range(turns):
        grid.step()
        trace.append(tuple((e.cell_x, e.cell_y) for e in entities))
    return trace


def distinct_cells(trace, index=0):
    return len({row[index] for row in trace})


# --------------------------------------------------------------------------- #
# 1. An unset seed still answers, and answers the same thing twice.
#    This must run FIRST, before any set_random_seed() call in this file.
# --------------------------------------------------------------------------- #
generated = mcrfpy.get_random_seed()
check(isinstance(generated, int) and not isinstance(generated, bool),
      "get_random_seed() must return an int, got %r" % (type(generated),))
check(0 <= generated <= 0xFFFFFFFF,
      "generated seed out of 32-bit range: %r" % (generated,))
check(mcrfpy.get_random_seed() == generated,
      "get_random_seed() must be stable, got %d then %d"
      % (generated, mcrfpy.get_random_seed()))

# Reading it must not be a side effect on the stream either: consuming randomness
# does not change the reported seed.
trace_gen = run_scenario()
check(mcrfpy.get_random_seed() == generated,
      "get_random_seed() changed after the scenario ran: %d -> %d"
      % (generated, mcrfpy.get_random_seed()))
print("unset seed materialised as %d and stayed put across a scenario" % generated)

# --------------------------------------------------------------------------- #
# 2. The generated seed is a real seed: replaying at it reproduces the run that
#    used it. (The cross-process form of this is the load-bearing one; this is the
#    same claim inside one process, which is cheap and catches a different half.)
# --------------------------------------------------------------------------- #
mcrfpy.set_random_seed(generated)
trace_replay = run_scenario()
check(trace_replay == trace_gen,
      "replaying at the seed the engine generated (%d) did not reproduce the run"
      % generated)

# --------------------------------------------------------------------------- #
# 3. The scenario is not a stopped clock. Every equality above and below is an
#    equality between movement traces; if nothing moved they would all hold for an
#    engine with no RNG at all.
# --------------------------------------------------------------------------- #
check(len(trace_gen) == TURNS,
      "scenario must record %d turns, got %d" % (TURNS, len(trace_gen)))
for i in range(len(STARTS)):
    moved = distinct_cells(trace_gen, i)
    check(moved >= 4,
          "entity %d must wander (>= 4 distinct cells in %d turns), got %d"
          % (i, TURNS, moved))
print("scenario: %d turns, entities visited %s distinct cells"
      % (TURNS, [distinct_cells(trace_gen, i) for i in range(len(STARTS))]))

# --------------------------------------------------------------------------- #
# 4. set_random_seed echoes.
# --------------------------------------------------------------------------- #
for value in (0, 1, 42, 4294967295, 20260727):
    mcrfpy.set_random_seed(value)
    got = mcrfpy.get_random_seed()
    check(got == value, "set_random_seed(%d) read back as %r" % (value, got))
print("seed echoes exactly for 0, 1, 42, 2**32-1 and 20260727")

# --------------------------------------------------------------------------- #
# 5. set_random_seed RESETS the streams -- it is not just a place to store a
#    number. The only way to see the difference is to run the same scenario twice
#    WITHOUT reseeding and require that it does not repeat.
# --------------------------------------------------------------------------- #
SEED = 20260727
mcrfpy.set_random_seed(SEED)
first = run_scenario()
second_no_reseed = run_scenario()
mcrfpy.set_random_seed(SEED)
third_after_reseed = run_scenario()

check(second_no_reseed != first,
      "two consecutive scenarios without reseeding produced the same trace -- the "
      "stream is not advancing, so the reset check below would be vacuous")
check(third_after_reseed == first,
      "set_random_seed(%d) did not rewind the stream: the run after reseeding "
      "differs from the first run at the same seed" % SEED)
print("set_random_seed rewinds: run1 != run2 (no reseed), run3 == run1 (reseeded)")

# --------------------------------------------------------------------------- #
# 6. Different seeds diverge -- what makes every equality above non-vacuous.
# --------------------------------------------------------------------------- #
mcrfpy.set_random_seed(SEED + 1)
other = run_scenario()
check(other != first,
      "seeds %d and %d produced identical traces -- the RNG is not being consulted"
      % (SEED, SEED + 1))
print("seeds %d and %d diverge" % (SEED, SEED + 1))

# --------------------------------------------------------------------------- #
# 7. Argument validation. A truncated seed is the dangerous case: 2**32 silently
#    becoming 0 would make two runs the caller believes are different identical.
# --------------------------------------------------------------------------- #
for bad, expected in [
    (-1, ValueError),
    (2 ** 32, ValueError),
    (2 ** 64 + 7, ValueError),
    ("42", TypeError),
    (1.5, TypeError),
    (None, TypeError),
    (True, TypeError),
]:
    try:
        mcrfpy.set_random_seed(bad)
    except expected:
        pass
    except Exception as exc:  # wrong exception type
        failures.append("set_random_seed(%r) raised %s, expected %s"
                        % (bad, type(exc).__name__, expected.__name__))
    else:
        failures.append("set_random_seed(%r) was accepted; expected %s"
                        % (bad, expected.__name__))

# A rejected seed must not have changed anything.
mcrfpy.set_random_seed(SEED)
try:
    mcrfpy.set_random_seed(2 ** 32)
except ValueError:
    pass
check(mcrfpy.get_random_seed() == SEED,
      "a rejected seed changed the seed in use: %d" % mcrfpy.get_random_seed())
print("out-of-range and wrong-typed seeds are rejected without side effects")

# --------------------------------------------------------------------------- #
if failures:
    for message in failures:
        print("FAILURE: %s" % message)
    print("%d check(s) did not hold" % len(failures))
    sys.exit(1)

print("PASS: #394 seed surface")
sys.exit(0)
