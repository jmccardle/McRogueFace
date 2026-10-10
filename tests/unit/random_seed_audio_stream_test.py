"""
#394 -- Sound.play_varied() draws from the seeded AUDIO stream, and that stream is
independent of the entity-behaviour stream.

Two separate claims, and the second is the one that makes a seeded engine usable:

  * play_varied is reproducible at a fixed seed. It used to draw from a private
    function-local `static std::mt19937` seeded from std::random_device -- the same
    defect as the behaviour RNG, in a second place.
  * the AUDIO and BEHAVIOR streams do not perturb each other. If both drew from one
    generator, whether a run played a sound would silently change how entities
    moved, so an audio-on and an audio-off run at the same seed would be different
    worlds and nothing in either would say so.

play_varied() plays the draw on its own voice and leaves the sound's pitch/volume
alone (#407), so its return value is the only observable record of the draw; without
it there is nothing here to assert on. The draw happens with audio off too (the
suite's --headless default, #406), which is what keeps the streams aligned.
"""

import sys

import mcrfpy

failures = []


def check(condition, message):
    if not condition:
        failures.append(message)
    return condition


# --------------------------------------------------------------------------- #
# Fixture. The buffer takes its own explicit seed, so the sound itself is fixed and
# only the playback variation is under test.
#
# volume is set to 50, NOT left at the default 100. play_varied clamps volume to
# [0, 100], and at 100 every positive draw clamps back to exactly 100.0 -- so the
# volume half of the comparison would be constant and would agree no matter what
# the RNG did. That is the vacuous-assertion trap, and 50 is the fix.
# --------------------------------------------------------------------------- #
buffer = mcrfpy.SoundBuffer.sfxr(preset="blip", seed=1)
sound = mcrfpy.Sound(buffer)
sound.volume = 50.0
sound.pitch = 1.0

DRAWS = 8
PITCH_RANGE = 0.5
VOLUME_RANGE = 20.0


def draw_batch(n=DRAWS):
    return [sound.play_varied(pitch_range=PITCH_RANGE, volume_range=VOLUME_RANGE)
            for _ in range(n)]


# --------------------------------------------------------------------------- #
# 1. play_varied reports the draw, and the draw is a real one.
# --------------------------------------------------------------------------- #
mcrfpy.set_random_seed(11)
batch = draw_batch()

check(all(isinstance(v, tuple) and len(v) == 2 for v in batch),
      "play_varied must return a (pitch, volume) tuple, got %r" % (batch[0],))
check(all(isinstance(v[0], float) and isinstance(v[1], float) for v in batch),
      "play_varied must return floats, got %r" % (batch[0],))

pitches = {v[0] for v in batch}
volumes = {v[1] for v in batch}
check(len(pitches) >= 2,
      "%d draws produced one pitch (%r) -- nothing varies, so every equality below "
      "would be vacuous" % (DRAWS, pitches))
check(len(volumes) >= 2,
      "%d draws produced one volume (%r) -- nothing varies, so every equality below "
      "would be vacuous (is the clamp at 100 swallowing the draw?)" % (DRAWS, volumes))
check(all(abs(p - 1.0) <= PITCH_RANGE + 1e-6 for p in pitches),
      "a drawn pitch left the requested range: %r" % (sorted(pitches),))
check(all(abs(v - 50.0) <= VOLUME_RANGE + 1e-6 for v in volumes),
      "a drawn volume left the requested range: %r" % (sorted(volumes),))
print("play_varied: %d draws, %d distinct pitches, %d distinct volumes"
      % (DRAWS, len(pitches), len(volumes)))

# The sound's own properties are restored, so the return value really is the only
# record -- this is the documented contract and the reason the return value exists.
check(abs(sound.pitch - 1.0) < 1e-6,
      "play_varied left pitch at %r instead of restoring 1.0" % (sound.pitch,))
check(abs(sound.volume - 50.0) < 1e-6,
      "play_varied left volume at %r instead of restoring 50.0" % (sound.volume,))

# --------------------------------------------------------------------------- #
# 2. Reproducible at a fixed seed, and divergent at a different one.
# --------------------------------------------------------------------------- #
mcrfpy.set_random_seed(11)
batch_again = draw_batch()
check(batch_again == batch,
      "same seed produced different playback variation:\n  %r\n  %r"
      % (batch, batch_again))

mcrfpy.set_random_seed(12)
batch_other = draw_batch()
check(batch_other != batch,
      "seeds 11 and 12 produced identical playback variation -- the AUDIO stream is "
      "not being consulted, which would make the replay check vacuous")
print("audio replay holds at seed 11 and diverges at seed 12")

# --------------------------------------------------------------------------- #
# 3. Stream independence, checked in BOTH directions.
#
# Direction A: drawing audio randomness must not shift the behaviour trace.
# Direction B: running behaviour must not shift the audio draws.
#
# A single shared generator would fail both. Two generators seeded from one master
# seed pass both, which is the property that lets an audio-on and an audio-off run
# be compared at the same seed.
# --------------------------------------------------------------------------- #
GRID_W, GRID_H = 13, 9
TURNS = 20
STARTS = [
    (2, 1, mcrfpy.Behavior.NOISE4),
    (9, 6, mcrfpy.Behavior.NOISE8),
    (11, 2, mcrfpy.Behavior.NOISE4),
]


def run_scenario(interleave_audio=False):
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
    for _ in range(TURNS):
        if interleave_audio:
            sound.play_varied(pitch_range=PITCH_RANGE, volume_range=VOLUME_RANGE)
        grid.step()
        trace.append(tuple((e.cell_x, e.cell_y) for e in entities))
    return trace


SEED = 4242

mcrfpy.set_random_seed(SEED)
trace_silent = run_scenario(interleave_audio=False)

mcrfpy.set_random_seed(SEED)
trace_noisy = run_scenario(interleave_audio=True)

check(len({row[0] for row in trace_silent}) >= 4,
      "the scenario must move for the independence check to mean anything, entity 0 "
      "visited %d cells" % len({row[0] for row in trace_silent}))
check(trace_silent == trace_noisy,
      "playing sounds changed the entity trace -- the AUDIO and BEHAVIOR streams "
      "are coupled, so an audio-on run and an audio-off run at the same seed are "
      "different worlds")
print("direction A: %d audio draws interleaved, behaviour trace unchanged" % TURNS)

mcrfpy.set_random_seed(SEED)
audio_alone = draw_batch()

mcrfpy.set_random_seed(SEED)
run_scenario(interleave_audio=False)
audio_after_behaviour = draw_batch()

check(audio_alone == audio_after_behaviour,
      "running entity behaviour changed the audio draws -- the streams are coupled")
print("direction B: %d turns of behaviour executed, audio draws unchanged" % TURNS)

# --------------------------------------------------------------------------- #
if failures:
    for message in failures:
        print("FAILURE: %s" % message)
    print("%d check(s) did not hold" % len(failures))
    sys.exit(1)

print("PASS: #394 audio stream seeding and stream independence")
sys.exit(0)
