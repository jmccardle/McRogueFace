"""Test Sound integration with SoundBuffer."""
import mcrfpy
import sys

# Test 1: Sound accepts SoundBuffer
buf = mcrfpy.SoundBuffer.tone(440, 0.5, "sine")
sound = mcrfpy.Sound(buf)
assert sound is not None
print("PASS: Sound(SoundBuffer) works")

# Test 2: Sound.buffer returns the SoundBuffer
got_buf = sound.buffer
assert got_buf is not None
assert abs(got_buf.duration - buf.duration) < 0.02
print("PASS: sound.buffer returns SoundBuffer")

# Test 3: Sound.pitch property
assert sound.pitch == 1.0, f"Default pitch should be 1.0, got {sound.pitch}"
sound.pitch = 1.5
assert abs(sound.pitch - 1.5) < 0.001
sound.pitch = 1.0
print("PASS: sound.pitch get/set")

# Test 4: Sound.play_varied (in headless mode, just verifies no crash)
sound.play_varied(pitch_range=0.1, volume_range=3.0)
print("PASS: sound.play_varied() works")

# Test 5: Sound from SoundBuffer has duration
assert sound.duration > 0
print(f"PASS: Sound from SoundBuffer has duration {sound.duration:.3f}s")

# Test 6: Sound from SoundBuffer has source '<SoundBuffer>'
assert sound.source == "<SoundBuffer>"
print("PASS: Sound.source is '<SoundBuffer>' for buffer-created sounds")

# Test 7: Backward compatibility - Sound still accepts string
# File may not exist, so we test that a string is accepted (not TypeError)
# and that RuntimeError is raised for missing files
sound2 = None
try:
    sound2 = mcrfpy.Sound("test.ogg")
    print("PASS: Sound(str) backward compatible (file loaded)")
except RuntimeError:
    # File doesn't exist - that's fine, the important thing is it accepted a string
    print("PASS: Sound(str) backward compatible (raises RuntimeError for missing file)")

# Test 8: Sound from SoundBuffer - standard playback controls
sound.volume = 75.0
assert abs(sound.volume - 75.0) < 0.1
sound.loop = True
assert sound.loop == True
sound.loop = False
print("PASS: Standard playback controls work with SoundBuffer")

# Test 9: sfxr buffer -> Sound pipeline
sfx = mcrfpy.SoundBuffer.sfxr("coin", seed=42)
coin_sound = mcrfpy.Sound(sfx)
assert coin_sound is not None
assert coin_sound.duration > 0
print(f"PASS: sfxr -> Sound pipeline ({coin_sound.duration:.3f}s)")

# Test 10: Effect chain -> Sound pipeline
processed = mcrfpy.SoundBuffer.tone(440, 0.3, "saw").low_pass(2000).normalize()
proc_sound = mcrfpy.Sound(processed)
assert proc_sound is not None
assert proc_sound.duration > 0
print(f"PASS: Effects -> Sound pipeline ({proc_sound.duration:.3f}s)")

# Test 11: Sound with invalid argument type
try:
    mcrfpy.Sound(42)
    assert False, "Should have raised TypeError"
except TypeError:
    pass
print("PASS: Sound(int) raises TypeError")

# Test 12: Sound.buffer is None for file-loaded sounds
if sound2 is not None:
    assert sound2.buffer is None
    print("PASS: Sound.buffer is None for file-loaded sounds")
else:
    print("PASS: Sound.buffer test skipped (file not available)")

print("\nAll soundbuffer_sound tests passed!")
sys.exit(0)
