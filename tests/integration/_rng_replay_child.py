"""
Child process for tests/integration/random_seed_replay_test.py (#394).

Leading underscore: run_tests.py skips it, it is not a test on its own.

Runs one fixed scenario that consumes engine randomness (NOISE4/NOISE8 entity
behaviour) and prints a digest of the resulting movement trace. The parent
compares digests ACROSS PROCESSES, which is the only honest form of "replays
byte-identically at a fixed seed" -- an in-process A/B cannot see process-global
state that survives a reseed.

Environment:
    MCRF_RNG_SEED        optional. If set, set_random_seed(int(...)) is called as
                         the first thing the script does, before any grid or entity
                         exists. If unset, the run is UNSEEDED and the engine must
                         generate and record a seed of its own.
    MCRF_RNG_READ_ORDER  'before' (default) reads get_random_seed() before the
                         scenario runs; 'after' reads it once the scenario has
                         already consumed randomness. Both must report the seed the
                         run actually used.

Prints exactly four lines, then exits 0:
    SEED <int>
    DIGEST <sha256 hex of the movement trace>
    DISTINCT <number of distinct cells entity 0 visited>
    STEPS <number of recorded turns>
"""

import os
import sys
import hashlib

import mcrfpy

# --------------------------------------------------------------------------- #
# The seed is set BEFORE anything else touches the engine. That is the ordering
# requirement 1 names -- "settable before any behaviour runs" -- and putting it
# anywhere later would not test it.
# --------------------------------------------------------------------------- #
_seed_env = os.environ.get("MCRF_RNG_SEED")
if _seed_env is not None:
    mcrfpy.set_random_seed(int(_seed_env))

READ_ORDER = os.environ.get("MCRF_RNG_READ_ORDER", "before")

reported_seed = None
if READ_ORDER == "before":
    reported_seed = mcrfpy.get_random_seed()

# --------------------------------------------------------------------------- #
# The scenario.
#
# Deliberately ASYMMETRIC in every dimension, because a symmetric fixture cannot
# detect a transposition by construction:
#   * 17 x 11 grid -- not square, so an (x, y) swap indexes out of the map;
#   * the wall runs down a COLUMN (x == 8) with a doorway at y == 5, so swapping
#     the axes moves the obstacle somewhere else entirely;
#   * an extra blob at (3, 2), (4, 2), (3, 3) that is not mirror-symmetric;
#   * five entities at five distinct non-mirrored positions, mixing NOISE4 and
#     NOISE8 so both candidate-generation paths are exercised.
# --------------------------------------------------------------------------- #
GRID_W, GRID_H = 17, 11
TURNS = 40
STARTS = [
    (2, 1, mcrfpy.Behavior.NOISE4),
    (3, 7, mcrfpy.Behavior.NOISE8),
    (12, 2, mcrfpy.Behavior.NOISE4),
    (14, 9, mcrfpy.Behavior.NOISE8),
    (5, 4, mcrfpy.Behavior.NOISE4),
]
BLOB = {(3, 2), (4, 2), (3, 3)}


def build_scenario():
    grid = mcrfpy.GridData(grid_size=(GRID_W, GRID_H))
    for y in range(GRID_H):
        for x in range(GRID_W):
            point = grid.at(x, y)
            border = (x == 0 or x == GRID_W - 1 or y == 0 or y == GRID_H - 1)
            wall = (x == 8 and y != 5)
            point.walkable = not (border or wall or (x, y) in BLOB)
            point.transparent = point.walkable
    entities = []
    for (x, y, behavior) in STARTS:
        entity = mcrfpy.Entity((x, y), grid=grid)
        entity.set_behavior(behavior)
        entity.move_speed = 0  # instant: cell_x/cell_y settle inside step()
        entities.append(entity)
    return grid, entities


def run_scenario():
    grid, entities = build_scenario()
    trace = []
    for _ in range(TURNS):
        grid.step()
        trace.append(tuple((e.cell_x, e.cell_y) for e in entities))
    return trace


trace = run_scenario()

if READ_ORDER == "after":
    reported_seed = mcrfpy.get_random_seed()

digest = hashlib.sha256(repr(trace).encode("utf-8")).hexdigest()
distinct = len({row[0] for row in trace})

print("SEED %d" % reported_seed)
print("DIGEST %s" % digest)
print("DISTINCT %d" % distinct)
print("STEPS %d" % len(trace))
sys.exit(0)
