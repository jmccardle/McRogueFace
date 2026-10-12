"""
#409 -- EngineRandom derives each subsystem stream from the master seed, and the
header claims the streams are decorrelated. Nothing gated it: replacing
`seed_seq{master, i}` with `seed_seq{master}` (every stream = the same raw mt19937
sequence) passed the whole suite.

The gate is a distribution-free dependence test, so it encodes no libstdc++
distribution internals. Over a fixed range of master seeds, record the BEHAVIOR
stream's first moves (an open-arena NOISE8 entity: the move delta *is* the
candidate index, 0..7) and the AUDIO stream's first draws (Sound.play_varied
pitch and volume, binned into 8 bins), then chi-square every behavior-vs-audio
pair as an 8x8 contingency table. Every pairing is checked, not just draw #1 vs
draw #1, so a stream that is merely a shifted copy of the other (the raw outputs
are consumed at different rates by the two distributions) is caught too.

Fully deterministic: fixed seeds, no wall clock. Under independence the statistic
for df=49 stays around 49 +- 10; the bound is 130 (p ~ 1e-8), while correlated
streams give values in the thousands.
"""
import sys
import mcrfpy

N_SEEDS = 3000
BINS = 8
TURNS = 3
CHI2_BOUND = 130.0
SIZE = 41

DIRS8 = [(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (1, -1), (-1, 1), (1, 1)]

grid = mcrfpy.GridData(grid_size=(SIZE, SIZE))
for y in range(SIZE):
    for x in range(SIZE):
        p = grid.at(x, y)
        p.walkable = True
        p.transparent = True
start = (SIZE // 2, SIZE // 2)
entity = mcrfpy.Entity(start, grid=grid)
entity.set_behavior(mcrfpy.Behavior.NOISE8)
entity.move_speed = 0

sound = mcrfpy.Sound(mcrfpy.SoundBuffer.sfxr(preset="blip", seed=1))
sound.volume = 50.0
sound.pitch = 1.0
PR, VR = 0.5, 20.0


def bin_of(value, centre, half):
    b = int((value - centre + half) / (2 * half) * BINS)
    return min(max(b, 0), BINS - 1)


def sample(seed):
    mcrfpy.set_random_seed(seed)
    entity.cell_pos = start
    moves = []
    for _ in range(TURNS):
        before = (entity.cell_x, entity.cell_y)
        grid.step()
        d = (entity.cell_x - before[0], entity.cell_y - before[1])
        moves.append(DIRS8.index(d))
    audio = []
    for _ in range(TURNS):
        pitch, vol = sound.play_varied(pitch_range=PR, volume_range=VR)
        audio.append(bin_of(pitch, 1.0, PR))
        audio.append(bin_of(vol, 50.0, VR))
    return moves, audio


rows = [sample(seed) for seed in range(N_SEEDS)]


def chi2(xs, ys):
    table = [[0] * BINS for _ in range(BINS)]
    for x, y in zip(xs, ys):
        table[x][y] += 1
    n = len(xs)
    rs = [sum(r) for r in table]
    cs = [sum(table[i][j] for i in range(BINS)) for j in range(BINS)]
    total = 0.0
    for i in range(BINS):
        for j in range(BINS):
            e = rs[i] * cs[j] / n
            if e > 0:
                total += (table[i][j] - e) ** 2 / e
    return total


failures = []
worst = 0.0
for bi in range(TURNS):
    xs = [r[0][bi] for r in rows]
    # non-vacuous: the behaviour series must actually spread over the bins
    if len(set(xs)) < BINS:
        failures.append("behaviour draw %d used only %d of %d moves" % (bi, len(set(xs)), BINS))
    for ai in range(2 * TURNS):
        ys = [r[1][ai] for r in rows]
        if len(set(ys)) < BINS:
            failures.append("audio draw %d used only %d of %d bins" % (ai, len(set(ys)), BINS))
        c = chi2(xs, ys)
        worst = max(worst, c)
        if c > CHI2_BOUND:
            failures.append("behaviour draw %d vs audio draw %d: chi2=%.1f > %.0f "
                            "(streams are dependent)" % (bi, ai, c, CHI2_BOUND))

# Streams must also not be identical at the raw level for one seed: two audio-visible
# sequences differing from the behaviour ones is covered above; additionally adjacent
# master seeds must not give the same first behaviour move more often than chance.
same = sum(1 for a, b in zip(rows, rows[1:]) if a[0][0] == b[0][0]) / (N_SEEDS - 1)
if abs(same - 1.0 / BINS) > 0.04:
    failures.append("adjacent seeds share first move with rate %.3f, expected ~%.3f"
                    % (same, 1.0 / BINS))

print("worst chi2 over %d pairings: %.1f (bound %.0f)" % (TURNS * 2 * TURNS, worst, CHI2_BOUND))
if failures:
    for f in failures:
        print("FAILURE:", f)
    sys.exit(1)
print("PASS")
sys.exit(0)
