"""
#394 -- cross-process replay of the engine's internal RNG.

Runs `_rng_replay_child.py` in separate processes of this same binary and compares
the movement-trace digests it prints. Separate processes, not one process reseeded
in a loop, because "replays byte-identically at a fixed seed" is a claim about a
RUN: an in-process A/B cannot see process-global state that survives a reseed, and
would pass for an implementation that only happens to be self-consistent.

Four properties, and the relationship between them is what makes any of them mean
anything:

  1. Same explicit seed, two processes  -> identical digest.
     Vacuous on its own: it passes trivially if the RNG is never consulted.
  2. Two different seeds                -> different digests.
     This is what makes (1) non-vacuous. Without it, (1) is satisfied by a world
     that never moves.
  3. Unseeded runs actually vary        -> different seeds AND different digests.
     This is what makes (4) non-vacuous. Without it, (4) is satisfied by an engine
     that secretly hardcodes one seed and reports it.
  4. An UNSEEDED run reports the seed it generated, and replaying at that reported
     seed in a fresh process reproduces it exactly. Checked with the seed read both
     BEFORE the scenario (materialising it) and AFTER it (once randomness has
     already been consumed) -- a read-back that only works in one order is not a
     read-back.
"""

import os
import subprocess
import sys

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
CHILD = os.path.join(THIS_DIR, "_rng_replay_child.py")

failures = []


def check(condition, message):
    if not condition:
        failures.append(message)
    return condition


def run_child(seed=None, read_order="before"):
    """Run one scenario in a fresh process. Returns (seed, digest, distinct, steps)."""
    env = os.environ.copy()
    env.pop("MCRF_RNG_SEED", None)
    if seed is not None:
        env["MCRF_RNG_SEED"] = str(seed)
    env["MCRF_RNG_READ_ORDER"] = read_order

    # sys.executable is the mcrogueface binary itself when running under --exec.
    proc = subprocess.run(
        [sys.executable, "--headless", "--exec", CHILD],
        capture_output=True, text=True, timeout=60, env=env,
    )
    if proc.returncode != 0:
        raise AssertionError(
            "child exited %d\nstdout:\n%s\nstderr:\n%s"
            % (proc.returncode, proc.stdout, proc.stderr)
        )
    fields = {}
    for line in proc.stdout.splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2 and parts[0] in ("SEED", "DIGEST", "DISTINCT", "STEPS"):
            fields[parts[0]] = parts[1].strip()
    missing = {"SEED", "DIGEST", "DISTINCT", "STEPS"} - set(fields)
    if missing:
        raise AssertionError(
            "child did not report %s\nstdout:\n%s" % (sorted(missing), proc.stdout)
        )
    return (int(fields["SEED"]), fields["DIGEST"],
            int(fields["DISTINCT"]), int(fields["STEPS"]))


# --------------------------------------------------------------------------- #
# 0. The scenario is not a stopped clock.
#
# Every comparison below is between digests of a movement trace. If the world did
# not move, every digest would be the same digest and properties 1 and 4 would hold
# for an engine with no RNG at all. Gate that first, with a number.
# --------------------------------------------------------------------------- #
SEED_A = 20260727
SEED_B = 20260728

a1_seed, a1_digest, a1_distinct, a1_steps = run_child(seed=SEED_A)
check(a1_steps == 40, "scenario must record 40 turns, got %d" % a1_steps)
check(a1_distinct >= 4,
      "entity 0 must actually wander (>= 4 distinct cells in 40 turns), got %d"
      % a1_distinct)
print("scenario: %d turns, entity 0 visited %d distinct cells" % (a1_steps, a1_distinct))

# --------------------------------------------------------------------------- #
# 1. Same explicit seed, two separate processes -> byte-identical trace.
# --------------------------------------------------------------------------- #
a2_seed, a2_digest, a2_distinct, _ = run_child(seed=SEED_A)

