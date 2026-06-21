"""fuzz_audio_dsp - SoundBuffer DSP chain fuzzing (#312, Tier B).

Targets the 14 signal-processing methods + factory/composition entry points
on mcrfpy.SoundBuffer. None of these were exercised by the #283 harness.

Surface (verified against src/PySoundBuffer.cpp and src/audio/AudioEffects.cpp):
    Factories : from_samples(data:y*, channels:II), tone(...), sfxr(...)
    Compose   : concat([...], overlap), mix([...])
    Effects   : pitch_shift, low_pass, high_pass, echo, reverb, distortion,
                bit_crush, gain, normalize, reverse, slice, sfxr_mutate
    Props     : duration, sample_count, sample_rate, channels, sfxr_params

Why it bites: the AudioEffects math runs on a CPU vector<int16_t> with several
unguarded divisions by sample_rate and no NaN/inf clamping on most parameters
(echo feedback, reverb room/damping, distortion drive, lp/hp cutoff). Extreme
and special-float parameters are deliberately injected to flush out UB.

No audio device or GL context is needed -- this is pure buffer math, so it runs
in the windowless fuzz build. Contract: fuzz_one_input(data: bytes) -> None.
"""

import mcrfpy

from fuzz_common import ByteStream, EXPECTED_EXCEPTIONS, safe_reset

MAX_OPS = 24

WAVEFORMS = ("sine", "square", "saw", "triangle", "noise", "bogus", "")
SFXR_PRESETS = ("coin", "laser", "explosion", "powerup", "hurt", "jump",
                "blip", "not_a_preset", "")


def weird_float(stream):
    """A float that is sometimes a special value (inf/-inf/nan) or extreme."""
    sel = stream.u8() % 8
    if sel == 0:
        return float("inf")
    if sel == 1:
        return float("-inf")
    if sel == 2:
        return float("nan")
    if sel == 3:
        return 0.0
    if sel == 4:
        return stream.float_in_range(-1e9, 1e9)
    if sel == 5:
        return stream.float_in_range(-1.0, 1.0)
    if sel == 6:
        return -stream.float_in_range(0.0, 1e6)
    return stream.float_in_range(0.0, 1000.0)


def weird_int(stream):
    sel = stream.u8() % 5
    if sel == 0:
        return 0
    if sel == 1:
        return -stream.int_in_range(0, 1_000_000)
    if sel == 2:
        return stream.int_in_range(0, 32)
    if sel == 3:
        return stream.int_in_range(0, 1_000_000)
    return stream.int_in_range(-5, 20)


def make_from_samples(stream):
    """Build a SoundBuffer from raw fuzzer bytes interpreted as int16 PCM."""
    n = stream.int_in_range(0, 4096)
    raw = stream.take(n)
    channels = stream.int_in_range(0, 4)        # 0 -> ValueError (guarded)
    rate = stream.pick_one((0, 1, 8000, 22050, 44100, 48000, 96000))
    return mcrfpy.SoundBuffer.from_samples(raw, channels, rate)


def make_tone(stream):
    freq = weird_float(stream)
    dur = stream.float_in_range(0.0, 0.2)       # keep buffers small/fast
    wave = stream.pick_one(WAVEFORMS)
    return mcrfpy.SoundBuffer.tone(
        freq, dur, wave,
        stream.float_in_range(-0.1, 0.5),       # attack
        stream.float_in_range(-0.1, 0.5),       # decay
        stream.float_in_range(-0.5, 2.0),       # sustain
        stream.float_in_range(-0.1, 0.5),       # release
        stream.pick_one((0, 1, 8000, 44100)),   # sample_rate
    )


def make_sfxr(stream):
    if stream.bool():
        return mcrfpy.SoundBuffer.sfxr(stream.pick_one(SFXR_PRESETS),
                                       stream.u32() if stream.bool() else None)
    # Custom-parameter mode: 24 floats, several pushed to extremes.
    params = tuple(weird_float(stream) for _ in range(24))
    return mcrfpy.SoundBuffer.sfxr(None, None, *params)


FACTORIES = (make_from_samples, make_tone, make_sfxr)


def make_buffer(stream):
    """Return a SoundBuffer or None (never raises out)."""
    factory = stream.pick_one(FACTORIES)
    try:
        return factory(stream)
    except EXPECTED_EXCEPTIONS:
        return None


def apply_effect(stream, buf):
    """Apply one randomly chosen effect, returning the (possibly new) buffer."""
    which = stream.u8() % 12
    try:
        if which == 0:
            return buf.pitch_shift(weird_float(stream))
        if which == 1:
            return buf.low_pass(weird_float(stream))
        if which == 2:
            return buf.high_pass(weird_float(stream))
        if which == 3:
            return buf.echo(weird_float(stream), weird_float(stream), weird_float(stream))
        if which == 4:
            return buf.reverb(weird_float(stream), weird_float(stream), weird_float(stream))
        if which == 5:
            return buf.distortion(weird_float(stream))
        if which == 6:
            return buf.bit_crush(weird_int(stream), weird_int(stream))
        if which == 7:
            return buf.gain(weird_float(stream))
        if which == 8:
            return buf.normalize()
        if which == 9:
            return buf.reverse()
        if which == 10:
            return buf.slice(weird_float(stream), weird_float(stream))
        return buf.sfxr_mutate(weird_float(stream),
                               stream.u32() if stream.bool() else None)
    except EXPECTED_EXCEPTIONS:
        return buf


def read_props(buf):
    for name in ("duration", "sample_count", "sample_rate", "channels", "sfxr_params"):
        try:
            _ = getattr(buf, name)
        except EXPECTED_EXCEPTIONS:
            pass


def fuzz_compose(stream, pool):
    """Exercise concat/mix over a list of accumulated buffers."""
    if not pool:
        return None
    k = stream.int_in_range(0, len(pool))
    chosen = [pool[stream.int_in_range(0, len(pool) - 1)] for _ in range(k)]
    try:
        if stream.bool():
            return mcrfpy.SoundBuffer.concat(chosen, weird_float(stream))
        return mcrfpy.SoundBuffer.mix(chosen)
    except EXPECTED_EXCEPTIONS:
        return None


def fuzz_one_input(data):
    stream = ByteStream(data)
    pool = []
    try:
        n = stream.int_in_range(1, MAX_OPS)
        for _ in range(n):
            if stream.remaining < 1:
                break
            choice = stream.u8() % 5
            if choice == 0 or not pool:
                buf = make_buffer(stream)
                if buf is not None:
                    read_props(buf)
                    if len(pool) < 6:
                        pool.append(buf)
            elif choice == 1:
                buf = fuzz_compose(stream, pool)
                if buf is not None and len(pool) < 6:
                    pool.append(buf)
            else:
                # Apply a chain of effects to an existing buffer.
                buf = pool[stream.int_in_range(0, len(pool) - 1)]
                chain = stream.int_in_range(1, 4)
                for _ in range(chain):
                    buf = apply_effect(stream, buf)
                    if buf is None:
                        break
                if buf is not None:
                    read_props(buf)
    except EXPECTED_EXCEPTIONS:
        pass
