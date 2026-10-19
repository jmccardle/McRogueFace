"""#519: a map used as its own operand is read as it was before the operation (memmove)."""
import sys
import mcrfpy


def hm_row(vals):
    h = mcrfpy.HeightMap((len(vals), 1))
    for i, v in enumerate(vals):
        h[i, 0] = float(v)
    return h


def hm_vals(h):
    return [h[i, 0] for i in range(h.size[0])]


def dm_row(vals):
    d = mcrfpy.DiscreteMap((len(vals), 1))
    for i, v in enumerate(vals):
        d.set(i, 0, v)
    return d


def dm_vals(d):
    return [d.get(i, 0) for i in range(d.size[0])]


def check(name, got, want):
    if got != want:
        print("FAIL %s: got %r, want %r" % (name, got, want))
        sys.exit(1)


# forward overlap (dest after source): the case that smeared
h = hm_row(range(6)); h.copy_from(h, pos=(1, 0), source_pos=(0, 0), size=(4, 1))
check("hm copy_from forward", hm_vals(h), [0, 0, 1, 2, 3, 5])
# backward overlap
h = hm_row(range(6)); h.copy_from(h, pos=(0, 0), source_pos=(1, 0), size=(4, 1))
check("hm copy_from backward", hm_vals(h), [1, 2, 3, 4, 4, 5])
# another combiner: add reads the pre-operation operand too
h = hm_row([1, 2, 3, 4, 5, 6]); h.add(h, pos=(1, 0), source_pos=(0, 0), size=(4, 1))
check("hm add", hm_vals(h), [1, 3, 5, 7, 9, 6])
h = hm_row([5, 1, 4, 2, 3, 0]); h.max(h, pos=(1, 0), source_pos=(0, 0), size=(4, 1))
check("hm max", hm_vals(h), [5, 5, 4, 4, 3, 0])
# 2D: dest below source
h = mcrfpy.HeightMap((2, 3))
for y in range(3):
    for x in range(2):
        h[x, y] = float(y * 2 + x)
h.copy_from(h, pos=(0, 1), source_pos=(0, 0), size=(2, 2))
check("hm 2d", [h[x, y] for y in range(3) for x in range(2)], [0, 1, 0, 1, 2, 3])

d = dm_row(range(6)); d.copy_from(d, pos=(1, 0), source_pos=(0, 0), size=(4, 1))
check("dm copy_from forward", dm_vals(d), [0, 0, 1, 2, 3, 5])
d = dm_row(range(6)); d.copy_from(d, pos=(0, 0), source_pos=(1, 0), size=(4, 1))
check("dm copy_from backward", dm_vals(d), [1, 2, 3, 4, 4, 5])
d = dm_row([1, 2, 3, 4, 5, 6]); d.add(d, pos=(1, 0), source_pos=(0, 0), size=(4, 1))
check("dm add", dm_vals(d), [1, 3, 5, 7, 9, 6])
d = dm_row([1, 3, 3, 3, 3, 1]); d.bitwise_xor(d, pos=(1, 0), source_pos=(0, 0), size=(4, 1))
check("dm xor", dm_vals(d), [1, 2, 0, 0, 0, 1])

# distinct maps are unaffected
a = hm_row(range(4)); b = hm_row([9, 9, 9, 9]); a.copy_from(b)
check("distinct", hm_vals(a), [9, 9, 9, 9])
print("PASS")
sys.exit(0)
