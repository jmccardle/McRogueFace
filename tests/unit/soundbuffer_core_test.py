"""Test SoundBuffer core creation and properties."""
import mcrfpy
import sys
import struct

# Test 1: SoundBuffer type exists
assert hasattr(mcrfpy, 'SoundBuffer'), "mcrfpy.SoundBuffer not found"
print("PASS: SoundBuffer type exists")

# Test 2: from_samples factory
# Create 1 second of silence (44100 mono samples of int16 zeros)
sample_rate = 44100
channels = 1
num_samples = sample_rate  # 1 second
raw_data = b'\x00\x00' * num_samples  # int16 zeros
buf = mcrfpy.SoundBuffer.from_samples(raw_data, channels, sample_rate)
assert buf is not None
print("PASS: from_samples creates SoundBuffer")

# Test 3: Properties
assert abs(buf.duration - 1.0) < 0.01, f"Expected ~1.0s duration, got {buf.duration}"
assert buf.sample_count == num_samples, f"Expected {num_samples} samples, got {buf.sample_count}"
assert buf.sample_rate == sample_rate, f"Expected {sample_rate} rate, got {buf.sample_rate}"
assert buf.channels == channels, f"Expected {channels} channels, got {buf.channels}"
print("PASS: Properties correct (duration, sample_count, sample_rate, channels)")

# Test 4: sfxr_params is None for non-sfxr buffer
assert buf.sfxr_params is None
print("PASS: sfxr_params is None for non-sfxr buffer")

# Test 5: repr works
r = repr(buf)
assert "SoundBuffer" in r
assert "duration" in r
print(f"PASS: repr = {r}")

# Test 6: from_samples with actual waveform data
# Generate a 440Hz sine wave, 0.5 seconds
import math
num_samples2 = int(sample_rate * 0.5)
samples = []
for i in range(num_samples2):
    t = i / sample_rate
    val = int(32000 * math.sin(2 * math.pi * 440 * t))
    samples.append(val)
raw = struct.pack(f'<{num_samples2}h', *samples)
buf2 = mcrfpy.SoundBuffer.from_samples(raw, 1, 44100)
assert abs(buf2.duration - 0.5) < 0.01
print("PASS: from_samples with sine wave data")

# Test 7: stereo from_samples
stereo_samples = b'\x00\x00' * (44100 * 2)  # 1 second stereo
buf3 = mcrfpy.SoundBuffer.from_samples(stereo_samples, 2, 44100)
assert buf3.channels == 2
assert abs(buf3.duration - 1.0) < 0.01
print("PASS: Stereo from_samples")

print("\nAll soundbuffer_core tests passed!")
sys.exit(0)
