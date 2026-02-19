"""Test SoundBuffer tone generation."""
import mcrfpy
import sys

# Test 1: Basic sine tone
buf = mcrfpy.SoundBuffer.tone(440, 0.5, "sine")
assert buf is not None
assert abs(buf.duration - 0.5) < 0.02, f"Expected ~0.5s, got {buf.duration}"
assert buf.sample_rate == 44100
assert buf.channels == 1
print("PASS: Sine tone 440Hz 0.5s")

# Test 2: Square wave
buf = mcrfpy.SoundBuffer.tone(220, 0.3, "square")
assert abs(buf.duration - 0.3) < 0.02
print("PASS: Square wave")

# Test 3: Saw wave
buf = mcrfpy.SoundBuffer.tone(330, 0.2, "saw")
assert abs(buf.duration - 0.2) < 0.02
print("PASS: Saw wave")

# Test 4: Triangle wave
buf = mcrfpy.SoundBuffer.tone(550, 0.4, "triangle")
assert abs(buf.duration - 0.4) < 0.02
print("PASS: Triangle wave")

# Test 5: Noise
buf = mcrfpy.SoundBuffer.tone(1000, 0.1, "noise")
assert abs(buf.duration - 0.1) < 0.02
print("PASS: Noise")

# Test 6: ADSR envelope
buf = mcrfpy.SoundBuffer.tone(440, 1.0, "sine",
    attack=0.1, decay=0.2, sustain=0.5, release=0.3)
assert abs(buf.duration - 1.0) < 0.02
print("PASS: ADSR envelope")

# Test 7: Custom sample rate
buf = mcrfpy.SoundBuffer.tone(440, 0.5, "sine", sample_rate=22050)
assert buf.sample_rate == 22050
assert abs(buf.duration - 0.5) < 0.02
print("PASS: Custom sample rate")

# Test 8: Invalid waveform raises ValueError
try:
    mcrfpy.SoundBuffer.tone(440, 0.5, "invalid_waveform")
    assert False, "Should have raised ValueError"
except ValueError:
    pass
print("PASS: Invalid waveform raises ValueError")

# Test 9: Negative duration raises ValueError
try:
    mcrfpy.SoundBuffer.tone(440, -0.5, "sine")
    assert False, "Should have raised ValueError"
except ValueError:
    pass
print("PASS: Negative duration raises ValueError")

# Test 10: Samples are non-zero (tone actually generates audio)
buf = mcrfpy.SoundBuffer.tone(440, 0.1, "sine")
# In headless mode, sample_count should be nonzero
assert buf.sample_count > 0, "Expected non-zero sample count"
print(f"PASS: Tone has {buf.sample_count} samples")

print("\nAll soundbuffer_tone tests passed!")
sys.exit(0)
