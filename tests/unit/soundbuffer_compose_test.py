"""Test SoundBuffer composition (concat, mix)."""
import mcrfpy
import sys

# Create test buffers
a = mcrfpy.SoundBuffer.tone(440, 0.3, "sine")
b = mcrfpy.SoundBuffer.tone(880, 0.2, "sine")
c = mcrfpy.SoundBuffer.tone(660, 0.4, "square")

# Test 1: concat two buffers
result = mcrfpy.SoundBuffer.concat([a, b])
assert result is not None
expected = a.duration + b.duration
assert abs(result.duration - expected) < 0.02, f"Expected ~{expected:.3f}s, got {result.duration:.3f}s"
print(f"PASS: concat([0.3s, 0.2s]) -> {result.duration:.3f}s")

# Test 2: concat three buffers
result3 = mcrfpy.SoundBuffer.concat([a, b, c])
expected3 = a.duration + b.duration + c.duration
assert abs(result3.duration - expected3) < 0.03
print(f"PASS: concat([0.3s, 0.2s, 0.4s]) -> {result3.duration:.3f}s")

# Test 3: concat with crossfade overlap
overlapped = mcrfpy.SoundBuffer.concat([a, b], overlap=0.05)
# Duration should be about 0.05s shorter than without overlap
expected_overlap = a.duration + b.duration - 0.05
assert abs(overlapped.duration - expected_overlap) < 0.03, \
    f"Expected ~{expected_overlap:.3f}s, got {overlapped.duration:.3f}s"
print(f"PASS: concat with overlap=0.05 -> {overlapped.duration:.3f}s")

# Test 4: mix two buffers
mixed = mcrfpy.SoundBuffer.mix([a, b])
assert mixed is not None
# mix pads to longest buffer
assert abs(mixed.duration - max(a.duration, b.duration)) < 0.02
print(f"PASS: mix([0.3s, 0.2s]) -> {mixed.duration:.3f}s (padded to longest)")

# Test 5: mix same duration buffers
d = mcrfpy.SoundBuffer.tone(440, 0.5, "sine")
e = mcrfpy.SoundBuffer.tone(660, 0.5, "sine")
mixed2 = mcrfpy.SoundBuffer.mix([d, e])
assert abs(mixed2.duration - 0.5) < 0.02
print(f"PASS: mix([0.5s, 0.5s]) -> {mixed2.duration:.3f}s")

# Test 6: concat empty list raises ValueError
try:
    mcrfpy.SoundBuffer.concat([])
    assert False, "Should have raised ValueError"
except ValueError:
    pass
print("PASS: concat([]) raises ValueError")

# Test 7: mix empty list raises ValueError
try:
    mcrfpy.SoundBuffer.mix([])
    assert False, "Should have raised ValueError"
except ValueError:
    pass
print("PASS: mix([]) raises ValueError")

# Test 8: concat with non-SoundBuffer raises TypeError
try:
    mcrfpy.SoundBuffer.concat([a, "not a buffer"])
    assert False, "Should have raised TypeError"
except TypeError:
    pass
print("PASS: concat with invalid types raises TypeError")

# Test 9: concat single buffer returns copy
single = mcrfpy.SoundBuffer.concat([a])
assert abs(single.duration - a.duration) < 0.02
print("PASS: concat single buffer works")

# Test 10: mix single buffer returns copy
single_mix = mcrfpy.SoundBuffer.mix([a])
assert abs(single_mix.duration - a.duration) < 0.02
print("PASS: mix single buffer works")

print("\nAll soundbuffer_compose tests passed!")
sys.exit(0)
