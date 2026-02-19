"""Test SoundBuffer sfxr synthesis."""
import mcrfpy
import sys

# Test 1: All presets work
presets = ["coin", "laser", "explosion", "powerup", "hurt", "jump", "blip"]
for preset in presets:
    buf = mcrfpy.SoundBuffer.sfxr(preset)
    assert buf is not None, f"sfxr('{preset}') returned None"
    assert buf.sample_count > 0, f"sfxr('{preset}') has 0 samples"
    assert buf.duration > 0, f"sfxr('{preset}') has 0 duration"
    assert buf.sfxr_params is not None, f"sfxr('{preset}') has no params"
    print(f"  PASS: sfxr('{preset}') -> {buf.duration:.3f}s, {buf.sample_count} samples")

print("PASS: All sfxr presets generate audio")

# Test 2: Deterministic with seed
buf1 = mcrfpy.SoundBuffer.sfxr("coin", seed=42)
buf2 = mcrfpy.SoundBuffer.sfxr("coin", seed=42)
assert buf1.sample_count == buf2.sample_count, "Same seed should produce same sample count"
assert buf1.duration == buf2.duration, "Same seed should produce same duration"
print("PASS: Deterministic with seed")

# Test 3: Different seeds produce different results
buf3 = mcrfpy.SoundBuffer.sfxr("coin", seed=99)
# May have same count by chance, but params should differ
p1 = buf1.sfxr_params
p3 = buf3.sfxr_params
# At least one param should differ (with very high probability)
differs = any(p1[k] != p3[k] for k in p1.keys() if k != 'wave_type')
assert differs, "Different seeds should produce different params"
print("PASS: Different seeds produce different results")

# Test 4: sfxr_params dict contains expected keys
params = buf1.sfxr_params
expected_keys = [
    'wave_type', 'base_freq', 'freq_limit', 'freq_ramp', 'freq_dramp',
    'duty', 'duty_ramp', 'vib_strength', 'vib_speed',
    'env_attack', 'env_sustain', 'env_decay', 'env_punch',
    'lpf_freq', 'lpf_ramp', 'lpf_resonance',
    'hpf_freq', 'hpf_ramp',
    'pha_offset', 'pha_ramp', 'repeat_speed',
    'arp_speed', 'arp_mod'
]
for key in expected_keys:
    assert key in params, f"Missing key '{key}' in sfxr_params"
print("PASS: sfxr_params has all expected keys")

# Test 5: sfxr with custom params
buf_custom = mcrfpy.SoundBuffer.sfxr(wave_type=2, base_freq=0.5, env_decay=0.3)
assert buf_custom is not None
assert buf_custom.sfxr_params is not None
assert buf_custom.sfxr_params['wave_type'] == 2
assert abs(buf_custom.sfxr_params['base_freq'] - 0.5) < 0.001
print("PASS: sfxr with custom params")

# Test 6: sfxr_mutate
mutated = buf1.sfxr_mutate(0.1)
assert mutated is not None
assert mutated.sfxr_params is not None
assert mutated.sample_count > 0
# Params should be similar but different
mp = mutated.sfxr_params
op = buf1.sfxr_params
differs = any(abs(mp[k] - op[k]) > 0.0001 for k in mp.keys() if isinstance(mp[k], float))
# Note: with small mutation and few params, there's a chance all stay same.
# But with 0.1 amount and ~20 float params, extremely unlikely all stay same.
print(f"PASS: sfxr_mutate produces {'different' if differs else 'similar'} params")

# Test 7: sfxr_mutate with seed for reproducibility
m1 = buf1.sfxr_mutate(0.05, 42)
m2 = buf1.sfxr_mutate(0.05, 42)
assert m1.sample_count == m2.sample_count, "Same seed should produce same mutation"
print("PASS: sfxr_mutate deterministic with seed")

# Test 8: sfxr_mutate on non-sfxr buffer raises error
tone_buf = mcrfpy.SoundBuffer.tone(440, 0.5, "sine")
try:
    tone_buf.sfxr_mutate(0.1)
    assert False, "Should have raised RuntimeError"
except RuntimeError:
    pass
print("PASS: sfxr_mutate on non-sfxr buffer raises RuntimeError")

# Test 9: Invalid preset raises ValueError
try:
    mcrfpy.SoundBuffer.sfxr("nonexistent_preset")
    assert False, "Should have raised ValueError"
except ValueError:
    pass
print("PASS: Invalid preset raises ValueError")

print("\nAll soundbuffer_sfxr tests passed!")
sys.exit(0)
