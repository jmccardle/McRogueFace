"""#461: SoundBuffer.from_samples(b"") memcpy'd from a null pointer, and a trailing
partial sample or frame was dropped silently. Data must now be a non-empty whole
number of frames (channels * 2 bytes); anything else raises ValueError."""
import sys

import mcrfpy

failures = []


def expect_value_error(data, channels, label):
    try:
        mcrfpy.SoundBuffer.from_samples(data, channels, 44100)
    except ValueError as e:
        print(f"ok: {label} -> ValueError: {e}")
        return
    failures.append(label)
    print(f"FAIL: {label} was accepted")


expect_value_error(b"", 1, "empty data")
expect_value_error(b"\x00", 1, "one byte, mono")
expect_value_error(b"\x00\x00\x00", 1, "1.5 samples, mono")
expect_value_error(b"\x00\x00", 2, "one sample, stereo")
expect_value_error(b"\x00" * 6, 2, "1.5 frames, stereo")

buf = mcrfpy.SoundBuffer.from_samples(b"\x00\x00" * 4410, 1, 44100)
if abs(buf.duration - 0.1) > 1e-6:
    failures.append("mono duration")
    print(f"FAIL: 4410 mono samples gave duration {buf.duration}")
buf = mcrfpy.SoundBuffer.from_samples(b"\x00\x00" * 4, 2, 44100)
if buf.channels != 2:
    failures.append("stereo")
    print("FAIL: two stereo frames")

if failures:
    sys.exit(1)
print("PASS")
sys.exit(0)