check(a1_seed == SEED_A, "run 1 must report the seed it was given: %d" % a1_seed)
check(a2_seed == SEED_A, "run 2 must report the seed it was given: %d" % a2_seed)
check(a1_digest == a2_digest,
      "same seed %d in two processes must produce the same trace: %s vs %s"
      % (SEED_A, a1_digest, a2_digest))
check(a1_distinct == a2_distinct,
      "same seed must visit the same cells: %d vs %d" % (a1_distinct, a2_distinct))
print("replay at seed %d: %s == %s" % (SEED_A, a1_digest[:16], a2_digest[:16]))

# --------------------------------------------------------------------------- #
# 2. Different seeds diverge. This is what makes property 1 mean anything.
# --------------------------------------------------------------------------- #
b_seed, b_digest, _, _ = run_child(seed=SEED_B)
check(b_seed == SEED_B, "run must report the seed it was given: %d" % b_seed)
check(b_digest != a1_digest,
      "seeds %d and %d must produce different traces, both gave %s -- the RNG is "
      "not being consulted, which would make the replay check vacuous"
      % (SEED_A, SEED_B, b_digest))
print("divergence at seed %d: %s != %s" % (SEED_B, b_digest[:16], a1_digest[:16]))

# --------------------------------------------------------------------------- #
# 3. Unseeded runs genuinely vary -- different seeds AND different traces.
#
# This is what makes property 4 non-vacuous. An engine that ignored
# std::random_device and always used seed 42 would satisfy "reports its seed and
# replays" perfectly, and would be exactly the defect #394 describes.
# --------------------------------------------------------------------------- #
unseeded = [run_child(seed=None) for _ in range(3)]
unseeded_seeds = [u[0] for u in unseeded]
unseeded_digests = [u[1] for u in unseeded]

check(len(set(unseeded_seeds)) >= 2,
      "three unseeded runs must not all report the same seed, got %s -- the engine "
      "is using a constant, not generating one" % (unseeded_seeds,))
check(len(set(unseeded_digests)) >= 2,
      "three unseeded runs must not all produce the same trace, got %s"
      % ([d[:16] for d in unseeded_digests],))
check(SEED_A not in unseeded_seeds and SEED_B not in unseeded_seeds,
      "an unseeded run reported a seed from a previous seeded run: %s"
      % (unseeded_seeds,))
print("unseeded runs: seeds %s (%d distinct), %d distinct digests"
      % (unseeded_seeds, len(set(unseeded_seeds)), len(set(unseeded_digests))))

# --------------------------------------------------------------------------- #
# 4. THE ONE MOST LIKELY TO BE SKIPPED: an unseeded run reports the seed it
#    generated, and replaying at that reported seed reproduces it exactly.
#
#    Checked in both read orders. 'before' materialises the seed prior to any
#    consumption; 'after' asks once randomness has already been drawn. If those two
#    disagree, the reported number is not the number in use.
# --------------------------------------------------------------------------- #
for read_order in ("before", "after"):
    u_seed, u_digest, u_distinct, _ = run_child(seed=None, read_order=read_order)
    check(u_distinct >= 4,
          "unseeded run (read %s) must wander, got %d distinct cells"
          % (read_order, u_distinct))

    r_seed, r_digest, r_distinct, _ = run_child(seed=u_seed)
    check(r_seed == u_seed,
          "replay must report the seed it was given: %d vs %d" % (r_seed, u_seed))
    check(r_digest == u_digest,
          "replaying an unseeded run at its own reported seed %d (read %s) must "
          "reproduce it: %s vs %s" % (u_seed, read_order, u_digest, r_digest))
    check(r_distinct == u_distinct,
          "replay visited a different number of cells: %d vs %d"
          % (r_distinct, u_distinct))
    print("unseeded replay (read %s): seed %d, %s == %s"
          % (read_order, u_seed, u_digest[:16], r_digest[:16]))

# --------------------------------------------------------------------------- #
if failures:
    for message in failures:
        print("FAILURE: %s" % message)
    print("%d check(s) did not hold" % len(failures))
    sys.exit(1)

print("PASS: #394 cross-process replay, divergence, and unseeded read-back")
sys.exit(0)
