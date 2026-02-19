"""Test SoundBuffer DSP effects."""
import mcrfpy
import sys

# Create a test buffer: 0.5s 440Hz sine
src = mcrfpy.SoundBuffer.tone(440, 0.5, "sine")

# Test 1: pitch_shift
higher = src.pitch_shift(2.0)
assert higher is not None
assert higher.sample_count > 0
# Higher pitch = shorter duration
assert higher.duration < src.duration, f"pitch_shift(2.0) should be shorter: {higher.duration} vs {src.duration}"
print(f"PASS: pitch_shift(2.0) -> {higher.duration:.3f}s (was {src.duration:.3f}s)")

lower = src.pitch_shift(0.5)
assert lower.duration > src.duration, f"pitch_shift(0.5) should be longer: {lower.duration} vs {src.duration}"
print(f"PASS: pitch_shift(0.5) -> {lower.duration:.3f}s")

# Test 2: low_pass
lp = src.low_pass(500.0)
assert lp is not None
assert lp.sample_count == src.sample_count
assert lp.duration == src.duration
print("PASS: low_pass preserves sample count and duration")

# Test 3: high_pass
hp = src.high_pass(500.0)
assert hp is not None
assert hp.sample_count == src.sample_count
print("PASS: high_pass preserves sample count")

# Test 4: echo
echoed = src.echo(200.0, 0.4, 0.5)
assert echoed is not None
assert echoed.sample_count == src.sample_count  # same length
print("PASS: echo works")

# Test 5: reverb
reverbed = src.reverb(0.8, 0.5, 0.3)
assert reverbed is not None
assert reverbed.sample_count == src.sample_count
print("PASS: reverb works")

# Test 6: distortion
dist = src.distortion(2.0)
assert dist is not None
assert dist.sample_count == src.sample_count
print("PASS: distortion works")

# Test 7: bit_crush
crushed = src.bit_crush(8, 4)
assert crushed is not None
assert crushed.sample_count == src.sample_count
print("PASS: bit_crush works")

# Test 8: normalize
normed = src.normalize()
assert normed is not None
assert normed.sample_count == src.sample_count
print("PASS: normalize works")

# Test 9: reverse
rev = src.reverse()
assert rev is not None
assert rev.sample_count == src.sample_count
print("PASS: reverse preserves sample count")

# Test 10: slice
sliced = src.slice(0.1, 0.3)
assert sliced is not None
expected_duration = 0.2
assert abs(sliced.duration - expected_duration) < 0.02, f"Expected ~{expected_duration}s, got {sliced.duration}s"
print(f"PASS: slice(0.1, 0.3) -> {sliced.duration:.3f}s")

# Test 11: slice out of bounds is safe
empty = src.slice(0.5, 0.5)  # zero-length
assert empty.sample_count == 0
print("PASS: slice with start==end returns empty")

# Test 12: Chaining effects (effects return new buffers)
chained = src.low_pass(1000).distortion(1.5).normalize()
assert chained is not None
assert chained.sample_count > 0
print("PASS: Chaining effects works")

# Test 13: Effects don't modify original
orig_count = src.sample_count
src.pitch_shift(2.0)
assert src.sample_count == orig_count, "Original should not be modified"
print("PASS: Effects don't modify original buffer")

# Test 14: pitch_shift with invalid factor raises ValueError
try:
    src.pitch_shift(-1.0)
    assert False, "Should have raised ValueError"
except ValueError:
    pass
print("PASS: pitch_shift with negative factor raises ValueError")

print("\nAll soundbuffer_effects tests passed!")
sys.exit(0)
